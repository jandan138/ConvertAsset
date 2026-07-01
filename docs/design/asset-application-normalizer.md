# Asset Application Normalizer

> Status: MVP design contract, 2026-06-30
> Owner repo: ConvertAsset
> First target: LabUtopia-style Isaac 5.1 USD assets -> EBench Isaac Sim 4.1 runtime package
> First acceptance asset: DryingBox
> Contract milestone: AAN-00 Contract Freeze completed for Phase 1 MVP
> Phase 1 closeout: `docs/records/2026-07-01-aan-phase1-closeout-handoff.md`
> Downstream interface: `docs/operations/asset-application-normalizer-consumer-handoff.md`

## 一句话定位

Asset Application Normalizer 不是“任意资产万能转换器”，而是一个
target-contract normalizer：给定一个 source asset / source task 和一个 target
benchmark profile，它把资产、材质、物理、铰接、任务入口和验证证据整理到“目标
benchmark 能加载、能渲染、能 step、能评测或明确阻断”的状态。

面向产品经理的通俗说法是：AAN 是资产进入评测系统前的“准入整理和验收流水线”。
它把 USD 资产、材质依赖、物理属性、关节信息、任务入口和运行证据打包成目标
benchmark 能读取的 package，并明确告诉我们：哪些已经可用，哪些带 waiver，哪些必须
阻断。

核心原则是 source-first preservation、compatibility fallback、evidence-tracked synthesis：
原始 USD / MDL / texture / physics authoring 尽量保留；目标 runtime 不能直接消费时，再
附加兼容层；缺失的物理属性可以规范生成，但每个生成值都必须有来源、方法和验收证据。

第一阶段只做窄而硬的能力：USD rigid body 和 articulated body 进入 EBench Isaac
Sim 4.1。LabUtopia / EBench / GenManip 只消费 normalizer 输出的 package、
task contract 和 evidence manifest，不再手工维护 USD / MDL / texture / articulation
修补逻辑。

2026-07-01 阶段收口后，其他项目接入 AAN 时不要从内部 Python 模块开始读；应从
`docs/operations/asset-application-normalizer-consumer-handoff.md` 开始，按 CLI、package
layout、manifest、task files、PM evidence table 和 claim boundary 接入。

“保留万能转换能力”的准确含义是：保留统一接入和验收框架，使 arbitrary USD、URDF、
MJCF、MuJoCo、Genesis asset 能以 adapter/profile 方式逐步进入；不是承诺任意资产在
MVP 中都能自动转换、自动修复、自动评测。

## AAN-00 Contract Freeze

AAN-00 是 Phase 1 MVP 的冻结点。本文是后续 `AAN-01 Manifest Seed` 到
`AAN-09 Negative Gate` 的实现合同；如果要改变合同，需要追加日期化 record，并说明
manifest / CLI / gate / claim boundary 的兼容影响。

冻结内容：

1. Lineage contract：使用 `source_format`、`source_runtime_lineage`、
   `target_runtime_profile`、`target_benchmark_profile`，不把 LabUtopia、EBench、AutoBio
   当核心抽象名硬编码。
2. Repo boundary：ConvertAsset 拥有 normalizer 实现；EOS、LabUtopia、GenManip、EBench
   只消费 package、task contract、manifest 和 evidence。
3. MVP scope：Phase 1 只支持 Isaac 5.1-oriented USD rigid/articulated assets 到
   EBench Isaac Sim 4.1 package。DryingBox 是首验资产，Cabinet Drawer 和 Transparent
   Beaker / `Beaker_01` 是 AAN-08 复制验收候选。
4. CLI contract：第一版新增 flat `normalize-asset` subcommand，MVP 拒绝 MJCF / URDF 等
   非 USD 输入，拒绝非 `isaac41` / 非允许 benchmark profile。
5. Package layout：target package 以 `asset.usd`、`assets/`、`task/`、`evidence/`、
   `waivers/` 为第一阶段稳定布局。
6. Manifest schema：`manifest.json` 是 LabUtopia / EBench / 周报消费的主接口，必须覆盖
   lineage、entrypoints、required prims、dependency/material/physics/articulation closure、
   gates、runtime evidence、environment、waivers、blockers、claims 和 commands。
7. Gate semantics：状态只使用 `pass`、`fail`、`blocked`、`waived`、
   `not_applicable`、`not_run`；总状态只使用 `ready`、`ready_with_waivers`、`failed`、
   `blocked`、`dry_run_incomplete`。
8. Material policy：source-first preservation；原始 MDL / texture / material binding
   优先保留，PreviewSurface 是兼容 fallback，不代表丢弃原材质。
9. Physics policy：authored value 优先保留；缺失值只能按 `derived`、`template`、
   `manual_override` 生成并记录 provenance。
10. Claim boundary：waiver 不是 pass，会改变 total status 和 forbidden claims；AAN-00 不
    承诺任意 USD、URDF、MJCF、AutoBio official reproduction、deformable/liquid、official
    leaderboard comparability 或 pixel-perfect/render/physics parity。

## 为什么不是已有工具已经解决

| 工具或项目 | 解决的问题 | 不能直接替代我们的原因 |
|---|---|---|
| OpenUSD / `usdchecker` | 检查 USD 文件、composition、asset reference 等基础合法性 | 不知道 EBench、Isaac Sim 4.1 runtime、benchmark task contract、policy/evaluator 入口 |
| Omniverse Asset Validator / OpenUSD Exchange SDK | USD validation、converter authoring、部分自动修复 | 是 validator / authoring building block，不是 benchmark application contract |
| NVIDIA SimReady / SimReady Foundation | 用 OpenUSD 表达 simulation-ready 语义、profile、物理属性 | 更像 simulation asset 标准；不替代 EBench Isaac 4.1 runtime smoke 和任务契约验证 |
| Isaac Sim URDF / MJCF / Mesh importer | 把 URDF / MJCF / mesh 导入 Isaac / USD | importer 只负责“进来”，不负责“进来后能不能按某个 benchmark 被评测” |
| Isaac Asset Transformer | 新版 Isaac 侧的 profile-based robot USD 重组和报告 | 方向接近，但目标是新版 Isaac asset layout；不能直接覆盖 Isaac 5.1 -> EBench Isaac 4.1 的兼容 contract |
| OpenAssetIO | 资产身份、版本、发布、解析和 asset manager / host 集成 | 管 asset，不管 USD/MJCF 语义转换、物理闭环、runtime smoke |
| RoboVerse / MetaSim | 多 simulator / 多 task 的统一运行和任务抽象 | 更像 execution platform；我们的重点是 asset/task 被应用到 target benchmark 前后的证据化验收 |

结论：这些工具应该被复用为底层 building blocks，但 Product 形态应定义为
Asset Application Normalizer，而不是再做一个 importer、validator 或 asset manager。

## 名字和谱系要分清

后续文档和代码不要把 LabUtopia、EBench、AutoBio 只当项目名硬编码。更稳的写法是
四层 lineage：

| 维度 | 例子 | 含义 |
|---|---|---|
| `source_format` | USD, MJCF, URDF | 资产原始文件格式 |
| `source_runtime_lineage` | Isaac 5.1, MuJoCo | 源资产原本面向的 runtime / simulator |
| `target_runtime_profile` | Isaac Sim 4.1, Genesis native | 目标实际执行环境 |
| `target_benchmark_profile` | EBench Lift2, EOS scenario pack, AutoBio official | 目标 benchmark / evaluator 契约 |

这能避免一个常见误区：LabUtopia 和 AutoBio 不是同一种输入。LabUtopia 目前应视为
Isaac 5.1-oriented USD asset source；EBench 是 Isaac Sim 4.1 / GenManip target
benchmark profile；AutoBio 的第一性来源是 MuJoCo / MJCF assets 和 MuJoCo task
semantics。

## 仓库边界

### ConvertAsset

ConvertAsset 是主实现仓库。原因是它已经拥有：

- USD / MDL / UsdPreviewSurface 的处理代码；
- no-MDL、material inspection、render、mesh、GLB 等资产处理能力；
- Isaac Python wrapper 和资产实验文档；
- route-neutral asset conversion 的工程定位。

第一阶段实现形态采用 manifest-first、USD-only、EBench Isaac 4.1 target-profile-first。
不要一开始铺完整 adapter 框架。建议先落一个偏扁平的 MVP 包：

```text
convert_asset/asset_application_normalizer/
  __init__.py
  cli.py
  model.py
  package_layout.py
  pipeline.py
  usd_inventory.py
  dependency_closure.py
  material_closure.py
  physics_checks.py
  target_ebench_isaac41.py
  runtime_smoke.py
  evidence_manifest.py
```

模块边界：

| Module | Responsibility |
|---|---|
| `cli.py` | `normalize-asset` CLI 参数解析，保持现有 flat argparse 风格 |
| `model.py` | 只放 MVP 稳定 IR，不表达完整 USD 世界模型 |
| `package_layout.py` | target package 目录、相对路径、hash 和 artifact 命名 |
| `pipeline.py` | 串联 inventory、closure、checks、runtime smoke 和 manifest |
| `usd_inventory.py` | 只读扫描 root layer、sublayer、reference、payload、variant、clip、texture、MDL、defaultPrim、required prim 候选 |
| `dependency_closure.py` | package-local copy/mirror、remote URI 分类、绝对路径/外部路径清理、重写到 package 内相对路径 |
| `material_closure.py` | source material preservation、MDL/texture local mirror、`native_resolved` / `local_mirror` / `preview_surface_fallback` / `explicit_waiver` / `blocked` policy 和 report |
| `physics_checks.py` | authored physics preservation、derived/template/manual override provenance、rigid body、collision、mass、inertia、scale、visibility、spawn/reset pose、articulation、joint limit、drive、DOF mapping 检查 |
| `target_ebench_isaac41.py` | EBench Isaac 4.1 profile：allowed roots、required checks、task contract 字段、waiver policy |
| `runtime_smoke.py` | Isaac Sim 4.1 cold load、render readback、step、reset smoke |
| `evidence_manifest.py` | manifest schema、check result、artifact path/hash、waiver/blocker、weekly summary |

等 MJCF / Genesis / EOS 路线真的进入实现后，再拆成 `source_adapters/`、
`target_profiles/`、`validators/` 等多层结构。

### 与现有 ConvertAsset 模块的关系

- `convert_asset/no_mdl/` 是 material fallback implementation，不是 normalizer owner。
  Normalizer 可以复用其 MDL 识别、纹理抽取、PreviewSurface 构建和 no-MDL 诊断能力，
  但 package closure、material policy、waiver/blocker 和 evidence manifest 属于
  normalizer。
- `convert_asset/no_mdl/references.py` 已覆盖 sublayer / reference / payload / variant /
  clip 的 USD 组合依赖扫描。Normalizer 的 `usd_inventory.py` 应复用其思路，并扩展到
  MDL sourceAsset、UsdUVTexture file、MDL pin texture、`.mdl` 文本推断 texture 和 target
  required files。
- `convert_asset/render/` 只提供渲染能力。Normalizer 的 runtime smoke 负责把渲染结果变成
  gate evidence。
- `convert_asset/mesh/` 和 `convert_asset/glb/` 不进入第一阶段主路径。
- `pxr`、`omni.*`、Isaac runtime 仍必须懒加载，遵守 `CLAUDE.md` 中的约束。

### EmbodiedEval OS

EOS 不应该承载 USD / MDL / MJCF 细节转换。EOS 的职责是消费 normalizer 产物：

- `AssetResolutionRequest`
- `AssetResolutionResult`
- `ExternalAssetRef`
- `AssetBundleManifest`
- `EpisodeTrace`
- benchmark adapter / scenario pack 的 evidence 和 claim boundary

换句话说，EOS 负责“评测证据和声明边界”，ConvertAsset 负责“资产应用前的规范化和闭环”。

### LabUtopia / GenManip / EBench 集成仓库

这些仓库只做 source / target integration evidence：

- 证明某个 LabUtopia source asset 如何进入 EBench / GenManip；
- 保存 Lift2 / DryingBox 这类 concrete POC；
- 接入 normalizer 输出的 task config、required prim mapping、metric/evaluator 和周报证据；
- 不把一次 POC 膨胀成通用 normalizer owner。

## 核心数据流

```text
source asset/task
  -> source inventory
  -> canonical package IR
  -> dependency/material/physics/articulation closure
  -> target profile
  -> validators and runtime smoke
  -> target-ready package + evidence manifest
```

## Preservation-first normalization policy

AAN 不以“降级能跑”为目标，而是以“最大保真地封装资产，并为目标运行时补齐兼容层”为
目标。任何 material / physics 的保留、推导、生成、人工覆盖都必须带 provenance 和
evidence。

### Material preservation

- 原始 material binding、MDL source、texture source、UsdShade 网络和解析路径必须先进入
  inventory 和 dependency closure。
- remote MDL / texture 首选 local mirror，并把 package-relative path、hash、owner layer
  写入 manifest。
- UsdPreviewSurface fallback 是兼容层，不代表丢弃原 MDL / texture。即使 target
  entrypoint 使用 no-MDL USD，package 和 evidence 仍要保留 source material closure
  记录。
- 透明材质是第一阶段重点验收面。Transparent Beaker 这类资产至少要保留可见轮廓、base
  color / opacity 或等价透明策略、roughness 和核心 texture provenance；render readback
  看不见目标资产时必须 `blocked`。

### Physics preservation and synthesis

- 已 authored 的 rigid body、collision、mass、inertia、joint axis、joint limits、drive 和
  reset pose 默认原样保留，并记录 `value_source=authored`。
- 缺失的 mass / inertia / collision 可以生成，但必须分级记录：
  `derived` 表示从 mesh、bbox、volume、density 等确定性输入推导；
  `template` 表示按资产类别和版本化模板填充；
  `manual_override` 表示由 task contract 或人工审核确认。
- joint axis、joint limit、DOF mapping、reset pose 这类语义强字段不能静默猜测。没有
  source authoring 或 contract 支持时， articulated asset 必须 `blocked` 或进入
  `manual_override` 审核。
- 所有 generated physics value 必须记录 method、input artifacts、template id 或 owner，
  并通过 Isaac 4.1 step / reset smoke 后才能进入 `ready` 或 `ready_with_waivers`。

### Claim boundary

- fallback / generated value 允许资产进入受限任务，但会改变 claims。manifest 不能声明
  full material parity、physical parameter parity 或 official comparability。
- Waiver 只覆盖明确风险，不覆盖 provenance 缺失。没有来源、方法和证据的默认值不能通过
  waiver 伪装成 pass。

## Long-term capability architecture

长期架构按六层能力地图理解。这个分层保留 arbitrary USD、URDF、MJCF、MuJoCo 和
Genesis asset 的接入路径，但第一阶段只实现 `USD source -> EBench Isaac41 target profile`
这一条竖切。

| Layer | 长期职责 | MVP 实例 |
|---|---|---|
| 1. Source ingestion | 接入 USD、URDF、MJCF、MuJoCo package、Genesis asset 等来源 | USD root layer + dependency inventory |
| 2. Source semantic inventory | 抽取 source 的 geometry、material、physics、articulation、task hints、runtime lineage | Isaac 5.1-oriented USD inventory |
| 3. Canonical asset application IR | 只表达“资产应用到目标 benchmark 所需的最小事实”，不是万能场景模型 | package / evidence / task contract IR |
| 4. Closure and transformation | 做 dependency、material、physics、articulation、version compatibility closure | USD package-local closure、MDL/texture policy、rigid/articulation checks |
| 5. Target profile gates | 把目标 runtime / benchmark 的硬约束变成 gate policy | EBench Isaac Sim 4.1 profile |
| 6. Evidence package handoff | 输出 target-ready package、manifest、waiver、blocked reasons、allowed/forbidden claims | DryingBox package + evidence manifest |

这层架构必须区分“架构预留”和“产品支持状态”。Phase 1 的 supported path 只有：
DryingBox-first、USD rigid/articulated asset、Isaac 5.1-oriented source lineage、EBench
Isaac Sim 4.1 target profile。其他格式在 Phase 1 中只能被描述为 future adapter family；
CLI 传入时应报 unsupported，而不是 fallback 到猜测转换。

其中 canonical package IR 不是“全世界唯一真理模型”，而是为了稳定描述：

- source lineage；
- asset dependency graph；
- material binding 和 material closure 状态；
- rigid body / collision / mass / inertia 状态；
- articulation joint / limit / drive / reset pose 状态；
- task entrypoint、required prim paths、success predicate 所需语义；
- target profile 的 required checks 和 waiver policy；
- 每个 gate 的 evidence、waiver、blocker 和 allowed/forbidden claims。

## Canonical IR 最小稳定对象

Canonical IR 不是 universal scene graph，也不是所有 simulator 的共同语义语言。它只记录
target benchmark application 所需的事实、证据、semantic gap、waiver 和 claim boundary。
未来 URDF / MJCF / MuJoCo / Genesis adapter 也必须先降落到这个 contract，而不是绕过
evidence gate。

`model.py` 第一阶段只需要稳定这些对象：

| Object | Fields |
|---|---|
| `Lineage` | `source_format`, `source_runtime_lineage`, `target_runtime_profile`, `target_benchmark_profile` |
| `PackageIdentity` | source root、source asset id/hash、target package root、root layer、default prim、output root USD |
| `DependencyEntry` | kind、owner layer、owner prim、authored path、resolved path、target package path、URI scheme、status |
| `MaterialClosureRecord` | material prim、owning layer、shader/material type、MDL source、texture deps、source preservation status、closure strategy、fallback/fidelity notes、waiver/blocker id |
| `PhysicsBodyRecord` | prim path、body kind、collision state、mass、inertia、scale、visibility、spawn/reset pose、value provenance、status |
| `ArticulationRecord` / `JointRecord` | articulation root、joint prim、type、axis、limits、drive、DOF mapping、reset value、value provenance、status |
| `TaskContract` | benchmark profile、required prim paths、task config path、evaluator/metric entrypoint reference、reset assumptions |
| `CheckResult` | check id、stage、status、command、log/artifact paths、summary |
| `EvidenceManifest` | package files、hashes、checks、waivers、blockers、runtime evidence、render readback evidence |
| `SemanticGap` / `BlockedReason` | unsupported source semantic、target profile 不支持的 schema/runtime 行为、需要 waiver 或阻断的原因 |

重点：IR 是 evidence/package contract，不是完整 USD schema wrapper，也不是 benchmark task
semantic language。

## CLI contract

第一版推荐新增 flat subcommand `normalize-asset`，保持 `convert_asset/cli.py` 现有
argparse 风格，不做多层子命令：

```bash
./scripts/isaac_python.sh ./main.py normalize-asset <source_usd> \
  --out <package_dir> \
  --asset-id DryingBox \
  --asset-class rigid|articulated|auto \
  --source-runtime isaac51 \
  --target-runtime isaac41 \
  --target-benchmark ebench-lift2 \
  --task-id Lift2.DryingBox \
  --contract <task_contract.yaml|json> \
  --required-prim /World/... \
  --material-policy native-or-mirror|preview-fallback|waiver-ok|block-on-gap \
  --allow-waiver <waivers.yaml> \
  --gates static,runtime,benchmark \
  --evidence-out <manifest.json> \
  --dry-run
```

边界：

- MVP 只接受 USD。MJCF / URDF 传入应返回参数错误，不能隐式转换。
- `--dry-run` 可写 evidence manifest，但不得写 target package 内容；用于 inventory 和 gate
  诊断。
- `--gates static` 不启动 Isaac runtime；`runtime` 才允许走 load / render / step / reset
  smoke。
- `--target-runtime` MVP 只允许 `isaac41`；`--target-benchmark` MVP 只允许
  `ebench-lift2` 或明确的窄 profile 名。
- `--contract` 是用户 / EBench 接入面，不自动猜 success predicate。
- 返回码建议：`0` pass 或 pass-with-waiver；`2` 参数/输入不存在；`3` runtime/open 异常；
  `4` contract/gate fail；`5` blocked，需要人工 waiver 或代码支持。

反对命名成 `labutopia-to-ebench`。这会把 lineage 和 benchmark profile 硬编码到产品名。

## Target package layout

第一阶段 target package 最小布局：

```text
<package_dir>/
  asset.usd
  assets/
    usd/
    textures/
    mdl/
  task/
    task_config.yaml
    required_prims.yaml
    evaluator.yaml
  evidence/
    manifest.json
    static_usd_report.json
    material_report.json
    physics_report.json
    articulation_report.json
    runtime_smoke.json
    render/
      front.png
      left.png
      back.png
      right.png
  waivers/
    waivers.yaml
```

要求：

- package 内 root USD 是 EBench 消费入口；
- 所有 copy / mirror / rewrite 必须能从 manifest 追溯；
- target package 内禁止未授权 remote URI、未授权绝对路径和路径逃逸；
- 组合关系默认保留，不 flatten；
- texture / MDL mirror 后写 package-relative path；
- waiver 不是 pass，它会改变总状态和 forbidden claims。

## Missing / remote dependency resolution policy

Dependency closure 不能停在“发现缺失或 remote URI”这一层。AAN 必须把每条 dependency
收敛到一个明确、机器可读、可审计的处理结论：

| Resolution | 含义 | 允许条件 | Manifest / claim impact |
|---|---|---|---|
| `mirrored` | 找到等价本地文件或合法下载/同步远程文件，并复制到 target package | hash、source URI/source path、owner layer、package path 都可追溯；USD/MDL/texture 路径已重写为 package-relative | 可以进入 `pass`，但只能声明 package-local closure，不声明材质/物理语义完全等价 |
| `pruned` | 依赖属于当前 task scope 之外的背景/装饰/未激活 branch，被安全裁剪或从 task entrypoint 排除 | task contract 证明该依赖不在 required prim、required material、required collision/runtime 路径上；裁剪前后 required prim 仍存在 | 可以进入 task-scope `pass`；forbidden claims 必须禁止 full source-scene closure |
| `waived` | 依赖缺口已知且短期不阻断目标任务，但风险需要保留 | 有 waiver id、owner、reason、impact、review/expiry、forbidden claims；runtime/material gate 不能把风险声明为 pass | 总状态只能是 `ready_with_waivers`，不能是 clean `ready` |
| `blocked` | 依赖对 package / task / material / physics / runtime closure 必需，且不能合法 mirror、不能安全 prune、不能 waiver | required USD/helper/texture/MDL 缺失；remote URI 无本地 mirror 或授权 resolver；路径逃逸；缺 provenance | CLI 返回 blocked，周报显示 blocker，不继续冒充可交付资产 |

处理顺序固定为：

1. `inventory`: 记录 raw path、owner layer、owner prim、arc kind、URI scheme、required/task
   relevance、初始 resolved path。
2. `local search`: 在 source tree、dataset mirror、overlay sidecar、Isaac/Omni MDL roots 和显式
   mirror roots 中寻找同名或等价文件；找到后进入 `mirrored`。
3. `remote mirror`: 对 remote URI 只允许在 license / cache / allowlist 明确时下载或同步，并记录
   original URI、hash、fetch command、mirror time；否则保持 unauthorized remote。
4. `task-scope prune`: 只有 target task contract 证明该依赖不影响 required prim、runtime load、
   render readback、collision/articulation、metric/evaluator 时，才允许 prune。
5. `waiver review`: 只覆盖非阻断风险，且必须改变 claims；waiver 不能补 provenance，也不能让
   required dependency 缺失变成 pass。
6. `block`: 以上都不能成立时必须 blocked，并把 required resolution 写进 manifest。

具体到当前 DryingBox 证据：

- `DryingBox_01.usd` 缺 `UnitsAdjust-*.metricsAssembler`：先在 LabUtopia source export、dataset、
  历史 package 和 overlay 中查找。如果找回，则 mirror；如果证明它只是 exporter 残留且不影响
  units/scale/geometry/material/physics/runtime load，可按 task-scope prune 或 waiver；如果影响
  scale/units 或无法证明无影响，必须 blocked。
- 原始 `lab_001.usd` 的 unauthorized remote URI：优先 mirror 到本地 package 或显式 mirror
  cache；如果是 task 无关背景 cabinet，可通过 task-scope prune 生成 DryingBox task package；
  如果是 required material / USD dependency 且不能 mirror，必须 blocked。

## Evidence manifest schema

`manifest.json` 是 LabUtopia / EBench / 周报消费的主接口。最小字段：

```json
{
  "schema_version": "asset_application_normalizer.v1",
  "package_id": "drying_box_ebench_isaac41",
  "asset_id": "DryingBox",
  "task_id": "Lift2.DryingBox",
  "milestone": "AAN-06-runtime-smoke",
  "source": {
    "path": "/source/DryingBox.usd",
    "sha256": "...",
    "source_format": "usd",
    "source_runtime_lineage": "isaac51"
  },
  "target": {
    "target_runtime_profile": "isaac41",
    "target_benchmark_profile": "ebench-lift2"
  },
  "entrypoints": {
    "root_usd": "asset.usd",
    "default_prim": "/World/DryingBox",
    "task_config": "task/task_config.yaml",
    "required_prims": "task/required_prims.yaml",
    "metric_evaluator": "task/evaluator.yaml"
  },
  "normalization_policy": {
    "material": "preserve_source_then_add_compatibility_fallback",
    "physics": "preserve_authored_then_generate_with_provenance",
    "allowed_value_sources": ["authored", "derived", "template", "manual_override"]
  },
  "required_prim_paths": [
    {
      "name": "asset_root",
      "path": "/World/DryingBox",
      "role": "asset_root",
      "required": true
    }
  ],
  "dependency_closure": {
    "local_files": [],
    "missing": [],
    "remote_uri": [],
    "unauthorized_remote_uri": [],
    "resolution_summary": {
      "mirrored": 0,
      "pruned": 0,
      "waived": 0,
      "blocked": 0
    }
  },
  "material_closure": [],
  "physics_closure": {},
  "articulation_closure": {},
  "stage_gates": [],
  "runtime_evidence": {},
  "environment": {},
  "waivers": [],
  "blocked_reasons": [],
  "claims_allowed": [],
  "claims_forbidden": [],
  "commands": {},
  "created_at": "2026-06-30T00:00:00Z",
  "tool_version": "convert_asset.asset_application_normalizer.v1",
  "git_commit": "..."
}
```

Runtime evidence 应可被周报直接聚合：

```json
{
  "runtime_evidence": {
    "cold_load": {
      "status": "pass",
      "runtime_version": "Isaac Sim 4.1",
      "command_id": "cold_load_001",
      "duration_sec": 12.3,
      "required_prims_found": true,
      "error_count": 0,
      "warning_count": 3,
      "log_path": "evidence/cold_load.log"
    },
    "render_readback": {
      "status": "pass",
      "frames_passed": 4,
      "frames_expected": 4,
      "representative_frame": "evidence/render/front.png",
      "failure_modes": []
    },
    "physics_step": {
      "status": "pass",
      "asset_kind": "rigid",
      "steps": 240,
      "finite_state": true,
      "contact_or_motion_sane": true,
      "failed_checks": []
    },
    "reset_smoke": {
      "status": "pass",
      "root_pose_restored": true,
      "joint_pose_restored": true,
      "max_pose_error": 0.0001
    }
  },
  "weekly_summary": {
    "load": "pass",
    "render": "pass",
    "step": "pass",
    "articulation": "not_applicable",
    "ready_for_ebench_task_contract": true
  }
}
```

周报层只消费 `overall_status`、runtime 子项状态、失败模式、waiver 数量和代表性 artifact
路径；stdout/stderr、PNG、per-joint/per-frame 数据保留为 linked artifact。

## Stage gate semantics

Gate 状态必须机器可判：

| Status | Meaning |
|---|---|
| `pass` | required check 完整通过，有 evidence artifact |
| `fail` | check 执行完成但不满足 contract；不能交给 EBench task config |
| `blocked` | 缺依赖、schema/runtime 不支持、无法打开 stage、缺 required prim，或需要无 provenance 默认值才能继续 |
| `waived` | fail/block 被显式 waiver 覆盖；必须有 `waiver_id`, `owner`, `reason`, `expires_or_review_by`, `impact`, `claims_forbidden` |
| `not_applicable` | rigid asset 没有关节等 N/A 情况；manifest 要说明 asset class 判定依据 |
| `not_run` | dry-run 或 runtime 不可用；不能被当作 pass |

总状态建议：

- `ready`
- `ready_with_waivers`
- `failed`
- `blocked`
- `dry_run_incomplete`

`pass-with-waiver` 可以给 CLI 返回码 `0`，但 manifest 总状态必须是
`ready_with_waivers`，且 forbidden claims 必须明确。

## Numbered acceptance plan

编号统一使用 `AAN-NN-short-name`。`NN` 固定两位数，短名用 2-4 个英文 token，便于周报、
issue、manifest 和 artifact 路径引用。例如：

- 周报：`AAN-06 Runtime Smoke: DryingBox load/render/step/reset pass`
- manifest：`"milestone": "AAN-06-runtime-smoke"`
- issue：`[AAN-04 Material Closure] DryingBox MDL local mirror`

范围划分：

- MVP core：`AAN-00` 到 `AAN-07`
- MVP exit：`AAN-08` 到 `AAN-09`
- Post-MVP expansion：`AAN-10+`

| ID | Short name | Scope | Deliverable | Acceptance criteria | Fail / blocked criteria | Class |
|---|---|---|---|---|---|---|
| `AAN-00` | Contract Freeze | 冻结第一阶段 contract | AAN 设计契约：lineage、repo boundary、CLI、package layout、manifest schema、gate semantics、material policy、status semantics | 文档明确 MVP 只支持 USD rigid/articulated -> EBench Isaac 4.1；明确 `pass/fail/blocked/waived/not_applicable/not_run`；明确 waiver 会改变 total status 和 forbidden claims | 仍使用 LabUtopia/AutoBio 作为核心抽象名；MVP 范围包含 MJCF/URDF/deformable/leaderboard claims；gate 状态不可机器判定 | MVP core |
| `AAN-01` | Manifest Seed | DryingBox 手工 manifest 基线 | DryingBox / Lift2 的人工 evidence manifest seed，记录 source、lineage、required prim、dependency、material、physics、task fields、known waiver/blocker | manifest 字段覆盖 `schema_version/source/target/entrypoints/required_prim_paths/dependency_closure/material_closure/physics_closure/articulation_closure/stage_gates/waivers/blockers/claims`；能作为后续自动化输出对照 | 缺 required prim；缺 source/target lineage；只记录成功项不记录 blocker/waiver；无法解释 DryingBox 当前是否可进入 EBench | MVP core |
| `AAN-02` | CLI Skeleton | `normalize-asset` 最小入口和包结构 | `convert_asset/asset_application_normalizer/` MVP 模块骨架、flat CLI、IR model、package layout、manifest writer、dry-run path | CLI 支持设计中的核心参数；MVP 拒绝非 USD、非 `isaac41`、非允许 benchmark profile；`--dry-run` 可写 manifest 但不写 target package 内容；`pxr` / `omni.*` 继续懒加载 | CLI 隐式接受 MJCF/URDF；dry-run 写 package；导入模块时加载 `pxr` 或 `omni.*`；返回码无法区分参数、runtime、gate、blocked | MVP core |
| `AAN-03` | USD Closure | USD inventory + dependency package closure | DryingBox package-local USD tree、dependency report、static USD report | 列出 root layer、sublayer、reference、payload、variant、clip、texture、MDL、defaultPrim、required prim；package 内无未授权 remote URI、无缺失 local dependency、无 package escape；组合关系保留、不 flatten | required USD 缺失；remote URI 未 mirror/allow/waive 就通过；绝对路径或路径逃逸残留；variant/clip required branch 未扫描 | MVP core |
| `AAN-03R` | Dependency Resolution | missing / remote URI 收敛策略 | 每条 missing / remote dependency 的 `mirrored/pruned/waived/blocked` 决策记录，raw source 和 task-scope source 各自有结论 | DryingBox overlay 继续 pass；raw single / raw lab 的缺口不只报错，必须给出查找范围、resolution decision、required_resolution、claim impact；remote URI 无授权时不能 pass | missing / remote 只停留在列表；未证明 task irrelevant 就 prune；required dependency 用 waiver 伪装 pass；下载/同步 remote 无 hash/source/license 记录 | MVP core |
| `AAN-04` | Material Closure | MDL / texture closure policy | material report + manifest material records；优先 source preservation 和 local mirror，必要时附加 PreviewSurface fallback 或 waiver/block | 每个材质都有 `native_resolved/local_mirror/preview_surface_fallback/explicit_waiver/blocked` 五选一；source MDL/texture raw/resolved/package path/hash 可追溯；fallback 记录 channel provenance、defaults、losses、residual MDL；透明材质记录 opacity/visibility 策略 | 丢弃原始 MDL/texture 只保留 fallback；active residual MDL 在 no-MDL profile 下无说明；缺核心 texture 却静默 fallback；透明/语义关键材质不可见仍放行；material waiver 没有 owner/reason/impact/expiry/forbidden claims | MVP core |
| `AAN-05` | Physics Static | rigid/articulation static checks | physics report、articulation report、manifest closure records | authored collision、mass、inertia、scale、spawn/reset pose、joint type/axis/limit/drive 优先保留；缺失或非正/非 finite mass/inertia 可用 `derived/template/manual_override` 补齐并记录 method/input/template/owner；articulation 检查 root、DOF mapping、reset value | 找不到 required body/collision/articulation prim；joint limit/axis/drive 不可解释且无 manual override；用无来源默认值掩盖 schema gap；static checker 把 runtime-only 风险声明为 pass | MVP core |
| `AAN-06` | Runtime Smoke | Isaac Sim 4.1 cold runtime evidence | runtime smoke report、render artifacts、logs、manifest runtime evidence | Isaac 4.1 headless 新进程 cold load 成功；记录 runtime fingerprint；root/required prim 存在；render readback 非空且记录 mean RGB、non-background ratio、bbox ratio、hash；step N frames finite；reset pose 恢复；退出码 0 | stage load error/crash/hang；PNG 存在但 readback blank/all-background/invalid；step 出现 NaN/Inf 或异常爆炸；reset 不可恢复；runtime gate 未运行却被标 pass | MVP core |
| `AAN-07` | Benchmark Contract | EBench task entry contract | `task/task_config.yaml`、`required_prims.yaml`、`evaluator.yaml` 或等价 manifest entrypoints | required prim 覆盖 asset root、manipulated body、collision prim、articulation/root 或 N/A、spawn anchor、goal/target semantic prim；LabUtopia/EBench adapter 能读取 package、task contract、manifest；claims allowed/forbidden 明确 | 自动猜 success predicate；缺 evaluator/metric entrypoint；required prim mapping 与 stage 不一致；waiver 后仍声明 full parity 或 official comparability | MVP core |
| `AAN-08` | Replication Set | 第二/第三 USD asset 复制验收 | 另外 2-3 个 USD asset 的独立 package + manifest + evidence | 至少一个 rigid-only 或 mostly-rigid prop；至少一个非 DryingBox articulated asset；不新增 hard-coded DryingBox path/name；所有 asset manifest schema、gate 名称、status semantics 一致；2026-06-30 retained run 使用 `MuffleFurnace` 和 `Beaker_01` 通过 static/runtime/benchmark gates | 只能跑 DryingBox；新增隐式规则而非 contract 输入；第二/第三资产发现 semantic gap 但未写 blocked/waived；输出 schema 不一致 | MVP exit |
| `AAN-09` | Negative Gate | 负例和 waiver/block 边界验收 | 一个缺 MDL、不可 mirror remote URI 或 schema gap 的负例 package/evidence | 负例稳定产生 `blocked` 或 `ready_with_waivers`；waiver 字段完整；CLI 返回码与 manifest total status 一致；周报能聚合失败模式、waiver 数量、representative artifact；2026-07-01 retained run 使用 unauthorized remote URI 负例验证 blocked 边界 | 负例被误判 ready；blocked 没有 reason；waiver 没有 forbidden claims；`not_run` 被当作 pass | MVP exit |
| `AAN-09.5` | PM Evidence Table | 周报/验收汇总口径 | PM-facing evidence table JSON/Markdown，从 AAN-07/08/09 manifests 聚合资产状态、gate、evidence、failure mode、claim boundary | 至少同时展示 ready、contract-ready-runtime-pending、blocked 三类；`not_run` 不被当作 pass；每行链接源 manifest；failure mode 和 waiver count 可周报聚合；2026-07-01 retained run 输出 `pm_evidence_table.json` / `.md` | 把 contract-only DryingBox 误报成 runtime-ready；只展示成功资产；blocked/waiver 无法聚合；claim boundary 丢失 | MVP exit |
| `AAN-10` | MJCF Scout | AutoBio / MJCF research lane | MJCF source adapter research report 和 semantic gap manifest prototype | 抽取 MJCF geometry、body tree、joint、actuator、sensor、material、contact/plugin/task semantic；明确哪些能转 USD，哪些必须 surrogate/waiver/block；不承诺 official reproduction；2026-07-01 retained run 输出 `aan10.mjcf_scout.v1` manifest | 把 MJCF 强行先转 USD 后宣称语义无损；MuJoCo plugin/fluid/process/contact gap 静默通过；`normalize-asset` 隐式接受 MJCF | Post-MVP |
| `AAN-11` | Profiles | 多 source / target profile 扩展 | `source_adapters/`、`target_profiles/`、`validators/` 的重构方案或实现 | 只有在 USD -> EBench MVP 稳定后再抽象；保持 AAN-00 到 AAN-09 manifest 兼容；新增 profile 有独立 gate matrix | 过早抽象破坏 MVP；旧 manifest 不兼容；profile 之间共享隐式硬编码 | Post-MVP |

产品口径：`AAN-00` 到 `AAN-07` 证明 DryingBox 可以从 source USD/task 进入 EBench
Isaac 4.1 package contract；`AAN-08` 到 `AAN-09` 证明这不是单资产特化，并且失败/waiver
边界可机器判定；`AAN-09.5` 把这些证据整理成 PM/周报可直接消费的表；`AAN-10+`
才进入 MJCF、AutoBio、多 target profile、deformable 或 official benchmark comparability
等扩展。

## MVP check matrix

第一阶段只承诺 USD rigid body 和 articulated body。验收要覆盖：

| Stage | 目标 | 通过标准 |
|---|---|---|
| Source inventory | 读清楚 source USD 包 | 列出 root layer、sublayer、reference、payload、variant、clip、texture、MDL、required prim |
| Dependency closure | 资产路径闭环 | target package 内无未授权 remote URI、无缺失 local dependency、无 package escape |
| Material closure | 材质可解释且 source 优先保留 | source MDL/texture 可追溯；native binding / local mirror / UsdPreviewSurface compatibility fallback / explicit waiver / blocked 五选一且记录 |
| Rigid-body closure | 刚体可物理运行 | authored collision、mass、inertia、scale、visibility、spawn pose 保留；缺失值按 provenance 生成后被目标 runtime 接受 |
| Articulation closure | 铰接可操作 | authored joint type、axis、limit、drive、root articulation、reset pose、DOF mapping 保留；缺失语义必须 manual override 或 blocked |
| Version compatibility | Isaac 5.1 -> Isaac 4.1 差异处理 | 不依赖目标 runtime 不支持的 schema、extension、material path 或 resolver 行为 |
| Runtime smoke | 不是纸面通过 | 在目标 Isaac Sim 4.1 环境执行 cold load / render readback / step / reset smoke |
| Benchmark contract | 可进入 EBench task | required prim paths、task config、metric/evaluator 入口、evidence manifest 全部存在 |

这些 Stage 完成后，可以对产品说：

> 这类 USD 刚体/铰接资产，不只是“能打开文件”，而是能被包装成一个 EBench 可消费的资产包；
> 我们知道它的材质怎么来的、物理怎么进 runtime、铰接怎么动、渲染是否正常、以及失败时失败在哪一层。

不能对产品说：

> 任意 USD、任意柔性体、任意液体、任意官方 leaderboard 任务已经自动可评测。

## Product claim boundary

可以对产品经理和外部协作方说：

- 第一阶段支持 USD rigid body / articulated body 的标准化接入；
- 输出 EBench 可消费的 asset package、task contract 和 evidence manifest；
- 能检查并记录 dependency、material、physics、articulation、runtime smoke 的状态；
- 能最大保真保留 source material / physics authoring；目标 runtime 不兼容时附加兼容层；
- 能为缺失 physics value 生成规范填充值，但每个填充值都有 provenance 和 runtime evidence；
- 能把 missing dependency / unauthorized remote URI 收敛成 `mirrored/pruned/waived/blocked`
  四类可审计结论，而不是只把问题留给人工排查；
- 能区分 `ready`、`ready_with_waivers`、`failed`、`blocked`，避免把问题藏在转换流程里；
- DryingBox 是首个验收资产，后续会用 2-3 个额外 USD 资产验证不是单资产特化；
- AAN 把 LabUtopia / EBench 中手工维护的 USD、MDL、texture、physics 修补逻辑收敛到
  ConvertAsset。

不能说：

- 任意 USD 都能自动转换并评测；
- 已支持 MJCF / URDF / AutoBio official reproduction；
- 已达到 EBench official leaderboard comparability；
- 能保证 pixel-perfect 渲染一致；
- rich MDL 能无损转换到所有 runtime；
- fallback 后仍具备 full material parity；
- generated physics value 等同于 source-authored physical parameter parity；
- 能自动理解任意 task success predicate；
- 柔性体、液体、颗粒、布料等复杂仿真语义已经闭环。

安全表述：

> 我们不承诺所有资产都能自动跑通，但承诺每个资产为什么能跑、为什么不能跑、哪些风险被
> waiver，都有可追溯证据。

## Static USD / MDL / texture closure matrix

| Check | PASS | WARN | FAIL/BLOCK |
|---|---|---|---|
| USD composition | all sublayers/references/payloads/clips/variants resolved inside package or allowed roots | opaque usdz / partial variant coverage | missing required USD, path escapes package |
| Remote URI | mirrored locally or explicitly allowed by target resolver evidence | allowed for dev-only profile | unauthorized remote, no resolver evidence |
| MDL source | source MDL native resolved or mirrored; compatibility fallback may be added | external-only with waiver and forbidden claims | source MDL discarded, missing required MDL, or no fallback/block decision |
| Texture closure | every used texture exists, mirrored, rewritten package-relative | absolute path awaiting mirror | missing required texture, hash conflict, package escape |
| Fallback fidelity | channel provenance recorded and target accepts PreviewSurface | defaulted noncritical channels with source preserved | semantic/display-critical material degraded, transparent target invisible, or fallback has no provenance |
| Residual MDL | no active local/external residue under target no-MDL profile | blocked/forced-blocked recorded | active residual MDL without policy allowance |
| Variant/clip coverage | all declared branches checked | active selection only | unscanned required branch |
| Evidence manifest | source path, resolved path, package path, policy decision recorded | incomplete optional metadata | missing decision for required dependency |

Path status 分类建议：

- `local_existing`
- `local_missing`
- `local_mirrored`
- `task_scope_pruned`
- `remote_allowed_native`
- `remote_mirrored`
- `remote_unresolved`
- `explicit_waiver`
- `package_escape`
- `unsupported_scheme`

Remote URI 不能默认通过。只有两种可通过：target profile 明确允许并有 runtime resolver
证据，或已经 local mirror 到 target package 并重写为 package-relative。

对 PM 和周报来说，`local_missing` / `remote_unresolved` 不是最终状态；它们只是发现阶段状态。
每条进入周报的缺口必须有最终 resolution：`mirrored`、`pruned`、`waived` 或 `blocked`。

## Material closure policy

Material closure 要单独成为 policy，不混进 Lift2 task contract。

优先级和含义：

1. `native_resolved`: target runtime 能直接解析 source material binding，source material
   artifact 仍记录 hash 和 owner layer。
2. `local_mirror`: remote MDL / texture 被复制或镜像到 target package，并重写 binding。
3. `preview_surface_fallback`: rich MDL 被转换为 UsdPreviewSurface，保住 base color /
   roughness / metallic / normal / opacity 等核心通道；fallback 是 target compatibility
   output，不删除 source MDL / texture closure 记录。
4. `explicit_waiver`: 资产可用于物理或任务 smoke，但材质不完整；必须写 waiver id、原因、
   影响范围和不能声明的内容。
5. `blocked`: 材质缺失会影响任务语义或产品展示，不能通过。

例如 `Aluminum_Anodized_Charcoal.mdl` 这类 remote dependency，合理路线是 local
mirror，并把它记录在 material closure evidence；如果短期只用 waiver，也必须明确它不是
full material parity。

Transparent Beaker / Beaker_01 这类透明资产不能用“能打开 stage”代替材质验收。它的
material record 至少要说明透明策略来自 source MDL pin、texture、constant、UsdShade
input、template 还是 manual override；render readback 必须证明目标资产不是全透明、
全背景或不可分辨轮廓。

### UsdPreviewSurface fallback 允许条件

- source MDL 可解析到足够信息：至少 base color texture 或 base color constant；
  roughness、metallic、normal、opacity 可缺省但必须记录。
- target profile 不要求 MDL native fidelity，或 remote/local MDL mirror 不可用但 benchmark
  允许 PreviewSurface。
- fallback 不影响任务语义。颜色/纹理参与识别、抓取目标判别、产品展示时，缺核心贴图不能
  静默 fallback。
- 透明材质 fallback 必须给出可见性证据。若 opacity / transmission 映射导致资产在目标视角
  不可见，render gate 必须 `blocked`。
- fallback 后材质必须有普通 `outputs:surface`，且 residual MDL 状态明确为 cleaned /
  blocked / external waived。

### Fidelity fields

每个 fallback record 至少记录：

- `closure_mode`
- `source_mdl_asset`
- `source_shader_prim`
- `material_prim`
- `binding_scope`
- `source_assets_preserved`: true / false
- `compatibility_surface_path`
- `extracted_channels`: baseColor / roughness / metallic / normal，逐项记录
  `source=pin|mdl_text|constant|default|missing`
- `texture_paths`: raw / resolved / mirrored target path / hash
- `color_space`: baseColor=sRGB，roughness/metallic/normal=raw
- `roughness_transform`: direct 或 gloss inverted
- `transparency_strategy`: opaque / opacity_input / alpha_texture / approximated /
  unsupported
- `defaults_used`
- `losses`: unsupported MDL parameters、procedural/noise、clearcoat、emission、opacity、
  anisotropy、UDIM uncertainty
- `evidence_level`: pin exact / mdl text heuristic / defaulted / waived
- `residual_mdl`: local/external/blocked/forced-blocked counts
- `visibility_evidence`: render frame path、bbox ratio、non-background ratio、failure mode

注意：当前 no-MDL 代码默认保留相对 texture path，只有 CLI
`--resolve-textures-to-absolute` 才启用旧的绝对路径行为。Normalizer 设计应以当前代码
行为为准。

## Physics and articulation checks

### Value provenance

Physics closure 的默认策略是 authored value 优先，其次才是规范生成。所有 value record
都要有 `value_source`：

| Value source | 含义 | 允许场景 | Evidence |
|---|---|---|---|
| `authored` | source USD 已提供 | 默认优先保留 | owning layer、attribute path、raw value、unit/scale |
| `derived` | 从 mesh、bbox、volume、convex hull、density 等确定性输入推导 | 缺 mass/inertia/collision，且任务不要求真实物理标定 | method、input artifact hash、formula/version、generated value |
| `template` | 按资产类别使用版本化模板 | 玻璃烧杯、金属箱体、塑料把手等常见类别；需要 asset class 明确 | template id、density/friction/restitution 参数、适用范围 |
| `manual_override` | 由 task contract 或人工审核给定 | joint axis/limit/reset pose、required prim semantic、特殊 collision proxy | owner、reason、review date、source note、forbidden claims |

`derived` 和 `template` 不是 waiver；它们是可追溯的生成值。只有当生成值影响结论可信度，
但目标 task 仍可执行时，才额外附带 waiver 和 forbidden claims。

### Static gate

Static gate 负责“资产声明是否完整、可解释”：

- mass：是否 authored，单位/数量级，缺失时是否有 `derived` / `template` /
  `manual_override` policy；
- inertia：是否存在、finite、正定/数量级合理；
- collision：collider prim、approximation、enabled、collision group/filter、mesh 是否存在；
- joint limit：lower/upper 是否存在、顺序是否有效、单位约定；
- reset pose：root pose、joint default pose、required prim path、DOF mapping；
- dependency/material/schema compatibility：缺失路径、unsupported schema、MDL/texture closure。

第一阶段 `physics_checks.py` 以检查和最小 override 建议为主，不做大规模自动物理修复器。
自动生成或 override 必须有 evidence 记录和 target profile 授权。没有 provenance 的默认
mass、inertia、collision proxy、joint limit 或 reset pose 不能通过。

推荐的第一阶段填充策略：

- rigid prop 缺 mass / inertia：可从 bbox/mesh volume 和 asset-class density template
  生成，runtime step 稳定后通过；
- Transparent Beaker 缺 collision：可生成 conservative convex hull 或 cylinder proxy，但
  必须保留 visual mesh，并记录 proxy 与 visual bbox 的差异；
- articulated asset 缺 joint axis / limit：不能自动猜。Cabinet Drawer 这类复制验收资产
  必须从 source 或 manual contract 得到 axis、limit 和 reset pose；
- collision mesh 缺失且无法从 visual mesh 生成合理 proxy：`blocked`。

### Runtime gate

Runtime gate 负责“Isaac Sim 4.1 是否真的接受并执行”：

- mass/inertia 是否被 physics engine 实际加载，是否导致 warning/error；
- collision 是否产生合理 contact，不穿透、不爆炸；
- joint limit 是否在 runtime articulation view / dynamic control 层可见并生效；
- reset pose 是否能在 runtime 应用，step 后保持 finite；
- articulated DOF 是否可枚举、可控制、可回读；
- static 看似合法但 runtime 不支持的 schema/extension，必须由 runtime gate 判 fail 或 waiver。

## Temporary waiver and blocked policy

Temporary waiver 只能覆盖“已记录、已知影响、短期不阻断目标任务”的缺口。Waiver 不是 pass，
也不能替代 source preservation 或 value provenance。

允许 temporary waiver 的缺口：

- 非语义关键材质细节损失，例如 clearcoat、anisotropy、细微 roughness/normal 差异；source
  MDL/texture 已保留，fallback channel provenance 已记录。
- 透明材质用 PreviewSurface opacity 近似，但 task 只评估 grasp / place / collision /
  position；manifest 必须禁止 full material parity 和 product-display claim。
- 非语义 decorative texture 缺失，且 render readback 仍能识别目标资产。
- mass / inertia 使用 `derived` 或 `template` 生成，runtime step/reset 稳定，且任务不评估
  真实动力学参数；manifest 必须禁止 physical-parameter parity。
- headless runtime 的非阻断 warning，例如 audio、windowing、deprecation warning；cold load /
  render / step / reset 必须通过，日志归档。
- active variant only coverage，前提是 EBench task contract 明确只使用该 active variant。
- MVP 阶段 performance budget 未冻结；只能作为 soft gate，不能声明性能达标。

必须 blocked 的缺口：

- required USD dependency 缺失、package escape、未授权 absolute path 或 unauthorized remote
  URI 未 mirror / allow。
- required prim path 缺失：asset root、manipulated body、collision prim、joint/root prim、
  spawn anchor、goal/target semantic prim。
- stage 无法打开，或 Isaac 4.1 cold load crash、hang、fatal error。
- source material 被丢弃，只剩无 provenance fallback；或语义关键 texture / transparency
  缺失导致任务目标不可识别。
- Transparent Beaker render readback 中全透明、全背景、全黑/白、bbox 太小或无法分割。
- rigid body 缺 collision 且无法生成合理 proxy；step 出现 NaN/Inf、穿透爆炸或不可解释漂移。
- articulated joint type / axis / limit / drive / reset pose 不可解释，且没有 manual override；
  runtime 报 zero DOF 或 DOF mapping 与 contract 不一致。
- reset pose 不能恢复 root 或 joint state。
- EBench contract 缺 task config、required prim mapping、metric/evaluator entrypoint。
- `conda isaac41` 或 Isaac 4.1 环境在验证过程中被 install/update/remove 修改，或 pre/post
  fingerprint 不一致且无可信解释。

## Runtime evidence gates

### Test environment policy for Isaac 4.1

Runtime gate 可以使用已有的 `conda isaac41` 环境作为测试 shell / 路径上下文，也可以使用
干净 shell 加 `ISAAC_SIM_ROOT`。关键约束是：环境只能读和运行，不能被 normalizer 测试修改。

允许：

- 使用已经存在的 `conda isaac41` 环境；
- 使用 `ISAAC_SIM_ROOT` 指向已有 Isaac Sim 4.1 安装目录；
- 通过仓库统一入口运行命令：`./scripts/isaac_python.sh ./main.py ...`；
- 运行只读环境探测命令，例如 `which python`、`python --version`、
  `conda list --explicit`、`pip freeze`、`git rev-parse HEAD`；
- runtime gate 只允许 headless Isaac 4.1 smoke：cold load、render readback、step、reset。

禁止：

- `conda install`、`conda update`、`conda env update`、`conda remove`；
- `pip install`、`pip uninstall`、`python -m pip install`；
- 修改 conda env 文件、site-packages、Isaac 安装目录、Kit extension cache；
- 为了测试临时 patch wrapper，或修改 `PYTHONPATH` / `LD_LIBRARY_PATH` 的持久配置；
- 启动 GUI / full Isaac app 作为 normalizer 验收路径。

Environment fingerprint 建议写入 manifest 的 `environment.fingerprint`，完整 conda / pip 输出
放到 `evidence/env/` 下，manifest 记录路径和 hash：

```json
{
  "environment": {
    "fingerprint": {
      "conda_env_name": "isaac41",
      "conda_prefix": "...",
      "conda_explicit_sha256": "...",
      "pip_freeze_sha256": "...",
      "python_executable_before_wrapper": "...",
      "python_version_before_wrapper": "...",
      "isaac_sim_root": "...",
      "isaac_python_runner": "<ISAAC_SIM_ROOT>/python.sh",
      "isaac_version": "Isaac Sim 4.1.x",
      "kit_version": "...",
      "pxr_version": "...",
      "gpu": "...",
      "driver_version": "...",
      "cuda_runtime": "...",
      "renderer": "PathTracing",
      "headless": true,
      "wrapper": "scripts/isaac_python.sh",
      "wrapper_sha256": "...",
      "git_commit": "...",
      "created_at": "..."
    }
  }
}
```

每个 runtime gate 都要在 manifest 的 `commands` 字段记录不可变 command contract：

```json
{
  "commands": {
    "runtime_smoke_001": {
      "stage": "runtime_smoke",
      "cwd": "/cpfs/user/zhuzihou/dev/ConvertAsset",
      "argv": [
        "./scripts/isaac_python.sh",
        "./main.py",
        "normalize-asset",
        "asset.usd",
        "--gates",
        "runtime",
        "--target-runtime",
        "isaac41"
      ],
      "env_policy": {
        "allowed_existing_conda_env": "isaac41",
        "mutation_allowed": false,
        "requires_isaac_sim_root": true,
        "headless_only": true
      },
      "env_fingerprint_id": "env_isaac41_001",
      "stdout_path": "evidence/runtime_smoke.stdout.log",
      "stderr_path": "evidence/runtime_smoke.stderr.log",
      "exit_code": 0
    }
  }
}
```

环境未变更的判定应由 pre/post fingerprint 支持：

- runtime 前后各采集 `conda list --explicit`、`pip freeze`、`CONDA_PREFIX`、
  `ISAAC_SIM_ROOT`、`which python` 和 `scripts/isaac_python.sh` hash；
- `conda_explicit_sha256`、`pip_freeze_sha256`、wrapper hash 前后一致；
- 没有执行 install / update / remove 类命令；
- Isaac 安装目录不作为 normalizer 输出路径。

| ID | Check | PASS | FAIL/BLOCK |
|---|---|---|---|
| `ENV-01` | Isaac41 环境来源 | 使用已有 `conda isaac41` 或干净 shell；`ISAAC_SIM_ROOT` 指向已有 Isaac Sim 4.1；通过 `scripts/isaac_python.sh` 执行 | 创建/更新 conda 环境；未记录 Isaac root；绕过 wrapper 且无法复现 |
| `ENV-02` | 环境只读性 | pre/post `conda list --explicit`、`pip freeze`、wrapper hash 一致；manifest 记录 mutation check | 执行 `conda install/update/remove`、`pip install/uninstall`；pre/post fingerprint 不一致且无解释 |
| `ENV-03` | Runtime command contract | 每个 runtime gate 在 manifest 中记录 cwd、argv、env policy、fingerprint id、stdout/stderr、exit code | 只有人工描述没有命令；缺 env fingerprint；无法证明 headless Isaac 4.1 是实际运行环境 |
| `ENV-04` | Headless-only runtime | runtime gate 使用 Isaac Sim 4.1 headless 新进程；不启动 GUI/full Isaac | 依赖手动 GUI 操作；运行过程不可批处理复现 |
| `ENV-05` | Claims boundary | `not_run`、`blocked`、`waived` 与环境状态绑定；环境不可用时不声明 runtime pass | 环境未验证却声明 ready；waiver 未禁止相关 runtime/material/render claims |

### Cold load

通过标准：

- 使用 Isaac Sim 4.1 headless 新进程，`SimulationApp(headless=True)` 成功创建；
- 创建 `SimulationApp` 前不导入 `omni.*` / Isaac runtime 模块；
- 记录 runtime 指纹：Isaac/Kit 版本、Python 路径、关键 extension、GPU/driver、
  renderer preset、是否 cold extension cache；
- 通过 `omni.usd.get_context().open_stage()` 打开 normalized root USD；
- 等待 `ctx.is_stage_loading()` / `ctx.is_standby()` 结束后，`ctx.get_stage()` 非空；
- root prim、target asset prim、required rigid/articulation prim paths 全部存在且有效；
- USD/Omni 日志中无 fatal/error 级别 load failure；
- 进程正常 close，退出码为 0，无 hang、crash、segfault、uncaught exception。

### Render readback

Render evidence 不能只看 PNG 是否存在。每帧至少记录：

- view name、path、bytes、sha256；
- renderer、resolution、warmup/render steps；
- camera prim、camera fit、bbox source；
- mean RGB、non-background pixel ratio、2D bbox ratio；
- blank / near-black / saturated / all-background 判定；
- material/render failure modes。

关键失败模式：

- `SimulationApp` / viewport failure；
- stage 未加载完成就 capture；
- bbox 非有限、bbox 被环境壳污染、相机看空、near/far clipping 错；
- RGBA readback 为 `None`、shape 不对、全透明、全黑、全背景、NaN/Inf；
- 缺 texture/MDL 导致红/黑/灰 fallback 且无 material waiver；
- 多视角 hash 完全一致且相机应移动；
- 目标 2D bbox 太小、被遮挡、超出画面。

### Physics step and reset

Rigid asset：

- runtime 中能找到 rigid body prim，PhysicsRigidBodyAPI / collider / mass schema 可被
  Isaac 4.1 接受；
- reset 到 spawn pose 后，step N 帧无 crash、无 NaN/Inf transform、无异常速度爆炸；
- 若资产应静止，step 后 pose drift 小于阈值；
- 若资产应受重力，短步进后高度变化方向合理，最终不穿透 ground plane 到异常深度；
- 记录 collider prim 数量、approximation 类型、enabled 状态。

Articulated asset：

- articulation root 可被 Isaac 4.1 识别；
- DOF 数量、joint 名称、joint type、axis、limit、drive 与 static inventory 对齐；
- reset pose 可应用，关节位置在 limit 内；
- step N 帧后 root transform、link transforms、joint positions/velocities 全部 finite；
- 对每个 controllable DOF 做小幅 target 或 velocity smoke，确认 joint 有响应且不越过 hard
  limit；
- 记录 failed joints：missing drive、limit invalid、axis unsupported、DOF mapping mismatch、
  articulation not created、runtime reports zero DOF。

## DryingBox first acceptance

DryingBox 是首个验收对象。首验清单：

- static inventory 列出 root layer、sublayer、reference、payload、variant、clip、
  textures、MDL、defaultPrim；
- package closure 后，target package 内无缺失 local dependency；remote URI 必须被 local
  mirror、fallback 或 waiver 覆盖；
- required prim paths 至少覆盖 asset root、manipulated object/body、collision prim、
  articulation/root 或明确 N/A、task spawn anchor、goal/target semantic prim；
- material gate 对每个材质给出 closure status；若用 waiver，周报只能声明
  “runtime/task smoke passed with material waiver”，不能声明 full material parity；
- physics gate 证明 collision、mass/inertia、scale、visibility、spawn pose 可被 Isaac
  4.1 接受；
- runtime gate 在 Isaac Sim 4.1 完成 load、render readback、step N frames、reset；
- benchmark gate 输出 EBench task config、required prim mapping、metric/evaluator path，
  并能被 LabUtopia / EBench adapter 读取；
- evidence manifest 可直接进入周报：含 commands、timestamps、artifact paths、claims
  allowed/forbidden。

## 多资产复制验收

DryingBox 通过后，必须扩到另外 2-3 个 USD asset，证明不是单资产特化：

- 至少一个 rigid-only 或 mostly-rigid prop；
- 至少一个非 DryingBox articulated asset，必须有真实 joint/limit/drive/reset pose；
- 可选一个负例资产，带缺失 MDL、不可镜像 remote URI 或 schema gap，用来验证
  `blocked/waived` 边界；
- 不允许新增 hard-coded DryingBox path/name；只改 contract/manifest 输入；
- 所有资产 manifest schema 一致，gate 名称一致；
- 每个资产都能生成独立 package 和 evidence；
- 若第二/第三资产暴露新 semantic gap，必须以 `blocked` 或 `waived` 入 manifest，不能扩展
  隐式规则。

2026-06-30 retained AAN-08 run 使用以下两个 LabUtopia 原始资产作为复制验收对象：

| ID | Asset | Source role | 验收角色 | Acceptance focus | Retained evidence |
|---|---|---|---|---|---|
| `AAN-08a` | `MuffleFurnace` | 非 DryingBox articulated lab instrument | 非 DryingBox articulated asset | authored articulation root、revolute joint axis/limit/DOF mapping；invalid zero mass/inertia 以 `bbox_shell_density_template_v0` 写回 package 并记录 `derived` provenance | `docs/records/evidence/2026-06-30-aan-08-replication-set/muffle_furnace_manifest.json` |
| `AAN-08b` | `Beaker_01` | LabUtopia transparent beaker | 透明材质 rigid prop | MDL local mirror、opacity/transparency strategy、render readback visibility、collision、derived mass/inertia provenance | `docs/records/evidence/2026-06-30-aan-08-replication-set/beaker_01_manifest.json` |

原建议候选仍保留为后续扩展池：

| ID | Asset | LabUtopia task signal | 验收角色 | Acceptance focus |
|---|---|---|---|---|
| `AAN-08a` | Cabinet Drawer | `level1_open_drawer`、`level1_close_drawer`、`level2_openclose` | 非 DryingBox articulated asset | joint type / axis / limit / reset pose / DOF mapping；证明 drawer/prismatic-like motion 不是 DryingBox hinge hard-code |
| `AAN-08b` | Transparent Beaker / `Beaker_01` | `level1_place`、`level1_pour`、`level2_TransportBeaker`、`level2_PourLiquid`、`level3_TransportBeaker`、`level4_CleanBeaker` | 透明材质 rigid prop | MDL/texture local mirror、opacity/transparency fallback、render readback visibility、collision proxy、mass/inertia provenance |

真实 source USD path、defaultPrim、required prim path、asset class 和 task contract 必须在
`AAN-01 Manifest Seed` 或对应资产 manifest 中由 LabUtopia asset inventory 填入后才能验收。
仅有任务名不能视为通过。

## Future adapter families

Future adapter family 只表示架构预留，不表示当前支持。新增 source adapter 必须交付：

- source semantic inventory；
- loss / semantic gap report；
- dependency / material / physics / articulation closure 策略；
- target profile 映射；
- runtime evidence；
- 明确的 unsupported semantics、waiver policy 和 blocked reason。

长期 adapter family：

| Family | Source truth | First-class concern | Phase 1 status |
|---|---|---|---|
| Arbitrary USD | USD layers and composed stage | 更复杂的 variant、payload、asset resolver、schema/version gap | 只保留 inventory + gap reporting 演进方向 |
| URDF | Robot geometry / kinematics | link/joint/collision 可迁移；rich material 通常不足 | Future adapter，不作为 MVP 输入 |
| MJCF / MuJoCo | MuJoCo model and task semantics | actuator、sensor、contact、tendon、equality、plugin、task semantic | Future adapter / `AAN-10` research lane |
| Genesis native | Genesis asset/runtime contract | target runtime profile、physics/render behavior、evidence schema | Future target profile |
| EOS adapter | Asset resolution and evaluation evidence | 消费 package/manifest/claim boundary，不拥有 USD/MDL 修补逻辑 | Future consumer adapter |

保留这组 family 的目的，是让后续格式都能通过 adapter/profile 进入同一套 gate、waiver、
blocked reason 和 claim boundary 机制，而不是为每个 benchmark 写一套一次性转换脚本。

## AutoBio / MJCF 扩展路线

AutoBio 不能被当成“另一个 LabUtopia”。它的 source truth 是 MuJoCo / MJCF 和
MuJoCo task semantics。后续扩展时应新增 `mjcf_package` source adapter，而不是把
MJCF 先强行压成 USD 再假装语义没损失。

MJCF route 的推荐原则：

- MJCF source adapter 先抽取 geometry、body tree、joint、actuator、sensor、material、
  equality / tendon / contact / plugin / task semantic；
- 如果 target 是 EBench / Isaac，target adapter 再决定哪些能转 USD、哪些必须写 surrogate
  或 waiver；
- 如果 target 是 EOS / Genesis，则输出对应 target profile 的 evidence，而不是绕路经过
  EBench；
- MuJoCo plugin、thread contact、fluid / process primitives 不能静默转换，必须成为
  explicit semantic gap。

2026-07-01 的 `AAN-10 MJCF Scout` retained run 已经把这条路线落成最小原型：

- 输入是 AutoBio-like MJCF fixture，不是官方 AutoBio 复现声明；
- 输出 `aan10.mjcf_scout.v1` manifest，只记录 source inventory 和 semantic gap；
- 已抽取 body tree、geom、joint、site、mesh、texture、material、actuator、sensor、
  contact、equality、tendon 和 plugin；
- `overall_status` 固定为 `semantic_gap_report_only`；
- forbidden claims 明确禁止“MJCF 已转换成 USD”和“AutoBio official reproduction is
  supported”。

这个 scout 可以作为后续 `source_adapters/mjcf` 的设计输入，但不能被 EBench 或 AAN MVP
当成 ready asset package。

## 暂不承诺的范围

当前设计不承诺：

- arbitrary USD 都自动可用；
- deformable body、cloth、particle、liquid、granular media 的完整可评测闭环；
- AutoBio official reproduction；
- EBench official leaderboard comparability；
- policy success；
- pixel-perfect render parity；
- rich MDL 到所有 target runtime 的无损转换；
- 自动理解任意 task success predicate；
- LabUtopia / EBench 仓库维护 USD/MDL/物理修补逻辑；
- 架构预留的 arbitrary USD / URDF / MJCF / MuJoCo / Genesis family 已经达到产品支持状态。

这些不是不做，而是要在 MVP 之后作为独立 source adapter、target profile 和 validator 扩展。

## 实施顺序建议

1. `AAN-00 Contract Freeze`：冻结本文的 lineage、repo boundary、MVP Stage、CLI、package
   layout、manifest schema、gate semantics、material policy 和 status semantics。
2. `AAN-01 Manifest Seed`：把 LabUtopia DryingBox / Lift2 POC 的手工步骤转成 manifest：
   source root、root USD、依赖、remote URI、MDL/texture、required prim、EBench task
   fields、已知 waiver/blocker。
3. `AAN-02 CLI Skeleton`：落 `normalize-asset` flat CLI、MVP 模块骨架、IR model、package
   layout、manifest writer 和 dry-run path。
4. `AAN-03 USD Closure`：实现 `usd_inventory + dependency_closure`，输出 package-local
   USD tree。验收：无未授权 remote URI、无缺失 local dependency、组合关系仍保留，不
   flatten。
5. `AAN-03R Dependency Resolution`：把 raw source 中发现的 missing / remote URI 缺口收敛成
   `mirrored/pruned/waived/blocked` 决策。验收：DryingBox overlay pass 继续成立；单体
   `DryingBox_01.usd` 的 `UnitsAdjust-*.metricsAssembler` 和 raw `lab_001.usd` 的 remote URI
   都有查找范围、处理结论、claim impact，而不是只停在 blocker 列表。
6. `AAN-04 Material Closure`：先保留 source material binding、MDL 和 texture，并做 local
   mirror；目标 Isaac 4.1 不能稳定解析时才附加 PreviewSurface fallback。每个材质必须有
   closure record、channel provenance 和 source preservation evidence。
7. `AAN-05 Physics Static`：检查 collision、mass、inertia、rigid body API、joint
   type/axis/limit/drive/reset pose。authored value 原样保留；缺失值只能按
   `derived/template/manual_override` 生成并记录 provenance；第一轮允许 report/block，不急着
   大规模自动修。
8. `AAN-06 Runtime Smoke`：生成 Isaac Sim 4.1 cold load、render readback、step、reset
   smoke 证据，并写入 evidence manifest。
9. `AAN-07 Benchmark Contract`：输出 EBench task config、required prim mapping、
   metric/evaluator entrypoint，并由 LabUtopia / EBench adapter 消费。
10. `AAN-08 Replication Set`：用另外 2-3 个 rigid/articulated USD assets 证明不是
   DryingBox-only pipeline。2026-06-30 retained run 已用 `MuffleFurnace` 和
   `Beaker_01` 生成 package、manifest、runtime render/readback 和 benchmark contract
   evidence；Cabinet Drawer 保留为后续更强 prismatic/drawer 复制对象。
11. `AAN-09 Negative Gate`：用一个缺 MDL、不可镜像 remote URI 或 schema gap 的资产验证
    `blocked/waived` 是否清晰。2026-07-01 retained run 使用
    `remote_uri_block.usda`，稳定产生 `aan03_block_remote_uri`、CLI return code `5` 和
    weekly summary `status=pass`，同时证明后续 `not_run` gate 没有被当作 pass。
12. `AAN-09.5 PM Evidence Table`：把 DryingBox runtime-ready evidence、AAN-08 replication
    evidence 和 AAN-09 blocked negative evidence 聚合成 PM/周报表。2026-07-01 retained
    table 刷新后显示 3 个 `ready`、1 个 `blocked`，并把 `aan03_block_remote_uri`
    聚合为 failure mode。
13. `AAN-10+ Post-MVP Expansion`：进入 MJCF / AutoBio、多 source adapter、多 target
    profile、Genesis / MuJoCo / EOS adapter 等路线；先做 source adapter 和 semantic gap
    report，不承诺一口气完成 official reproduction。

### AAN-05 / AAN-06 implementation contract

当前实现采用 gate-by-gate 收敛：

- `--gates static` 默认跑到 `AAN-05-physics-static`。manifest 中必须包含
  `physics_closure`、`articulation_closure`、`static_physics_report`、
  `static_articulation_report`，并把 `runtime_evidence.status` 写成 `not_run`，不能暗示
  runtime 已通过。
- `--gates static,runtime` 才启动 `AAN-06-runtime-smoke`。runtime smoke 必须通过
  `scripts/isaac_python.sh` 新进程进入既有 Isaac 环境，写出 command contract、
  `cold_load`、`render_readback`、`physics_step`、`reset` 和 stdout/stderr/report/render
  artifacts。
- AAN-06 可以声明“配置的 headless Isaac runtime wrapper 完成 smoke”，但只有 manifest
  记录了明确 Isaac Sim 4.1 environment fingerprint 时，才允许声明“精确 Isaac Sim 4.1
  二进制验收通过”。
- AAN-05 的 static scope 以 `required_prim_paths` 为准，避免同一 scene 里的 beaker、
  table 等旁路 physics 污染 DryingBox 结论。
- AAN-05 对 `asset_class=articulated` 是严格 gate：缺 articulation root、缺 joint、revolute /
  prismatic joint 缺 axis 或有效 limit 都是 blocked；缺 drive 会记录为 `not_authored`，但对
  外部机械臂操作型任务不单独 blocked。
- AAN-06 的 render pass 只证明目标 runtime 有非空 readback、目标 bbox 可见、step/reset
  finite；它不等同于 full material parity。若 MDL 在 runtime 中有 fallback 或编译 warning，
  manifest 仍必须禁止 full visual material parity claim，直到 material/render parity 有单独证据。

### AAN-07 implementation contract

当前 `AAN-07-benchmark-contract` 采用显式 contract 输入，不自动猜 EBench success
predicate：

- 只有 `--gates` 包含 `benchmark` 时才运行 AAN-07；`static` 默认仍停在 AAN-05，
  `static,runtime` 默认仍停在 AAN-06。
- AAN-07 必须在 AAN-05 通过后运行；如果同时请求 `runtime`，则必须在 AAN-06 通过后运行。
- AAN-07 要求 `--contract` 指向 JSON 或 simple YAML task contract。contract 必须包含
  `task_config.task_id`、`task_config.benchmark`、`task_config.asset_id`、
  `required_prims.asset_root`、`required_prims.manipulated_body`、
  `required_prims.collision_root`、`required_prims.spawn_anchor`、
  `required_prims.goal_target`、`evaluator.entrypoint` 和 `evaluator.metric`。
- articulated asset 还必须包含 `required_prims.articulation_root`；rigid / auto asset 可以把
  articulation root 写成 `N/A` 或省略。
- 每个非 `N/A` required prim 必须能在 packaged `asset.usd` 中打开并找到。mapping 与 stage
  不一致时是 blocking，不允许用 task readiness claim 掩盖。
- AAN-07 pass 时写出 `task/task_config.yaml`、`task/required_prims.yaml`、
  `task/evaluator.yaml`，并在 manifest `entrypoints`、`benchmark_contract` 和
  `task_contract_report` 中记录。
- AAN-07 pass 只声明“EBench adapter handoff contract ready”；它不声明 official
  leaderboard comparability、full material parity、full physics parity 或真实 EBench episode
  metric 已经完成。

### EBench-01 consumer handoff contract

EOS BPL + EBench adapter 的第一步消费 milestone 记为 `EBench-01`。它是 AAN 的
downstream consumer，不是新的 ConvertAsset gate，也不是 EBench runtime / score gate。

EBench-01 只能读取 AAN 输出：

```text
asset.usd
task/task_config.yaml
task/required_prims.yaml
task/evaluator.yaml
manifest.json or evidence/manifest.json
```

它必须检查 `AAN-07-benchmark-contract` 和 `benchmark_contract.status=pass`，再把
`task_config`、required prim role mapping、evaluator/metric、waiver、blocker 和
allowed/forbidden claims 投影成 EOS BPL 证据。当前 AAN evidence 中可能出现
`overall_status=pass`；consumer 不能只看这个字段，必须同时检查 AAN-07 gate 和
benchmark contract。

EBench-01 明确禁止下游再手工修补：

```text
DryingBox USD path
MDL / texture path
articulation / joint path
required prim mapping
evaluator entrypoint
success predicate
```

如果 AAN package 缺 manifest、缺 task YAML、AAN-07 没 pass、required prim 不存在、
evaluator/metric 缺失、closure 被 blocked 或 waiver 不可审计，EBench-01 必须输出
structured blocker，不能 fallback 成伪成功。

EBench-01 的最小 claim boundary：

```text
manual_usd_mdl_articulation_patch_required=false
manual_patch_count=0
runtime_execution_status=not_attempted
score_eligibility_status=not_evaluated
standard_model_score=null
official_benchmark_reproduction=false
backend_parity=false
```

EOS 侧详细验收文档：

```text
/cpfs/user/zhuzihou/dev/embodied-eval-os/docs/operations/ebench01-aan-package-consumer-acceptance.md
```

## Multi-agent discussion summary

设计讨论拆成两轮只读审阅，并由主会话集成到本文。

第一轮确认 MVP contract：

| Reviewer | Focus | 采纳结论 |
|---|---|---|
| Architecture planner | 模块边界、IR、迁移顺序 | 第一阶段走 manifest-first、USD-only、EBench Isaac 4.1 target-profile-first；使用扁平 `asset_application_normalizer/`，不要过早抽象 |
| Feature designer | CLI、package layout、manifest、gate semantics | 新增 `normalize-asset` flat CLI；manifest 是外部消费主接口；waiver 必须改变总状态和 forbidden claims |
| Asset validator | USD/MDL/texture static closure | 复用 no-MDL 的 USD 组合依赖、MDL 识别、texture 抽取经验，但拆出只读 scanner；remote URI 默认不通过 |
| Isaac headless tester | cold runtime、render readback、step/reset smoke | static pass 不等于可用；MVP claim 必须绑定 Isaac 4.1 cold load、render readback、physics step、reset evidence |

第二轮补强长期架构、编号验收、环境策略和产品表达：

| Reviewer | Focus | 采纳结论 |
|---|---|---|
| Long-term architecture reviewer | arbitrary USD / URDF / MJCF / MuJoCo / Genesis 扩展能力 | 用六层能力地图保留 multi-source / multi-target 路线；Phase 1 只支持 USD -> EBench Isaac41 竖切 |
| Numbered acceptance reviewer | AAN 编号计划与验收标准 | 使用 `AAN-00` 到 `AAN-09` 管理 USD -> EBench MVP；`AAN-10+` 才进入 MJCF / 多 profile 扩展 |
| Isaac41 environment reviewer | 已有 `conda isaac41` 环境只读使用策略 | 可以用现有环境，但禁止 install/update/remove；runtime evidence 必须记录 pre/post fingerprint 和 command contract |
| Product framing reviewer | 产品经理可理解但不夸大的表述 | AAN 是资产准入整理和验收流水线；不承诺所有资产自动跑通，但承诺 pass/waiver/blocked 都有证据 |

采纳的设计决策：

- 不新建独立 repo；
- 不把实现放 EOS core；
- 不用 LabUtopia / AutoBio 作为核心抽象名；
- 使用 `source_format`、`source_runtime_lineage`、`target_runtime_profile`、
  `target_benchmark_profile`；
- MVP 先做 USD rigid + articulated -> EBench Isaac Sim 4.1；
- 材质闭环作为独立 policy，URDF importer 的材质缺口由 ConvertAsset no-MDL /
  UsdPreviewSurface / local mirror 路线补齐；
- 材质和物理采用 source-first preservation：原始 authoring 尽量保留，fallback 是附加兼容层；
  缺失物理值可以生成，但必须记录 `authored/derived/template/manual_override` provenance；
- LabUtopia / EBench 只消费输出 package、task contract 和 evidence，不维护 USD/MDL/物理
  修补逻辑；
- arbitrary USD / URDF / MJCF / MuJoCo / Genesis 是长期 adapter family，不是 Phase 1
  产品支持状态；
- runtime smoke 可用已有 `conda isaac41` 环境，但必须只读使用并记录环境未变更证据。

## References

- OpenUSD Toolset / `usdchecker`: https://openusd.org/dev/toolset.html
- NVIDIA Omniverse Asset Validator: https://docs.omniverse.nvidia.com/kit/docs/asset-validator/latest/index.html
- NVIDIA OpenUSD Exchange SDK: https://github.com/NVIDIA-Omniverse/usd-exchange
- NVIDIA SimReady: https://docs.omniverse.nvidia.com/simready/latest/overview.html
- NVIDIA SimReady Foundation: https://github.com/nvidia/simready-foundation
- Isaac Sim URDF importer: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html
- Isaac Sim MJCF importer: https://docs.isaacsim.omniverse.nvidia.com/4.5.0/robot_setup/import_mjcf.html
- Isaac Lab converters: https://isaac-sim.github.io/IsaacLab/main/source/api/lab/isaaclab.sim.converters.html
- Isaac Asset Transformer: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/robot_setup/asset_transformer_tutorials.html
- OpenAssetIO: https://openassetio.github.io/OpenAssetIO/
- RoboVerse / MetaSim: https://roboverse.wiki/metasim/
- MetaSim asset conversion guide: https://roboverse.wiki/metasim/developer_guide/converting_asset
- MuJoCo modeling / MJCF: https://mujoco.readthedocs.io/en/stable/modeling.html
