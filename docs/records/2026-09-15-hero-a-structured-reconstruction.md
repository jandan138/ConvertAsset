# 2026-09-15：Hero A 结构化复刻与真实素材替换

> 任务开始：2026-09-15；完成与最终复查：2026-09-16。

## 目标与调查

用户认可既有 Fig. 1，同时希望将宣传式 A 候选基本复刻为结构更清楚、可编辑的系统总览。批准两版并排比较：玻璃核心和矢量核心；左侧采用 ACL 材质球，场景和导航使用已有真实记录。此次交付独立放在 `paper/shared/figures/tmp/hero_A_structured/`，不接入论文。

主会话采用 `build-scientific-figures`、`research-figure-ai-slot-composer` 和 imagegen 工作流。调查 A 参考、ACL 四组球体来源、ICLR 干净干预 manifest、Qwen3-VL-2B 已保存预测及导航结束帧。文档作者核对 `prepare_evidence.py`、`evidence_manifest.json`、`build_hero.py`、装置提示词及现有审计输出。

## 设计与实现

两版共用 12×6 英寸白底横幅和蓝橙条件配色；左侧材质对照、中央 ConvertAsset、右上定位和区域探针、右下导航保持 A 的阅读顺序。左侧成对素材以关联关系连接转换器，避免表达成转换已完成后又进入转换器。中央明确 MDL 到 UsdPreviewSurface；玻璃版的无字装置经 imagegen 单独生成，矢量版使用原生模块。

新目录中的 `prepare_evidence.py` 仅打包已有素材及元数据；`build_hero.py` 以统一布局生成两版 SVG、PPTX、PDF、PNG、图形规范和几何检查记录。文字、线、箭头、目标框及预测点均可编辑，位图独立嵌入。PPTX 经 LibreOffice 实际导出，Ghostscript 生成 PDF 1.5，Poppler 输出 300 dpi PNG；另将 SVG 经 LibreOffice 独立渲染用于比较。

| 素材 | 来源与处理 |
| --- | --- |
| 木、石、陶瓷、金属八张球体 | ACL `fig1_material_pairs_v1` 逐文件字节复制；作为材质概念插画 |
| 玻璃核心 | A 参考的无字独立装置，提示词和透明留白裁切记录保存在 assets；不作为实验素材 |
| 四个定位输入 | `board02.q0.side0` 的 Original、Converted、Target、Context 完整 1216×450 输入及已有预测 |
| 两张导航地图 | `kujiale0036_0066` 的 `898_898` 独立定性录制，原始结束帧右半部 `(512,0,1024,512)` 无损裁切 |

预测原始坐标为 normalized-1000；按完整输入尺寸转为像素后，Original 为 `[304,180]`（命中），Converted 为 `[404.928,202.5]`（未命中），Target 为 `[364.8,135]`（命中），Context 为 `[304,180]`（命中）。主读出使用 Original／Converted 对应记录；区域探针作为独立辅助输入面板，显示各自完整 crossover 输入中 `[120,25,480,415]` 的精确局部，完整视图灰框标出对应范围。导航保留红色执行／绿色参考路径，原始和转换录制帧号分别为 106 和 382；取景可能不同，不贴入主运行分数。

## 迭代记录

1. 保存 A 参考与受保护来源基线，准备八张球体、四张完整定位输入和两张地图。
2. 从同一布局导出玻璃、矢量两版，保存首轮图和生成器快照。
3. 根据首轮复查拆分蓝、橙独立 VLM 路径，修正输入输出对应；将 Target／Context 置于独立区域探针面板，加入目标框图例。
4. 调整玻璃核心副标题为两行并避开装置边缘，收紧矢量说明与模块间距；保存下一轮快照，重新导出两版。

5. 放大 Target／Context 局部并逐像素验证，与完整视图灰框对应；明确 Target／Prediction 图例，修复对比度及预测图例间距。
6. 通过种子连接的中性像素测量玻璃面板安静区域，确认 21 pt 标题与两行副标题的文字边界落在该区域内；两版及 5.5 英寸宽预览最终独立视觉复查均 PASS。

## 验证与复建

素材准备由 evidence agent 校验：八张球体字节一致，四张输入尺寸与来源哈希匹配，预测样本身份／目标／坐标系一致，两张地图裁切像素与源图相应区域一致。最终 `geometry_qa.json` 两版文字边界和文字框相交检查均 PASS，字号为 15.5／18／21／28 pt，按 5.5 英寸图宽最小约 7.10 pt。

主会话最终确认并由文档作者核对审计产物：

- 两份 figure-spec 严格校验均为 0 errors、0 warnings。
- 玻璃版原生 PPTX：118 个形状、33 个文本、15 张图片、52 个词；矢量版：119 个形状、33 个文本、14 张图片、53 个词。两版均无外部关系、机器路径、主题效果及审计违规。
- 直接核对原生 PPTX 预测点对象，位置与完整 1216×450 输入上的已保存 Original／Converted 坐标一致。区域局部和导航右半幅裁切均逐像素一致。
- 全部来源及预测哈希一致，受保护的 `main.tex`、`main.pdf`、`overview.png` 和 A 参考哈希一致。
- 实际 PPTX→LibreOffice PDF→PNG 与独立 SVG→LibreOffice PDF→PNG 可见一致，两版及 5.5 英寸宽比较均通过独立视觉复查。

```bash
python paper/shared/figures/tmp/hero_A_structured/prepare_evidence.py
python paper/shared/figures/tmp/hero_A_structured/build_hero.py --variant both
python paper/shared/figures/tmp/hero_A_structured/measure_hub.py
python paper/shared/figures/tmp/hero_A_structured/review_exports.py
```

依赖、导出文件和 schema 说明见 [候选目录 README](../../paper/shared/figures/tmp/hero_A_structured/README.md)。最终审阅以重新导出的文件及其哈希为准，不沿用旧快照的结论。

## 交付与边界

交付两版可编辑 PPTX、自包含 SVG、PDF、高清 PNG、素材清单、构建脚本与迭代快照；另有 `comparison_at_paper_width.pdf/png` 双版实尺寸比较和 `comparison_with_reference.pdf/png` 参考加双版比较。`artifact_manifest.json` 记录来源、代码和导出哈希及迭代笔记，`validation.json` 汇总最终验收。重新运行导出复查脚本会重置视觉状态，须针对新产物再次目视确认。真实记录图像不经 imagegen 修改；只有材质球和中央装置承担概念说明。定位与导航为并行研究分支，采用各自的场景记录。

此次未新增实验、推理或仿真，没有改写既有论文或 Fig. 1，也未执行 commit／push／upload。下一步由用户查看两版候选后选择视觉方向。
