# ICLR 2027 投稿准备

## 主线与入口

当前标题：**Same Scene, Different Decisions: Material Sensitivity in Embodied Models**。

当前论文主线是“材质输入变化—模型视觉定位—下游导航”。模型机制和导航都在正文，
正文以发现推进，详细来源、协议和适用范围集中到附录。

- 主稿：`paper/venues/iclr27/main.tex`
- 实验：`paper/shared/evidence/experiments/11_iclr_model_behavior/README.md`
- 状态：`paper/venues/iclr27/STATUS.md`
- OpenReview 复制材料：`paper/venues/iclr27/OPENREVIEW_METADATA.md`

## 日常命令

在仓库根目录运行：

```bash
make -C paper iclr27
make -C paper iclr27-check
make -C paper iclr27-stage
```

构建会先重算 `raw/iclr_model_behavior/analysis_v1/`，再生成 ICLR 图表。
`check` 校验模板、数据/图表指纹、引用、PDF 内容和正文页数；不要求正文出现防御性词汇。
`stage` 只生成本地 `paper/submissions/iclr27_candidate/`，没有上传或发表副作用。

## 系统总览与扩展附录维护

系统总览使用永久来源 `paper/shared/figures/iclr_system_hero/`，经
`paper/venues/iclr27/scripts/figure_hero.py` 重建。新系统图为 Fig. 1，原总览保留为
Fig. 2；先前 `tmp/hero_A_structured/` 是用户挑选时的候选记录，不作为日常覆盖目标。

附录由 `appendix/details.tex` 串联七节：输入外观、材质线索、干净定位构造、完整读出、
额外定位结果、导航与运行、复现。六张附录表由既有记录生成：

```bash
python paper/venues/iclr27/scripts/figure_hero.py
python paper/venues/iclr27/appendix/build_tables.py
python paper/venues/iclr27/scripts/figure_supplement.py
```

附录含 15 张图版及 12 个导航定性案例；历史定位探针按当前评分函数和原坐标契约重算。
2026-09-16 集成版共 33 页、正文 8 页，新系统图在第 2 页、原总览在第 3 页。
构建、检查、候选打包、97 项测试和全部页面独立视觉复查通过，详情见
[2026-09-16 集成记录](../records/2026-09-16-iclr-title-hero-supplement-integration.md)。
来源核验查看 `ASSET_PROVENANCE.json` 和 `appendix/table_sources.json`，旧图迁移去向见
`FIGURE_MIGRATION.md/json`；引用审计查看 `REFERENCES_VERIFIED.md` 与 `citation_audit/`。
本轮引用绑定为 `PASS_BINDINGS`，有效状态 `REVIEW_REQUIRED`：SSIM 的原始 resolver
元数据失败与有证据的规范化分开保存，21 个人工条目仍为 `NOT_CHECKED`。

## 官方格式

本仓库已下载 ICLR 2027 官方 style kit，归档 URL 和 SHA-256 写入
`TEMPLATE_PROVENANCE.json`。初稿正文上限 9 页，参考文献和附录另计；推荐同一 PDF
在参考文献后放附录。AI use statement 是今年明确要求的单独章节，不计正文页数。

- https://iclr.cc/Conferences/2027/AuthorGuidelines
- https://iclr.cc/Conferences/2027/AIPolicyForAuthors
- 摘要：2026-09-18 23:59 AoE；全文：2026-09-25 23:59 AoE。

## 实验状态的读取方式

机器构建成功表示产物一致，不代表后续科学实验已经完成。
当前已重算六配置 readout 档案，并完成三个模型的干净来源窗口干预；导航保留
99 对已有完整记录。早期新增场景 RTX 原始图捕获曾超时；导航重复和同位姿探针
已准备输入但尚未运行。扩展路径和实际阻塞见实验 README。

## 写作与数据维护

正文不复用旧 ACL 的 evidence-gate/allowed-forbidden claim 表。每个关键结论写清
发生了什么，再解释机制；真正改变数值含义的分母、坐标定义写进方法。
禁止把“可解析子集上的命中率”直接当成“全部查询的任务成功率”，也不要把模型
被告知目标类别后的复述当成独立识别能力。

新增实验必须独立版本输出。用 `models.json` 固定环境、checkpoint、解码参数；
不再用临时 shell job 文件作为唯一复现入口。正文图表由脚本生成，同时更新
`results_manifest.yaml`、`claims.yaml` 与 `ASSET_PROVENANCE.json`。
