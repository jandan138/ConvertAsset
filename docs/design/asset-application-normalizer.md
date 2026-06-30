# Asset Application Normalizer

> Status: design proposal, 2026-06-30
> Owner repo: ConvertAsset
> First target: LabUtopia-style Isaac 5.1 USD assets -> EBench Isaac Sim 4.1 runtime package

## 一句话定位

Asset Application Normalizer 不是一个“任意资产万能转换器”，而是一个
target-contract normalizer：给定一个 source asset / source task 和一个 target
benchmark profile，它负责把资产、材质、物理、铰接、任务入口和验证证据整理到
“目标 benchmark 能加载、能渲染、能 step、能评测或明确阻断”的状态。

第一阶段先做窄而硬的能力：USD rigid body 和 articulated body 进入 EBench Isaac
Sim 4.1。后续再扩展到 MJCF / AutoBio、Genesis-based benchmark、EOS adapter 等
路线。

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
Asset Application Normalizer，而不是再做一个 importer 或 asset manager。

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

## URDF / MJCF / 材质的原则

URDF importer 可以用，但 URDF 不是高保真材质载体。URDF 常用于 robot geometry /
kinematics 交换，材质表达通常远弱于 Omniverse MDL 或完整 USD material network。
因此从 URDF 进 Isaac 时，能保住 link / joint / collision 不代表能保住 rich MDL
material。

ConvertAsset 已有 no-MDL 能力：把 MDL material 转成 portable UsdPreviewSurface。
因此后续策略是：

1. 如果 source USD 已有可解析 MDL / native material binding，优先保留或 local mirror。
2. 如果 target runtime 缺 remote MDL dependency，优先做 local mirror。
3. 如果 rich material 无法可靠进入目标环境，降级为 UsdPreviewSurface，并写入 material
   fidelity report。
4. 如果确实只能放行缺失材质，必须使用 explicit waiver，不能静默通过。

这也解释了为什么 Isaac importer 和 ConvertAsset material closure 是互补关系：importer
解决格式入口，ConvertAsset 负责目标环境的 material closure 和证据。

## 仓库边界

### ConvertAsset

ConvertAsset 是主实现仓库。原因是它已经拥有：

- USD / MDL / UsdPreviewSurface 的处理代码；
- no-MDL、material inspection、render、mesh、GLB 等资产处理能力；
- Isaac Python wrapper 和资产实验文档；
- route-neutral asset conversion 的工程定位。

未来模块建议：

```text
convert_asset/asset_application_normalizer/
  source_adapters/
    usd_package/
    mjcf_package/
    urdf_robot/
  core_ir/
    lineage.py
    asset_package.py
    scene_package.py
    task_contract.py
    material_closure.py
    physics_closure.py
    evidence_manifest.py
  normalizers/
    usd_dependency_closure.py
    usd_material_closure.py
    usd_physics_closure.py
    usd_articulation_closure.py
    version_compatibility.py
  target_profiles/
    ebench_isaac41.py
    eos_asset_resolution.py
    genesis_native.py
    autobio_mujoco.py
  validators/
    static_usd.py
    cold_runtime.py
    render_readback.py
    step_smoke.py
    benchmark_contract.py
```

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
- 不把一次 POC 膨胀成通用 normalizer owner。

## 核心数据流

```text
source asset/task
  -> source adapter
  -> canonical package IR
  -> normalizers
  -> target profile
  -> validators
  -> target-ready package + evidence manifest
```

其中 canonical package IR 不是“全世界唯一真理模型”，而是为了稳定描述：

- source lineage；
- asset dependency graph；
- material binding 和 material closure 状态；
- rigid body / collision / mass / inertia 状态；
- articulation joint / limit / drive / reset pose 状态；
- task entrypoint、required prim paths、success predicate 所需语义；
- target profile 的 required checks 和 waiver policy。

## MVP: USD rigid + articulated -> EBench Isaac Sim 4.1

第一阶段只承诺 USD rigid body 和 articulated body。验收要覆盖：

| Stage | 目标 | 通过标准 |
|---|---|---|
| Source inventory | 读清楚 source USD 包 | 列出 root layer、sublayer、reference、payload、texture、MDL、required prim |
| Dependency closure | 资产路径闭环 | target package 内无未授权 remote URI、无缺失 local dependency |
| Material closure | 材质可解释 | native binding / local mirror / UsdPreviewSurface fallback / explicit waiver 四选一且记录 |
| Rigid-body closure | 刚体可物理运行 | collision、mass、inertia、scale、visibility、spawn pose 可被目标 runtime 接受 |
| Articulation closure | 铰接可操作 | joint type、axis、limit、drive、root articulation、reset pose、DOF mapping 可被目标 runtime 接受 |
| Version compatibility | Isaac 5.1 -> Isaac 4.1 差异处理 | 不依赖目标 runtime 不支持的 schema、extension、material path 或 resolver 行为 |
| Runtime smoke | 不是纸面通过 | 在目标 Isaac Sim 4.1 环境执行 load / render / step / reset smoke |
| Benchmark contract | 可进入 EBench task | required prim paths、task config、metric/evaluator 入口、evidence manifest 全部存在 |

这些 Stage 完成后，可以对产品说：

> 这类 USD 刚体/铰接资产，不只是“能打开文件”，而是能被包装成一个 EBench 可消费的资产包；
> 我们知道它的材质怎么来的、物理怎么进 runtime、铰接怎么动、渲染是否正常、以及失败时失败在哪一层。

不能对产品说：

> 任意 USD、任意柔性体、任意液体、任意官方 leaderboard 任务已经自动可评测。

## Material closure policy

Material closure 要单独成为 policy，不混进 Lift2 task contract。

优先级：

1. `native_resolved`: target runtime 能直接解析 source material binding。
2. `local_mirror`: remote MDL / texture 被复制或镜像到 target package，并重写 binding。
3. `preview_surface_fallback`: rich MDL 被转换为 UsdPreviewSurface，保住 base color /
   roughness / metallic / normal 等核心通道。
4. `explicit_waiver`: 资产可用于物理或任务 smoke，但材质不完整；必须写 waiver id、原因、
   影响范围和不能声明的内容。
5. `blocked`: 材质缺失会影响任务语义或产品展示，不能通过。

例如 `Aluminum_Anodized_Charcoal.mdl` 这类 remote dependency，后续更合理的路线是
local mirror，并把它记录在 full material closure follow-up；如果短期只用 waiver，
也必须明确它不是最终闭环。

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

## 暂不承诺的范围

当前设计不承诺：

- arbitrary USD 都自动可用；
- deformable body、cloth、particle、liquid、granular media 的完整可评测闭环；
- AutoBio official reproduction；
- EBench official leaderboard comparability；
- policy success；
- pixel-perfect render parity；
- rich MDL 到所有 target runtime 的无损转换；
- 自动理解任意 task success predicate。

这些不是不做，而是要在 MVP 之后作为独立 target profile 和 validator 扩展。

## 实施顺序建议

1. Documentation contract：冻结本文的 lineage、repo boundary、MVP Stage、material policy。
2. DryingBox extraction：把 LabUtopia DryingBox / Lift2 POC 的手工步骤抽象成 ConvertAsset
   normalizer 术语和 manifest。
3. Static USD package scanner：复用并增强现有 USD dependency / material inspection 能力。
4. EBench Isaac 4.1 target profile：定义 required prim paths、allowed dependency roots、
   articulation checks、runtime smoke command。
5. Material closure follow-up：完成 remote MDL local mirror 和 UsdPreviewSurface fallback
   的统一报告。
6. Second/third USD asset replication：用另外两个 rigid/articulated assets 证明不是
   DryingBox-only pipeline。
7. MJCF / AutoBio research lane：只做 source adapter 和 semantic gap report，不承诺一口气
   完成 official reproduction。

## Multi-agent discussion summary

本轮讨论拆成两个只读审阅：

- External ecosystem reviewer：确认已有生态主要覆盖 USD validation、asset profile、
  importer、asset manager、simulator/task execution platform；缺口是 target benchmark
  application contract。
- Repo boundary reviewer：确认文档和未来实现先放 ConvertAsset；EOS 只消费 evidence /
  asset resolution contract；LabUtopia / GenManip 保持 integration evidence 角色。

采纳的设计决策：

- 不新建独立 repo；
- 不把实现放 EOS core；
- 不用 LabUtopia / AutoBio 作为核心抽象名；
- 使用 `source_format`、`source_runtime_lineage`、`target_runtime_profile`、
  `target_benchmark_profile`；
- MVP 先做 USD rigid + articulated -> EBench Isaac Sim 4.1；
- 材质闭环作为独立 policy，URDF importer 的材质缺口由 ConvertAsset no-MDL /
  UsdPreviewSurface / local mirror 路线补齐。

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
