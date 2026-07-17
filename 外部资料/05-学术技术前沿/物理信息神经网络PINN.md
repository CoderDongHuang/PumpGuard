# 物理信息神经网络（PINN）与旋转机械 PHM

> Physics-Informed Neural Networks — 将物理规律注入深度学习模型。

---

## 核心综述

### 1. RUL Estimation for Rotating Machinery

| 项目 | 内容 |
|------|------|
| **标题** | "A Comprehensive Review of Remaining Useful Life Estimation Approaches for Rotating Machinery" |
| **作者** | Kumar et al. |
| **期刊** | *Energies*, 2024, 17(22), 5538 |
| **链接** | <https://www.mdpi.com/1996-1073/17/22/5538> |

**核心发现：**
- 系统分析旋转机械（泵、涡轮、压缩机、电机）RUL 估算五阶段：数据采集 → 健康指标构建 → 失效阈值确定 → RUL 估算 → 评估指标
- 明确将 **PINN** 和**迁移学习**列为 RUL 预测前沿方法
- 泵和压缩机因气蚀、腐蚀等特殊失效机制，需要专门的 RUL 方法

### 2. Physics-Informed ML in Condition Monitoring of Rotating Machinery

| 项目 | 内容 |
|------|------|
| **作者** | Wang et al. |
| **平台** | SSRN（预印本） |
| **链接** | <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6691187> |

**核心发现：**
- 系统综述 PIML 在旋转机械状态监测中的应用
- 按物理知识注入方式分类：物理约束 loss、物理初始化、物理数据增强
- 覆盖状态检测、故障诊断、预测三大任务
- 关键挑战：数据稀缺、跨域泛化、模型鲁棒性、可解释性

---

## PINN 在泵领域的应用案例

| 应用 | 信号类型 | 方法特点 |
|------|---------|---------|
| 电磁泵 RUL 预测 | 振动 + 压力 | 气蚀退化建模 |
| 液压齿轮泵 RUL | 振动 + 流量 + 压力 | 多信号融合 |
| 反应堆冷却泵故障预测 | 轴封泄漏 | 物理退化模型 + DL |
| 离心泵混合建模 | 多传感器 | 物理动态 + AI 模块并行 |

---

## 本方案关联

本方案的 **"机理+数据融合"** 本质上是 PINN 思想在工业 PHM 中的实践：

| PINN 概念 | 本方案对应 |
|----------|-----------|
| 物理约束 loss | Q-H-η 曲线作为 HI 基线 |
| 物理初始化 | 效率/振动理论值作为先验 |
| 物理数据增强 | 仿真引擎基于退化机理生成故障样本 |
| 可解释性 | 偏离度可追溯到具体物理参数 |

## 引用建议

> "物理信息神经网络（PINN）正成为旋转机械 PHM 的前沿方向——Kumar et al.（2024）和 Wang et al. 的综述均将其列为 RUL 预测的核心技术趋势。本方案以水泵 Q-H-η 特性曲线作为物理先验注入健康指数模型，以仿真退化引擎基于物理机理生成训练数据，实践这一技术路线。"

## 外部链接

- Kumar et al. 综述 (MDPI Energies)：<https://www.mdpi.com/1996-1073/17/22/5538>
- Wang et al. 综述 (SSRN)：<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6691187>
