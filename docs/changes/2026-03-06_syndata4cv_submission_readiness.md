# 2026-03-06 SynData4CV Submission Readiness

## 背景

本记录用于沉淀一次针对 `paper/` 目录的投稿就绪度核查，目标 venue 为 `SynData4CV @ CVPR 2026`。

核查目标分为三部分：

- 官方提交要求到底是什么
- 当前仓库里已经具备哪些可提交材料
- 还差多少准备，分别从“材料是否齐全”“格式是否合规”“内容是否够强”三个维度判断

本记录基于 `2026-03-06` 当天可访问的官方页面和仓库本地文件，后续若官方页面更新，应以更新后的页面为准。

## 官方要求核对

### 已核对的官方信息

以下信息已通过 workshop 官方页、CVPR 官方页或 OpenReview 公开 invitation 核对：

- `SynData4CV` 是 `CVPR 2026` 官方 workshop 列表中的正式 workshop
- 使用 `CVPR 2026 template`
- `short paper` 为 `4 pages`，`long paper` 为 `8 pages`，均 **不含 references**
- 提交平台为 `OpenReview`
- 评审形式为 `double-blind`
- workshop 官网写明 `accepted papers will NOT be included in CVPR proceedings`
- workshop 官网写明 `submission deadline = March 12, 2026`
- `notification` 和 `camera-ready deadline` 截至本次核查仍为 `TBD`
- OpenReview 公开 `Submission` invitation 已存在，表单字段包含：
  - `title`
  - `authors`
  - `authorids`
  - `keywords`
  - `TLDR`
  - `abstract`
  - `pdf`
- OpenReview invitation 明确要求所有作者事先拥有 OpenReview profile
- CVPR 官方 `Complete Your OpenReview Profile` 页面明确说明：profile 不完整可能导致 desk rejection

### 截止时间的说明

官方 workshop 页面写的是 `March 12, 2026`，但没有标明时区。

OpenReview invitation 的 `duedate` 对应 `2026-03-13 11:59 UTC`。这与常见的 `March 12 AoE` 非常接近，但由于 workshop 页面没有直接写明 AoE，本记录只将其视作**高置信推断**，不当作 workshop 页面明文事实。

### 当前未公开的事项

截至本次核查，未发现以下公开 invitation 或明确要求：

- 公开的 `Camera_Ready` invitation
- 公开的 `Supplementary_Material` invitation
- 单独的 abstract-only 提交通道

这意味着当前能确认的最小提交包，核心仍是 **OpenReview metadata + 匿名 PDF**。

## 本地材料盘点

### 已具备的提交核心材料

当前仓库内已经具备一份完整的 workshop 论文提交基线：

- 主稿源文件：
  - `paper/writing/main.tex`
  - `paper/writing/sections/introduction.tex`
  - `paper/writing/sections/related_work.tex`
  - `paper/writing/sections/methodology.tex`
  - `paper/writing/sections/results.tex`
  - `paper/writing/sections/discussion.tex`
  - `paper/writing/sections/conclusion.tex`
- 已编译主稿 PDF：
  - `paper/writing/main.pdf`
- 样式与参考文献构建文件：
  - `paper/writing/cvpr.sty`
  - `paper/writing/ieeenat_fullname.bst`
  - `paper/writing/main.bbl`
- 当前正文已使用的图：
  - `paper/results/figures/fig_render_pairs.pdf`
  - `paper/results/figures/fig_image_quality.pdf`
  - `paper/results/figures/fig_feature_similarity.pdf`
  - `paper/results/figures/fig_tsne_dino.pdf`
- 当前正文已使用的结果数据：
  - `paper/results/raw/perf_benchmark.csv`
  - `paper/results/raw/image_quality.csv`
  - `paper/results/raw/feature_similarity.csv`
  - `paper/results/raw/detection_results.json`
  - `paper/results/raw/statistical_tests.json`
  - `paper/results/raw/clip_embeddings.npz`
  - `paper/results/raw/dino_embeddings.npz`
- 参考文献与投稿规划：
  - `paper/references/references.bib`
  - `paper/references/related_work.md`
  - `paper/references/submission_plan.md`
  - `paper/references/venue_recommendations.md`
- 内部 review 与行动项：
  - `paper/reviews/content_review.md`
  - `paper/reviews/format_review.md`
  - `paper/reviews/action_items.md`

### 尚未在仓库中看到的材料

本次核查没有在仓库中看到以下文件或材料：

- OpenReview 提交元数据草稿
  - 例如作者名单定稿、`authorids`、keywords、TLDR、最终 abstract 文案快照
- 单独的 supplementary 文档或打包目录
- camera-ready 相关材料
- 独立的投稿自检清单
- `paper/references/verification_report.md`

另外，`paper/EXPERIMENT_CHECKLIST.md` 中原计划提到的若干结果产物仍未出现，例如：

- `feature_distribution.json`
- `segmentation_results.json`
- `retrieval_results.json`
- `rl_results.json`

这些不是 `SynData4CV` 明文要求的必交件，但会影响稿件的说服力和后续扩展空间。

## 格式状态

### 当前状态

主稿当前使用：

- `\usepackage[review]{cvpr}`
- 匿名作者块
- CVPR 风格的双栏版式

本次重新编译 `paper/writing/main.tex` 时，`pdflatex` 成功生成 `paper/writing/main.pdf`。

后续又额外做了一轮匿名投稿收敛：

- 为 `hyperref` 启用 `pagebackref`
- 收掉稿件中的显式项目名 `ConvertAsset`
- 将 detection 和阈值相关表述进一步收敛为更保守的 workshop 语气

当前未再发现此前 review 中提到的表格溢出、caption 位置、未定义引用等明显构建级问题。

### 格式层面的剩余风险

1. workshop 页只写了 `double-blind`，未展开匿名细则；因此仍需按 CVPR 常规标准做一次人工双盲检查
2. 尽管正文中的显式项目名已收掉，但若外部公开仓库、图像或附带材料仍可反查作者，双盲风险仍未完全归零

### 格式 readiness 判断

判断：**中高，接近可投**

当前格式不是主要瓶颈。真正需要补的不是 TeX 结构，而是：

- 最终提交 metadata 是否准备完整
- 双盲风险是否彻底排查

## 内容状态

### 当前内容的强项

当前稿件已经具备完整的问题定义和实验链路：

- 有明确的 toolkit/pipeline 叙事
- 有像素级质量评估
- 有渲染性能对比
- 有 feature-level 分析
- 有零样本 detection 结果
- 有统计检验文件落地

对 workshop 来说，这已经不是“只有想法”的阶段，而是一篇完整的 case-study 稿件。

### 当前内容的主要短板

1. 数据范围明显偏窄
   - 当前样本基本是 `4` 个 `chest-of-drawers`
   - 属于单类别、小规模 case study

2. 下游 AI 证据偏弱
   - 当前正文真正落地的是 zero-shot detection proxy
   - 尚未达到 detection / segmentation transfer 级别的说服力

3. 计划中的扩展实验尚未补齐
   - distributional analysis
   - segmentation
   - retrieval
   - RL transfer

4. 部分 discussion 中的 practical thresholds 仍偏经验化
   - 更适合表述为“初步经验阈值”而不是强结论

### 内容 readiness 判断

判断：**中等，可投 workshop，但不算强**

按 `SynData4CV` workshop 的标准，它已经具备提交资格，也具备被接收的可能；但若目标是“中稿把握较高”，目前证据仍不够厚。

更贴近的风险画像是：

- `weak accept / weak reject` 边缘
- 接收概率将明显受 reviewer 对“pilot-style case study”容忍度影响

## 三维度总评

### 1. 材料是否齐全

判断：**基本齐了，但还没形成低风险提交包**

已经齐的部分：

- 匿名 PDF
- LaTeX 源
- 当前正文对应的图和 raw results
- 参考文献

还需人为补齐或确认的部分：

- OpenReview 最终 metadata
- 最终作者名单和 `authorids`
- OpenReview profile 完整性
- 双盲检查记录

注：后续已新增一份单作者 OpenReview 草稿，见 `docs/changes/2026-03-06_syndata4cv_submission_package.md`。

### 2. 格式是否合规

判断：**基本合规**

当前已经接近直接提交，剩余工作主要是：

- 处理 `pagebackref` warning
- 做最后一轮匿名性检查

### 3. 内容是否够中

判断：**够投，不够稳中**

当前最像一篇：

- 有完整结构和初步说服力的 workshop 稿件

但还不像一篇：

- 证据厚度足够、内容上明显强于阈值的 workshop submission

## 截稿前建议优先级

若目标是 `2026-03-12` 前尽快稳定提交，建议按以下优先级处理：

1. 先锁定作者名单与 OpenReview profiles
2. 做一次双盲检查，重点检查 `ConvertAsset` 命名和任何可识别链接
3. 整理 OpenReview metadata
   - title
   - authors
   - authorids
   - keywords
   - abstract
   - TLDR
4. 再考虑是否做小幅内容收敛
   - 适度弱化过强 claim
   - 更明确承认单类别限制
   - 将 detection 结论表述为 preliminary observation

若目标是提高中稿把握，而不是只完成提交，则优先级应转为：

1. 强化下游任务证据
2. 扩大资产类别覆盖
3. 补强 discussion 中阈值和实践建议的依据

## 本次核查使用的官方来源

- SynData4CV 官方页：`https://syndata4cv.github.io/`
- CVPR 2026 Workshops：`https://cvpr.thecvf.com/Conferences/2026/Workshops`
- CVPR 2026 Dates：`https://cvpr.thecvf.com/Conferences/2026/Dates`
- CVPR 2026 Complete Your OpenReview Profile：`https://cvpr.thecvf.com/Conferences/2026/CompleteYourORProfile`
- CVPR 2026 Author Guidelines：`https://cvpr.thecvf.com/Conferences/2026/AuthorGuidelines`
- OpenReview Submission invitation：
  `https://api2.openreview.net/invitations?id=thecvf.com%2FCVPR%2F2026%2FWorkshop%2FSynData4CV%2F-%2FSubmission`

## 结论

截至 `2026-03-06`，这篇稿件对 `SynData4CV` 而言已经达到“可以提交”的状态，但还没有达到“提交风险很低、内容把握较高”的状态。

简化总结如下：

- 材料：**基本齐**
- 格式：**基本过**
- 内容：**能投，但不稳中**
