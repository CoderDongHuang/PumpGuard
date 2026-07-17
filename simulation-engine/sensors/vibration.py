"""
振动传感器仿真：生成振动频谱数据

输出：三轴振动 RMS 值 (mm/s) + 频谱特征频率列表
参考：PumpSpectra (Adaika 2025) / NASA IMS 数据集振动特征
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class VibrationReading:
    """单次振动读数"""
    rms_x: float       # X 轴 RMS (mm/s)
    rms_y: float       # Y 轴 RMS (mm/s)
    rms_z: float       # Z 轴 RMS (mm/s)
    rms_overall: float # 总 RMS
    peak_frequencies: Dict[float, float]  # 频率(Hz) → 幅度(dB)
    crest_factor: float  # 波峰因子


class VibrationSensor:
    """
    振动传感器仿真

    信号模型：
      signal(t) = base + degradation + fault_signature + noise
    """

    def __init__(self, noise_std: float = 0.15, rng: np.random.Generator = None):
        self.noise_std = noise_std
        self.rng = rng or np.random.default_rng()

    def simulate(self, theoretical_rms: float, degradation_offset: float,
                 fault_signature: Dict[float, float], speed: float) -> VibrationReading:
        """
        仿真一次振动测量

        Args:
            theoretical_rms: 物理模型给出的理论振动 RMS
            degradation_offset: 退化导致的振动增量
            fault_signature: 故障特征频率 dict
            speed: 当前转速 (RPM)
        """
        # 基础振动 + 退化增量
        base_rms = theoretical_rms + degradation_offset

        # 三轴分量（随机分配，Z 轴通常略低）
        weights = np.array([0.40, 0.38, 0.22]) + self.rng.uniform(-0.05, 0.05, 3)
        weights = weights / weights.sum()

        # 加噪声
        rms_x = base_rms * weights[0] + self.rng.normal(0, self.noise_std)
        rms_y = base_rms * weights[1] + self.rng.normal(0, self.noise_std)
        rms_z = base_rms * weights[2] + self.rng.normal(0, self.noise_std * 0.7)

        # 确保正值
        rms_x = max(0.1, rms_x)
        rms_y = max(0.1, rms_y)
        rms_z = max(0.1, rms_z)

        rms_overall = np.sqrt(rms_x**2 + rms_y**2 + rms_z**2)

        # 构建频谱特征频率
        peak_freqs = self._build_spectrum(speed, fault_signature)

        # 波峰因子 (正常 ≈ 3-5，有冲击故障时增大)
        crest_factor = 3.5 + self.rng.uniform(-0.5, 0.5)
        if fault_signature:
            crest_factor += max(fault_signature.values()) / 10.0

        return VibrationReading(
            rms_x=round(rms_x, 3),
            rms_y=round(rms_y, 3),
            rms_z=round(rms_z, 3),
            rms_overall=round(rms_overall, 3),
            peak_frequencies=peak_freqs,
            crest_factor=round(crest_factor, 2),
        )

    def _build_spectrum(self, speed: float, fault_signature: Dict[float, float]) -> Dict[float, float]:
        """构建振动频谱特征频率"""
        f1x = speed / 60.0  # 1× 转频

        peaks = {
            f1x: round(0.0 + self.rng.uniform(-2, 2), 1),          # 1× RPM
            f1x * 2: round(-6.0 + self.rng.uniform(-3, 3), 1),     # 2× RPM
            f1x * 3: round(-12.0 + self.rng.uniform(-3, 3), 1),    # 3× RPM
        }

        # 叠加故障特征频率
        for freq, db_gain in fault_signature.items():
            peaks[freq] = peaks.get(freq, -20.0) + db_gain

        # 加噪声
        for freq in peaks:
            peaks[freq] += self.rng.uniform(-1, 1)

        return {round(k, 1): round(v, 1) for k, v in peaks.items()}
