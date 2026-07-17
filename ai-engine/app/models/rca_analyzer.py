"""
根因分析引擎

方法：故障特征库 + 因果推理
输出：可能故障原因（排序）+ 置信度 + 建议处置方案

与架构说明书 3.2.4 完全对齐。
"""

from typing import List, Dict


class RCAAnalyzer:
    """根因分析器"""

    def __init__(self):
        self.fault_library = self._build_library()

    def _build_library(self) -> List[Dict]:
        """
        故障特征库

        每条记录：故障类型 → 特征条件 → 置信度权重 → 建议方案
        """
        return [
            {
                "cause": "轴承内圈磨损",
                "fault_type": "bearing_inner_race_wear",
                "features": {
                    "vibration_peak_abnormal": True,
                    "crest_factor_high": True,
                    "temperature_high": True,
                },
                "confidence_weight": 0.90,
                "suggested_action": "更换轴承，参考备件编号 SKF-6305，预计工时 4 小时",
                "spare_parts": ["轴承 SKF-6305", "密封垫片", "润滑脂"],
            },
            {
                "cause": "轴承外圈磨损",
                "fault_type": "bearing_outer_race_wear",
                "features": {
                    "vibration_peak_abnormal": True,
                    "crest_factor_high": True,
                    "temperature_high": False,
                },
                "confidence_weight": 0.85,
                "suggested_action": "检查轴承外圈跑道，必要时更换轴承组件，预计工时 3 小时",
                "spare_parts": ["轴承组件", "润滑脂"],
            },
            {
                "cause": "叶轮气蚀",
                "fault_type": "impeller_cavitation",
                "features": {
                    "vibration_hf_high": True,
                    "pressure_unstable": True,
                    "flow_below_rated": True,
                },
                "confidence_weight": 0.80,
                "suggested_action": "检查进口压力、NPSH 裕量，修复/更换叶轮，预计工时 6 小时",
                "spare_parts": ["叶轮", "口环", "密封件"],
            },
            {
                "cause": "泵与电机不对中",
                "fault_type": "misalignment",
                "features": {
                    "vibration_2x_high": True,
                    "vibration_high_rms": True,
                    "temperature_high": True,
                },
                "confidence_weight": 0.92,
                "suggested_action": "激光对中仪校正联轴器，预计工时 2 小时",
                "spare_parts": ["联轴器弹性体", "地脚螺栓垫片"],
            },
            {
                "cause": "机械密封泄漏",
                "fault_type": "seal_leakage",
                "features": {
                    "pressure_declining": True,
                    "vibration_normal": True,
                    "flow_declining": True,
                },
                "confidence_weight": 0.75,
                "suggested_action": "更换机械密封，检查轴套磨损，预计工时 4 小时",
                "spare_parts": ["机械密封组件", "轴套", "O 型圈"],
            },
            {
                "cause": "电机定子绕组故障",
                "fault_type": "motor_electrical_fault",
                "features": {
                    "current_thd_high": True,
                    "temperature_winding_high": True,
                },
                "confidence_weight": 0.88,
                "suggested_action": "检查绕组绝缘，做耐压测试，必要时送修或更换电机，预计工时 8 小时",
                "spare_parts": ["电机定子", "绝缘材料", "接线端子"],
            },
            {
                "cause": "转子不平衡",
                "fault_type": "unbalance",
                "features": {
                    "vibration_1x_high": True,
                    "vibration_2x_normal": True,
                },
                "confidence_weight": 0.85,
                "suggested_action": "叶轮动平衡校正，预计工时 3 小时",
                "spare_parts": ["平衡配重块"],
            },
        ]

    def analyze(self, req) -> "RCAResponse":
        """
        根因分析

        1. 提取当前传感器特征
        2. 遍历故障特征库 → 计算匹配度
        3. 排序输出
        """
        data = req.current_data
        features = self._extract_features(data)

        results = []
        for fault in self.fault_library:
            match_score = self._match_features(fault["features"], features)
            if match_score > 0.3:
                results.append({
                    "cause": fault["cause"],
                    "fault_type": fault["fault_type"],
                    "confidence": round(fault["confidence_weight"] * match_score, 2),
                    "suggested_action": fault["suggested_action"],
                    "spare_parts": fault["spare_parts"],
                })

        # 按置信度降序
        results.sort(key=lambda x: x["confidence"], reverse=True)

        from app.main import RCAResponse
        return RCAResponse(
            device_id=req.device_id,
            root_causes=results[:3] if results else [
                {
                    "cause": "待人工诊断",
                    "confidence": 0.0,
                    "suggested_action": "特征不匹配任何已知故障模式，建议现场工程师检查",
                    "spare_parts": [],
                }
            ],
        )

    def _extract_features(self, data) -> dict:
        """从传感器数据提取特征"""
        features = {}

        # 振动
        vib = data.vibration if hasattr(data, 'vibration') else data.get("vibration", {})
        if vib:
            features["vibration_high_rms"] = vib.get("rms_overall", 0) > 6.0
            features["crest_factor_high"] = vib.get("crest_factor", 3.5) > 4.0
            peaks = vib.get("peak_frequencies", {})
            features["vibration_peak_abnormal"] = any(v > 3.0 for v in peaks.values())
            features["vibration_hf_high"] = features["vibration_peak_abnormal"]  # 近似
            features["vibration_1x_high"] = features["vibration_peak_abnormal"]
            features["vibration_2x_high"] = len(peaks) >= 2
            features["vibration_2x_normal"] = not features["vibration_2x_high"]
            features["vibration_normal"] = not features["vibration_peak_abnormal"]

        # 电流
        cur = data.current if hasattr(data, 'current') else data.get("current", {})
        if cur:
            features["current_thd_high"] = cur.get("thd", 3.0) > 8.0

        # 温度
        thm = data.thermal if hasattr(data, 'thermal') else data.get("thermal", {})
        if thm:
            features["temperature_high"] = thm.get("bearing_temp", 25) > 50
            features["temperature_winding_high"] = thm.get("winding_temp", 30) > 65

        # 压力
        pres = data.pressure if hasattr(data, 'pressure') else data.get("pressure", {})
        if pres:
            features["pressure_unstable"] = False   # 需要历史数据，默认 false
            features["pressure_declining"] = False

        # 流量
        features["flow_below_rated"] = data.flow_rate < 30 if hasattr(data, 'flow_rate') else False
        features["flow_declining"] = False

        return features

    def _match_features(self, conditions: dict, features: dict) -> float:
        """计算特征匹配度"""
        if not conditions:
            return 0.0

        matched = 0
        total = len(conditions)
        for key, expected_value in conditions.items():
            actual = features.get(key)
            if actual is not None and actual == expected_value:
                matched += 1

        return matched / max(total, 1)
