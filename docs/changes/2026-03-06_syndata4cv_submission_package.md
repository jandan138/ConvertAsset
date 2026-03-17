# 2026-03-06 SynData4CV Submission Package

## 背景

本记录用于把 `SynData4CV @ CVPR 2026` 的实际提交包准备工作落到文档里，包括：

- 本地稿件层面的匿名与格式收敛
- OpenReview 单作者提交草稿
- 哪些步骤已经在仓库中完成
- 哪些步骤仍必须由作者本人登录 OpenReview 完成

本记录默认采用以下提交假设：

- 作者数量：`4`
- 第一作者：`Zihou Zhu`，OpenReview profile：`~Zihou_Zhu1`
- 第二作者：`Haitao Mei`，OpenReview profile：`~Mei_Haitao1`
- 第三作者：`Haolong Zheng`，OpenReview profile：`~Haolong_Zheng2`
- 第四作者：`Zhou Zhang`，OpenReview profile：`~Zhou_Zhang7`

## 本次已完成的稿件侧收敛

相对前一个 readiness 版本，本次额外完成了以下稿件调整：

1. 修复 `hyperref` 配置，启用 `pagebackref`
   - `paper/writing/main.tex`
2. 收掉正文中显式的项目名 `ConvertAsset`
   - 避免在匿名投稿稿件中直接暴露可识别项目名
   - 改为 `open-source conversion toolkit` / `our conversion toolkit`
3. 收敛 detection 相关措辞
   - 将 `detection-neutral` 改为更保守的 limited-setting 表述
4. 收敛 discussion 中的阈值建议
   - 把 CLIP / DINOv2 阈值改成 heuristic/manual-review signal
   - 不再写成硬性的 go/no-go rule
5. 正规化 `paper/references/references.bib`
   - 正式发表条目改用正式 journal / proceedings 版本
   - 预印本条目改为 arXiv-only
   - 不再让 submission 版 bibliography 把 `note` 当作 verification log 输出
6. 新增 `paper/references/verification_report.md`
   - 按 `FORMAL / ARXIV_ONLY / SOFTWARE` 分组记录当前参考文献状态

## 编译验证

本次调整后，重新编译 `paper/writing/main.tex`，当前匿名稿件可正常生成：

- 输出文件：`paper/writing/main.pdf`
- 页数：`9 pages`
- 参考文献仍单独计页

此前 `pagebackref` warning 已消除。当前最后一次编译未见前述 review 中的表格溢出或未定义引用问题。

## OpenReview 单作者提交草稿

### 作者身份来源

基于 `OpenReview API` 对 `~Zihou_Zhu1` 的公开 profile 核对，当前可见公开信息包括：

- Name: `Zihou Zhu`
- OpenReview ID: `~Zihou_Zhu1`
- Current affiliation history entry: `Shanghai Artificial Intelligence Laboratory`
- Previous history entry: `Fudan University`
- Expertise: `Robotics`, `Simulation`

这些信息用于确认 `authorids` 解析无误，不应用于匿名 PDF 内文。

### 表单字段草稿

以下内容可直接作为 OpenReview submission 草稿使用。

| Field | Draft |
|---|---|
| `title` | `Evaluating the Trade-offs of MDL-to-UsdPreviewSurface Material Simplification in NVIDIA Isaac Sim: Visual Quality, Feature Preservation, and AI Task Performance` |
| `authors` | `Zihou Zhu, Haitao Mei, Haolong Zheng, Zhou Zhang` |
| `authorids` | `~Zihou_Zhu1, ~Mei_Haitao1, ~Haolong_Zheng2, ~Zhou_Zhang7` |
| `keywords` | `synthetic data`, `Isaac Sim`, `USD`, `MDL`, `UsdPreviewSurface`, `material simplification` |
| `TLDR` | `We quantify how converting Isaac Sim assets from MDL to UsdPreviewSurface affects visual fidelity, feature similarity, and rendering performance across single-object and large-scene workloads.` |
| `pdf` | `paper/writing/main.pdf` |

### Abstract 草稿

```text
Physics-based simulation platforms such as NVIDIA Isaac Sim use MDL (Material Definition Language) materials to achieve photorealistic rendering, but these materials limit interoperability with standard 3D tools and web-based viewers. We present a systematic multi-level evaluation of MDL-to-UsdPreviewSurface material simplification, measuring its impact across three dimensions: pixel-level image quality (PSNR, SSIM, LPIPS), rendering performance (cold-start load time, GPU memory, FPS), and feature-level semantic preservation (CLIP and DINOv2 cosine similarity). Our experiments on four chest-of-drawers assets rendered from six viewpoints show that the conversion preserves high visual fidelity (mean PSNR 35.52 dB, SSIM 0.990, LPIPS 0.020) and maintains strong semantic similarity (CLIP cosine similarity 0.925, DINOv2 cosine similarity 0.872). In a headless single-object benchmark, conversion reduces first-load latency variability but yields near-identical steady-state FPS and GPU memory usage; in a supplemental single-scene GRScenes startup benchmark, the converted scene reaches a fully warmed ready-to-render state 3.8x faster and uses roughly 200 MB less GPU memory. We release an open-source conversion toolkit (available upon acceptance) automating the pipeline with composition-preserving USD traversal, and provide preliminary guidelines for synthetic data practitioners on when material simplification is safe for AI training pipelines.
```

## 当前仍需作者本人在线完成的步骤

以下步骤无法在当前仓库内代办，必须由作者本人登录 OpenReview 完成：

1. 登录 OpenReview，确认 `~Zihou_Zhu1` profile 可正常被 submission form 识别
2. 确认 profile 内容完整，至少满足 CVPR 官方 profile 要求
3. 在 submission form 中填写：
   - `title`
   - `authors`
   - `authorids`
   - `keywords`
   - `TLDR`
   - `abstract`
4. 上传 `paper/writing/main.pdf`
5. 预览并再次检查匿名性
6. 最终点击提交

## 仍需人工做的匿名检查

尽管稿件文本层面已经把显式项目名收掉，最终提交前仍建议再人工检查以下风险：

- PDF metadata 是否包含本地作者信息
- 文中是否还有可识别外链、仓库名或视频名
- 图中是否嵌入了暴露作者身份的水印或路径信息

## 当前提交风险总结

相较于上一版 readiness 评估，本次提交包准备后，风险已经进一步收敛：

- 材料风险：从“缺少 metadata 草稿”收敛到“只差在线填表和上传”
- 格式风险：`pagebackref` 已处理，匿名稿件可正常编译
- 内容风险：仍然存在，但主要属于说服力问题，不再是明显的 submission blocker

最保守的结论是：

- 这份稿件现在已经具备“可提交”的本地包
- 剩余步骤主要集中在 OpenReview 在线填写与最终人工检查

## 参考文献正规化说明

本次还对 `paper/references/references.bib` 做了 submission-friendly 清理，采用以下规则：

- 正式发表的论文使用正式 `journal` / `booktitle` 元数据
- 只有预印本的工作保留为 arXiv-only
- 软件资源保留仓库地址和版本信息
- 不再把内部核验 URL 通过 `note` 暴露到提交版 bibliography 中

这一轮还顺手修正了一条正文 citation key：

- `Singh2024Synthetica` -> `Singh2025Synthetica`

对应核查报告见：

- `paper/references/verification_report.md`

## 官方来源

- SynData4CV 官方页：`https://syndata4cv.github.io/`
- OpenReview Submission invitation：
  `https://api2.openreview.net/invitations?id=thecvf.com%2FCVPR%2F2026%2FWorkshop%2FSynData4CV%2F-%2FSubmission`
- OpenReview Profile API：
  `https://api2.openreview.net/profiles?id=~Zihou_Zhu1`
- CVPR 2026 Complete Your OpenReview Profile：
  `https://cvpr.thecvf.com/Conferences/2026/CompleteYourORProfile`
