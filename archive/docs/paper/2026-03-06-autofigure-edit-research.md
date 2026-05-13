# 2026-03-06 AutoFigure-Edit Research

## 背景

本记录用于沉淀一次 agent-team 调研：评估 `https://github.com/ResearAI/AutoFigure-Edit`
是否适合为 ConvertAsset 项目的论文生成科研插图。

调研时间为 `2026-03-06`。本次目标不是评估“它能不能替代整篇论文的图表管线”，
而是回答一个更具体的问题：

- 它是否适合我们当前 paper 的图需求
- 最适合补哪些图
- 哪些图不应该交给它

## 项目侧图需求

### 当前论文已有的图

当前稿件的主要图像内容，基本都来自确定性的实验脚本或渲染结果：

- `paper/results/figures/fig_render_pairs.pdf`
- `paper/results/figures/fig_image_quality.pdf`
- `paper/results/figures/fig_feature_similarity.pdf`
- `paper/results/figures/fig_tsne_dino.pdf`

这些图分别对应：

- MDL / UsdPreviewSurface 渲染对比
- PSNR / SSIM / LPIPS 定量结果
- CLIP / DINOv2 特征相似度
- DINOv2 t-SNE 可视化

对应生成脚本见 `paper/results/gen_figures.py`。这些图本质上都是
**数据绑定或结果绑定图表**，不适合交给 LLM 进行自由生成。

### 当前论文缺的图

`paper/writing/sections/methodology.tex` 已经把方法写成了清晰的三阶段 pipeline：

1. Recursive USD Traversal
2. Material Conversion
3. Asset Path Rewriting

但当前正文里没有配套的 pipeline architecture diagram。审稿意见也明确指出，
方法部分如果补一张流程图会明显增强可读性。

因此，从项目角度看，最真实的图需求不是“更多结果图”，而是：

- 一张方法流程图
- 或一张更概括的系统总览图

## AutoFigure-Edit 的实际能力

### 官方定位

`AutoFigure-Edit` README 的核心定位是：

- `From Method Text to Editable SVG`
- 从论文方法文字生成方法示意图
- 输出可编辑 SVG
- 支持在内嵌 `svg-edit` 中继续人工修改

其公开 README 还提到：

- 支持 style transfer
- 支持生成中间产物和最终 SVG
- 提供 Web 界面和 CLI

### 实际工作流

结合 README、`autofigure2.py` 和 `server.py`，其工作流大致为：

1. 输入 method text
2. 调用外部多模态模型生成一张 raster 草图
3. 用 SAM3 检测图标区域
4. 裁切图标并做背景去除
5. 生成占位式 SVG 模板
6. 将图标重新组装到 SVG
7. 在 Web 端继续编辑

它的核心价值不是“直接一次性生成最终投稿图”，而是：

- 快速搭一个方法图草稿
- 产出可编辑 SVG
- 便于后续手工校正术语、对齐、配色和布局

### 依赖与运行门槛

它不是一个纯本地、纯开源、零外部依赖的工具链。

根据 `autofigure2.py` 与 README：

- 生成阶段依赖外部 provider：
  - `Gemini`
  - `OpenRouter`
  - `Bianxie`
- SAM3 不随仓库 vendored，需要单独安装
- 也可以走 `fal.ai` 或 `Roboflow` API
- 还依赖 `torch`、`torchvision`、`transformers`、`kornia`
- Web 工作流依赖内嵌的 `svg-edit`

这意味着它更接近“研究原型 + 在线模型服务组合”，而不是完全自给自足的稳定制图工具。

## 适配性判断

### 最适合的 use case

对 ConvertAsset 当前论文，`AutoFigure-Edit` 的最适合用途是：

- 为 methodology 补一张 pipeline diagram
- 为 introduction 或 project page 补一张系统总览图

具体可以围绕以下结构起稿：

- 输入：Isaac Sim USD scene with MDL materials
- Stage 1：recursive traversal over references / payloads / sublayers / variants
- Stage 2：MDL -> UsdPreviewSurface conversion
- Stage 3：asset path rewriting to `*_noMDL.usd`
- 输出：converted USD assets
- 可选延伸：GLB export / downstream evaluation renders

这类图的特点是：

- 结构清晰
- 主要传达流程和模块关系
- 不依赖精确数值
- 允许先自动起稿、再人工精修

`AutoFigure-Edit` 在这个范围内是有现实价值的。

### 明显不适合的内容

它不适合承担以下图形任务：

- 渲染前后对比图
- 柱状图、折线图、散点图、误差条图
- t-SNE / embedding visualization
- 表格
- 任何需要严格复现真实实验数值的图

原因很直接：

- 它不是数据驱动制图工具
- 它的主流程是“文字 -> 草图 -> SVG”，而不是“结构化数据 -> 可复现图表”
- 结果图一旦交给 LLM 自由生成，容易引入数值错位、标签幻觉和视觉误导

因此，当前论文的结果图应继续保持 `paper/results/gen_figures.py`
这条脚本化、可复现的生成路线。

## 风险与限制

### 1. 适用面窄

它对我们不是“通用科研插图方案”，而是“方法图草稿工具”。

### 2. 默认风格未必匹配投稿论文

源码中默认 prompt 包含：

- `Generate a professional academic journal style figure`
- `The figure should be engaging and using academic journal style with cute characters`

这说明它的默认输出风格可能偏插画化、偏花，不一定自然契合
我们当前偏克制、偏 CVPR/ICRA 风格的版面。

若要实际使用，最好：

- 提供参考图压风格
- 生成后做一轮人工 SVG 清理

### 3. 不是完全矢量化流程

虽然它强调 editable SVG，但从实现路径看，最终 SVG 可能包含嵌入的 PNG 图标资产。
因此它更准确地说是：

- SVG 布局骨架
- 叠加部分位图图标资产

这对最终投稿图的精修和导出仍有影响。

### 4. 外部服务与保密风险

这是一条推断，但风险真实存在：

- 如果论文仍未公开
- 如果 method text 仍处于双盲投稿阶段
- 那么把方法段落直接发往外部模型服务或在线平台需要谨慎

### 5. 项目仍较新

根据 GitHub repo metadata：

- 仓库创建于 `2026-02-03`
- 最近一次 push 为 `2026-03-03`
- 截至 `2026-03-06` 公开 `open issues = 5`
- 当前没有公开 release

这说明它并非无人维护，但成熟度仍偏早期。

## 结论

最终建议是：`limited yes`。

更具体地说：

- **可以试用**
  - 仅限 methodology pipeline diagram 或系统总览图
- **不应依赖**
  - 不要把它当成整篇 paper 的统一科研插图方案
- **不要替代现有结果图管线**
  - 所有定量图、结果图继续使用脚本生成

最务实的落地方式是：

1. 用 `methodology.tex` 的三阶段文字喂给 `AutoFigure-Edit`
2. 同时提供一张风格参考图
3. 让它产出 SVG 草稿
4. 再用 `svg-edit`、Inkscape 或 Illustrator 做人工校正

## Sources Checked

- GitHub repo:
  - <https://github.com/ResearAI/AutoFigure-Edit>
- README:
  - <https://github.com/ResearAI/AutoFigure-Edit/blob/main/README.md>
- Core pipeline:
  - <https://github.com/ResearAI/AutoFigure-Edit/blob/main/autofigure2.py>
- Web backend:
  - <https://github.com/ResearAI/AutoFigure-Edit/blob/main/server.py>
- Requirements:
  - <https://github.com/ResearAI/AutoFigure-Edit/blob/main/requirements.txt>
- AutoFigure paper:
  - <https://openreview.net/forum?id=5N3z9JQJKq>
- arXiv mirror:
  - <https://arxiv.org/abs/2602.03828>
- GitHub repo metadata API:
  - <https://api.github.com/repos/ResearAI/AutoFigure-Edit>
- GitHub issues:
  - <https://github.com/ResearAI/AutoFigure-Edit/issues>

## 后续建议

如果后续决定真正试跑 `AutoFigure-Edit`，建议补一份更具体的使用记录，至少包括：

- 实际输入 prompt
- 参考图选择
- 生成出来的方法图草稿效果
- 最终人工修改量
- 是否满足投稿匿名与保密要求
