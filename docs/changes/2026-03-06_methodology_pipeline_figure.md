# 2026-03-06 Methodology Pipeline Figure

## 状态更新

截至 `2026-03-06` 的最新 team conclusion：

- 当前已经接入论文的 methodology pipeline figure，应按**人工绘制 / 人工收敛后的临时图**定性
- 它**不是**通过 `AutoFigure-Edit` 生成的官方最终图
- 因此，它**不满足**用户新增的更严格要求：final paper figure 必须经由 `AutoFigure-Edit` 产出
- 当前仓库中这张已入稿的图，只能作为 manuscript 草稿阶段的 provisional background，不应被记录成 compliant final figure

这一定性覆盖了本文件早先“已完成最终图接入”的表述。下文仍保留既有实现经过，但仅作为背景记录。

## 官方替换状态

当前 official replacement 处于 **blocked**，直到 provider 与 SAM 相关凭据就位为止。

### Blocker Matrix

| 环节 | 最低要求 | 当前状态 | 结论 |
|---|---|---|---|
| Provider 生成步骤 | 至少提供一组可用 provider key；这是 mandatory，不存在无 key 的 official path | 未提供 | 无法启动 `AutoFigure-Edit` 的生成主流程 |
| SAM / 分割步骤 | 需要可用的 SAM 能力；当前推荐的最小外部路径是 `Roboflow` | 未提供 | 无法完成图标区域分割与后续编辑链路 |
| Web 路径 | 不能把 Web UI 视为匿名兜底方案 | 当前 web path not anonymous | 不能在无凭据条件下作为正式替换方案 |
| 推荐最小可落地路径 | `OpenRouter` + `Roboflow` | 两侧凭据均未提供 | 官方替换继续 blocked |

换言之，当前最务实的 unblock 条件是：

1. 提供一个可用的 provider key，推荐最小路径是 `OpenRouter`
2. 提供一个可用的 SAM 侧凭据，推荐最小路径是 `Roboflow`

在这两项都具备之前，团队不能把当前论文中的图升级为符合要求的 official final figure。

## 背景

本记录最初用于沉淀一次方法图接线工作：先把一张 methodology pipeline figure
放入仓库，并接入 `paper/writing/sections/methodology.tex`，用于论文草稿排版、
review 响应和 narrative 收敛。

按最新结论回看，这一阶段的目标是“先有一张可用的草稿图”，而不是证明最终图
已经满足 `AutoFigure-Edit` 合规要求。

因此，本文件下半部分描述的内容应理解为：

- 已经完成过一轮 writing-side asset 接线
- 已经验证过 manuscript 中插图位置与 LaTeX 引用方式
- 但这些都只是后续 official replacement 的前置背景，而不是最终完工证明

## 调研与设计结论

本次实现延续了同日的两条流程结论：

- `docs/changes/2026-03-06_autofigure_edit_research.md`
- `docs/changes/2026-03-06_paper_figure_asset_placement.md`

核心设计决策如下：

1. 方法图作为 writing-side asset 管理，而不是放入 `paper/results/figures/`
2. 只提交最终 curated 资产，不提交中间掩码、日志、run 目录
3. 为了可复现与便于继续迭代，同时保留：
   - 可编辑源文件：`SVG`
   - LaTeX 直接引用文件：`PDF`
   - 预览文件：`PNG`
4. 图的视觉风格保持克制、论文化，不引入插画化或第三方 branding

## 已有接线与资产落点

以下内容仍然有效，并继续作为后续官方替换时的落点约束：

### 新增图资产目录

- `paper/writing/figures/`

### 论文章节接线

- `paper/writing/sections/methodology.tex`

该位置此前已经接入：

- `figure*` 环境
- caption
- label `fig:method_pipeline`
- 正文中的 `Figure~\ref{fig:method_pipeline}` 引用

这部分说明 writing-side asset placement 与 LaTeX wiring 已经打通；后续若拿到
合规的 `AutoFigure-Edit` 结果，替换时优先沿用这一接线路径。

## 当前已入稿图的定性

按最新团队结论，当前真正进入论文的图应被视为：

- 人工绘制 / 人工收敛的临时图
- 用于当前 manuscript 的版面占位与叙事辅助
- 不满足“final paper figure 必须由 `AutoFigure-Edit` 生成”的 stricter requirement

这意味着当前图的存在价值主要是：

1. 证明 methodology 部分确实适合放一张 pipeline figure
2. 证明 `paper/writing/figures/` 与 `methodology.tex` 的接线可工作
3. 为后续基于 `AutoFigure-Edit` 的正式替换提供 caption、label、版式参考

## 既有实现历史（保留作为 provisional background）

以下内容保留，用于说明此前为了尽快推进论文草稿，团队曾做过哪些接线与草稿生成尝试。
这些记录不应再被解读为 official figure provenance。

### 历史草稿生成脚本

- `paper/writing/figures/gen_method_pipeline.py`

本文件早先记录过一个本地脚本化方案，用于快速生成方法图草稿并验证接线。该历史记录保留，
但它只代表一轮前期尝试，不代表当前论文最终图已经满足 `AutoFigure-Edit` 来源要求。

该脚本历史上曾生成：

- `paper/writing/figures/fig_method_pipeline.svg`
- `paper/writing/figures/fig_method_pipeline.pdf`
- `paper/writing/figures/fig_method_pipeline.png`

### 草稿图内容

该图聚焦 `Methodology` 中的三阶段转换流程：

1. `Traverse`
   - 收集 sublayers / references / payloads / variants / clips
   - 不 flatten
   - cycle detection + de-duplication
2. `Convert`
   - 每个文件独立执行 MDL -> UsdPreviewSurface
   - 显示 4 个主要映射通道
   - 提示 advanced MDL features 被丢弃
3. `Rewrite`
   - 将 composition arcs 指向 sibling `*_noMDL.usd`
   - 保留 scene structure

同时图中保留：

- 输入：MDL-based USD scene
- 主输出：converted USD
- 次级用途：GLB / Eval

## 历史验证记录

以下命令是此前草稿接线阶段执行过的验证，保留作为实现背景：

```bash
python paper/writing/figures/gen_method_pipeline.py
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

验证结果：

- 图资产成功生成到 `paper/writing/figures/`
- `paper/writing/main.tex` 可成功重新编译
- 一版方法图曾成功进入 `paper/writing/main.pdf`

这些验证只能证明“图资产接线和论文编译可行”，不能证明当前入稿图满足
`AutoFigure-Edit` 合规来源要求。

## 影响范围

本次变更不修改：

- `paper/results/raw/`
- `paper/results/figures/`
- 实验脚本
- `convert_asset/` 代码

相关历史实现仅涉及论文写作侧资产与对应章节引用，不触及 `convert_asset/` 代码。

## 当前限制与后续条件

1. 当前已入稿图不满足“final figure 必须来自 `AutoFigure-Edit`”这一更严格要求
2. 在 provider key 与 SAM 侧凭据补齐前，official replacement 无法开始
3. 即便后续拿到凭据，也仍需对生成结果做人审、术语校对和版式清理后才能替换入稿
4. 当前 `figure*` 全宽布局、caption、label 可复用，但图内文案与视觉元素应以正式替换版本为准
