# 螺纹 15 mL 离心管与漏斗 PBD 参数卡

这篇文档记录同事倒液场景拆分后、已经在 Isaac Sim 4.1 重组通过的液体配置，
并区分 exact-source kinematic v1 与默认消费的 dynamic v2。
它只适用于：

- 螺纹版 15 mL 离心管体 `tube15_threaded_liquid_ready`
- 同场景 small-v2 漏斗 `funnel_small_v2_liquid_ready`
- 独立 1948 粒子 overlay `small_v2_liquid_seed_1948`

不要把这套当成 small-v2。`scientific_workbench_small_gpu_pbd_v2` 是另一条已验证配方，
粒子更细、速度上限更高，对应无螺纹单 mesh 离心管和漏斗 pass 包。两套不能互换，
也不能从本文复制数值去 `--liquid-recipe` 重新采样。

## 唯一真源

消费场景必须引用拆出的 overlay USD 和 producer manifest，不要再手写一份粒子配方。

- 源场景：`scenario-forge/external_artifacts/incoming/from_wangshuai/lixinguan_funnel_liquid.usd`
- 源场景 SHA-256：`25270c616797769dd7448a85f648dc86c4c7460ef54b5e12fdc5a459034c1e7f`
- overlay 入口：`outputs/wangshuai_funnel_tube15_exact_asset_set_20260826/packages/small_v2_liquid_seed_1948/asset.usda`
- overlay manifest：同目录 `evidence/manifest.json`
- Scenario Forge 目录副本：`scenario-forge/outputs/scientific_workbench_funnel_tube15_liquid_asset_set_20260826/`
- runtime：`isaac41`

## 两个版本的职责

- `outputs/wangshuai_funnel_tube15_exact_asset_set_20260826/` 是不可变来源夹具。
  它保留同事原 USD 中管体和漏斗的 `kinematicEnabled=true`，用于证明拆分没有改变源行为。
- `outputs/wangshuai_funnel_tube15_dynamic_asset_set_20260827/` 是下游默认版本。
  三件器材根均为 dynamic，入口 identity；碰撞、SDF、视觉和液体 overlay 与 v1 相同，
  只增加版本化的 provisional-geometry 质量、质心和惯量。

动态版的质量不是实测值：管体沿用 `0.015 kg` provisional profile，管盖为
`0.002 kg`，漏斗按闭合网格体积与 `2230 kg/m³` 玻璃密度计算为约
`0.0315034 kg`。更换真实 profile 不应改碰撞。

## 液体 ParticleSystem

源 USD 只作者了下面三个 ParticleSystem 字段；其余 PhysX 粒子属性保持 Isaac 默认。

| 字段 | 数值 | 含义 |
|---|---:|---|
| `maxVelocity` | `0.1` | 粒子最大速度 0.1 m/s；16 秒才 100% 入管，8 秒只有 84.856% |
| `particleContactOffset` | `0.002 m` | 2 mm 接触半径 |
| `restOffset` | `0.002 m` | 与 contact offset 相同，不是 small-v2 的 0.55 mm |

## 液体 ParticleSet

| 字段 | 数值 |
|---|---|
| 粒子数 | `1948` |
| `points` SHA-256 | `e0008cf3681377935bcf56b4f22432003fe4d0f525b71ac66edb6ec7ef13f36b` |
| `velocities` | 全部为 `(0, 0, 0)` |
| `widths` | 全部为 `0.002376 m` |
| 可见性 | `invisible` |
| sampler | 源 Cone 体积采样，overlay 内保留 `physxParticleSampling:volume = true` |

这是冻结的 1948 个点，不是按 spacing 现采的配方。ParticleSet 没有作者 `fluid`、
`selfCollision`、`mass` 或 `spacing`。不要补这些字段来“对齐 small-v2”。

源 USD 没有显式作者 ParticleSystem isosurface 参数、液体材质或材质绑定；本卡只记录
已经验证的物理 overlay，不声明一套源文件中不存在的渲染配方。需要可见液体时必须另行
版本化视觉层，不能把临时显示设置回写成这套 exact-source 配置的一部分。

## 漏斗碰撞（液体可交互几何，不含液体）

根节点 `/FunnelSmallV2LiquidReady`：`RigidBodyAPI`，`kinematicEnabled = true`。
视觉 mesh 同时是碰撞 mesh：

| 字段 | 数值 |
|---|---|
| approximation | `sdf` |
| contact offset | `0.00035 m` |
| rest offset | `0.000175 m` |
| SDF resolution | `256` |
| SDF subgrid resolution | `6` |
| SDF margin / narrow band | `0.00035 m` |
| bits per subgrid pixel | `BitsPerPixel16` |
| remeshing | `false` |

漏斗 mesh 与旧 pass 包相同。上面的 kinematic 描述只对应 exact-source v1；任务集成
默认使用 dynamic v2，不要在 Scenario Forge 把它重新锁成 kinematic。

## 螺纹离心管碰撞（液体可交互几何，不含液体）

exact-source v1 根节点 `/Tube15ThreadedLiquidReady`：`RigidBodyAPI`，
`kinematicEnabled = true`；dynamic v2 的同名入口不作者该锁定，并带 MassAPI。

| prim | approximation | 已作者偏移 |
|---|---|---|
| `/node_/mesh_` 管体 | `sdf` | `restOffset = 0` |
| `/node_/Cone` | `convexHull` | 无额外 offset |

管体没有作者 contact offset / SDF resolution；保持源文件缺省，不要用 small-v2
管包的 `0.00035 / 512` 去覆盖。

源管体 mesh 还带一个指向 `/World/PhysicsMaterial` 的悬空 physics-material 关系，
但源场景并不存在该 prim，因此没有可继承的摩擦/恢复参数。拆分包保留这一 source
signature，不得凭空补一套物理材质。

螺纹封闭管盖是独立动态刚体（`kinematicEnabled = false`），带 SDF 碰撞，默认不参与
倒液 overlay。拧盖成功未验证。

## 集成运行配置

重组 fixture 使用：Z-up、米制、重力 `(0,0,-1)` × `9.81`、GPU broadphase、
GPU dynamics、TGS、`120 Hz`。overlay 自身不含 PhysicsScene，由消费场景提供
**一个** GPU PhysicsScene。

合格窗口是 16 秒：源场景和三次重组均为 `1948/1948` 入管、零漏地。8 秒只有
`1653/1948`，这是 `maxVelocity = 0.1` 的结果，不是失败。

动态 v2 中，管体、盖子和漏斗各三次冷启动均响应重力，并可在自身保持 dynamic 的条件下
通过 fixed-joint 测试载具平移 10 cm。三次静止导流均保持 1948 粒子身份，漏斗到管体接收
超过 95%。但是装液管体抬高 10 cm 的保留率有明显波动，曾低于 90%；因此
`dynamic_loaded_liquid_transport=false`。本卡不声明 robot-policy、装液搬运、拧盖、任务或
benchmark 成功。

## 不要混用

| | 本卡（螺纹管 + 同事倒液 overlay） | small-v2 参数卡 |
|---|---|---|
| 配方 | 冻结 1948 点 overlay | `scientific_workbench_small_gpu_pbd_v2` |
| `maxVelocity` | `0.1` | `0.2` |
| contact / rest | `0.002 / 0.002` | `0.0007 / 0.00055` |
| 粒子宽度 | `0.002376` | `0.001188` |
| 离心管 | 螺纹版 kinematic SDF + Cone convexHull | 单 mesh 隐藏 SDF 代理 |
| 漏斗根 | kinematic rigid body | 仅碰撞、无刚体根 |

相关记录：

- [exact-source 拆分与重组](../records/2026-08-26-wangshuai-funnel-tube15-exact-asset-set.md)
- [small-v2 漏斗/离心管参数卡](funnel-tube15-small-particle-pbd.md)
