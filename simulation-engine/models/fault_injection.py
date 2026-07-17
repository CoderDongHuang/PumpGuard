"""
故障注入引擎：在正常退化基础上叠加故障特征

支持的故障类型（与架构说明书 1.3 / 开发步骤 1.3 一致）：
  - bearing_inner_race_wear  : 轴承内圈磨损
  - bearing_outer_race_wear  : 轴承外圈磨损
  - impeller_cavitation      : 叶轮气蚀
  - misalignment             : 不对中
  - seal_leakage             : 密封泄漏
  - motor_electrical_fault   : 电机电气故障
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class FaultConfig:
    """单个故障配置"""
    fault_type: str
    onset_day: float                # 故障开始时间 (第 N 天)
    severity: float                 # 0-1，故障严重程度
    progression_rate: float = 0.5   # 故障发展速率 (0=缓慢, 1=快速)


class FaultInjector:
    """
    故障注入器

    每种故障类型影响不同的传感器信号：
      - 振动频谱增加特征频率分量
      - 温度异常升高
      - 出口压力下降（密封泄漏）
      - 电流谐波畸变（电气故障）
    """

    def __init__(self, pump_specs, rng: np.random.Generator):
        self.specs = pump_specs
        self.rng = rng
        self.faults: list[FaultConfig] = []

    def add_fault(self, fault: FaultConfig):
        """添加一个故障"""
        self.faults.append(fault)

    def get_active_faults(self, day: float) -> list[FaultConfig]:
        """获取当天激活的故障列表"""
        active = []
        for f in self.faults:
            if day >= f.onset_day:
                # 故障发展：严重程度随时间增长
                days_since_onset = day - f.onset_day
                ramp_days = 30 * (1.0 - f.progression_rate) + 5  # 快速发展期 5~35 天
                if days_since_onset < ramp_days:
                    factor = days_since_onset / ramp_days
                else:
                    factor = 1.0
                active.append(FaultConfig(
                    fault_type=f.fault_type,
                    onset_day=f.onset_day,
                    severity=f.severity * factor,
                    progression_rate=f.progression_rate,
                ))
        return active

    def get_vibration_fault_signature(self, day: float, base_freqs: dict) -> dict:
        """
        获取故障对应的振动频谱特征

        返回 dict：频率(Hz) → 相对幅度(dB 相对于基线)
        """
        signature = {}
        active_faults = self.get_active_faults(day)
        N = self.specs.rated_speed
        blades = self.specs.num_blades

        for f in active_faults:
            ft = f.fault_type
            sev = f.severity

            if ft == "bearing_inner_race_wear":
                # BPFI = 0.6 × N_blades × RPM/60
                bpfi = 0.6 * blades * N / 60.0
                signature[bpfi] = signature.get(bpfi, 0) + 6 + sev * 18  # 6-24 dB 增强
                # BPFI 谐波
                for k in range(2, 4):
                    signature[bpfi * k] = signature.get(bpfi * k, 0) + 3 + sev * 10

            elif ft == "bearing_outer_race_wear":
                # BPFO = 0.4 × N_blades × RPM/60
                bpfo = 0.4 * blades * N / 60.0
                signature[bpfo] = signature.get(bpfo, 0) + 5 + sev * 15
                for k in range(2, 4):
                    signature[bpfo * k] = signature.get(bpfo * k, 0) + 2 + sev * 8

            elif ft == "impeller_cavitation":
                # 气蚀：5-20 kHz 宽频噪声增强
                for freq in [5000, 8000, 12000, 16000]:
                    signature[freq] = signature.get(freq, 0) + sev * 20  # 0-20 dB

            elif ft == "misalignment":
                # 不对中：1× 和 2× 转频分量增强
                f1x = N / 60.0      # 1× RPM
                f2x = 2 * N / 60.0  # 2× RPM
                signature[f1x] = signature.get(f1x, 0) + 3 + sev * 15
                signature[f2x] = signature.get(f2x, 0) + 5 + sev * 20

        return signature

    def get_temperature_fault_offset(self, day: float) -> float:
        """故障导致的额外温升 (°C)"""
        offset = 0.0
        active_faults = self.get_active_faults(day)
        for f in active_faults:
            if f.fault_type in ("bearing_inner_race_wear", "bearing_outer_race_wear", "misalignment"):
                offset += f.severity * 25.0  # 最高额外 25°C
            elif f.fault_type == "motor_electrical_fault":
                offset += f.severity * 35.0
        return offset

    def get_pressure_fault_offset(self, day: float) -> float:
        """故障导致的出口压力下降 (bar)"""
        offset = 0.0
        active_faults = self.get_active_faults(day)
        for f in active_faults:
            if f.fault_type == "seal_leakage":
                offset += f.severity * 2.0  # 最高下降 2 bar
            elif f.fault_type == "impeller_cavitation":
                offset += f.severity * 0.5  # 轻微压力波动
        return offset

    def get_current_thd_offset(self, day: float) -> float:
        """故障导致的电流谐波畸变率增量 (%)"""
        offset = 0.0
        active_faults = self.get_active_faults(day)
        for f in active_faults:
            if f.fault_type == "motor_electrical_fault":
                offset += f.severity * 15.0  # THD 最高增加 15%
            elif f.fault_type in ("bearing_inner_race_wear", "bearing_outer_race_wear"):
                offset += f.severity * 3.0
        return offset
