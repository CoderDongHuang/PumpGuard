"""
PumpGuard AI Engine — FastAPI 入口

四核心服务：
  - HI 计算 (健康指数)
  - 故障预测
  - RUL 预测 (剩余寿命)
  - 根因分析

与架构说明书 3.2 节完全对齐。
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import time

from app.models.hi_calculator import HICalculator
from app.models.fault_predictor import FaultPredictor
from app.models.rul_predictor import RULPredictor
from app.models.rca_analyzer import RCAAnalyzer

app = FastAPI(
    title="PumpGuard AI Engine",
    description="水泵智慧预测与健康管理 AI 引擎",
    version="1.0.0",
)

# 延迟加载模型（首次请求时初始化）
hi_calc: Optional[HICalculator] = None
fault_pred: Optional[FaultPredictor] = None
rul_pred: Optional[RULPredictor] = None
rca_analyzer: Optional[RCAAnalyzer] = None


def _ensure_models():
    """确保模型已加载"""
    global hi_calc, fault_pred, rul_pred, rca_analyzer
    if hi_calc is None:
        hi_calc = HICalculator()
        fault_pred = FaultPredictor()
        rul_pred = RULPredictor()
        rca_analyzer = RCAAnalyzer()


# ─── Request / Response Models ─────────────────────────────────────

class SensorData(BaseModel):
    """单次传感器读数（与仿真引擎输出格式一致）"""
    timestamp: str
    device_id: str
    device_type: str = "smart"
    pump_type: str = "centrifugal_small"
    health_index: Optional[float] = None
    vibration: dict = {}
    current: dict = {}
    thermal: dict = {}
    pressure: dict = {}
    flow_rate: float = 0.0
    rotation_speed: float = 0.0


class HIRequest(BaseModel):
    """HI 计算请求"""
    device_id: str
    pump_specs: dict = Field(..., description="含 rated_flow/rated_head/rated_efficiency/rated_power/rated_speed")
    current_data: SensorData
    history: Optional[List[SensorData]] = None


class HIResponse(BaseModel):
    device_id: str
    health_index: float = Field(..., ge=0, le=100)
    grade: str                     # 健康 / 关注 / 警告 / 严重 / 危险
    sub_scores: Dict[str, float]   # 各子维度得分
    degradation_rate: float        # HI 变化率/天


class FaultRequest(BaseModel):
    """故障预测请求"""
    device_id: str
    sensor_sequence: List[SensorData] = Field(..., description="最近 30 天传感器数据序列")


class FaultResponse(BaseModel):
    device_id: str
    predictions: List[Dict] = Field(..., description="[{fault_type, probability, warning_days}]")


class RULRequest(BaseModel):
    """RUL 预测请求"""
    device_id: str
    pump_type: str
    hi_sequence: List[float] = Field(..., description="最近 30 天 HI 序列")


class RULResponse(BaseModel):
    device_id: str
    estimated_rul_days: float
    confidence_interval: List[float]  # [lower, upper]


class RCARequest(BaseModel):
    """根因分析请求"""
    device_id: str
    current_data: SensorData
    hi_sub_scores: Optional[Dict[str, float]] = None


class RCAResponse(BaseModel):
    device_id: str
    root_causes: List[Dict]  # [{cause, confidence, suggested_action}]


class FeedbackRequest(BaseModel):
    """维修反馈请求"""
    device_id: str
    ai_diagnosis: str           # AI 原始诊断
    actual_fault: str           # 实际故障
    is_correct: bool            # AI 诊断是否正确
    timestamp: str


# ─── API Routes ────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "pumpguard-ai-engine"}


@app.post("/api/v1/hi/compute", response_model=HIResponse)
async def compute_hi(req: HIRequest):
    """
    健康指数计算

    基于 Q-H-η 物理基线 + 数据偏差融合
    HI = f(ΔV_振动, Δη_效率, ΔT_温升, t_运行时长)
    """
    _ensure_models()
    try:
        return hi_calc.compute(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/fault/predict", response_model=FaultResponse)
async def predict_fault(req: FaultRequest):
    """
    故障预测

    LSTM/Transformer 时序模型 + 机理规则联合判定
    """
    _ensure_models()
    try:
        return fault_pred.predict(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/rul/predict", response_model=RULResponse)
async def predict_rul(req: RULRequest):
    """
    剩余寿命预测

    HI 退化趋势外推 + 同型号相似性匹配
    """
    _ensure_models()
    try:
        return rul_pred.predict(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/rca/analyze", response_model=RCAResponse)
async def analyze_root_cause(req: RCARequest):
    """
    根因分析

    故障特征库 + 因果推理
    """
    _ensure_models()
    try:
        return rca_analyzer.analyze(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/model/update")
async def update_model(req: FeedbackRequest):
    """
    模型在线更新（反馈闭环入口）

    维修工程师反馈 → 增量学习 → 模型版本升级
    """
    _ensure_models()
    try:
        # 存储反馈数据
        from app.ml.update import store_feedback
        store_feedback(req)

        # 累计足够反馈后触发增量训练
        from app.ml.update import maybe_trigger_retraining
        result = maybe_trigger_retraining()
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
