# CVIU 三场景试验：12 对输入与 72 条预测完成

## 结果

三次独立 Qwen3-VL-8B 运行得到相同结果：原始、转换条件各 **11/12 命中（91.7%）**，成功→失败 **0**，失败→成功 **0**。有效坐标输出率均为100%。同条件重复的命中分歧均为0/36；三次运行的原始回答也逐条相同。

这批试验没有复现成功状态翻转。它不能证明材料转换普遍无影响：12个配对的指点坐标都发生变化，平均位移21.26像素，最大78.40像素（1024×768输入）。这里观察到的是坐标改变但命中状态保持，不应把它写成“证明了成功集合迁移”。

| 指标 | 原始条件 | 转换条件 |
|---|---:|---:|
| 可见目标mask命中（每次运行） | 11/12 | 11/12 |
| 可见目标框命中（辅助） | 12/12 | 12/12 |
| 固定图像中心点命中（基线） | 5/12 | 5/12 |
| 三次重复中的同条件分歧 | 0/36 | 0/36 |

## 范围与证据

- 3个既定pilot场景，各2个不同目标、每目标2视角，12对、24图。
- 第一家庭场景：沙发、笔记本；第二家庭场景：沙发、嵌入式烤箱；商业场景：无靠背凳、猫。
- 源类别toy和microwave分别更正为可见的cat和built-in oven，均在推理前完成；源类别、目标prim及修改理由保留。
- 同机Isaac4.1、相同配对相机/光源/分辨率、静止时间捕获；独立缓存路径经真实token回执验证。标签仅在session layer，不出现在RGB输入。
- 原始与转换几何最终重审：8738、4080、1278个mesh，逐mesh顶点、面拓扑和世界变换一致；三场景两条件未解析依赖均为0。
- 全24图和可见mask经过本地视觉检查（非独立人工受试实验）；12对mask逐像素相同。
- 三次运行分别启动新模型进程，BF16、SDPA、greedy、max_new_tokens=128，seed为20261114/15/16；每次24条，共72条，零runtime_error。
- 改变seed但不随机采样，不意味着覆盖随机解码分布；重复结果只约束当前固定解码运行配置。

## 关键案例

1. 商业凳子视角0：两条件预测都落在凳子腿间空隙，mask评分均失败，但bbox评分均成功。原始点(496,375)、转换点(496,427)，位移39.94像素。需区分对象区域定位与实际可见表面定位。
2. 商业凳子视角1：两条件都命中，点从(477,477)变为(474,375)，位移78.40像素，是本批最大变化。
3. 猫视角0：两条件均命中，位移26.67像素。该输入的源类别为toy，已在预测前按可见内容更正查询。

全部12个案例的三次点坐标、命中状态、输入图像路径和原始回答见下方报告及results.json。

## 产物入口

- [冻结输入清单](../../paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/manifest.json)
- [选定图像的QA及哈希](../../paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/selected_qa.json)
- [来源与排除记录](../../paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/selected_progress.json)
- [三次运行回执](../../paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/inference/campaign.json)
- [逐案例报告](../../paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/analysis/report.md)
- [统计及原始回答索引](../../paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/analysis/results.json)
- [独立重评分与哈希审计](../../paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/analysis/independent_prediction_audit.json)
- [最终场景几何审计](../../paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/completion_stage_audit.json)
- [完成验收表](../../paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/completion_audit.json)
- [完整排障过程](2026-11-14-cviu-pilot-restoration-running.md)
- [评审修改跟踪](../../paper/venues/cviu/REVIEW_RESPONSE_TRACKER.md)

每个inference/repeat目录保存24行predictions.jsonl、metadata.json、runner/engine快照及checkpoint配置文件。大图、mask和场景副本在CPFS独立实验目录，manifest包含路径与哈希；未重新分发源场景。

## 验证命令

```bash
python -m pytest -q tests/test_cviu_pilot_analysis.py tests/test_cviu_pilot_inference.py tests/test_cviu_inventory.py
PYTHONPATH=. ./scripts/isaac_python.sh tests/test_mdl_texture_anchor.py
python paper/shared/evidence/experiments/12_cviu_diagnostics/pilot_inference.py --manifest paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/manifest.json --repeat 0 --out /tmp/cviu-unused-validation-output --validate-only
```

前者12项通过；MDL路径回归包含相对/绝对路径及同名冲突检查。最终独立审计重新读取24图/mask的哈希、72条原始回答和mask评分，重算结果与报告一致；完整性由completion_audit.json逐项给出。

## 已解决与仍未完成

本goal要求的三场景端到端试验已经完成。排障中修复了目录指针、MDL纹理路径基准、headless viewport等待、RTX挂载/GUI菜单问题、Isaac4.1缓存参数传递，以及视角遮挡和无效实例ID标注。失败图与中断日志保留，不算模型失败。本次可运行捕获通路固定为Isaac4.1；不声称所有Isaac4.5启动问题均已修复。

数据是双条件可见性合格的小型试验子集，排除了被墙遮挡等无效视角；不能据此估计所有转换场景的失败比例。3场景、6对象、重复视角并非72个独立样本。

CVIU整篇工作仍未完成：30场景扩展、强模型矩阵、目标/背景四条件干预、风险预测、99导航episode重复、完整稿件改写与引用核验仍待执行。本试验不关闭这些评审问题，也不代表稿件已可投稿。
