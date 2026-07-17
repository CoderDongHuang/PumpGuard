"""
退化动力学模型：模拟泵设备随时间的自然退化过程

参考：架构说明书 6.2 节
- 振动缓升（指数型）
- 效率缓降（线性型）
- 温度缓升（指数型）
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DegradationParams:
    """退化参数配置（每台泵独立随机初始化，体现制造差异）"""
    vibration_growth_rate: float      # 振动年增长率 (mm/s / year)
    efficiency_decay_rate: float      # 效率年衰减率 (绝对百分点 / year)
    temperature_growth_rate: float    # 温度年增长率 (°C / year)
    initial_health_index: float = 98.0  # 初始 HI (0-100)

    @classmethod
    def random_for_pump(cls, pump_type: str, rng: np.random.Generator) -> "DegradationParams":
        """为某台泵随机生成退化参数"""
        if "centrifugal" in pump_type:
            vib = rng.uniform(0.3, 1.5)
            eff = rng.uniform(0.005, 0.025)
            temp = rng.uniform(0.5, 3.0)
        elif "axial" in pump_type:
            vib = rng.uniform(0.2, 1.0)
            eff = rng.uniform(0.003, 0.020)
            temp = rng.uniform(0.3, 2.0)
        else:
            vib = rng.uniform(0.3, 1.2)
            eff = rng.uniform(0.004, 0.022)
            temp = rng.uniform(0.4, 2.5)

        return cls(
            vibration_growth_rate=vib,
            efficiency_decay_rate=eff,
            temperature_growth_rate=temp,
            initial_health_index=rng.uniform(96.0, 99.5),
        )


class DegradationModel:
    """
    退化模型

    正常退化路径：
      vibration(t) = vibration_theoretical + vib_growth * exp(λ_vib * t/365)
      efficiency(t) = efficiency_theoretical - eff_decay * t/365
      temperature(t) = temperature_theoretical + temp_growth * exp(λ_temp * t/365)

    其中 λ 控制退化加速程度，随机变化体现设备异质性
    """

    def __init__(self, params: DegradationParams, rng: np.random.Generator):
        self.params = params
        self.rng = rng
        # 退化加速因子（体现不同设备差异）
        self.lambda_vib = rng.uniform(1.5, 3.0)
        self.lambda_temp = rng.uniform(1.3, 2.5)

    def get_vibration_offset(self, day: float) -> float:
        """给定运行天数，返回振动退化增量 (mm/s)"""
        if day <= 0:
            return 0.0
        years = day / 365.0
        return self.params.vibration_growth_rate * np.exp(self.lambda_vib * years) - self.params.vibration_growth_rate

    def get_efficiency_decay(self, day: float) -> float:
        """给定运行天数，返回效率退化量 (绝对百分点)"""
        if day <= 0:
            return 0.0
        years = day / 365.0
        return self.params.efficiency_decay_rate * years

    def get_temperature_offset(self, day: float) -> float:
        """给定运行天数，返回温度退化增量 (°C)"""
        if day <= 0:
            return 0.0
        years = day / 365.0
        return self.params.temperature_growth_rate * np.exp(self.lambda_temp * years) - self.params.temperature_growth_rate

    def get_health_index(self, vibration_deviation: float, efficiency_decay: float,
                         temperature_offset: float, running_days: float) -> float:
        """
        根据偏离度计算健康指数 HI (0-100)

        HI = 100 - (W_v × V_score + W_η × E_score + W_T × T_score + W_t × t_score)
        权重与架构说明书 3.2.1 一致：W_v=40, W_η=30, W_T=20, W_t=10
        """
        # 归一化为 0-100 的分数
        v_score = min(100, vibration_deviation / 8.0 * 100)   # 8 mm/s 偏离 → 100 分
        e_score = min(100, efficiency_decay / 0.15 * 100)      # 15% 效率衰减 → 100 分
        t_score = min(100, temperature_offset / 30.0 * 100)    # 30°C 温升 → 100 分
        t_aging = min(100, running_days / 3650 * 100)          # 10 年 → 100 分

        W_v, W_eta, W_T, W_t = 40, 30, 20, 10
        hi = 100 - (W_v * v_score + W_eta * e_score + W_T * t_score + W_t * t_aging) / 100.0
        return max(0.0, min(100.0, hi))
