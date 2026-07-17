# Kaggle — Industrial Pump Physics-Grounded Digital Twin

> **与本方案仿真数据引擎最为对齐的数据集。**

---

## 基本信息

| 项目 | 内容 |
|------|------|
| **名称** | Industrial Equipment: Physics-Grounded Digital Twin |
| **上传者** | ishanpradhan95 |
| **平台** | Kaggle |
| **设备** | 150 台工业泵 |
| **数据行数** | **379,786 行** × 32 列 |
| **故障率** | **0.11%**（稀有故障，贴近真实） |

## 数据特点

- **高保真 run-to-failure 仿真**：基于物理退化机理（磨损、发热、效率衰减耦合）
- **含 RUL 标签**：可直接用于 RUL 回归模型训练
- **设备异质性**：150 台泵有不同的退化轨迹，模拟真实制造差异
- **32 列特征**：涵盖传感器读数、退化指标、运行工况等

## 典型 Notebook

| Notebook | 方法 | 效果 |
|----------|------|------|
| PumpAnalysis | 基于数字孪生的 RUL 预测 | 约 9.37 小时误差（105 小时预测范围） |

## 本方案用途

- **仿真数据引擎设计的直接参考模板** → 数据格式、特征维度、退化机理建模
- 对比自己的仿真引擎输出是否合理
- RUL 模型的原型验证

## 外部链接

- Kaggle 数据集：<https://www.kaggle.com/datasets/ishanpradhan95/industrial-pump-physics-grounded-digital-twin>
- PumpAnalysis Notebook：<https://www.kaggle.com/code/hanaaelkhateeb/pumpanalysis>
