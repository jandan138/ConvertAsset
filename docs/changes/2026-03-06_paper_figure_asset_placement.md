# 2026-03-06 Paper Figure Asset Placement

## 背景

本记录用于沉淀一次 agent-team 调研后的流程结论：对于一张由外部工具
（例如 `AutoFigure-Edit`）生成的 methodology pipeline diagram 或 system overview，
是否可以直接放进本仓库的 `paper/` 目录，以及应该放到哪里。

本结论形成于 `2026-03-06`，依据是当前本地 `paper/` 目录结构、LaTeX 引图方式，
以及已有 review comments 对方法图缺口的指向。

## 当前 paper 结构

当前 `paper/` 目录中的图形资产大致分成两类：

- `paper/results/raw/`
  - 原始实验数据
- `paper/results/figures/`
  - 结果图（PNG + PDF）
- `paper/writing/sections/`
  - 论文章节源码

现有正文中的 `\includegraphics` 路径也都指向 `paper/results/figures/`，
例如：

- `paper/writing/sections/results.tex`
- `paper/writing/sections/discussion.tex`

同时，`paper/results/gen_figures.py` 与 `paper/EXPERIMENT_CHECKLIST.md`
都把 `paper/results/figures/` 视为**实验结果图输出目录**。

因此，从当前仓库语义上看：

- `paper/results/figures/` = 实验结果图
- 生成式方法图 / 系统总览图 ≠ 实验结果图

## 结论

结论是：**可以把最终方法图放进 `paper/`，但不应把整套原始生成产物直接扔进 `paper/`。**

更具体地说：

- 应该放进仓库的是**人工筛选和清洗后的最终交付版本**
- 不应该放进仓库的是一次生成 run 的原始中间产物集合

## 推荐位置

### 首选位置

首选位置是：

- `paper/writing/figures/`

推荐命名方式：

- `paper/writing/figures/fig_method_pipeline.svg`
- `paper/writing/figures/fig_method_pipeline.pdf`
- `paper/writing/figures/fig_system_overview.svg`
- `paper/writing/figures/fig_system_overview.pdf`

选择 `paper/writing/figures/` 的原因：

1. 这些图属于 manuscript asset，而不是 results artifact
2. 与 `paper/writing/sections/*.tex` 的语义更一致
3. 后续在 `paper/writing/sections/methodology.tex` 中引用路径自然，例如：

```latex
\includegraphics[width=\linewidth]{../figures/fig_method_pipeline.pdf}
```

4. 可以避免把“实验脚本生成图”和“人工/LLM 生成的论文静态图”混在一起

### Fallback 位置

如果目标是**零重构、最快接入 LaTeX**，fallback 才是：

- `paper/results/figures/`

例如：

- `paper/results/figures/fig_method_pipeline.pdf`

这是技术上可行的，但不是语义上最干净的放法。原因在于：

- 它会把 methodology figure 和 results figure 混在一起
- 后续维护时更难区分哪些图来自实验脚本，哪些图来自手工/外部工具

## 允许提交到仓库的内容

推荐只提交**最终 curated 版本**：

- `*.svg`
  - 作为可编辑源文件
- `*.pdf`
  - 作为 LaTeX 优先引用版本
- `*.png`
  - 仅在确有需要时保留，用于快速预览或兼容场景

如果只保留最小集合，优先级建议是：

1. `SVG` editable source
2. `PDF` LaTeX final asset

## 不应提交到 `paper/` 的内容

以下内容不建议直接落进 `paper/`：

- 原始 `figure.png`
- `sam.png` / `samed.png`
- `boxlib.json`
- `icons/` 或 icon crops
- 整次 run 的输出目录
- 运行日志
- 未命名、未经人工检查的 `final.svg`

这些文件更适合：

- 临时目录
- 外部实验目录
- 单独的草稿/缓存目录

而不是作为论文正式资产进入 `paper/`。

## 入库前质量门槛

一张生成式方法图在进入 `paper/` 前，至少应满足以下条件：

1. **术语一致**
   - 图中的阶段名、模块名、箭头语义必须与
     `paper/writing/sections/methodology.tex` 保持一致
2. **风格收敛**
   - 不能保留过强的插画化、卡通化或与论文版式冲突的视觉风格
3. **无外部污染**
   - 不得包含 provider logo、水印、聊天式文案、无关装饰
4. **文件命名规范**
   - 使用项目内可读文件名，如 `fig_method_pipeline.*`
5. **LaTeX 可用**
   - 至少提供一份实际可引入的 `PDF`
6. **人工校对完成**
   - 已检查文字、配色、字体、对齐和箭头关系

## 与 review comments 的关系

本结论还受到 review comments 的直接影响。

当前 review 明确指出 methodology 部分缺少 pipeline architecture diagram，
因此这类图确实值得补；但 review 并没有要求新增更多 results figures。

这进一步支持以下判断：

- 方法图应作为 writing-side asset 管理
- 不应伪装成 `results/figures/` 中的一部分

## 最终建议

最终建议可以压缩成一句话：

**可以把生成的一张方法流程图或系统总览图放到 `paper/` 下，但只应提交人工清洗后的最终版本；首选位置是 `paper/writing/figures/`，只有在追求零结构改动时才退回 `paper/results/figures/`。**

## 本次核查涉及的本地文件

- `paper/writing/main.tex`
- `paper/writing/sections/methodology.tex`
- `paper/writing/sections/results.tex`
- `paper/writing/sections/discussion.tex`
- `paper/results/gen_figures.py`
- `paper/EXPERIMENT_CHECKLIST.md`
- `paper/reviews/action_items.md`
