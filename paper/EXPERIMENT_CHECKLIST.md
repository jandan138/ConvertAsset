# 论文实验工作清单

> **论文主题**：Isaac Sim 中 MDL 材质简化（→ UsdPreviewSurface）对视觉质量与 AI 任务性能的影响分析
>
> **核心问题**：材质从高保真 MDL 简化为 UsdPreviewSurface 后，在图像质量、视觉特征、下游 AI 任务三个层面的影响分别有多大？值不值得简化？

---

## 项目目录结构

```
paper/
├── EXPERIMENT_CHECKLIST.md      ← 本文件
├── shared/
│   ├── evidence/
│   │   ├── experiments/         ← 实验脚本（由 paper-experiment-runner 编写）
│   │   ├── raw/                 ← 原始数据（CSV / JSON / NPZ / renders）
│   │   ├── references/          ← 文献调研、投稿计划、核查记录
│   │   └── reviews/             ← 历史 review/action items
│   ├── figures/                 ← 图表生成脚本与论文图表（PNG + PDF）
│   ├── references.bib           ← BibTeX 数据库
│   └── sections/                ← 共享论文章节（LaTeX）
└── venues/
    ├── aaai27/                  ← AAAI 2027 目标 wrapper
    ├── acl27/                   ← ACL 2027 Japan route candidate wrapper
    └── cvpr26/                  ← 保留的 CVPR/SynData4CV wrapper
```

---

## 论文实验工作清单

| # | 实验任务 | 负责 Agent | 输入 | 输出 | 评测指标 | 目的 |
|---|---|---|---|---|---|---|
| **0** | **数据准备：渲染成对图片** | paper-experiment-runner | 同一批 USD 场景（原始 MDL + `*_noMDL.usd`） | `shared/evidence/raw/renders/`：成对图 A（MDL）/ B（简化）各 N 张 | — | 所有后续实验的基础数据；相机/光源/几何完全一致，只有材质不同 |
| **1** | **渲染性能对比** | paper-experiment-runner | A/B 两版场景 | `shared/evidence/raw/perf_benchmark.csv` | 加载时间(s)、GPU 显存(MB)、FPS | 量化简化带来的计算收益，证明工程价值 |
| **2** | **图像质量对比** | paper-experiment-runner | 成对图 (A, B) | `shared/evidence/raw/image_quality.csv` | PSNR(↑)、SSIM(↑)、LPIPS(↓) | 在像素和感知层面评估材质简化的视觉损失 |
| **3a** | **配对特征相似度** | paper-experiment-runner | 成对图 (A, B) → CLIP / DINOv2 特征 | `shared/evidence/raw/clip_embeddings.npz`、`dino_embeddings.npz` | 均值余弦相似度(↑) | 每对 A/B 在特征空间的接近程度——简化后 AI "看到的"是否一样 |
| **3b** | **特征分布差异** | paper-experiment-runner | 全部 A 的特征 vs 全部 B 的特征 | `shared/evidence/raw/feature_distribution.json` | FID(↓)、Wasserstein 距离(↓) | 两种材质风格在特征空间的整体偏移量 |
| **3c** | **特征可视化** | paper-figure-generator | `clip_embeddings.npz` / `dino_embeddings.npz` | `shared/figures/fig_tsne_*.pdf` | t-SNE / UMAP 聚类分离度（视觉判断） | 直观展示 A/B 特征是否可分，辅助读者理解 |
| **4a** | **目标检测迁移评测** | paper-experiment-runner | A 训 → A/B 测（或 B 训 → A/B 测） | `shared/evidence/raw/detection_results.json` | mAP、mAP@50 | 材质变化对检测任务准确率的影响 |
| **4b** | **语义分割迁移评测** | paper-experiment-runner | 同上 | `shared/evidence/raw/segmentation_results.json` | mIoU | 材质变化对分割任务准确率的影响 |
| **4c** | **CLIP 零样本检索** | paper-experiment-runner | 用 A 建索引库，用 B 图片当查询 | `shared/evidence/raw/retrieval_results.json` | Top-1 / Top-5 准确率、mAP | 证明简化材质不破坏跨模态语义检索能力 |
| **5** | **RL 策略迁移实验** | paper-experiment-runner | A 环境训练策略，B 环境测试（双向） | `shared/evidence/raw/rl_results.json` | 收敛步数、成功率(%)、平均奖励 | 材质差异是否真正影响策略学习和泛化 |
| **6a** | **GRScenes VLM grounding** | paper-experiment-runner | `benchmark_source_dataset` 使用 `/cpfs/user/zhuzihou/assets/zzh-grscenes` 原始 GRScenes-100；episode-backed pilot 优先从 30 个 home episode scenes 选样；commercial scenes 只做 metadata-driven stress test；`engineering_validation_dataset` 只用于 smoke/debug；no-MDL 从 scratch copy 生成成对渲染，PIO-style prompts | `shared/evidence/raw/grscene_vlm_grounding/score_summary.json` | point-in-box / point-in-mask accuracy、answer consistency | ACL 主线实验：材质/纹理泛化是否影响 VLM 的语言 grounding |
| **6b** | **InternNav / VL-LN navigation extension** | paper-experiment-runner | 原始 GRScenes-100 benchmark scenes + `benchmark/mm_episodes.json` / `sn_episodes.json` + InternNav / VL-LN configs；不要把 test0 mirror 当 benchmark 源 | `shared/evidence/raw/internnav_vln_results.json` | SR、SPL、dialog efficiency、goal success delta | ACL 下游扩展：材质变化是否影响语言条件导航 |
| **7** | **综合 Trade-off 分析** | paper-writer | 以上所有结果 | `shared/sections/discussion.tex` | — | 回答"何时可以简化、何时要小心"，形成论文核心结论 |

---

## 实验进度追踪

| # | 脚本实现 | 小样本验证 | 全量运行 | 图表生成 | 写入论文 |
|---|---|---|---|---|---|
| 0 渲染成对图片 | ⬜ | ⬜ | ⬜ | — | — |
| 1 渲染性能对比 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 2 图像质量对比 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 3a 配对特征相似度 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 3b 特征分布差异 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 3c 特征可视化 | — | — | — | ⬜ | ⬜ |
| 4a 目标检测迁移 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 4b 语义分割迁移 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 4c CLIP 零样本检索 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 5 RL 策略迁移 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 6a GRScenes VLM grounding | 🔄 | 🔄 | ⬜ | ⬜ | ⬜ |
| 6b InternNav / VL-LN navigation | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 7 综合讨论 | — | — | — | — | ⬜ |

> 状态：⬜ 未开始 ｜ 🔄 进行中 ｜ ✅ 完成

---

## 当前离论文完成还差几步

截至 2026-05-22，ACL 主线不是还差“写几段文字”，而是还差下面 5 个
证据门槛。只有这些门槛都过了，论文才算真正可投稿：

| 顺序 | 门槛 | 当前状态 | 完成标准 |
|---|---|---|---|
| 1 | 全量 no-MDL 数据集 | ✅ 已完成并验证 | `full_nomdl_multi_root_run_report.json` 记录 `dry_run=false`、99 个顶层 raw scene 转换完成，且 `full_nomdl_apply_verification_report.json` 记录 `passed=true`、原始 `/cpfs/user/zhuzihou/assets/zzh-grscenes` 没有 `_noMDL` sidecar 污染 |
| 2 | 原始/简化成对渲染 | 🔄 部分完成 | 23 个 unique target x 4 view 的 original/no-MDL 成对图生成完成，图像哈希、相机、目标 bbox/point 投影全部入账；当前已完成 21 个 centerline-clear 候选中的 10 个默认推荐视角 + 11 个替代清晰视角的 smoke renders、投影 QA 和盲视觉 QA，得到 4 个 PASS pair |
| 3 | VLM/下游评测 | 🔄 小样本 pilot 已完成 | canonical `predictions.jsonl`、`score_summary.json`、必要的 InternNav/VL-LN 扩展结果生成，指标能回答材质变化是否影响 grounding/navigation；当前只有 `probes/gemma4_pass_only_*` 的 4-pair Gemma4 PASS-only pilot，不能当最终性能 |
| 4 | 图表和结论 | ⬜ 未完成 | 质量图、VLM 表、失败案例/定性图、trade-off 结论全部进入 `paper/shared/figures/`、`paper/shared/tables/` 和 `results_manifest.yaml`；pilot 只能作为下一轮实验设计依据 |
| 5 | 论文写作与审稿式自查 | ⬜ 未完成 | ACL/AAAI wrapper 能编译，Abstract/Intro/Method/Experiments/Discussion/Limitations 与证据一致，完成至少一轮 reviewer-style 反向审阅 |

当前最短路径：先扩大第 2 步的干净 PASS 渲染池，同时冻结第 3 步的坐标协议。
当前 4-pair Gemma4 PASS-only pilot 已经证明真实模型链路能跑通，但样本太小，
且 Gemma4 输出的是 normalized visual coordinates 而不是 raw pixel coordinates。
下一步应优先 retake/WARN 视角或补新的清晰视角，形成更大的 PASS set，再跑
Gemma4 + 至少一个第二 VLM backend，最后把结果写成论文表格和失败案例图。

---

## 论文 Agent 使用说明

### 开始实验（数据准备 → 定量评测）
```
给 paper-experiment-runner：
"实现并运行实验 #0（渲染成对图片），场景路径在 assets/usd/，
输出图片到 paper/shared/evidence/raw/renders/"
```

### 生成图表
```
给 paper-figure-generator：
"读取 paper/shared/evidence/raw/image_quality.csv，
生成 PSNR/SSIM/LPIPS 对比柱状图（带误差线），
输出到 paper/shared/figures/"
```

### 写论文章节
```
给 paper-writer：
"基于 paper/shared/evidence/raw/ 中的实验数据，
撰写 Experiments 章节的 Image Quality 子节，LaTeX 格式"
```

### 查文献 / 核查引用
```
给 paper-research-advisor：
"搜索关于 sim-to-real 视觉迁移的相关论文，
整理到 paper/shared/evidence/references/related_work.md，
并核查所有引用的真实性"
```

### 规划投稿
```
给 paper-research-advisor：
"我打算投 ICRA 2026，查询投稿要求并给出论文章节字数分配方案"
```

---

## 核心实验依赖关系

```
实验 #0（渲染成对图片）
    ↓
    ├── 实验 #1（性能对比）    → 独立，可与 #2/#3a 并行
    ├── 实验 #2（图像质量）    → 需要 A/B 渲染图
    ├── 实验 #3a（特征相似度） → 需要 A/B 渲染图
    │       ↓
    │   实验 #3b（分布差异）   → 需要 #3a 的特征文件
    │       ↓
    │   实验 #3c（可视化）     → 需要 #3a 的特征文件
    ├── 实验 #4a（检测迁移）   → 需要 A/B 渲染图 + 标注
    ├── 实验 #4b（分割迁移）   → 需要 A/B 渲染图 + 标注
    ├── 实验 #4c（CLIP 检索）  → 需要 #3a 的特征文件
    ├── 实验 #5（RL 实验）     → 需要 Isaac Sim 环境
    ├── 实验 #6a（GRScenes VLM grounding） → 需要 A/B 渲染图 + 语义目标/box/mask
    └── 实验 #6b（InternNav / VL-LN）      → 需要 #6a 的 grounding pilot 和 InternNav 配置

所有实验完成 → 实验 #7（综合讨论）
```
