"""
水泵物理模型：Q-H-η 特性曲线建模 + 理论运行参数计算

与架构说明书 3.2.1 一致：
  HI = f(ΔV_振动, Δη_效率, ΔT_温升, t_运行时长)
  物理基线来自 Q-H-η 曲线
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PumpSpecs:
    """水泵额定参数"""
    pump_id: str
    pump_type: str                     # centrifugal_small / centrifugal_large / axial_flow / mixed_flow
    rated_flow: float                  # m³/h
    rated_head: float                  # m
    rated_efficiency: float            # 0-1
    rated_power: float                 # kW
    rated_speed: float                 # RPM
    qh_curve_a: float = 0.0            # Q-H 曲线二次项系数 H = a*Q² + b*Q + c
    qh_curve_b: float = 0.0
    qh_curve_c: float = 0.0
    qe_curve_a: float = 0.0            # Q-η 曲线二次项系数
    qe_curve_b: float = 0.0
    qe_curve_c: float = 0.0
    bearing_type: str = "rolling"      # rolling / sleeve
    num_blades: int = 6
    num_poles: int = 2                 # 电机极数


class PumpPhysicsModel:
    """
    水泵物理模型

    根据 Q-H-η 特性曲线，计算给定工况下的理论运行参数：
      - 理论振动 RMS（基于 ISO 10816 和工况相似性）
      - 理论效率
      - 理论轴承温升
      - 理论电流
    """

    # ISO 10816-7 参考振动限值 (mm/s RMS)  — 用于小型泵 (功率 < 15 kW)
    ISO_VIBRATION_LIMITS = {
        "rigid_foundation": 3.5,     # 刚性基础
        "flexible_foundation": 5.5,  # 柔性基础
    }

    def __init__(self, pump_specs: PumpSpecs):
        self.specs = pump_specs
        self._build_curves()

    def _build_curves(self):
        """根据额定参数构建 Q-H 和 Q-η 特性曲线"""
        Q_r = self.specs.rated_flow
        H_r = self.specs.rated_head
        eta_r = self.specs.rated_efficiency

        # 构造标准抛物线型特性曲线
        # 假设设计点 (Q_r, H_r) 是最高效率点 (BEP)

        # Q-H 曲线: H = a*Q² + b*Q + c
        # 已知：Q=0 时 H=1.15*H_r (关死扬程), Q=Q_r 时 H=H_r, Q=1.2*Q_r 时 H=0.7*H_r
        Q1, H1 = 0.0, 1.15 * H_r
        Q2, H2 = Q_r, H_r
        Q3, H3 = 1.2 * Q_r, 0.7 * H_r

        A = np.array([[Q1**2, Q1, 1], [Q2**2, Q2, 1], [Q3**2, Q3, 1]])
        B = np.array([H1, H2, H3])
        self.specs.qh_curve_a, self.specs.qh_curve_b, self.specs.qh_curve_c = np.linalg.solve(A, B)

        # Q-η 曲线: η = a*Q² + b*Q + c
        # 已知：Q=0 时 η=0, Q=Q_r 时 η=η_r, Q=1.2*Q_r 时 η=0.85*η_r
        A2 = np.array([[Q1**2, Q1, 1], [Q2**2, Q2, 1], [Q3**2, Q3, 1]])
        B2 = np.array([0.0, eta_r, 0.85 * eta_r])
        self.specs.qe_curve_a, self.specs.qe_curve_b, self.specs.qe_curve_c = np.linalg.solve(A2, B2)

    def get_head(self, flow: float) -> float:
        """给定流量，返回理论扬程"""
        a, b, c = self.specs.qh_curve_a, self.specs.qh_curve_b, self.specs.qh_curve_c
        return a * flow**2 + b * flow + c

    def get_efficiency(self, flow: float) -> float:
        """给定流量，返回理论效率"""
        a, b, c = self.specs.qe_curve_a, self.specs.qe_curve_b, self.specs.qe_curve_c
        eta = a * flow**2 + b * flow + c
        return max(0.0, min(eta, self.specs.rated_efficiency))

    def get_theoretical_vibration(self, flow: float, speed: float) -> float:
        """
        计算理论振动 RMS 值 (mm/s)

        基于 ISO 10816-7 和工况相似性：
        - 偏离 BEP 越远，振动越大（水力不平衡）
        - 转速越高，振动基线越高
        """
        Q_r = self.specs.rated_flow
        N_r = self.specs.rated_speed

        # BEP 附近的基准振动
        base_vibration = 1.5 if self.specs.pump_type in ("centrifugal_small", "mixed_flow") else 2.0

        # 偏离 BEP 的振动惩罚
        flow_deviation = abs(flow - Q_r) / Q_r if Q_r > 0 else 0
        flow_penalty = flow_deviation * 3.0  # 偏离 100% = 振动额外增加 3 mm/s

        # 转速影响
        speed_factor = (speed / N_r) ** 1.5

        vibration = (base_vibration + flow_penalty) * speed_factor
        return vibration

    def get_theoretical_temperature_rise(self, flow: float, ambient_temp: float = 25.0) -> float:
        """
        计算理论轴承温升 (°C 高于环境温度)

        基于效率损失转化为热量：
        - 实际效率偏离额定效率越多，温升越大
        - 负载越大，温升基线越高
        """
        eta_actual = self.get_efficiency(flow)
        eta_rated = self.specs.rated_efficiency

        # 效率损失百分比
        eta_loss = max(0, eta_rated - eta_actual)

        # 负载率
        load_ratio = flow / self.specs.rated_flow if self.specs.rated_flow > 0 else 0

        # 温升模型：基线 + 效率损失惩罚
        base_rise = 15.0 + 20.0 * load_ratio
        efficiency_penalty = eta_loss * 80  # 每损失 10% 效率，温升增加 8°C

        return base_rise + efficiency_penalty

    def get_theoretical_current(self, flow: float, speed: float) -> float:
        """
        计算理论电机电流 (A)

        P_hydraulic = ρ × g × Q × H / η
        P_shaft = P_hydraulic / η_motor
        I = P_shaft / (√3 × V × cosφ)
        """
        rho = 1000  # kg/m³
        g = 9.81    # m/s²
        Q_actual = flow / 3600  # m³/h → m³/s
        H_actual = self.get_head(flow)
        eta_actual = max(0.1, self.get_efficiency(flow))

        # 水力功率 (W)
        p_hydraulic = rho * g * Q_actual * H_actual

        # 轴功率 (W)
        motor_efficiency = 0.90  # 假定电机效率 90%
        p_shaft = p_hydraulic / (eta_actual * motor_efficiency)

        # 电流 (A) — 假定 380V 三相，功率因数 0.85
        voltage = 380.0
        power_factor = 0.85
        current = p_shaft / (np.sqrt(3) * voltage * power_factor)

        return current


def make_pump_specs(pump_id: str, pump_type_config: dict) -> PumpSpecs:
    """从配置字典创建 PumpSpecs"""
    return PumpSpecs(
        pump_id=pump_id,
        pump_type=pump_type_config["name"],
        rated_flow=pump_type_config["rated_flow"],
        rated_head=pump_type_config["rated_head"],
        rated_efficiency=pump_type_config["rated_efficiency"],
        rated_power=pump_type_config["rated_power"],
        rated_speed=pump_type_config["rated_speed"],
    )
