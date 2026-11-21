# paper-figure-generator Memory

只记录稳定的、项目级的、跨会话仍有价值的图表经验。

- 记录颜色规范、尺寸约定、输出格式要求
- 不记录单次出图的临时审美意见

- ACL 主文图的稳定视觉编码：结构/Original MDL 使用 `#0F4D92`，noMDL 使用
  `#E67E22`，通过/保留使用 `#168A45`，InternNav 执行轨迹使用
  `#7A40C8`，NVIDIA baseline 使用中性灰 `#6B7280`。
- ACL 主文 Python 图稿以 7.2 英寸双栏宽度生成，交付 SVG（可编辑文本）、
  PDF（LaTeX）和 300 dpi PNG；真实渲染在 PDF 中应保持至少 300 ppi。
- ACL-only 改图使用版本化新文件并由 venue wrapper 引用，避免覆盖 AAAI 或
  supplement 仍在使用的共享历史资产。
- Story-first 方法图的稳定复杂度门槛：不超过 100 个 shape、35 个文本对象、
  100 个词和 4 档字号，最小字号不低于 6 pt；同时必须在最终论文页尺度复核。
- 生图只承载可替换的解释性位图组件，真实实验依据、文字、箭头和版式继续由
  已登记数据与确定性代码控制；论文 caption 和 manifest 都要声明证据边界。
- 从生成图集裁切透明组件时，只保留 alpha mask 的最大连通域，以去除脱离主体
  的阴影和碎片；成对组件还应检查质心和可见高度的一致性。
- 论文 hero schematic 可用 `python-pptx` 生成原生可编辑母版，但正式验收必须
  经过 LibreOffice 的 PPTX -> PDF -> PNG 回渲；仅检查 slide XML 不足以发现
  字体替换、文本裁切和连接线漂移。
- PPTX 图稿统一使用 Linux 可用的开放字体、显式文本框、固定换行和字体实测；
  禁用自动缩放、主题效果与阴影，并用 `audit_pptx_figure.py --require-flat` 审计。
- Matplotlib 论文图中的 `fig.text` 不提供隐式右边界；左侧行标签靠近图片网格时，
  应使用固定右对齐锚点、显式换行和 renderer bounding-box 检查，不能只凭归一化
  起始坐标判断是否留有 gutter。
- ACL 双栏尾部出现大块留白时，先检查 double-column float 队列与强制分页；在最终
  页序视觉验收通过的前提下，可允许第三个顶端双栏浮动并适度提高 `dbltopfraction`，
  不应优先缩小已经可读的论文图。
- ARR/ACL 的 Limitations 与 Ethical Considerations 属于不计页区域，不能包含新的
  figure/table、实验或分析；主文证据图必须在 Results 的浮动队列中并于 Conclusion
  之前落版，不能利用 post-Conclusion 浮动“借用”不计页空间。
- 生图 atlas 的视觉网格不保证 alpha 组件严格落在等分 cell 内；切分前应在全图上
  找显著连通域并按质心映射槽位，同时检查轮廓首末有效扫描行相对最大直径是否过宽，
  以捕获材质球被行边界削平的情况。

- Isaac Python 的 Matplotlib 字体缓存可能漏掉系统已安装的 Liberation Sans；出图前用 `font_manager.addfont` 显式登记字体，并为图例符号保留 DejaVu Sans fallback，避免静默替换与缺字。
- ICLR 附录诊断图通过 `appendix_render_sources.py` 读取独立的已审查重渲染清单；不要重新从共享 legacy atlas 常量取图，也不要覆盖历史推理输入。材质依赖已修好不代表旧 PNG 已更新，需核对实际图片哈希与渲染日志。
