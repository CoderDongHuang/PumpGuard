# NASA IMS 轴承数据集

> 预测性维护领域最经典的开源数据集之一。

---

## 基本信息

| 项目 | 内容 |
|------|------|
| **全称** | NASA Intelligent Maintenance Systems (IMS) Bearing Dataset |
| **提供方** | 辛辛那提大学 IMS 中心，托管于 NASA PCoE |
| **轴承型号** | Rexnord ZA-2115 双列轴承 × 4 |
| **实验类型** | 三组 run-to-failure 实验 |
| **转速** | 2,000 RPM |
| **径向负载** | 6,000 lbs |
| **传感器** | PCB 353B33 高灵敏度石英 ICP 加速度计 |

## 数据规格

| 属性 | 值 |
|------|-----|
| 采样率 | **20 kHz** |
| 每文件采样数 | 20,480（1 秒快照） |
| 记录间隔 | 每 10 分钟 |
| 总文件数 | 9,463 |
| 总大小 | 约 **6.1 GB**（解压后） |
| 格式 | ASCII 文本 |
| 是否有标签 | 是（失效模式标注） |
| 失效模式 | 内圈故障（Set 1）、外圈故障（Set 3-B3） |

## 下载地址

| 平台 | 链接 |
|------|------|
| **NASA PCoE 官方** | <https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/> |
| **PHM Society 镜像** | <https://phm-datasets.s3.amazonaws.com/NASA/4.+Bearings.zip> |
| **Kaggle（原始数据）** | <https://www.kaggle.com/datasets/vinayak123tyagi/bearing-dataset> |
| **Kaggle（特征工程版）** | <https://www.kaggle.com/datasets/jawadulkarim117/nasa-bearing-dataset> |
| **Zenodo（修正版）** | 修复了原版文件夹命名错误 |

## 本方案用途

- RUL 预测算法的基准测试与验证
- 振动信号特征提取 pipeline 开发
- 退化趋势可视化参考
- 不直接适用于水泵 → 但方法论（HI 构建、RUL 回归）完全可迁移

## 外部链接

- NASA PCoE 主页：<https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/>
- awesome-industrial-datasets（含详细说明）：<https://github.com/jonathanwvd/awesome-industrial-datasets/blob/master/markdown/nasa_bearing_dataset.md>
