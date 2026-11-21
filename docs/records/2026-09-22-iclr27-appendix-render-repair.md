# 2026-09-22 — ICLR27 附录异常红色渲染修复

## 背景与当前状态

用户在准备替换 OpenReview 投稿 PDF 时发现附录 Isaac Sim 渲染图存在异常红色，要求逐图定位并修复。本记录区分历史实验输入与用于附录展示的新渲染，避免把材质修复后的图像误写成历史模型实际接收的输入。

**修复与验收已完成：五个案例的十张配对图均已重新渲染并通过主会话视觉检查，最终 33 页 PDF 已重新 staging。**

## 定位结果

以下位置已在最终 `paper/submissions/iclr27_candidate/main.pdf` 中重新核对。

| PDF 位置 | 异常面板 | 样本 ID |
|---|---|---|
| 第 24 页，Figure 14 | Backpack / Original | `47aa36277a54f6ca90cc.zoom_019` |
| 第 24 页，Figure 14 | Clock / Original | `f35ef3d86c42446b7ddf.zoom_019` |
| 第 25 页，Figure 15 | Cup / Original | `bb985fd4504a1afe8516.zoom_017` |
| 第 25 页，Figure 15 | Faucet / Original | `c8ee4b66274b05d242c2.zoom_017` |
| 第 25 页，Figure 15 | Picture 背景 / Original | `ef6a4fe9448f672c2ecc.zoom_017` |

主会话定位交接确认：五张旧 Original 图片对应的历史日志包含 MDL 模块解析或着色器创建错误；当前依赖中的 KooPbr 绝对导入已经修复，但修复前的附录仍引用旧截图。在本轮已分析的预测来源中，每张旧图的哈希均匹配 41 行预测记录。该结果仅描述已分析来源，不能据此推断尚未审计的数据范围。

最终 33 页 PDF 已以联系表逐页复查，第 24、25 页另外进行全尺寸检查。其余附录未发现同类大面积红色故障；导航轨迹的红色标注不属于此次材质故障。

## 决策与数据边界

- 按用户确认范围仅修复附录定性展示；五个案例均重新生成 Original / Converted 配对，共十张图片。
- 不重跑模型，不改历史预测、数值或原图；新图不是历史读出实验的输入，旧预测不能被解释为在新图上的预测。
- 沿用保存的相机、几何、灯光、600×450 分辨率及 RTX 设置，直接复用已修复的 MDL 依赖；本轮没有修改材质文件，也没有对图片调色或裁剪。
- Figure 1 保持原状，包括此前确认保留的 Parse / Align 文字。
- 附录正文和图注已明确：新展示为修复 MDL 依赖后的定性重渲染，历史实验包含渲染故障输入。

## 实施

- 新图与来源清单位于 `paper/shared/evidence/raw/iclr_model_behavior/appendix_rerender_v1/`；外部运行副本位于 canonical assets root 下的 `experiments/grscenes/appendix_rerender_20260922/`。
- 新增 `paper/shared/evidence/experiments/11_iclr_model_behavior/rerender_appendix.py`，记录新旧图哈希、相机与场景来源、渲染命令、日志及逐图审查。
- 新增 `paper/venues/iclr27/scripts/appendix_render_sources.py`：限定五对图片和版本目录，校验 SHA256、拒绝旧 Original 哈希，检查渲染就绪、材质错误与逐图视觉审查。缺图、哈希不符或未通过审查时构图失败，不回退旧图。
- `figure_supplement.py`、`check_submission.py` 接入新来源与检查；`paper/venues/iclr27/appendix/05_grounding_results.tex` 更新正文及图注，说明历史读出包含渲染故障输入，重渲染图没有预测叠加，也不承载历史预测结果。公共 CLI 未变。
- 新增 `tests/test_iclr_appendix_rerender.py` 回归覆盖；Figure 1 及其他 13 张附录图版 PNG 均未变化。

## 验证结果

验证命令与结果由主会话交接，并以版本目录内的 `audit.json` 和 `manifest.json` 留档：

| 检查 | 结果 |
|---|---|
| 五对、共十张新图 | 均成功捕获；每张图的五项材质诊断计数均为零 |
| 逐图目标、背景、反射及配对视角 | 主会话逐张检查通过；不是独立审查 |
| 历史图片与预测来源 | 354 个文件哈希未变 |
| 渲染运行来源 | 1694 个文件哈希未变；没有修改材质文件 |
| 数值表格、CSV 与 Figure 1 来源 | 15 个文件哈希未变；Figure 1 PNG 字节一致 |
| `python -m pytest -q tests/test_iclr_appendix_rerender.py tests/test_paper_layout.py` | 101 passed，19.45 秒 |
| `make -C paper iclr27-stage` | 成功，检查器零失败；正文结束于第 9 页，PDF 共 33 页 |
| PDF 视觉复查 | 33 页联系表检查；第 24、25 页全尺寸检查通过 |

Original 图片的强红像素筛查变化如下（百分比）：

| 案例 | 旧图 | 新图 |
|---|---:|---:|
| Backpack | 57.3607 | 0 |
| Clock | 11.3904 | 0 |
| Cup | 24.1393 | 0.2456 |
| Faucet | 35.6789 | 0 |
| Picture | 1.0563 | 0.3189 |

残留红色为杯子场景中的水果及局部暖色地面材质，已结合图像逐一确认。强红比例只是辅助筛查，不能用来直接判定材质故障。渲染器仍输出既有 mesh-normal / extension 警告，但没有剩余材质故障。

视觉证据保存在 `paper/venues/iclr27/visual_iterations/appendix_repair_20260922/`：`pdf_review.json`、`page-24.png`、`page-25.png` 与 `before_after.png`。原始审计位于 `paper/shared/evidence/raw/iclr_model_behavior/appendix_rerender_v1/audit.json`，来源清单视觉审查状态为 `PASS`。

## 交付与历史数据限制

最终 PDF：`paper/submissions/iclr27_candidate/main.pdf`，33 页，44,438,198 字节。

```text
SHA256 9442d2265f561f442e09ce626f3004cf49dbc84899493b3d59216400b821fbb1
```

本轮只修复附录展示。原始故障图片、历史模型回复与分数继续保留，没有新推理，也未将历史结果移植到重渲染图上。既有分析器报告的 16 条历史 changed-image 记录是修复前已存在的问题，实验入口 `paper/shared/evidence/experiments/11_iclr_model_behavior/README.md` 已说明两个旧 canonical 文件各引用八张后来被替换的图片；本次 354 个历史来源文件哈希保持不变，不能把这 16 条记录解释为本次修复造成的变化。
