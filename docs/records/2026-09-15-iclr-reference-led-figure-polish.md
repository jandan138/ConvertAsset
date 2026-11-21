# 2026-09-15：ICLR 顶会参考驱动的多轮图表精修

## 目标与调查

用户认可已有论文结构，要求参考相近顶会的优秀图表，并实际进行多轮美化。
本轮沿用已有实验、分析结果、预测点和真实录制素材，不新增模型推理、仿真、渲染采集或扩样。
论文叙事结构保持，正文仅同步必要图注。前一轮图文和引用工作见
[论文提质记录](2026-09-15-iclr-paper-quality-refresh.md)。

主会话提供的原始 PDF 图页调研覆盖 VIMA、RoboPoint、Molmo/PixMo；
图表作者另核对 VIMA Fig. 4 与 RoboPoint Fig. 3。采用 `build-scientific-figures`、
`nature-figure` 的 Python 路线和独立 `render-visual-reviewer` 复查。
参考来源、采用与舍弃的设计元素及版本比较见
[设计复查记录](../../paper/venues/iclr27/visual_iterations/DESIGN_REVIEW.md)。
仅保存来源链接和设计笔记，不将外部论文图片打包为本论文素材。

## 设计和实现

| 图 | 本轮改变 |
| --- | --- |
| Fig. 1 / overview | 在 balanced、detail、compact 三种候选中选择 balanced；放大真实材质对照，定位分支增加显式来源框和局部放大，导航保留 99 个任务的单位网格及 30/99 主数字 |
| Fig. 2 / interventions | 四种条件使用相同 `(120,25,480,415)` 局部范围，完整画面条提供定位框，绿色框标出目标；命中计数保持 |
| Fig. 3 / protocol | 热图和计数表均使用 Normalized / Pixels 组标题，统一行基线与字号，提高辅助标签可读性 |
| Fig. 4 / navigation | 17 lost 与 13 gained 采用相反方向条形，区分 -4.0 pp 净变化与 30/99 changed，场景比较使用统一蓝橙点图 |
| Fig. 5 / trajectories | 将原有 1024×512 结束帧在 x=512 拆为两个 512×512 观察和地图列，三组案例严格对齐，像素内容不重绘 |

`paper/venues/iclr27/scripts/figure_style.py` 负责统一字体、语义色、导出、边界检查及来源登记；
新 `figure_overview.py` 管理三个总览候选和最终 figure-spec；
新 `figure_panels.py` 管理另外四张正文图。
`build_assets.py` 继续作为构建入口；共享来源注册表纳入四份生成脚本的哈希，
裁切范围另记于 `figures/crop_manifest.json`。导出为 SVG、PDF 与 360 dpi PNG。

定位放大图中两种条件的预测点均投影到明确标出的原图参考上；共同分支表示实验设计，
不表示两项评估共用同一画面或已经证明因果中介。导航案例继续来自独立定性录制，
不与主实验任务分数混配。主会话静态核对 InternNav evaluator 的 `common.draw_action_pil`
确认既有红色动作覆盖标注的来源；本轮没有启动该运行时。

## 实际迭代

- **Round 0：** 保存旧图、生成源和旧 PDF，作为比较基线。
- **Round 1：** 导出 balanced、detail、compact 三组 Fig. 1 SVG/PDF/PNG 候选。
- **Round 2：** 在 `visual_iterations/panel_work/round2/` 完成另外四张图，保存边界与裁切记录。
- **Round 3：** 独立审阅选择 balanced > compact > detail；修改总览网格密度与分支连接，澄清裁切框图例，加强 30/99 与 -4.0 pp 的视觉区分，保存六图与生成源快照。
- **Round 4：** 重建论文并按实际页面检查，保存最终快照和全部页面复查。保持图表宽松的几何尺寸，将轨迹图从 `H` 改为正常 `!t` 浮动，让结论填充第 7 页；浮动屏障仍在结论之后、正文结束标记及声明之前，Fig. 5 位于第 8 页并计入正文。此举减少第 7 页大块空白，没有缩小图或文字。

## 验证与交付状态

主会话确认最终结果，文档作者核对生成脚本与 panel handoff：

- `make -C paper iclr27-check`：PASS。正文及全部正文图在第 8 页结束，PDF 共 13 页。
- `python -m pytest -q tests/test_iclr_model_behavior.py tests/test_paper_layout.py`：**97 passed**，18.55 秒。
- 总览 figure-spec 严格校验：0 errors、0 warnings。全部来源、输出和四份生成器哈希一致。
- 六份 SVG 自包含、无活动脚本；17 个显式原图裁切范围合法；所有图中文字至少 7 pt。
- 独立复查将三种总览候选排序为 balanced > compact > detail；最终五张正文图均较 Round 0 改善，并通过实际论文页面对照。
- 主会话检查最终全部 13 页，精确绑定的复查保存在 `paper/venues/iclr27/VISUAL_REVIEW.json`，页面渲染位于 `build/visual_polish_final/`。
- `stage_submission.py`：PASS；本地候选 PDF 与最终 build PDF 字节一致。

最终 PDF SHA-256：

```text
e6580c4d6b86704f9fad2e747a623c7fe628282e6f3058f8d4287145fff4c0f5
```

原始分析结果的 SHA-256 保持不变：

```text
dea5ca75206bdaed906db00876357db0ff8c82558c1818f3e3977d7766e0babc
```

复建和回归入口：

```bash
make -C paper iclr27-check
python -m pytest -q tests/test_iclr_model_behavior.py tests/test_paper_layout.py
python paper/venues/iclr27/scripts/stage_submission.py
```

最终图位于 `paper/venues/iclr27/figures/`，候选论文位于
`paper/submissions/iclr27_candidate/main.pdf`。各轮记录位于
`paper/venues/iclr27/visual_iterations/`；`iterations.json` 记录四阶段过程，
`comparison/all_figures.pdf` 提供五页新旧对照，另有逐图比较 PNG 和来源哈希。

本轮只重新绑定引用上下文：14 个引用键、17 个上下文，严格状态保持
`REVIEW_REQUIRED`，没有新增引用来源调研或作者签认。既有引用审核的待确认项仍需
独立处理。本轮没有新增实验、提交 commit、推送或上传投稿系统。
