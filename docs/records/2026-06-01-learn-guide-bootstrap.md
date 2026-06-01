# Learning Guide bootstrap — interactive HTML book under `learn/`

> 日期: 2026-06-01 · 类型: 新增 feature（教学文档 artifact）

## 背景 / 目标

新增一本 **静态 HTML 交互式电子书**：`ConvertAsset Learning Guide —
From GAMES101 to a Production USD Asset Pipeline`。面向只有 **GAMES101** 基础的读者，
把课堂渲染器知识桥接到本项目所处的生产管线（USD / PBR·MDL 材质 / mesh simplification /
glTF·GLB / GPU·RTX / Isaac Sim / embodied-AI downstream），并以 **ConvertAsset 本身 +
其论文** 作为贯穿全书的 case study。

约束（来自用户）：
- 受众 = GAMES101 水平。
- 中文叙述；**架构术语 / 命令名 / 性能指标 / 概念名保留英文**。
- 多用 interactive 控件、动画、live 3D viewer、真实 repo 代码与 CLI。
- **先收集 primary sources，再整合**，不只靠模型先验。
- 前端实现走 frontend-app-builder skill（Image-Gen concept → 审批 → 忠实实现 → 浏览器验收）。

## Research / Investigation（primary sources）

联网抓取并落盘以下权威来源，写作据此整合：
OpenUSD intro / composition·LIVERPS、UsdPreviewSurface spec + proposal v2.2、
NVIDIA MDL 1.5 spec + tech intro、Khronos glTF 2.0 spec + quick-ref、
Garland & Heckbert SIGGRAPH 97 QEM（+ CMU thesis）、LearnOpenGL PBR / BRDF crash course /
Disney PBS、NVIDIA Turing & Ampere GA102 whitepaper、Isaac Sim docs、VLNVerse(arXiv)。
案例部分基于本仓库 `convert_asset/**` 源码与 `paper/venues/acl27` abstract / claims。
完整 bibliography 见书内附录 `learn/chapters/appendix/bibliography.html`。

## 设计决策

1. **Placement = 顶层 `learn/`**（与 `paper/` 平级），不进 `docs/` 的 purpose-based
   taxonomy，避免污染分类；教学交互书是独立 artifact 类型。
2. **Stack = 自包含 static HTML/CSS/vanilla-JS，零构建**，CDN 取 three.js / KaTeX / fonts。
   契合 Python+LaTeX 仓库；`python -m http.server` 即可服务。
3. **粒度 = 每节一页**（约 75 个 section 页面，8 个 Part / 16 章 + 附录）。
4. **导航单一事实源 = `learn/content.js`**（`window.BOOK`），书壳 `book.js` 据此生成
   侧栏树 / on-this-page / prev-next / 进度。
5. **design system 锁定**（concept-01/02/03，Image-Gen 概念稿经用户审批）：纯白底、
   indigo `#5b5bd6` 主色、teal `#0fb5a6` 仅用于交互元素；serif 标题 / sans 双语正文 /
   mono 代码；三栏阅读布局；`.lab` 整宽交互面板。

## Code changes（本次新增文件）

- `learn/content.js` — 完整 TOC（Part→Chapter→Section）+ flat 列表。
- `learn/assets/css/book.css` — design system / 三栏布局 / code·math·lab / dark mode / 响应式 / 各 widget 样式。
- `learn/assets/js/book.js` — 书壳：sidebar 树、on-this-page scroll-spy、进度条、prev-next、主题切换、移动菜单、代码高亮+复制、KaTeX 引导。
- `learn/index.html` — 封面 + asset-journey 图 + 动态目录。
- `learn/_template.html` — 新增 section 页面的模板。
- `learn/README.md` — 打开方式 / 结构 / 授权规则 / token。
- `learn/widgets/*.js` — 交互件：`ggx-playground`(three.js)、`liverps-resolver`、
  `glb-dissector`、`pipeline-stepper`、`evidence-gates`、`qem-collapse`(Canvas2D)、
  `bvh-traversal`(Canvas2D)。
- `learn/chapters/**/*.html` — 各 section 页面（按章组织）。

## Testing

- 本地 `python3 -m http.server 8099` 起服务；路由 index / section / css / js 全部 200。
- 因 Cursor 浏览器无法访问远程 host 的 localhost，改用 **Playwright Chromium headless**
  （node 24）截图 + 控制台捕获（fallback reason: IAB 网络隔离）。
- 已验收：landing、section `3-4 Cook-Torrance`、GGX lab —— 侧栏树高亮当前节、
  KaTeX 公式渲染（15 个，无裸 `$$`）、WebGL 球渲染并响应控件、prev-next / on-this-page
  正常，**0 console error / 0 request failure**。视觉与 concept-01/02/03 一致。
- 全部 widget `node --check` 通过。

## Open issues / 后续

- 其余 section 页面正在批量产出；完成后需：① 把上述 widget 用 `<script type="module">`/
  classic script 接到对应 section（mount id：liverps/qem/glb/pipeline/bvh/gates-mount）；
  ② 跨全部页面跑一次 headless QA sweep（链接、KaTeX、console error）；
  ③ 内容准确性校订（subagent 产出需复核 spec 数值与 repo 行为）。
- `theme-toggle` 图标已从 unicode 改为内联 SVG（避免字体缺字）。
