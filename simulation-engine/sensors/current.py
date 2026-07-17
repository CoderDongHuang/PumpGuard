"""
电流传感器仿真：生成电流波形与频谱特征

用于 MCSA（电机电流特征分析）——老旧泵非侵入式接入的核心技术
参考：PumpSpectra 91.2% 准确率 (Adaika et al., Sensors, 2025)
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class CurrentReading:
    """单次电流读数"""
    rms: float                # 电流有效值 (A)
    thd: float                # 总谐波畸变率 (%)
    frequency: float          # 基频 (Hz)，50 Hz 或根据转速换算
    sideband_amplitudes: dict # 旁瓣频率 → 幅度 (dB)


class CurrentSensor:
    """
    电流传感器仿真

    MCSA 特征频率（与故障注入引擎一致）：
      - 轴承故障：基频 ± BPFI/BPFO 调制
      - 不对中：基频 ± 2× 转频
      - 电气故障：槽通过频率 ± 基频
    """

    def __init__(self, noise_std: float = 0.3, rng: np.random.Generator = None):
        self.noise_std = noise_std
        self.rng = rng or np.random.default_rng()

    def simulate(self, theoretical_current: float, thd_offset: float,
                 fault_signature: dict, speed: float, num_poles: int = 2) -> CurrentReading:
        """
        仿真一次电流测量

        Args:
            theoretical_current: 物理模型给出的理论电流 (A)
            thd_offset: 故障注入的 THD 增量 (%)
            fault_signature: MCSA 旁瓣特征
            speed: 转速 (RPM)
            num_poles: 电机极数
        """
        # 基频 (Hz)
        slip = 0.03  # 假定 3% 转差率
        sync_speed = 120 * 50.0 / num_poles  # 同步转速 (50 Hz 电源)
        actual_freq = 50.0 * (1 - slip * speed / sync_speed) if sync_speed > 0 else 50.0

        # 电流 RMS + 噪声
        rms = theoretical_current + self.rng.normal(0, self.noise_std)
        rms = max(0.5, rms)

        # THD（正常 3-5%，电气故障会增大）
        base_thd = 3.0 + self.rng.uniform(0, 2.0)
        thd = base_thd + thd_offset
        thd = round(min(thd, 30.0), 2)

        # MCSA 旁瓣
        sidebands = self._simulate_sidebands(actual_freq, fault_signature, speed)

        return CurrentReading(
            rms=round(rms, 2),
            thd=thd,
            frequency=round(actual_freq, 2),
            sideband_amplitudes=sidebands,
        )

    def _simulate_sidebands(self, base_freq: float, fault_signature: dict,
                            speed: float) -> dict:
        """生成 MCSA 旁瓣特征（电机电流特征分析的核心）"""
        f_slip = (base_freq - 50.0 * (1 - 0.03)) if abs(base_freq - 50.0) > 0.5 else 0.5
        f_rotor = speed / 60.0  # 转频

        sidebands = {}

        # 正常状态下的旁瓣（非常小）
        # 在故障状态下，特定旁瓣会被 fault_signature 增强

        # 极通过频率 = 转频 × 极对数
        pole_pass_freq = f_rotor * 1  # 2 极电机

        # 轴承故障旁瓣：基频 ± k × 故障特征频率
        for fault_freq, amp in fault_signature.items():
            # 上旁瓣
            upper = base_freq + fault_freq
            # 下旁瓣
            lower = max(0.1, base_freq - fault_freq)
            sidebands[round(upper, 1)] = round(-30 + amp + self.rng.uniform(-2, 2), 1)
            sidebands[round(lower, 1)] = round(-30 + amp * 0.8 + self.rng.uniform(-2, 2), 1)

        return sidebands
