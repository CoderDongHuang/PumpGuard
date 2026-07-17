# 离心泵 AI 驱动 PHM 综述

---

## 核心综述

### AI-Driven Prognostics and Health Management for Centrifugal Pumps

| 项目 | 内容 |
|------|------|
| **标题** | Artificial Intelligence-Driven Prognostics and Health Management for Centrifugal Pumps: A Comprehensive Review |
| **作者** | Khalid S., Jo S.H., Shah S.Y., Jung J.H., Kim H.S.（韩国亚洲大学） |
| **期刊** | *Actuators*, 2024, Vol. 13, No. 12, 514 |
| **链接** | <https://doi.org/10.3390/act13120514> |

### 核心发现

**1. 离心泵主要故障模式**
- 轴承故障（最常见的旋转部件失效）
- 叶轮损伤（气蚀、腐蚀、磨损）
- 密封泄漏
- 不对中
- 电机电气故障

**2. 主流方法分类**

| 方法类别 | 代表技术 | 适用场景 |
|---------|---------|---------|
| 传统 ML | SVM、随机森林、XGBoost | 特征明确的分类任务 |
| 深度学习 | CNN、LSTM、Bi-LSTM | 时序信号自动特征学习 |
| 混合模型 | KPCA-LSTM、DCAE+Bi-LSTM | 降维 + 时序建模 |
| 迁移学习 | Domain Adaptation | 跨工况/跨设备泛化 |
| GAN 数据增强 | DCGAN、ACGAN | 故障样本不足时的数据扩充 |

**3. 自适应阈值方法**
- 传统固定阈值 → 工况变化下误报率高
- 自适应阈值基于运行工况动态调整 → 降低误报

**4. RUL 预测前沿**
- 混合模型（物理 + 数据驱动）预测最准确
- 纯数据驱动在小样本下泛化差

---

## 本方案关联

综述的核心结论——"混合模型（机理+数据驱动）是当前主流趋势"——直接支撑本方案的健康指数设计（Q-H-η 物理基线 + 数据残差学习）。

## 引用建议

> "据 2024 年离心泵 PHM 综述（Khalid et al., *Actuators*），混合模型（物理机理 + 数据驱动）是当前水泵健康管理的主流趋势，自适应阈值可有效降低变工况下的误报率。"

## 外部链接

- MDPI Actuators 论文：<https://doi.org/10.3390/act13120514>
