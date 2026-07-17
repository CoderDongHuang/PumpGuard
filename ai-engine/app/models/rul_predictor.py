"""
剩余寿命 RUL 预测引擎

方法（与架构说明书 3.2.3 一致）：
  1. HI 退化趋势外推（指数/线性拟合 → 失效阈值）
  2. 同型号相似性匹配（后续实现）

默认失效阈值：HI < 30
"""

import numpy as np
from typing import List
from scipy.optimize import curve_fit


class RULPredictor:
    """RUL 预测器"""

    FAILURE_THRESHOLD = 30.0   # HI < 30 → 失效
    MIN_HI_SEQUENCE = 7        # 最少需要 7 天的 HI 数据

    def predict(self, req) -> "RULResponse":
        """
        RUL 预测

        输入：最近 30 天 HI 序列
        输出：预估剩余天数 + 80% 置信区间
        """
        hi_seq = req.hi_sequence

        if len(hi_seq) < self.MIN_HI_SEQUENCE:
            return self._insufficient_data(req.device_id)

        # 清洗：去除明显的异常跳变（中值滤波）
        hi_clean = self._median_filter(hi_seq, window=3)

        # ── 1. 线性外推 ─────────────────────────────────────────
        linear_days = self._linear_extrapolate(hi_clean)

        # ── 2. 指数外推 ─────────────────────────────────────────
        exp_days = self._exponential_extrapolate(hi_clean)

        # ── 3. 融合 ─────────────────────────────────────────────
        # 取两者的加权平均（指数模型更能体现加速退化趋势）
        if exp_days > 0 and linear_days > 0:
            # 如果指数模型预测更短（加速退化）→ 偏向指数
            if exp_days < linear_days:
                estimated = exp_days * 0.7 + linear_days * 0.3
            else:
                estimated = exp_days * 0.5 + linear_days * 0.5
        elif exp_days > 0:
            estimated = exp_days
        elif linear_days > 0:
            estimated = linear_days
        else:
            estimated = 999  # 无退化趋势

        # 80% 置信区间
        margin = estimated * 0.3
        lower = max(1, estimated - margin)
        upper = estimated + margin

        from app.main import RULResponse
        return RULResponse(
            device_id=req.device_id,
            estimated_rul_days=round(estimated, 1),
            confidence_interval=[round(lower, 1), round(upper, 1)],
        )

    # ── 外推方法 ─────────────────────────────────────────────────

    def _linear_extrapolate(self, hi_seq: List[float]) -> float:
        """线性拟合外推至失效阈值"""
        x = np.arange(len(hi_seq))
        y = np.array(hi_seq)

        if len(x) < 2:
            return -1

        # 最小二乘线性拟合
        A = np.vstack([x, np.ones(len(x))]).T
        slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]

        if slope >= 0:  # HI 在上升或稳定 → 不预测
            return 999

        # 计算到达 HI=30 需要的天数
        days_to_failure = (self.FAILURE_THRESHOLD - intercept) / slope
        # 减去已经过去的天数
        remaining = days_to_failure - len(hi_seq)

        return max(1, remaining) if remaining > 0 else -1

    def _exponential_extrapolate(self, hi_seq: List[float]) -> float:
        """指数拟合外推至失效阈值"""
        x = np.arange(len(hi_seq))
        y = np.array(hi_seq)

        if len(x) < 3:
            return -1

        # 指数模型：HI(t) = a * exp(b * t) + c
        try:
            popt, _ = curve_fit(
                lambda t, a, b, c: a * np.exp(b * t) + c,
                x, y,
                p0=[60, -0.01, 30],
                maxfev=5000,
                bounds=([0, -0.5, 0], [200, 0.01, 100]),
            )
            a, b, c = popt

            if b >= 0:  # 退化不加速 → 不能用指数模型
                return -1

            # 解 HI(t) = 30 → t = ln((30-c)/a) / b
            if (self.FAILURE_THRESHOLD - c) / a > 0:
                t_failure = np.log((self.FAILURE_THRESHOLD - c) / a) / b
                remaining = t_failure - len(hi_seq)
                return max(1, remaining)
            else:
                return -1
        except Exception:
            return -1

    # ── 辅助 ─────────────────────────────────────────────────────

    def _median_filter(self, data: List[float], window: int = 3) -> List[float]:
        """中值滤波去噪"""
        if len(data) < window:
            return data
        result = data.copy()
        half = window // 2
        for i in range(half, len(data) - half):
            result[i] = np.median(data[i - half: i + half + 1])
        return result

    def _insufficient_data(self, device_id: str):
        from app.main import RULResponse
        return RULResponse(
            device_id=device_id,
            estimated_rul_days=999,
            confidence_interval=[999, 999],
        )
