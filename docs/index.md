# ConvertAsset 文档

> 最后更新: 2026-07-05

## 快速导航

- **[设计文档](design/README.md)** - 架构、模块职责、算法与实现深挖
- **[运维文档](operations/README.md)** - 运行环境、CLI、构建、排障与 agent 协作
- **[Setup](setup.md)** - Isaac Sim Python 与可选 native backend 环境说明
- **[Research asset layout](operations/research-asset-layout.md)** - `/cpfs/user/zhuzihou/assets/convertasset_research` 外部实验资产布局规范
- **[Asset Application Normalizer](design/asset-application-normalizer.md)** - USD/MJCF 等资产进入 target benchmark 前的资产、材质、物理、铰接、任务契约和证据闭环设计
- **[AAN Consumer Handoff](operations/asset-application-normalizer-consumer-handoff.md)** - EBench / EOS / LabUtopia / GenManip 等下游项目消费 AAN package、manifest、task files 和 PM evidence table 的接口说明
- **[AAN Object Interaction Profile](records/2026-07-14-aan-object-interaction-profile.md)** - package-owned unique rigid root、collider/open-top intent、named frames 与 runtime-tree closure 记录
- **[LabUtopia Vessel Static Packages](records/2026-07-14-aan-labutopia-vessel-static-packages.md)** - 锥形瓶与量筒的 source-bound profiles 和静态准入历史记录
- **[LabUtopia Vessel Runtime Qualification](records/2026-07-14-aan-labutopia-vessel-runtime-qualification.md)** - 四项 Isaac 4.1 interaction probes、量筒 compound proxy、runtime/MDL 兼容修复与最终证据
- **[Official EBench Soap-to-Dish Closure Plan](records/2026-07-05-official-ebench-scene-e1cf0d5b4d76-soap-to-dish-material-closure.md)** - `official_ebench_scene@e1cf0d5b4d76` 材质依赖闭包修复计划
- **[InternNav official evidence runbook](operations/internnav-official-evidence-runbook.md)** - official KuJiaLe downstream evidence 的运行、同步和 claim 边界
- **[过程记录](records/README.md)** - 变更日志、实现记录、审计与路线记录
- **[参考资料](reference/README.md)** - USD、UsdShade、MDL 与材质背景知识
- **[Learning Guide](../learn/README.md)** - `learn/` 下的交互式 HTML 电子书（GAMES101 → production USD asset pipeline）；bootstrap 记录见 [records/2026-06-01-learn-guide-bootstrap.md](records/2026-06-01-learn-guide-bootstrap.md)
- **[Superpowers 内部流程](superpowers/README.md)** - 本次设计/计划流程产物
- **[归档材料](../archive/README.md)** - 旧索引、legacy 文档、论文/提交相关历史材料

## 项目概述

ConvertAsset 是面向 NVIDIA Isaac Sim / USD 资产的转换与优化工具集。核心能力包括 no-MDL 转换、mesh 简化、USD 到 GLB 导出、缩略图渲染、材质检查与 MDL 材质导出。

所有需要 `pxr` 的命令都应通过 Isaac Sim Python 环境运行：

```bash
./scripts/isaac_python.sh ./main.py <subcommand> [args]
```

## 当前主线

- no-MDL：保留 composition，不 flatten，递归生成 `*_noMDL.usd`；
- mesh：Python QEM 为默认实现，C++ / `cpp-uv` 为可选加速路径；
- GLB：纯 Python 导出，支持 face-varying UV flattening 与 PBR 贴图；
- camera/rendering：为资产缩略图和单资产本地 Isaac 出图提供 orbit camera framing；
- AAN：Phase 1 USD -> EBench Isaac 4.1 normalization MVP 已完成阶段收口；下游集成从 [AAN Consumer Handoff](operations/asset-application-normalizer-consumer-handoff.md) 开始；
- docs：采用 Genesis-LLM 风格的 purpose-based taxonomy。

## 论文修订入口

- [Workshop review ingestion for AAAI 2027](records/2026-05-14-workshop-review-aaai27-roadmap.md)
- [Workshop-to-AAAI revision roadmap](../paper/shared/evidence/reviews/2026-05-workshop-to-aaai27-revision-roadmap.md)
- [CVPR review status and ACL goals](records/2026-05-23-cvpr-review-status-and-acl-goals.md)
- [ACL/VLM GRScenes grounding experiment runbook](../paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md)
- [InternNav VLN downstream prep](records/2026-05-23-internnav-vln-downstream-prep.md)
- [InternNav VLN runtime smoke](records/2026-05-23-internnav-vln-runtime-smoke.md)
- [InternNav VLN main-result scaffold](records/2026-05-23-internnav-vln-main-result-scaffold.md)
- [InternNav VLN main-result claim gate review](records/2026-05-23-internnav-vln-main-result-claim-gate-review.md)
- [InternNav runtime hang root cause](records/2026-05-24-internnav-runtime-hang-root-cause.md)
- [InternNav flat-filter runtime result](records/2026-05-24-internnav-flatfilter-runtime-result.md)
- [InternNav expanded30 and video rerun prep](records/2026-05-25-internnav-expanded30-and-video-rerun-prep.md)
- [InternNav official noMDL pair results](records/2026-05-25-internnav-official-nomdl-pair-results.md)
- [InternNav official noMDL visual assets](records/2026-05-25-internnav-official-visual-assets.md)
- [InternNav official val-unseen expansion goal](records/2026-05-25-internnav-official-val-unseen-expansion-goal.md)
- [InternNav official val-unseen 99 results](records/2026-05-25-internnav-official-val-unseen-99-results.md)
- [InternNav official selected qualitative videos](records/2026-05-25-internnav-official-selected-qualitative-videos.md)
- [Research asset layout normalization](records/2026-05-25-research-asset-layout-normalization.md)
- [Material-effect baseline experiment](design/material-effect-baseline-experiment.md)
- [Material-effect baseline bootstrap](records/2026-05-25-material-effect-baseline-bootstrap.md)
- [Material-effect supplemental diagnostics](records/2026-05-26-material-effect-supplemental-diagnostics.md)
- [Material-effect risk matrix](records/2026-05-26-material-effect-risk-matrix.md)
- [Material-effect paper claim integration](records/2026-05-26-material-effect-paper-claim-integration.md)
- [Reviewer closure status and next goal](records/2026-05-26-reviewer-closure-status-and-next-goal.md)
- [Reviewer closure package](records/2026-05-26-reviewer-closure-package.md)
- [Official-scene submission closure package](records/2026-05-26-official-scene-submission-closure-package.md)
- [Paper story progress snapshot](records/2026-05-26-paper-story-progress-snapshot.md)
- [ACL manuscript closure pass](records/2026-05-26-acl-manuscript-closure-pass.md)
- [ACL/ARR submission readiness audit](records/2026-05-26-acl-arr-submission-readiness-audit.md)
- [ACL citation and provenance closure](records/2026-05-26-acl-citation-provenance-closure.md)
- [ACL final packet closure pass](records/2026-05-26-acl-final-packet-closure-pass.md)
- [ACL/ARR submission staging smoke](records/2026-05-26-acl-submission-staging-smoke.md)
- [ACL OpenReview checklist packet](records/2026-05-26-acl-openreview-checklist-packet.md)
- [ACL model and asset license closure](records/2026-05-26-acl-model-asset-license-closure.md)
- [ACL target call policy audit](records/2026-05-26-acl-target-call-policy-audit.md)
- [ACL target policy refresh after current gate](records/2026-05-26-acl-target-policy-refresh-current-gate.md)
- [ACL target policy refresh after final-blocker handoff](records/2026-05-26-acl-target-policy-refresh-after-final-blocker-handoff.md)
- [ACL target policy refresh after private author status](records/2026-05-26-acl-target-policy-refresh-after-private-author-status.md)
- [ACL Fig.1 red-material root cause](records/2026-05-26-acl-fig1-red-material-root-cause.md)
- [ACL goal completion audit](records/2026-05-26-acl-goal-completion-audit.md)
- [ACL goal-completion report](records/2026-05-26-acl-goal-completion-report.md)
- [ACL reference web-trail audit](records/2026-05-26-acl-reference-web-trail-audit.md)
- [ACL final integrity delta audit](records/2026-05-26-acl-final-integrity-delta-audit.md)
- [ACL target lock and OpenReview rehearsal](records/2026-05-26-acl-target-lock-openreview-rehearsal.md)
- [ACL target policy gate](records/2026-05-26-acl-target-policy-gate.md)
- [ACL OpenReview metadata packet](records/2026-05-26-acl-openreview-metadata-packet.md)
- [ACL next large goal](records/2026-05-26-acl-next-large-goal.md)
- [ACL OpenReview author gate worksheet](records/2026-05-26-acl-openreview-author-gate-worksheet.md)
- [ACL pre-upload rehearsal refresh](records/2026-05-26-acl-preupload-rehearsal-refresh.md)
- [ACL reviewer-risk audit](records/2026-05-26-acl-reviewer-risk-audit.md)
- [ACL first-page fit hardening](records/2026-05-26-acl-first-page-fit-hardening.md)
- [ACL metadata consistency check](records/2026-05-26-acl-metadata-consistency-check.md)
- [ACL OpenReview checklist gate](records/2026-05-26-acl-openreview-checklist-gate.md)
- [ACL claim-boundary check](records/2026-05-26-acl-claim-boundary-check.md)
- [ACL citation-inventory check](records/2026-05-26-acl-citation-inventory-check.md)
- [ACL pre-upload gate runner](records/2026-05-26-acl-preupload-gate-runner.md)
- [ACL evidence-number check](records/2026-05-26-acl-evidence-number-check.md)
- [ACL author-gate filling guide](records/2026-05-26-acl-author-gate-filling-guide.md)
- [ACL author-gate checker](records/2026-05-26-acl-author-gate-checker.md)
- [ACL author-gate semantic check](records/2026-05-26-acl-author-gate-semantic-check.md)
- [ACL evidence-gate table](records/2026-05-26-acl-evidence-gate-table.md)
- [ACL PDF profile gate](records/2026-05-26-acl-pdf-profile-gate.md)
- [ACL packet checksum sidecar](records/2026-05-26-acl-packet-checksum-sidecar.md)
- [ACL final-integrity fingerprint gate](records/2026-05-26-acl-integrity-fingerprint-gate.md)
- [ACL final blocker report](records/2026-05-26-acl-final-blocker-report.md)
- [ACL final blocker clearance gate](records/2026-05-26-acl-final-blocker-clearance-gate.md)
- [ACL final blocker handoff details](records/2026-05-26-acl-final-blocker-handoff-details.md)
- [ACL OpenReview upload runbook](records/2026-05-26-acl-openreview-upload-runbook.md)
- [ACL author-gate initializer](records/2026-05-26-acl-author-gate-initializer.md)
- [ACL author-gate prefill](records/2026-05-26-acl-author-gate-prefill.md)
- [ACL OpenReview runbook prefill sync](records/2026-05-26-acl-openreview-runbook-prefill-sync.md)
- [ACL final next-action sequence](records/2026-05-26-acl-final-next-action-sequence.md)
- [ACL final-blocker required commands](records/2026-05-26-acl-final-blocker-required-commands.md)
- [ACL current-commit pre-upload gate](records/2026-05-26-acl-current-commit-preupload-gate.md)
- [ACL private author-gate status](records/2026-05-26-acl-private-author-gate-status.md)
- [GRScenes retake and zoom evidence expansion](records/2026-05-22-grscenes-retake-pass-pool-expansion.md)

## 结构说明

主导航遵循 `design/`、`operations/`、`records/`、`reference/`、`archive/` 的用途分类。
`docs/superpowers/` 是内部流程例外，用于保存 superpowers 设计与执行计划证据，不作为用户功能文档分类。
