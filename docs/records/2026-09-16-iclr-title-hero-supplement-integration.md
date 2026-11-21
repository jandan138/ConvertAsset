# 2026-09-16：ICLR 标题、系统总览与扩展附录集成

## 目标与调查

本轮将用户选定的玻璃核心系统总览接入 ICLR，并将 ACL 路线中不同类型的既有证据按研究问题迁入扩展附录。标题调整为 **Same Scene, Different Decisions: Material Sensitivity in Embodied Models**。先前的总览保留，继续承担具体发现与配对实验的解释任务。

主会话调查主稿、图表构建链、玻璃核心可编辑来源、ACL 补充材料和既有实验输出；文档作者核对 `main.tex`、`figure_hero.py`、`build_assets.py`、七份附录正文及 `appendix/build_tables.py`。此次只整理、重算和呈现已有记录，没有新增模型推理、仿真或实验。

## 正文与图表集成

- 新系统总览作为 Fig. 1；最终位于第 2 页，原总览作为 Fig. 2 位于第 3 页，正文为 8 页，整份 PDF 为 33 页。
- 永久来源位于 `paper/shared/figures/iclr_system_hero/`；`paper/venues/iclr27/scripts/figure_hero.py` 从可编辑布局重建 `system_hero.svg/pptx/pdf/png`，并验证素材哈希及原生预测点位置。先前 `tmp/hero_A_structured/` 候选保持不变。
- 初次永久导出的 PNG／SVG 与用户选定版本字节一致；最终仅加深系统图副标题颜色，以提升实尺寸对比度。原总览图像保持原样。玻璃核心及材质球承担概念说明，场景、预测和导航图保持实际记录对应。
- 标题同步主稿及投稿元信息；相关正文只做衔接修改，不改变现有实验故事。

永久图的 [validation.json](../../paper/shared/figures/iclr_system_hero/validation.json) 记录几何、素材及原生预测点检查；整体图表来源见 [ASSET_PROVENANCE.json](../../paper/venues/iclr27/ASSET_PROVENANCE.json)。

## 附录组织与数据迁移

扩展附录按七个问题组织，通过 `appendix/details.tex` 汇入同一 PDF：

| 附录 | 迁入内容 |
| --- | --- |
| 输入外观 | 物体与场景真实配对、已有图像质量和特征相似度结果 |
| 材质线索 | 静态材质检查、Clearcoat／程序纹理等实例及既有转换比较 |
| 干净定位构造 | 双视图、查询、目标与背景干预的构造及来源对应 |
| 完整空间读出 | 六配置输出协议及坐标基线 |
| 额外定位结果 | 早期干净池、开发探针、个例与随机解码结果 |
| 导航与运行 | 完整导航指标、场景加载记录及 12 个真实配对录制案例 |
| 复现 | 模型环境、重建命令及资产入口 |

`appendix/build_tables.py` 从既有 CSV／JSON／JSONL 生成六张附录表，输入哈希写入 [table_sources.json](../../paper/venues/iclr27/appendix/table_sources.json)。历史探针直接复用当前分析函数，按记录的坐标系重新评分，避免迁入旧的解析子集条件命中率。渲染指标、材质静态检查、定位命中和导航任务指标分别保留各自定义；导航定性录制不附加主运行分数。

最终为 **15 张附录图版、6 张新增表格、7 节附录**。迁移审计解析了 49 个活跃 ACL 图引用，覆盖 10 个图像指标视角、4 个场景视角、4 个干净及 5 个历史定位目标、6 个材质案例，以及 12 个导航案例的 72 张录制帧。逐项去向见 [FIGURE_MIGRATION.md](../../paper/venues/iclr27/FIGURE_MIGRATION.md) 和 [JSON 映射](../../paper/venues/iclr27/FIGURE_MIGRATION.json)。

最终来源闭包包含 263 个文件、28 个生成器和 103 个输出。排版迭代修复场景表头、将附录浮动页顶端对齐，并合并原先稀疏的第 24 页。

## 构建、审计与当前状态

在仓库根目录运行：

```bash
python paper/venues/iclr27/scripts/figure_hero.py
python paper/venues/iclr27/appendix/build_tables.py
python paper/venues/iclr27/scripts/figure_supplement.py
make -C paper iclr27
make -C paper iclr27-check
make -C paper iclr27-stage
```

`stage` 只创建本地候选包。`build_assets.py` 已串联附录表格和图版生成；上述独立命令用于局部复建。

- 最终构建、检查与直接 stage 均 PASS；[check_report.json](../../paper/venues/iclr27/build/check_report.json) 绑定最终 PDF，正文结束页为 8。
- `python -m pytest -q tests/test_iclr_model_behavior.py tests/test_paper_layout.py`：**97 passed，14.74 秒**。
- 独立只看图像的审阅覆盖全部 33 页及独立图版，布局、图注对应与导出一致性 PASS。真实来源对比度、部分导航结束帧偏暗及系统图缩略内容仍可见，均为非阻塞项。最终 [VISUAL_REVIEW.json](../../paper/venues/iclr27/VISUAL_REVIEW.json) 已绑定本轮文件哈希。
- 引用核验覆盖 **18 个引用键、21 处上下文、31 个 TeX、12 个表文件、57 个来源哈希**，绑定检查 `PASS_BINDINGS`。有效状态仍为 `REVIEW_REQUIRED`：原始 resolver 的 SSIM 作者元数据 `FAIL` 保留，附有证据的规范化及重放单独记录；21 个人工支持条目仍为 `NOT_CHECKED`，无人工签认。详见 [REFERENCES_VERIFIED.md](../../paper/venues/iclr27/REFERENCES_VERIFIED.md)。

最终构建 PDF 与本地 staged candidate 的 SHA-256 一致：

```text
de1cfdfc511020f5e3fb1def318305e10947f13c8cc0fefcd9a2660cd09972a8
```

## 交付与后续

本轮交付更新主稿、本地候选包、永久可编辑系统图、七节附录、生成表格与图版、来源及迁移记录。ACL 成稿和原始实验记录保留；本轮未执行新增实验、commit、push 或上传。

查看 [最终候选 PDF](../../paper/submissions/iclr27_candidate/main.pdf)、[前后对比](../../paper/venues/iclr27/visual_iterations/integration_20260916/before_after.pdf) 和 [图版画廊](../../paper/venues/iclr27/visual_iterations/integration_20260916/figure_gallery.pdf)。工程与视觉验收已完成，引用人工签认仍按审计报告单独保留。
