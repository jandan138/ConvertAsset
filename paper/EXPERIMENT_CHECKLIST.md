# 论文实验工作清单

> **论文主题**：Isaac Sim 中 MDL 材质简化（→ UsdPreviewSurface）对视觉质量与 AI 任务性能的影响分析
>
> **核心问题**：材质从高保真 MDL 简化为 UsdPreviewSurface 后，在图像质量、视觉特征、下游 AI 任务三个层面的影响分别有多大？值不值得简化？

---

## 项目目录结构

```
paper/
├── EXPERIMENT_CHECKLIST.md      ← 本文件
├── experiments/                 ← 实验脚本（由 paper-experiment-runner 编写）
│   ├── 01_render_pairs/         ← 渲染成对图片
│   ├── 02_perf_benchmark/       ← 渲染性能基准
│   ├── 03_image_quality/        ← PSNR / SSIM / LPIPS
│   ├── 04_visual_features/      ← CLIP / DINOv2 特征分析
│   ├── 05_downstream_tasks/     ← 检测 / 分割 / CLIP 检索
│   ├── 06_rl_training/          ← RL 策略迁移
│   └── figures/                 ← 图表生成脚本（由 paper-figure-generator 编写）
├── results/
│   ├── raw/                     ← 原始数据（CSV / JSON / NPZ）
│   └── figures/                 ← 论文图表（PNG + PDF）
├── references/
│   ├── related_work.md          ← 相关工作调研表
│   ├── references.bib           ← BibTeX 数据库
│   └── verification_report.md  ← 文献真实性核查报告
└── writing/
    └── sections/                ← 论文章节（LaTeX / Markdown）
```

---

## 论文实验工作清单

| # | 实验任务 | 负责 Agent | 输入 | 输出 | 评测指标 | 目的 |
|---|---|---|---|---|---|---|
| **0** | **数据准备：渲染成对图片** | paper-experiment-runner | 同一批 USD 场景（原始 MDL + `*_noMDL.usd`） | `results/raw/renders/`：成对图 A（MDL）/ B（简化）各 N 张 | — | 所有后续实验的基础数据；相机/光源/几何完全一致，只有材质不同 |
| **1** | **渲染性能对比** | paper-experiment-runner | A/B 两版场景 | `results/raw/perf_benchmark.csv` | 加载时间(s)、GPU 显存(MB)、FPS | 量化简化带来的计算收益，证明工程价值 |
| **2** | **图像质量对比** | paper-experiment-runner | 成对图 (A, B) | `results/raw/image_quality.csv` | PSNR(↑)、SSIM(↑)、LPIPS(↓) | 在像素和感知层面评估材质简化的视觉损失 |
| **3a** | **配对特征相似度** | paper-experiment-runner | 成对图 (A, B) → CLIP / DINOv2 特征 | `results/raw/clip_embeddings.npz`、`dino_embeddings.npz` | 均值余弦相似度(↑) | 每对 A/B 在特征空间的接近程度——简化后 AI "看到的"是否一样 |
| **3b** | **特征分布差异** | paper-experiment-runner | 全部 A 的特征 vs 全部 B 的特征 | `results/raw/feature_distribution.json` | FID(↓)、Wasserstein 距离(↓) | 两种材质风格在特征空间的整体偏移量 |
| **3c** | **特征可视化** | paper-figure-generator | `clip_embeddings.npz` / `dino_embeddings.npz` | `results/figures/fig_tsne_*.pdf` | t-SNE / UMAP 聚类分离度（视觉判断） | 直观展示 A/B 特征是否可分，辅助读者理解 |
| **4a** | **目标检测迁移评测** | paper-experiment-runner | A 训 → A/B 测（或 B 训 → A/B 测） | `results/raw/detection_results.json` | mAP、mAP@50 | 材质变化对检测任务准确率的影响 |
| **4b** | **语义分割迁移评测** | paper-experiment-runner | 同上 | `results/raw/segmentation_results.json` | mIoU | 材质变化对分割任务准确率的影响 |
| **4c** | **CLIP 零样本检索** | paper-experiment-runner | 用 A 建索引库，用 B 图片当查询 | `results/raw/retrieval_results.json` | Top-1 / Top-5 准确率、mAP | 证明简化材质不破坏跨模态语义检索能力 |
| **5** | **RL 策略迁移实验** | paper-experiment-runner | A 环境训练策略，B 环境测试（双向） | `results/raw/rl_results.json` | 收敛步数、成功率(%)、平均奖励 | 材质差异是否真正影响策略学习和泛化 |
| **6** | **综合 Trade-off 分析** | paper-writer | 以上所有结果 | `writing/sections/discussion.tex` | — | 回答"何时可以简化、何时要小心"，形成论文核心结论 |

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
| 6 综合讨论 | — | — | — | — | ⬜ |

> 状态：⬜ 未开始 ｜ 🔄 进行中 ｜ ✅ 完成

---

## 论文 Agent 使用说明

### 开始实验（数据准备 → 定量评测）
```
给 paper-experiment-runner：
"实现并运行实验 #0（渲染成对图片），场景路径在 assets/usd/，
输出图片到 paper/results/raw/renders/"
```

### 生成图表
```
给 paper-figure-generator：
"读取 paper/results/raw/image_quality.csv，
生成 PSNR/SSIM/LPIPS 对比柱状图（带误差线），
输出到 paper/results/figures/"
```

### 写论文章节
```
给 paper-writer：
"基于 paper/results/raw/ 中的实验数据，
撰写 Experiments 章节的 Image Quality 子节，LaTeX 格式"
```

### 查文献 / 核查引用
```
给 paper-research-advisor：
"搜索关于 sim-to-real 视觉迁移的相关论文，
整理到 paper/references/related_work.md，
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
    └── 实验 #5（RL 实验）     → 需要 Isaac Sim 环境

所有实验完成 → 实验 #6（综合讨论）
```
