"""
故障预测引擎

方法：机理规则 + 数据驱动联合判定
  - 机理规则层（优先实现）：基于振动频谱特征频率 + 电流特征
  - 数据驱动层（后续实现）：LSTM/Transformer 时序预测

与架构说明书 3.2.2 完全对齐。
"""

import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime


class FaultPredictor:
    """故障预测器"""

    def __init__(self):
        # 初始化机理规则库（替代 DL 模型，Demo 阶段先用规则）
        self.rules = self._build_rule_base()

    def _build_rule_base(self) -> List[Dict]:
        """
        故障特征规则库

        每条规则定义：
          - fault_type: 故障类型
          - conditions: 判定条件（振动/电流/温度/压力的特征）
          - base_probability: 满足条件时的基础概率
        """
        return [
            {
                "fault_type": "bearing_inner_race_wear",
                "conditions": {
                    "vibration_peak_ratio": 0.4,    # BPFI 分量 > 基线 × 1.4 = 6dB
                    "crest_factor_min": 3.8,
                    "temp_rise_threshold": 8.0,      # 额外温升 > 8°C
                },
                "base_probability": 0.85,
                "warning_days": 14,
            },
            {
                "fault_type": "bearing_outer_race_wear",
                "conditions": {
                    "vibration_peak_ratio": 0.35,    # BPFO 分量 > 基线 × 1.35 = 5dB
                    "crest_factor_min": 3.5,
                    "temp_rise_threshold": 6.0,
                },
                "base_probability": 0.80,
                "warning_days": 14,
            },
            {
                "fault_type": "impeller_cavitation",
                "conditions": {
                    "vibration_hf_energy_ratio": 0.3,   # 5-20 kHz 频段能量占比 > 30%
                    "pressure_fluctuation_min": 0.5,     # 出口压力波动 > 0.5 bar
                },
                "base_probability": 0.75,
                "warning_days": 7,
            },
            {
                "fault_type": "misalignment",
                "conditions": {
                    "vibration_2x_ratio": 0.5,   # 2× 转频分量 > 1× 的 50%
                    "vibration_rms_threshold": 6.0,
                },
                "base_probability": 0.90,
                "warning_days": 21,
            },
            {
                "fault_type": "seal_leakage",
                "conditions": {
                    "pressure_trend_decline": 0.1,   # 压力持续下降趋势
                    "no_vibration_signature": True,
                },
                "base_probability": 0.70,
                "warning_days": 10,
            },
            {
                "fault_type": "motor_electrical_fault",
                "conditions": {
                    "current_thd_min": 10.0,          # 电流 THD > 10%
                    "current_sideband_present": True,  # 存在故障旁瓣
                },
                "base_probability": 0.85,
                "warning_days": 7,
            },
        ]

    def predict(self, req) -> "FaultResponse":
        """
        故障预测

        1. 提取特征 → 2. 规则匹配 → 3. 概率输出
        """
        if not req.sensor_sequence:
            return self._empty_response(req.device_id)

        latest = req.sensor_sequence[-1]
        features = self._extract_features(req.sensor_sequence)

        predictions = []
        for rule in self.rules:
            prob = self._match_rule(rule, features, latest)
            if prob > 0.3:  # 只返回概率 > 30% 的预测
                predictions.append({
                    "fault_type": rule["fault_type"],
                    "probability": round(prob, 2),
                    "warning_days": rule["warning_days"],
                })

        # 按概率降序排列
        predictions.sort(key=lambda x: x["probability"], reverse=True)

        from app.main import FaultResponse
        return FaultResponse(
            device_id=req.device_id,
            predictions=predictions[:3],  # 只返回 Top-3
        )

    def _extract_features(self, sequence: List) -> Dict:
        """从传感器序列提取特征"""
        if not sequence:
            return {}

        latest = sequence[-1]
        features = {}

        # 振动特征
        vib = latest.vibration if hasattr(latest, 'vibration') else latest.get("vibration", {})
        if vib:
            peaks = vib.get("peak_frequencies", {})
            features["vibration_rms"] = vib.get("rms_overall", 0)
            features["crest_factor"] = vib.get("crest_factor", 3.5)

            # 检测特征频率增强
            if peaks:
                peak_values = list(peaks.values())
                features["max_peak_db"] = max(peak_values)
                features["num_abnormal_peaks"] = sum(1 for v in peak_values if v > 3.0)

        # 电流特征
        cur = latest.current if hasattr(latest, 'current') else latest.get("current", {})
        if cur:
            features["current_thd"] = cur.get("thd", 3.0)
            sidebands = cur.get("sideband_amplitudes", {})
            features["has_current_sidebands"] = len(sidebands) > 2

        # 温度特征
        thm = latest.thermal if hasattr(latest, 'thermal') else latest.get("thermal", {})
        if thm:
            features["bearing_temp"] = thm.get("bearing_temp", 25)

        # 压力特征
        pres = latest.pressure if hasattr(latest, 'pressure') else latest.get("pressure", {})
        if pres:
            features["outlet_pressure"] = pres.get("outlet_bar", 3)

        # 历史趋势
        if len(sequence) >= 3:
            pressures = []
            for s in sequence[-3:]:
                p = s.pressure if hasattr(s, 'pressure') else s.get("pressure", {})
                pressures.append(p.get("outlet_bar", 3) if p else 3)
            features["pressure_trend"] = (pressures[0] - pressures[-1]) / max(1, len(pressures))

        return features

    def _match_rule(self, rule: Dict, features: Dict, latest) -> float:
        """计算规则匹配概率"""
        conditions = rule["conditions"]
        score = 0.0
        matched = 0
        total = len(conditions)

        for key, threshold in conditions.items():
            if key == "vibration_peak_ratio":
                if features.get("max_peak_db", 0) > 3.0:
                    matched += 1
                    actual_ratio = features.get("max_peak_db", 0) / 6.0
                    score += min(1.0, actual_ratio)

            elif key == "crest_factor_min":
                if features.get("crest_factor", 0) > threshold:
                    matched += 1
                    score += min(1.0, features["crest_factor"] / 8.0)

            elif key == "temp_rise_threshold":
                actual_temp = features.get("bearing_temp", 25)
                if actual_temp > 50:  # 轴承温度 > 50°C 视为异常
                    matched += 1
                    score += min(1.0, (actual_temp - 40) / 30.0)

            elif key == "vibration_hf_energy_ratio":
                # 高频振动能量（通过异常峰值数量近似）
                if features.get("num_abnormal_peaks", 0) >= 2:
                    matched += 1
                    score += 0.8

            elif key == "vibration_2x_ratio":
                if features.get("num_abnormal_peaks", 0) >= 1:
                    matched += 1
                    score += 0.7

            elif key == "vibration_rms_threshold":
                if features.get("vibration_rms", 0) > threshold:
                    matched += 1
                    score += min(1.0, features["vibration_rms"] / 12.0)

            elif key == "pressure_trend_decline":
                if features.get("pressure_trend", 0) > threshold:
                    matched += 1
                    score += min(1.0, features["pressure_trend"] / 0.5)

            elif key == "current_thd_min":
                if features.get("current_thd", 0) > threshold:
                    matched += 1
                    score += min(1.0, features["current_thd"] / 20.0)

            elif key == "current_sideband_present":
                if features.get("has_current_sidebands", False):
                    matched += 1
                    score += 0.8

            elif key == "no_vibration_signature":
                # 没有明显振动特征但有压力下降 → 密封泄漏
                if features.get("max_peak_db", 0) < 3.0 and features.get("pressure_trend", 0) > 0.05:
                    matched += 1
                    score += 0.9

        if total == 0:
            return 0.0

        match_ratio = matched / total
        avg_score = score / max(matched, 1)
        probability = rule["base_probability"] * match_ratio * avg_score

        return min(0.99, probability)

    def _empty_response(self, device_id: str):
        from app.main import FaultResponse
        return FaultResponse(device_id=device_id, predictions=[])
