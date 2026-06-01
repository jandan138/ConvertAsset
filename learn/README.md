# ConvertAsset Learning Guide

一本 **静态 HTML 交互式电子书**：`From GAMES101 to a Production USD Asset Pipeline`。
面向只有 GAMES101 基础的读者，从课堂渲染器桥接到真实的 3D-asset & real-time rendering
生产管线，并以本仓库 **ConvertAsset** 与其论文作为贯穿全书的 case study。

> 叙述用中文；所有 **架构术语 / 命令名 / 性能指标 / 概念名保留英文**（符合论文阅读习惯）。

## 如何打开

本书零构建（no build step），但因为用了 `fetch` 之外的相对资源与 ES module widget，
**推荐用本地 http server 打开**（直接双击 `file://` 时 three.js widget 可能受 CORS 限制）：

```bash
cd learn
python3 -m http.server 8099
# 浏览器访问 http://localhost:8099/index.html
```

依赖均走 CDN（无需 npm）：
- [three.js](https://unpkg.com/three@0.160.0/) — 3D / WebGL 交互件
- [KaTeX](https://cdn.jsdelivr.net/npm/katex@0.16.9/) — 数学公式
- Google Fonts：Newsreader（serif 标题）/ Inter + Noto Sans SC（双语正文）/ JetBrains Mono（代码）

## 目录结构

```
learn/
  index.html                 # 封面 + 目录（目录由 content.js 动态生成）
  content.js                 # ★ 导航单一事实源 (window.BOOK)：Part → Chapter → Section
  assets/css/book.css        # design system：tokens / 三栏布局 / code / math / lab 面板 / dark mode
  assets/js/book.js          # 书壳：侧栏树 / on-this-page / 进度 / prev-next / 主题 / 代码高亮 / KaTeX
  widgets/                   # 可复用交互件（ES module，import map 解析 three）
    ggx-playground.js
  chapters/<NN-slug>/<id>-<slug>.html   # 每节一页
  chapters/appendix/...      # glossary / cli-cheatsheet / bibliography / math-refresher
  _template.html             # ★ 新增 section 页面的模板（复制它）
```

## design tokens（实现已锁定，勿随意改）

| token | light |
|---|---|
| `--bg` | `#ffffff`（纯白，勿改成米白） |
| `--ink` | `#16161d` |
| `--accent`（indigo，主色） | `#5b5bd6` |
| `--interactive`（teal，仅用于交互元素） | `#0fb5a6` |
| `--panel`（lab 面板底） | `#f7f7fb` + 1px hairline |
| 字体 | serif 标题 / sans 双语正文 / mono 代码 |

## 如何新增一节

1. 在 `content.js` 对应 chapter 的 `sections[]` 里加一条 `{ id, t, href }`（导航会自动出现）。
2. 复制 `_template.html` 到 `href` 指向的路径，改 `<body data-section-id>` 与正文。
3. `data-root` 一律 `"../../"`（section 页面都在 `chapters/<chapter>/` 两层深）。

### 可用的内容 CSS class（来自 book.css）

- `.reading` 包裹正文；`h1`/`h2[id]`/`h3`/`p`/`p.lead`
- `.eyebrow` — H1 上方的 `PART X · 标题`
- `.term` / `.term.term-accent` — 行内英文术语/概念高亮
- `.bridge`（`.ttl` = `From GAMES101`）— 桥接已学知识
- `.callout` / `.callout.warn` / `.callout.recap` — 提示框
- `.math-block` — 居中公式条（KaTeX，`$$...$$` 或 `\(...\)`）
- `.code`（`.code-head` + `.fname` + `.copy` + `<pre><code data-lang="python|json">`）— 代码块
- `.lab`（`.lab-head` + `.lab-tag` "互动 · Interactive" + `.lab-title` + `.lab-body` + `.lab-note`）— 交互件外壳

### 加交互件

在 `.lab-body` 里放一个挂载点 `<div id="xxx-mount"></div>`，并在页面底部加：

```html
<script type="importmap">{ "imports": {
  "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
  "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
}}</script>
...
<script type="module" src="../../widgets/xxx.js"></script>
```

（import map 仅在用到 three.js 的页面需要；纯 SVG/Canvas 2D 件可省。）

## 设计与资料出处

课程大纲、placement 决策与 primary-source bibliography 见
`docs/records/2026-06-01-learn-guide-bootstrap.md` 与本书附录 `chapters/appendix/bibliography.html`。
内容基于 OpenUSD / UsdPreviewSurface / NVIDIA MDL / Khronos glTF 2.0 / Garland-Heckbert QEM /
NVIDIA Turing·Ampere whitepaper / Isaac Sim 等 primary sources 整合，而非仅凭模型先验。
