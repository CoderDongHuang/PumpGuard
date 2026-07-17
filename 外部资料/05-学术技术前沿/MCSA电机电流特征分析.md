# MCSA 电机电流特征分析

> Motor Current Signature Analysis — 非侵入式故障检测核心技术

---

## 核心论文

### 1. PumpSpectra：MCSA 水泵故障检测平台

| 项目 | 内容 |
|------|------|
| **论文** | "PumpSpectra: An MCSA-Based Platform for Fault Detection in Centrifugal Pump Systems" |
| **作者** | Adaika et al. |
| **期刊** | *Sensors*, 2025, 25(22), 6916 |
| **方法** | MCSA + FFT/STFT + 透明规则模型 |
| **准确率** | **91.2%** |
| **误报率** | **3.8%**（0.1 Hz 分辨率下） |
| **实测地点** | 阿尔及利亚 El Oued 海水淡化厂 |
| **可检测故障** | 不对中、轴承缺陷、叶轮异常 |
| **效率提升** | 分析时间缩短 **95%** |

### 2. MCSA + AutoML

| 项目 | 内容 |
|------|------|
| **论文** | "Centrifugal pump and electrical motor fault detection with MCSA and automated machine learning" |
| **作者** | Khalikov et al. |
| **期刊** | *Journal of Mining Institute*, 2025, Vol. 275, pp. 42-55 |
| **方法** | MCSA + AutoML + Enhanced Park's Vector Transformation |
| **准确率** | **89%** |
| **亮点** | AutoML 显著优于传统梯度提升，使用接近真实工况的开放数据集 |

### 3. 模型基 MCSA（MBVI）

| 项目 | 内容 |
|------|------|
| **论文** | "Model-based voltage and current analysis for torque oscillation detection and improved condition monitoring of centrifugal pumps" |
| **作者** | Han et al. |
| **期刊** | *Mechanical Systems and Signal Processing*, 2025, Vol. 224 |
| **方法** | 模型基 MCSA (MBVI) + CNN-LSTM-Attention |
| **可检测** | 非设计工况运行、气蚀、叶轮损伤 |
| **亮点** | 可区分供电电压扰动与真实故障，灵敏度优于传统 MCSA |

---

## 本方案关联

老旧泵（无变频器）接入策略中，MCSA 通过钳形电流表非侵入式采集电流信号，不改造设备本体即可实现故障特征提取。以上论文提供了准确率验证（89-91.2%）和方法论支撑。

## 引用建议

> "据 PumpSpectra 平台在阿尔及利亚海水淡化厂的实地验证，MCSA 对水泵不对中、轴承缺陷、叶轮异常等故障的识别准确率达 91.2%，误报率仅 3.8%。本方案将此技术作为老旧泵非侵入式接入的核心手段。"

## 外部链接

- PumpSpectra 论文 (MDPI Sensors)：<https://www.mdpi.com/1424-8220/25/22/6916>
- MCSA + AutoML 论文 (J. Mining Institute)：<https://pmi.spmi.ru/pmi/article/view/16723>
- MBVI 论文 (ScienceDirect)：<https://www.sciencedirect.com/science/article/pii/S0888327024006794>
