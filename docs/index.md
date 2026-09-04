# ConvertAsset 文档

> 最后更新: 2026-08-18

## 快速导航

- **[Task 09 r14 双旋钮与60°门限位](records/2026-09-01-task09-r14-dual-knob-and-door-limit.md)** - 两套独立物理旋钮共享控制状态、缩放按压阈值与门阻尼/限位证据
- **[Task 09 r13 烘箱架与 materialized 烘箱](records/2026-08-31-task09-r13-oven-cart-and-materialized-oven.md)** - 紧凑承重架、100 kg 仿真载荷、直接 authored OmniGraph 与烧杯闭包修复
- **[复杂铰接家电 identity-root 迁移](design/articulated-appliance-relocation.md)** - 世界锚关节局部化、fixed-base v2 最终结构、hash-bound ScriptNode hook 与晋级边界
- **[IKA OVEN 125 identity-root 交付](records/2026-08-31-articulated-relocation-and-ika-oven.md)** - 三命名空间 Isaac 4.1 证据与 relocatable_task_scoped 结论
- **[IKA OVEN 125 Task 09/12 Fixed-Benchtop Admission](records/2026-08-31-ika-oven-125-task0912-fixed-benchtop.md)** - direct-stage、0.755 m baked mount、OmniGraph 与 Isaac 4.1 完整功能证据

- **[设计文档](design/README.md)** - 架构、模块职责、算法与实现深挖
- **[运维文档](operations/README.md)** - 运行环境、CLI、构建、排障与 agent 协作
- **[Setup](setup.md)** - Isaac Sim Python 与可选 native backend 环境说明
- **[Research asset layout](operations/research-asset-layout.md)** - `/cpfs/user/zhuzihou/assets/convertasset_research` 外部实验资产布局规范
- **[Asset Application Normalizer](design/asset-application-normalizer.md)** - USD/MJCF 等资产进入 target benchmark 前的资产、材质、物理、铰接、任务契约和证据闭环设计
- **[AAN Consumer Handoff](operations/asset-application-normalizer-consumer-handoff.md)** - EBench / EOS / LabUtopia / GenManip 等下游项目消费 AAN package、manifest、task files 和 PM evidence table 的接口说明
- **[Canonical Task-Object Facade](operations/build-canonical-task-object-facade.md)** - source-bound identity-entry object facade 与 interaction profile v2 使用说明
- **[Scientific Workbench Rigid-Object Packages](records/2026-07-31-aan-scientific-workbench-rigid-object-packages.md)** - 烧杯、漏斗、量筒和锥形瓶的任务资产准入及 claim boundary
- **[Scientific Workbench Asset Library Admission](records/2026-08-10-aan-scientific-workbench-asset-library.md)** - 新增搅拌棒、50 mL 离心管/盖、试管架、磁子、天平、培养皿、药匙与烧杯 r3 的 source-bound 准入
- **[Task 02 r8.1 Visible-Partition Collision Measured No-Go](records/2026-08-14-task02-r81-visible-partition-measured-no-go.md)** - 量筒可见薄壳 12/24/48 分区 convexDecomposition 的 Isaac 4.1 三轮冷启动否定证据与不晋级结论
- **[Task 02 40% Fill and Grasp-material Transfer](records/2026-08-16-task02-40pct-grasp-material-transfer.md)** - 保持 0812 粒子参数、以 580 粒子形成约 40% 液面，并为既有量筒碰撞拓扑增加 package-owned 抓取材质
- **[Task 02 Dynamic-loaded-start Qualification](records/2026-08-16-task02-dynamic-loaded-start.md)** - 量筒稳定根位姿与 580 粒子根局部初态的三次 Isaac 4.1 冷启动准入
- **[Task 02 GPU-PBD Four-fill Qualification v2](records/2026-08-17-task02-gpu-pbd-fill-sweep-v2.md)** - 20/40/60/80% 四档粒子初态的 live q95、三次冷启动和晋级绑定
- **[GPU-PBD Liquid Autofill](design/gpu-pbd-liquid-autofill.md)** - 将 Task 02 r10.3 经验固化为任意场景精确容器 prim 的 fail-closed 液体生产者
- **[GPU-PBD Liquid Autofill Runbook](operations/liquid-autofill.md)** - inspect、producer qualification 与 source closure 命令
- **[Simple-SDF Multi-liquid Producer](design/simple-sdf-multi-liquid.md)** - reviewed visual-Mesh SDF、独立 ParticleSet、共享 ParticleSystem 的窄路径
- **[Simple-SDF Multi-liquid CLI](operations/simple-sdf-multi-liquid.md)** - 两阶段 build、运行时验证与 claim 边界
- **[漏斗与 15 mL 离心管 small-v2 PBD 参数卡](operations/funnel-tube15-small-particle-pbd.md)** - 粒子配方、容器 SDF、ParticleSystem 材质绑定、组合运行条件与验证边界
- **[螺纹 15 mL 离心管与漏斗 exact-source PBD 参数卡](operations/wangshuai-threaded-tube-funnel-pbd.md)** - 同事倒液场景 1948 粒子 overlay、kinematic 螺纹管/漏斗碰撞与 16 秒入管边界
- **[Acrylic Spoon Rack Central Insertion](records/2026-08-17-aan-acrylic-spoon-rack-central-insertion.md)** - 透明七孔架的 source-bound 碰撞代理、中央孔插入证据与长时观察边界
- **[Scientific Workbench r9 Dynamic Context Assets](records/2026-08-16-scientific-workbench-r9-dynamic-context-assets.md)** - 6 个桌面丰富化资产的 source-bound 动态背景准入与消费边界
- **[Scientific Workbench Task 05 / Task 09 r11 Assets](records/2026-08-18-scientific-workbench-task05-task09-r11-assets.md)** - 原底烧瓶 29/42 闭合资产与模拟烘箱 identity facade、Isaac 4.1 交互/桌面稳定准入和 claim boundary
- **[LABSPIN X8 r6 Visual-fitted Lid Collision](records/2026-08-26-labspin-x8-r6-visual-fitted-lid-collision.md)** - 盖后空气墙诊断、命名视觉件 compound 代理和 Isaac 4.1 机械重验
- **[Wangshuai Funnel/Tube Exact Asset Set](records/2026-08-26-wangshuai-funnel-tube15-exact-asset-set.md)** - 螺纹管体/封闭管盖/漏斗/1948 粒子 overlay 的无物理调参拆分与重组回归
- **[Wangshuai Funnel/Tube Dynamic v2](records/2026-08-27-wangshuai-funnel-tube15-dynamic-v2.md)** - exact-source v1 保留，默认 dynamic v2 的 provisional 质量、三轮刚体/静止导流证据与装液搬运边界
- **[Threaded 15 mL Red Closed Single-Rigid Assembly](records/2026-08-27-threaded-tube15-red-closed-single-rigid-assembly.md)** - 新封顶螺纹盖与管体合为单一动态刚体，红盖材质、provisional 合并质量及三轮 Isaac 4.1 证据
- **[Non-threaded 15 mL Neck/Cap-fit Geometry Master](records/2026-08-28-nonthreaded-tube15-neck-cap-fit-master.md)** - 旧非螺纹管颈/帽套筒轴向失配诊断、17.24 mm 分段 mesh warp、闭合母版与三轮 Isaac 4.1 证据
- **[Long-neck Threaded 15 mL Geometry Admission](records/2026-09-01-long-neck-threaded-tube15-geometry-admission.md)** - 新长粗段管体与封顶螺纹管帽拆分为 identity-root 动态包；几何/SDF 晋级，旋合与 Task 08 明确 blocked
- **[Task 08 r12 Rack and Threaded-tube Visual Assets](records/2026-09-01-task08-r12-rack-and-threaded-tube-visual-assets.md)** - 18+4 架烘焙 1.1/1.1/1.3 与 SDF/18孔底托，长粗段管体统一玻璃材质和红色封顶管帽视觉变体
- **[Articulated Instance Scope and IKA OVEN r15](records/2026-09-01-articulated-instance-scope-and-ika-oven-r15.md)** - placement root 不变，完整铰接子树进入非 Xform 的 Instance Scope；三命名空间下复验双旋钮、按钮和门
- **[LICHEN Analytical-Balance r1 Sliding Doors](records/2026-08-18-analytical-balance-lichen-r1-doors.md)** - 程序化天平四扇滑动防风罩的 source-bound articulated 准入、Isaac 4.1 开关门资格与 Playable 时间轴
- **[LICHEN Front-Door Block Contact Opening](records/2026-08-18-analytical-balance-lichen-r1-front-door-contact.md)** - release5 前门把手凸包碰撞与 Isaac 4.1 挡块接触开关门资格
- **[Articulated Device Admission And Requalification](operations/articulated-device-admission-requalification.md)** - producer-owned articulated USD/proxy/profile/physics admission, promotion, and Scenario Forge loader handoff
- **[AAN Qualified Consumer Mounting Contract](records/2026-07-31-aan-qualified-consumer-mounting-contract.md)** - fixed-base articulated asset 的支撑面安装姿态、Isaac 4.1 稳定性资格与 manifest hash 绑定
- **[AAN Object Interaction Profile](records/2026-07-14-aan-object-interaction-profile.md)** - package-owned unique rigid root、collider/open-top intent、named frames 与 runtime-tree closure 记录
- **[AAN Dynamic Context Profile](records/2026-08-12-aan-dynamic-context-profile.md)** - 动态桌面背景物的窄合同：保留物理与碰撞，不声明抓取、任务或计分语义
- **[AAN Articulated Reset Capture Synchronization](records/2026-07-29-aan-articulated-reset-capture-synchronization.md)** - dynamic articulation reset baseline/cycle sampling alignment and Isaac 4.1 evidence
- **[Blender-generated Environment Admission](records/2026-07-30-aan-blender-generated-environment-admission.md)** - Blender 4.4 visual-static source facade, package closure, and room-zone profiling
- **[Generated-room Full-workcell Clearance](records/2026-08-03-aan-generated-room-workcell-clearance.md)** - request-declared room envelope audit with legacy-compatible defaults
- **[LabUtopia Vessel Static Packages](records/2026-07-14-aan-labutopia-vessel-static-packages.md)** - 锥形瓶与量筒的 source-bound profiles 和静态准入历史记录
- **[LabUtopia Vessel Runtime Qualification](records/2026-07-14-aan-labutopia-vessel-runtime-qualification.md)** - 四项 Isaac 4.1 interaction probes、量筒 compound proxy、runtime/MDL 兼容修复与最终证据
- **[Graduated Cylinder r3 EOS/GenManip Target-Grasp Qualification](records/2026-07-16-aan-graduated-cylinder-r3-eos-genmanip-target-grasp-qualification.md)** - source-bound r3 的固定右臂 target close/lift/hold 证据与严格 claim boundary
- **[DryingBox Family Admission Claim Correction](records/2026-07-13-aan-dryingbox-family-admission-and-claim-correction.md)** - 预修 `DryingBox_01_overlay` 证据不得外推至原始 `lab_001.usd` DryingBox 资产族
- **[Vessel Entry-reference Material Closure](records/2026-07-14-aan-vessel-entry-reference-material-closure.md)** - 资产入口 prim 被下游引用时的材质闭包、命名空间迁移与重建证据
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
- scientific workbench：[2.000 × 0.800 × 0.755 m 标准桌与 29/42 闭合资产交付](records/2026-08-11-scientific-workbench-table-and-closure-assets.md)；[承重 cube 不可见与中灰台面](records/2026-08-19-scientific-workbench-table-invisible-proxy-gray-top.md)；
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

## 近期交付

- [LABSPIN X8 r5 关节满足的默认姿态](records/2026-08-24-labspin-x8-r5-rest-pose.md) - 未运行即组装、首步零跳变，并复跑 OPEN/互锁/STOP 接触门禁
- [双入口液体与标准 SDF 烧杯](records/2026-08-24-dual-editable-liquid-and-sdf-beaker.md) - 冻结/高度可编辑 Cylinder 双入口、独立 ParticleSet、透明蓝共享系统材质与米制 source-bound 烧杯
- [Task 11 r5 static context and rack support](records/2026-08-24-task11-r5-static-context-and-rack-support.md) - 闭合 visual-static 背景管、目标孔底托与三次 Isaac 4.1 规定轨迹插管验证
- [29.77 mm magnetic stir-bar admission](records/2026-08-24-magnetic-stir-bar-29-77-admission.md) - source-bound identity package、圆柱抓取/承托碰撞与 Isaac 4.1 自由落体稳定性
- [LABSPIN X8 r4 contact controls](records/2026-08-24-labspin-x8-r4-contact-controls.md) - 真接触 OPEN/STOP、约 78° 自动开盖保持、转子互锁与可观测关机状态
- [Task 02 量筒简单碰撞 A/B](records/2026-08-21-task02-simple-collision-ab.md) - 同一580粒fixture证明视觉组件SDF与视觉mesh直接convex均失败，闭合统一代理静置/抬升通过
- [锥形瓶 90/35 玻璃轴对称 warp 交付](records/2026-08-21-conical-flask-90x35-glass-warp.md) - 烘焙 k_r(z)/k_h、identity 根缩放、Isaac 4.1 AAN 与开口/支撑/夹爪门禁 pass
- [Simple-SDF multi-liquid route](records/2026-08-20-simple-sdf-multi-liquid-route.md) - 独立 ParticleSet、共享 ParticleSystem 的试剂瓶/15 mL 管 golden regression
- [流体交互资产 producer v1](records/2026-08-20-fluid-interaction-asset-producer-v1.md) - reservoir/conduit/surface-guide 碰撞提案、人工复核与 Isaac 4.1 fail-closed 资格验证
- [参数化 OmniGlass glass_v1 交付记录](records/2026-08-18-aan-parameterized-omniglass-glass-v1.md)
- [HCI 视觉杯孔物理插入+关盖交付（r2）](records/2026-08-19-hci-15ml-physical-cup-insert-lid.md) - 短管变体、r10 包级杯孔碰撞、双管配平物理落管与两版 Isaac 4.1 mp4
- [HCI 适配闭合 15 mL 离心管交付](records/2026-08-18-hci-15ml-closed-insert-lid-delivery.md) - 非均匀缩放烘焙 closed 包、r9 插管/关盖门禁 pass 与 Isaac 4.1 演示 mp4
- [LICHEN 电子分析天平 r1 滑动门准入](records/2026-08-18-analytical-balance-lichen-r1-doors.md)
- [LICHEN 前门挡块接触开关门](records/2026-08-18-analytical-balance-lichen-r1-front-door-contact.md)

## 结构说明

主导航遵循 `design/`、`operations/`、`records/`、`reference/`、`archive/` 的用途分类。
`docs/superpowers/` 是内部流程例外，用于保存 superpowers 设计与执行计划证据，不作为用户功能文档分类。
