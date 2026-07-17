"""
健康指数 HI 计算引擎

HI = f(ΔV_振动, Δη_效率, ΔT_温升, t_运行时长)

物理基线来自 Q-H-η 曲线（水泵物理模型），
数据偏差通过加权融合得到 0-100 分的健康评分。

与架构说明书 3.2.1 完全对齐：
  - 权重 W_v=40, W_η=30, W_T=20, W_t=10
  - HI 分级: 85-100健康, 70-85关注, 50-70警告, 30-50严重, 0-30危险
"""

import math
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime


class HICalculator:
    """健康指数计算器"""

    # 权重（与架构说明书 3.2.1 一致）
    W_VIB = 40   # 振动偏离度权重
    W_EFF = 30   # 效率衰减度权重
    W_TMP = 20   # 温升趋势权重
    W_AGE = 10   # 运行时长老化权重

    # 各维度的最大允许偏离（用于归一化到 0-100 分）
    MAX_VIB_DEVIATION = 8.0     # mm/s — 偏离 8 mm/s → 100 分
    MAX_EFF_DECAY = 0.15        # 15% 效率绝对衰减 → 100 分
    MAX_TEMP_OFFSET = 30.0      # 30°C 额外温升 → 100 分
    MAX_AGE_DAYS = 3650         # 10 年运行 → 100 分

    HI_GRADES = [
        (85, "健康", "正常运行裕度充足，持续监测"),
        (70, "关注", "轻度退化，性能开始偏离基线，计划性检查"),
        (50, "警告", "中度退化，需安排维修，生成工单"),
        (30, "严重", "重度退化，故障概率高，紧急工单 + 备件预警"),
        (0,  "危险", "随时可能失效，立即停机维修"),
    ]

    def compute(self, req) -> "HIResponse":
        """
        计算健康指数

        输入：
          - device_id
          - pump_specs: 含 rated_flow, rated_head, rated_efficiency, rated_power, rated_speed
          - current_data: 最新传感器数据
          - history: 历史数据（用于退化速率计算）

        返回：
          - health_index: 0-100
          - grade: 健康等级
          - sub_scores: 各维度得分
          - degradation_rate: 退化速率 (HI 变化/天)
        """
        specs = req.pump_specs
        data = req.current_data
        history = req.history or []

        # ── 1. 计算各维度偏离度 ──────────────────────────────────

        # 1a. 振动偏离度
        theo_vib = self._estimate_theoretical_vibration(specs, data.flow_rate, data.rotation_speed)
        actual_vib = data.vibration.get("rms_overall", 0)
        vib_deviation = max(0, actual_vib - theo_vib)
        vib_score = min(100, vib_deviation / self.MAX_VIB_DEVIATION * 100)

        # 1b. 效率衰减度
        theo_eff = specs.get("rated_efficiency", 0.75)
        actual_eff = self._estimate_actual_efficiency(data, specs)
        eff_decay = max(0, theo_eff - actual_eff)
        eff_score = min(100, eff_decay / self.MAX_EFF_DECAY * 100)

        # 1c. 温升偏离度
        theo_temp_rise = self._estimate_theoretical_temp_rise(data.flow_rate, specs)
        ambient = data.thermal.get("ambient_temp", 25.0)
        actual_bearing = data.thermal.get("bearing_temp", ambient + 15)
        actual_temp_rise = actual_bearing - ambient
        temp_offset = max(0, actual_temp_rise - theo_temp_rise)
        temp_score = min(100, temp_offset / self.MAX_TEMP_OFFSET * 100)

        # 1d. 运行时长老化
        running_days = self._estimate_running_days(data, history)
        age_score = min(100, running_days / self.MAX_AGE_DAYS * 100)

        # ── 2. 加权融合 ─────────────────────────────────────────
        hi = 100.0 - (
            self.W_VIB * vib_score +
            self.W_EFF * eff_score +
            self.W_TMP * temp_score +
            self.W_AGE * age_score
        ) / 100.0
        hi = max(0.0, min(100.0, hi))

        # ── 3. 退化速率 ─────────────────────────────────────────
        degradation_rate = 0.0
        if history and len(history) >= 2:
            # 取最近两次历史记录计算 HI 变化率
            if hasattr(history[-1], 'health_index') and history[-1].health_index:
                prev_hi = history[-1].health_index
                prev_ts = self._parse_timestamp(history[-1].timestamp)
                curr_ts = self._parse_timestamp(data.timestamp)
                days_diff = max(0.5, (curr_ts - prev_ts).total_seconds() / 86400)
                degradation_rate = (prev_hi - hi) / days_diff

        # ── 4. 确定等级 ─────────────────────────────────────────
        grade, grade_desc, suggestion = "健康", "", ""
        for threshold, g, desc in self.HI_GRADES:
            if hi >= threshold:
                grade, grade_desc = g, desc
                break

        from app.main import HIResponse
        return HIResponse(
            device_id=req.device_id,
            health_index=round(hi, 1),
            grade=grade,
            sub_scores={
                "vibration_score": round(vib_score, 1),
                "efficiency_score": round(eff_score, 1),
                "temperature_score": round(temp_score, 1),
                "aging_score": round(age_score, 1),
            },
            degradation_rate=round(degradation_rate, 2),
        )

    # ── 辅助计算 ─────────────────────────────────────────────────

    def _estimate_theoretical_vibration(self, specs: dict, flow: float, speed: float) -> float:
        """基于 Q-H-η 曲线估算理论振动 RMS"""
        Q_r = specs.get("rated_flow", 100)
        N_r = specs.get("rated_speed", 2900)
        base_vib = 1.5
        flow_dev = abs(flow - Q_r) / max(Q_r, 1)
        flow_penalty = flow_dev * 3.0
        speed_factor = (speed / max(N_r, 1)) ** 1.5
        return (base_vib + flow_penalty) * speed_factor

    def _estimate_actual_efficiency(self, data, specs: dict) -> float:
        """从传感器数据估算实际效率"""
        rho, g = 1000, 9.81
        flow = data.flow_rate / 3600.0 if data.flow_rate > 0 else 0.001
        head = data.pressure.get("outlet_bar", 3.0) / 0.0981 if data.pressure else 30.0
        p_hydraulic = rho * g * flow * head
        power = data.current.get("rms", 10) * 380 * math.sqrt(3) * 0.85 / 1000  # kW
        power = max(0.1, power)
        eff = p_hydraulic / (power * 1000) if power > 0 else 0.7
        return min(0.95, max(0.1, eff))

    def _estimate_theoretical_temp_rise(self, flow: float, specs: dict) -> float:
        """估算理论轴承温升"""
        Q_r = specs.get("rated_flow", 100)
        load_ratio = flow / max(Q_r, 1)
        base_rise = 15.0 + 20.0 * min(load_ratio, 1.2)
        return base_rise

    def _estimate_running_days(self, data, history) -> float:
        """估算累计运行天数"""
        if history and len(history) > 0:
            first = self._parse_timestamp(history[0].timestamp)
            last = self._parse_timestamp(data.timestamp)
            return (last - first).total_seconds() / 86400
        return 0

    @staticmethod
    def _parse_timestamp(ts_str: str) -> datetime:
        """解析 ISO 格式时间戳"""
        try:
            return datetime.fromisoformat(ts_str)
        except Exception:
            return datetime.now()
