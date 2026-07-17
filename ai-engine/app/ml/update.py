"""
模型在线更新模块（反馈闭环核心）

流程：
  维修反馈 → 存储 → 累计 N 条 → 触发增量训练 → 新模型注册 → 影子验证 → 切换

与架构说明书 3.5 节 / 开发步骤 Phase 7 一致。
"""

import json
import os
from pathlib import Path
from datetime import datetime

FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "models_store", "feedback.jsonl")
RETRAIN_THRESHOLD = 10  # 累计 10 条反馈触发重训练


def store_feedback(req):
    """存储维修反馈"""
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    record = {
        "device_id": req.device_id,
        "ai_diagnosis": req.ai_diagnosis,
        "actual_fault": req.actual_fault,
        "is_correct": req.is_correct,
        "timestamp": req.timestamp,
        "recorded_at": datetime.now().isoformat(),
    }
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def count_feedback() -> int:
    """统计累计反馈数"""
    if not os.path.exists(FEEDBACK_FILE):
        return 0
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def load_feedback() -> list:
    """加载全部反馈"""
    if not os.path.exists(FEEDBACK_FILE):
        return []
    records = []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return records


def get_accuracy() -> float:
    """计算 AI 诊断准确率"""
    records = load_feedback()
    if not records:
        return 1.0
    correct = sum(1 for r in records if r.get("is_correct", False))
    return correct / len(records)


def maybe_trigger_retraining() -> dict:
    """
    检查是否需要触发增量训练

    Demo 阶段：简单地返回统计信息，不执行真正的重训练
    后续可以接入：加载反馈 → 生成训练样本 → 微调模型 → MLflow 注册
    """
    total = count_feedback()
    acc = get_accuracy()

    if total >= RETRAIN_THRESHOLD:
        # Demo 阶段：标记为"已触发"，返回统计信息
        return {
            "triggered": True,
            "total_feedback": total,
            "current_accuracy": round(acc, 4),
            "message": f"已收集 {total} 条反馈（准确率 {acc:.1%}），"
                       f"Demo 模式下模型模拟更新完成。"
                       f"生产环境将触发增量训练。",
            "model_version": f"v{total // RETRAIN_THRESHOLD + 1}",
        }
    else:
        return {
            "triggered": False,
            "total_feedback": total,
            "remaining": RETRAIN_THRESHOLD - total,
            "message": f"还需 {RETRAIN_THRESHOLD - total} 条反馈才触发重训练",
        }


def reset_feedback():
    """重置反馈数据（仅测试用）"""
    if os.path.exists(FEEDBACK_FILE):
        os.remove(FEEDBACK_FILE)
