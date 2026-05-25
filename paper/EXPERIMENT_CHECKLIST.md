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
| **6b** | **InternNav / VL-LN navigation extension** | paper-experiment-runner | 原始 GRScenes-100 benchmark scenes + `benchmark/mm_episodes.json` / `sn_episodes.json` + InternNav / VL-LN configs；不要把 test0 mirror 当 benchmark 源 | `shared/evidence/raw/internnav_vln_downstream/internnav_vln_results.json`; `paired_episode_analysis.json`; `video_case_manifest.json`; selected-only side-by-side videos | SR、SPL、NE、TL、OS、StR、FR、paired deltas、failure cases、video cases | ACL 下游扩展：材质变化是否影响语言条件导航；主结果门槛是 paired batch + 失败分类 + 论文级视频，不是单 episode smoke |
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
| 6a GRScenes VLM grounding | ✅ | ✅ | 🔄 stress 已完成 / clean 未完成 | ✅ expanded30 stress 表和图已生成 | 🔄 ACL 小节已接入，仍需全文审阅 |
| 6b InternNav / VL-LN navigation | ✅ prep + wrapper + batch/stat/video scaffold | ✅ one-episode real smoke + flat-filter partial batch diagnostics + official KuJiaLe val-unseen 99 pair | ✅ official KuJiaLe 99/99 original/noMDL pair completed; 🔄 GRScenes expanded30 input still not run | ✅ selected official KuJiaLe 0031 and 0036/0066 visual rerun media migrated into repo with QA/contact sheets | ✅ scoped official downstream sanity evidence; broad embodied benchmark claim still pending |
| 7 综合讨论 | — | — | — | — | ⬜ |

> 状态：⬜ 未开始 ｜ 🔄 进行中 ｜ ✅ 完成

---

## 当前离论文完成还差几步

截至 2026-05-25，ACL 主线已经完成 expanded30 GRScenes stress VLM
canonical 证据闭环，但还没有达到“ACL 主会稳妥投稿终版”。当前状态应读成：
VLM grounding 主实验已经成立；CVPR workshop reviewer 的一部分核心质疑已被
缓解；InternNav 真实 embodied downstream 已有 1-episode smoke，并进一步跑了
flat-filter 多 episode 诊断批次：original 14/14 完成，modified 12/14 后在
reset 后第一步模拟前卡住。随后补跑了一个官方 public InteriorAgent / KuJiaLe
`kujiale_0031` 受控 33-episode original/noMDL pair：原始场景 `SR=0.5152`,
`SPL=0.4793`，noMDL 场景 `SR=0.5758`, `SPL=0.4955`，并生成了 selected
six-case visual rerun QA 和 contact-sheet 图。之后官方 `val_unseen` 路线扩到
0031/0036/0066 三个场景、99 paired episodes，并补齐了 0036/0066 selected
qualitative videos。它可以作为 scoped official downstream sanity result，但仍不是
GRScenes 多场景统计性主结果；
InternNav 已补 per-episode extraction / paired analysis / video-case manifest
scaffold，并且 2026-05-25 已把 flat-filter 输入池扩到 30 episode / 16 scene
的 expanded30 候选 split；材料效应线已建立 expanded30 effect sample manifest，
并用 NVIDIA official fixture 跑通 Asset Converter USD baseline smoke；但
expanded30 真实 runtime、样本级 NVIDIA comparison、论文级视频和完整多 episode
embodied batch 仍未闭环。

| 顺序 | 门槛 | 当前状态 | 完成标准 |
|---|---|---|---|
| 1 | 全量 no-MDL 数据集 | ✅ 已完成并验证 | `full_nomdl_multi_root_run_report.json` 记录 `dry_run=false`、99 个顶层 raw scene 转换完成，且 `full_nomdl_apply_verification_report.json` 记录 `passed=true`、原始 `/cpfs/user/zhuzihou/assets/zzh-grscenes` 没有 `_noMDL` sidecar 污染 |
| 2 | 原始/简化成对渲染 | 🔄 部分完成；stress 渲染门槛已过 | 23 个 unique target x 多视角的 original/no-MDL 成对图生成完成，图像哈希、相机、目标 bbox/point 投影全部入账；当前 clean preservation pool 为 15 PASS pair，仍低于 20-pair final gate；zoom material-shift stress 已扩到 exactly 30 个 PASS/WARN pair，`retake_zoom_expanded30_paired_render_summary.json` 记录 30/30 非黑图，`retake_zoom_expanded30_target_projection_qa_report.json` 记录 30/30 projection_ok |
| 3 | VLM/下游评测 | ✅ expanded30 material-shift stress 已完成；clean-pool 仍是 15-pair pilot；InternNav 1-episode real smoke、flat-filter partial batch 诊断、official KuJiaLe val-unseen 99-episode pair 已跑通 | `stress_vlm_run_manifest_expanded30.json` 的 manifest-internal stress gate 已打开，canonical Gemma4 `stress_predictions.jsonl` / `stress_score_summary.json` 已生成，Qwen2.5-VL expanded30 diagnostic 已生成；`internnav_vln_downstream/prep_manifest.json` 和 `internnav_vln_results.json` 已记录 1-scene original/no-MDL VLN mini pair：两边 SR/SPL 都为 0，但 noMDL TL +33.5054、NE +33.7468；flat-filter original 14/14 完成，modified 12/14 后在 tvstand episode reset 后 hang，12-pair 诊断分析显示 TL/NE/OS 行为差异但 `acl_main_result_ready=false`；`official_val_unseen_99/paired_99_summary.json` 记录官方 KuJiaLe 3-scene / 99-episode pair：original/noMDL `SR=0.5253/0.4848`、`SPL=0.4739/0.4298`、`NE=3.6798/3.6306`、`TL=6.9754/7.0598`；`official_selected_qualitative_videos/` 记录 0031 和 0036/0066 selected mp4/still/contact-sheet QA；论文 claim 仍限 frozen 30-pair target-centered stress set、official InteriorNav/KuJiaLe downstream sanity check、partial runtime diagnostic 和 expanded30 input readiness，不能扩写成 broad embodied benchmark |
| 4 | 图表和结论 | 🔄 expanded30 stress 表和 VLM qualitative figure 已接入；trade-off 结论仍需全文收束 | 质量图、VLM 表、失败案例/定性图、trade-off 结论全部进入 `paper/shared/figures/`、`paper/shared/tables/` 和 `results_manifest.yaml`；当前 expanded30 stress 表可作为 frozen stress-set evidence，clean-pool 15-pair 表、旧 zoom-stress 表、coordinate ablation 和 failure taxonomy 仍是 pilot/protocol diagnostic |
| 5 | 论文写作与审稿式自查 | ✅ expanded30 ACL wrapper 已闭环；投稿终版仍需下一轮扩展 | `make -C paper acl27` 已通过，Abstract/Intro/Method/Experiments/Discussion/Limitations 已按 expanded30 evidence 收紧，且完成三路 reviewer-style 审阅并修订；下一轮目标是补 ACL/NLP related work、citation audit、baseline/ablation，或明确放弃 downstream claim |

## CVPR Workshop Reviewer 意见闭环状态

| Reviewer 主题 | 当前状态 | 解释 |
|---|---|---|
| 实验范围太小 | 🔄 部分缓解 | workshop 的 4 个家具资产没有被完全替换；但 ACL 路线新增 GRScenes 30-pair target-centered material-shift stress set，覆盖 cup、clock、faucet、bottle、backpack 等更多目标类别。仍缺系统材料矩阵。 |
| “AI Task Performance” 无真实任务 | 🔄 部分修复 | 已从 CLIP/DINOv2 proxy 推进到真实 Gemma4/Qwen2.5-VL image-level VLM grounding，并新增 InternNav/VLN real smoke、official KuJiaLe 3-scene / 99-episode sanity result 和 selected qualitative videos。仍缺 broad GRScenes / 5+ official-scene embodied benchmark。 |
| 缺 NVIDIA 官方 baseline | 🔄 已启动 | 已用 NVIDIA official `MDL_to_glTF.usd` fixture 跑通 `omni.kit.asset_converter` smoke：`usd_to_usd_preview` 和 `usd_to_usd_bake_flag` 都生成可打开 USD，PreviewSurface=4、active MDL=0。仍未完成样本级 ConvertAsset-vs-NVIDIA head-to-head。 |
| 缺 per-material-effect 分析 | 🔄 已启动 | 新增 `material_effect_baseline/effect_sample_manifest.json`，把 expanded30 GRScenes stress pair 链到 MDL 文件和 effect 标签：当前覆盖 opacity/transparency、emission、normal/bump、displacement/height；clearcoat 和 procedural texture 仍缺，需要官方/sample asset 补洞。 |
| general guideline 过度 | ✅ 已收紧 | 现在 claim 绑定到 frozen 30-pair target-centered stress set；clean preservation、broad GRScenes distribution、downstream embodied robustness 都明确不 claim。 |
| large-scene performance 太窄 | ❌ 未修 | 仍缺多 GRScenes 场景、多重复、variance/CI 的性能实验。 |
| 自动 recommender / safe-conversion detector | ❌ 未修 | 还没有 material-risk classifier 或 rule-based recommender。 |

## 下一阶段 ACL 投稿目标

优先级从高到低：

1. **补 baseline / ablation**：center/random point baseline、bbox-center oracle、prompt/coordinate ablation，先把 VLM grounding 证据变成 reviewer 更难打掉的 diagnostic study。
2. **补 ACL/NLP related work 和 citation audit**：把 synthetic asset conversion 写成 VLM grounding reliability / multimodal evaluation / embodied language data reliability 问题。
3. **扩大 InternNav/VLN downstream**：官方 InteriorNav / KuJiaLe `val_unseen` 已完成 3 scenes / 99 paired episodes，selected-only videos 已补到 0031 和 0036/0066。下一步若继续加强，应补 100+ episode / 5+ scene 以上的统计 gate，或回到 GRScenes expanded30 runtime；不能把当前 99 episodes 写成 broad embodied benchmark。
4. **补 NVIDIA baseline 或明确不可比边界**：baseline smoke 已通过，下一步是对 selected samples 跑 `usd_to_usd_preview` 或 `usd_to_usd_bake_flag`，并写清 ConvertAsset 与官方工具在 composition-preserving、batch scratch conversion、evidence manifest 方面的不同目标。
5. **补材料效应归因**：已建立第一版 effect sample manifest；下一步补 clearcoat/procedural 官方样本、sample-level NVIDIA baseline manifest、effect-grouped 表格和失败案例。

当前最短路径：不要继续盲目刷同一类 orbit 视角。第 2 步已经证明两件事：
clean preservation pool 扩到 15 但还没到 final gate；zoom stress pool 则显示很多目标
能看清，但 no-MDL 后材质、颜色、光照变化很大。第 3 步的最小真实模型链路和
冻结坐标/响应协议已经在 4-pair pilot 上跑通，但样本太小。
Qwen2.5-VL 第二后端也能跑通，但暴露了两个协议问题：历史直接 JSON 输出会坏成
`addCriterion` 片段；冻结 `structured_text` rerun 下，坐标语义仍不清楚，当前 raw
image-space box 解释比 normalized-1000 scaling 更好。
`canonical_vlm_run_manifest.json` 已把 4 个 PASS pair、11 个 WARN retake
candidate、6 个 FAIL 排除样本和 clean claim gate 串起来；它允许继续做 pilot
model run，但明确挡住 clean final benchmark claim。`stress_vlm_run_manifest_expanded30.json`
已经把 30 个 target-visible zoom stress pair、结构化 prompt/坐标协议和 stress
claim gate 串起来；它现在满足 30-pair stress input gate，并且 `model_run_blockers=[]`，
并且在 canonical stress predictions 和 score summary 生成后，已经打开 manifest-internal stress gate。
Gemma4 canonical expanded30 stress root run 生成了 60/60 行预测，答案 30/30 original
和 30/30 converted 全中，normalized-1000 点命中 27/30 original、29/30 converted，
27/30 pair 双边都中。Qwen2.5-VL expanded30 diagnostic 也已生成，55/60 answer 行可评分，
raw point hits 为 22/29 original、19/29 converted，normalized-1000 点命中则只有
3/29 和 3/29，继续说明不同 VLM 的坐标语义强烈依赖 prompt contract。
15-pair clean-pool 已补跑 Gemma4 与 Qwen2.5-VL；Gemma4 的答案稳定，但
normalized-1000 点命中从 original 8/15 降到 converted 6/15。Qwen 仍更像
raw image-space 坐标，适合作为协议敏感性证据。
zoom stress pool 也已补跑 Gemma4 与 Qwen2.5-VL；Gemma4 在目标更大的 zoom
视角中答案稳定，normalized-1000 点命中较高；Qwen 仍显示协议敏感性，并且 raw
point hit 从 original 9/14 降到 converted 6/13。两个旧 zoom stress probe
与 `stress_vlm_run_manifest.json` 的 28 条 `sample_id` 完全对齐，但 metadata 仍指向
旧的 `retake_zoom_target_projection_qa_report.json`，所以继续作为 pilot/protocol
证据，不复制成 root `stress_predictions.jsonl`。新增的 exactly-30 stress manifest
已经作为真实 VLM 推理入口跑完，不能再把 14-pair pilot probe 当主证据。这一轮已经把
clean-pool 表、expanded30 stress 表、VLM grounding qualitative figure、coordinate
ablation 和 appendix failure taxonomy 接入论文系统；其中 expanded30 stress 表可以支撑
frozen 30-pair target-centered stress-set claim，其他表仍是 pilot/protocol diagnostic。当前推荐主线
不再是单纯追 clean preservation benchmark，而是把 ACL 故事收束为
material/texture/rendering perturbations 如何影响 VLM grounding protocol
reliability。clean PASS set 继续作为 sanity-control gate；zoom stress、
coordinate ablation 和 failure taxonomy 应作为主故事的诊断支撑，同时明确 clean
preservation 和下游 embodied task 仍未闭环。
当前 stress 扩样不需要换数据集：首批 16 个 expansion candidate 经过 render/projection
机器 gate 后，有 5 个被 clean-room visual review 判为 FAIL；随后 11 个 replacement cup
candidate 中有 10 个可用。最终只选 5 个 replacement，构成 exactly-30 pool。
这个过程记录在 `docs/records/2026-05-22-grscenes-stress-expanded30-render-gate.md`，
也说明了一个关键坑：projection_ok 不等于人眼可见，VLM scoring 前必须保留独立视觉审阅。

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
