"""
温度传感器仿真：生成轴承/绕组温度读数
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class ThermalReading:
    """单次温度读数"""
    bearing_temp: float      # 轴承温度 (°C)
    winding_temp: float      # 绕组温度 (°C)
    ambient_temp: float      # 环境温度 (°C)


class ThermalSensor:
    """温度传感器仿真"""

    def __init__(self, noise_std: float = 0.5, rng: np.random.Generator = None):
        self.noise_std = noise_std
        self.rng = rng or np.random.default_rng()

    def simulate(self, theoretical_rise: float, degradation_offset: float,
                 fault_offset: float, ambient_temp: float = 25.0) -> ThermalReading:
        """
        仿真一次温度测量

        Args:
            theoretical_rise: 物理模型给出的理论温升
            degradation_offset: 退化导致的温升增量
            fault_offset: 故障导致的额外温升
            ambient_temp: 环境温度
        """
        # 轴承温度 = 环境 + 理论温升 + 退化 + 故障 + 噪声
        bearing = ambient_temp + theoretical_rise + degradation_offset + fault_offset
        bearing += self.rng.normal(0, self.noise_std)

        # 绕组温度通常比轴承高 10-20°C
        winding = bearing + 12.0 + self.rng.uniform(-3, 3)

        return ThermalReading(
            bearing_temp=round(bearing, 1),
            winding_temp=round(winding, 1),
            ambient_temp=round(ambient_temp + self.rng.uniform(-1, 1), 1),
        )
