# 2026-09-15：ICLR 论文图表、叙事与引用提质

## 目标与调查

本轮响应用户对 ICLR 图表质量、正文故事性和引用可靠性的要求，明确**不新增实验**。
继续使用既有预测、修正后的 `analysis_v1/results.json`、导航配对 CSV 和真实录制画面；
不运行新模型推理、仿真、渲染采集或扩样。导航保留在正文。

调查覆盖 ACL Fig. 1 的既有设计经验、ICLR 图表生成与构建入口、正文与附录、
引用数据库及素材来源。ACL 的可复用经验是白底、真实图像主导、轻分组和清晰阅读顺序，
而不是将此前 ACL 图中文字和实验结构照搬到 ICLR。

本轮使用 `build-scientific-figures`、`nature-figure`（Python）、
`polishing-academic-papers`、`citation-integrity-auditor` 和 `render-visual-reviewer`。
所有图片来自现有素材，未生成新的 imagegen 资产，原始实验来源只读。

## 图表设计与实现

`paper/venues/iclr27/scripts/figure_style.py` 集中管理 Matplotlib 绘图，
`paper/venues/iclr27/scripts/build_assets.py` 继续从修正后的分析结果生成表格和数字宏，
并调用统一绘图入口。配色以蓝色表示 Original、橙色表示 Converted；注册 Liberation Sans，
以 DejaVu Sans 作为后备字体。真实图像按原始比例完整放入画框，不拉伸。

| 图 | 已实现的表达 |
| --- | --- |
| Overview / Fig. 1 | 干净来源的真实材质前后图为主视觉，连接定位与导航研究分支，突出净损失 4 个成功任务与 30/99 次成败变化；分支不表示已验证的定位到导航因果传递 |
| Interventions | 展示真实区域交叉替换及模型结果，以原始命中计数说明目标窗口、背景窗口和整体变化 |
| Protocol | 并列呈现命中率变化与 numeric output coverage，避免格式可解析性与命中率混为一谈 |
| Navigation | 相反方向的成败转移和场景配对点图，直接显示 17 次成功转失败与 13 次失败转成功的抵消 |
| Trajectories | 放大既有独立定性重跑的结束画面及原始地图片段，保留红色执行路径与绿色参考路径，增加对应图例 |
| Grounding | 统一模型、条件、成功率及成败变化的排版；交付独立配套图，论文附录采用对应表格 |

每张图导出 SVG、PDF 和 360 dpi PNG。`figures/geometry_checks.json` 记录文字画布边界、
数据线坐标边界和字号；这些程序检查不能替代对最终图像及 PDF 的人工式视觉检查。
`ASSET_PROVENANCE.json` 记录两份生成脚本、分析结果、图片来源及输出的 SHA-256。
共享来源注册表 `paper/shared/figures/sources.yaml` 保持 `build_assets.py` 为入口，
明确列出六张图的输出；辅助绘图脚本通过新增 `generators` 哈希清单纳入 artifact checker。

## 正文与引用

正文将 “Same Scene, Different Decisions” 的主要发现前置：平均成功率仅下降约
4 个百分点，却有 30/99 个导航任务改变成败。定位、区域干预和导航按发现与证据推进，
减少流程汇报腔、重复总结和反复自我设限，详细适用范围与来源说明集中到附录。
最终标题为 “Same Scene, Different Decisions: Material Shifts in Grounding and Navigation”，
排为两行；本地投稿 metadata 的标题与摘要已同步。
必要统计定义保留：numeric output coverage 包括解析出的越界数值，不能解释为有效命中；
固定分母、样本层级和数值转换保持原有修正口径。导航定性重跑图与 99 个主实验配对任务
的统计记录明确区分，不将重跑画面直接绑定到主实验分数。

ICLR 使用独立 `paper/venues/iclr27/references.bib`，覆盖实际引用的 14 条文献；
元数据修正不改共享 ACL bibliography。`citation_audit/` 保存审计报告、来源下载及哈希、
元数据修正和逐处引用上下文。自动来源核对、机器给出的支持建议与作者签认分开记录：
`human-support.json` 的未确认项不会自动转换为人工审查通过。

## 验证记录

最终结果由主会话执行并汇总，文档作者同时核对了 `VISUAL_REVIEW.json`、生成脚本及本地交付路径：

- `make -C paper iclr27-check`：PASS；正文 8 页，总计 13 页。
- `python -m pytest -q tests/test_iclr_model_behavior.py tests/test_paper_layout.py`：**97 passed**，最终运行 16.90 秒。首轮来源注册表的旧生成器引用导致 1 项失败，修复后全部通过。
- Overview figure-spec 严格校验：0 errors、0 warnings；素材来源与输出哈希全部匹配。
- 六张 SVG 均通过 XML 检查，图像自包含，无脚本或外部资源引用；文字及观测点边界检查均无错误。Protocol 最小字号为 6.8 pt，已在论文尺寸下检查可读性。
- 独立 image-only 视觉审查首轮 WARN，放大定位局部图、补上共同干预设计的分支连线、补齐颜色与网格图例、错开导航数值标签并标明地图路径后，最终 PASS。覆盖正文五张图在第 2、5、6、7 页的呈现及独立 Grounding 图。
- 主会话复查最终全部 13 页，无 Critical 或 Major 问题。参考文献最后一页的自然留白保留。哈希绑定的结论位于 `paper/venues/iclr27/VISUAL_REVIEW.json`，页面渲染留在 `paper/venues/iclr27/build/visual_review/`。
- 引用审计覆盖 14 个键、17 个引用上下文；13 份 TeX 与 5 份生成表格的绑定哈希一致，44 份下载来源文件哈希一致。严格报告维持 `REVIEW_REQUIRED`，机器解析状态与作者签认分别记录；未伪造人工支持关系审核。
- `python paper/venues/iclr27/scripts/stage_submission.py`：PASS；本地候选 PDF 与最终 build PDF 字节一致。

最终 PDF 的 SHA-256：

```text
b1562da54b7365eb393328367eba19bf58ec213f7fa8ed3ecfe53ac0df5547a3
```

## 来源与复现入口

本轮读取的证据包括：

- `paper/shared/evidence/raw/iclr_model_behavior/analysis_v1/results.json`：修正后的统计量。
- `paper/shared/evidence/raw/iclr_model_behavior/interventions_clean_v2/manifest.json`：干净图像对与区域交叉替换素材索引。
- `paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/paired_episode_transitions.csv`：99 对导航任务的转移与场景统计。
- `paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/`：独立录制重跑的清单及结束帧。
- `paper/shared/figures/fig_acl_method_chain_v4.png`：视觉层次与字体参考。

复建图表、检查论文及生成本地候选使用现有命令；`iclr27-check` 会重算既有记录并重建资产，不运行新实验：

```bash
make -C paper iclr27-check
python -m pytest -q tests/test_iclr_model_behavior.py tests/test_paper_layout.py
python paper/venues/iclr27/scripts/stage_submission.py
```

## 交付与剩余事项

候选 PDF 位于 `paper/submissions/iclr27_candidate/main.pdf`；可重建图表、素材来源记录和
引用审计位于 `paper/venues/iclr27/`。引用支持关系仍待作者独立签认，机器解析未完成的项
保留状态，不将自动核查表述为人工审查通过。

文档作者更新本记录及两个索引链接；字体显式注册经验分别记入 figure-generator 与
docs-writer 的角色记忆，避免新会话依赖陈旧 Matplotlib 字体缓存。
本轮未提交 git commit、推送远端或上传 OpenReview，保留现有工作区改动。
