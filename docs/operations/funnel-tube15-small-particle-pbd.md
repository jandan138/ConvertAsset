# 漏斗与 15 mL 离心管 small-v2 PBD 参数卡

这篇文档记录当前已经在 Isaac Sim 4.1 实测通过的“7 mm 漏斗导流到
15 mL 离心管”液体配置。它是面向工程消费的参数卡；程序必须读取机器
真源，不要从本文复制数值重新造一份配置。

## 唯一真源

- recipe ID：`scientific_workbench_small_gpu_pbd_v2`
- 文件：`profiles/gpu_pbd/scientific_workbench_small_gpu_pbd_v2.json`
- canonical JSON SHA-256：
  `0532f5f3ced74a1b7d6a8a20abfb9d457788a312285c71e5b0de4108754188fa`
- runtime：`isaac41`

这里的 SHA 是 `liquid_recipe_sha256()` 对排序、紧凑 JSON 的语义哈希，
不是文件排版字节哈希。package、fixture 和资格报告都应绑定这个语义哈希。

同事螺纹离心管倒液场景是另一套冻结 overlay，不要用本卡替换：
[螺纹管/漏斗 exact-source PBD 参数卡](wangshuai-threaded-tube-funnel-pbd.md)。

## 液体粒子参数

### ParticleSystem

| 字段 | 数值 | 含义 |
|---|---:|---|
| `max_velocity_m_s` | `0.2` | 粒子最大速度上限；不是“永不漏液”保证 |
| `particle_contact_offset_m` | `0.0007` | 0.7 mm 粒子接触范围 |
| `effective_rest_offset_m` | `0.00055` | 0.55 mm 稳态间距尺度，必须小于 contact offset |
| `grid_filtering_passes` | `1` | isosurface 网格过滤次数 |
| `grid_smoothing_radius_m` | `0.005` | isosurface 网格平滑半径 |
| `mesh_smoothing_passes` | `1` | isosurface mesh 平滑次数 |
| `surface_distance_m` | `0.008` | isosurface 表面重建距离 |

### ParticleSet

| 字段 | 数值 |
|---|---:|
| `spacing_m` | `0.001` |
| `width_m` | `0.001188` |
| `mass_kg` | `2.282672253187432e-06` |
| `maximum_count` | `50000` |
| `fluid` | `true` |
| `self_collision` | `true` |

多坨初始液体共享一个 ParticleSystem，但每一坨必须拥有独立 ParticleSet；
不得把不同容器的粒子合并成一个无法追踪身份的 set。

### 包内液体材质

| 字段 | 数值 |
|---|---|
| shader | `UsdPreviewSurface` |
| diffuse color | `(0.32, 0.72, 0.95)` |
| emissive color | `(0.02, 0.12, 0.28)` |
| IOR | `1.333` |
| opacity | `0.34` |
| roughness | `0.02` |

Isaac 4.1 的生成 isosurface 从 **ParticleSystem** 读取渲染材质。只把
材质绑定到 ParticleSet 会让等值面退回白色默认材质。生产场景应同时保证
ParticleSystem 持有正确 render-material binding。录像中的高对比蓝色仅是
anonymous session layer 证据覆盖，不属于这份 canonical recipe。

## 容器碰撞参数

下面是容器 SDF 参数，不是液体 ParticleSystem 参数。两组数值不能互相
替代，也不能为了“看起来稳定”一起盲调。

| 参数 | 漏斗（conduit） | 15 mL 管（reservoir） |
|---|---:|---:|
| contact offset | `0.00035 m` | `0.00035 m` |
| rest offset | `0.000175 m` | `0.000175 m` |
| SDF resolution | `256` | `512` |
| SDF subgrid resolution | `6` | `6` |
| SDF margin | `0.00035 m` | `0.00035 m` |
| SDF narrow band | `0.00035 m` | `0.00035 m` |
| bits per subgrid pixel | `BitsPerPixel16` | `BitsPerPixel16` |
| remeshing | `false` | `false` |

漏斗直接用一个闭合、空心的 visual mesh 生成 SDF，喉管内径为 `7 mm`。
Task 02 的约 18 mm 大粒子必然无法通过，必须选 small-v2。

15 mL 管不使用底部 Cube，也不让 visual mesh 同时参与碰撞。唯一活动碰撞
体是一个与源视觉拓扑连通的隐藏 SDF mesh：

`/FluidInteractionAsset/__aan_pbd_collision_proxy/PBD_SingleMesh_ThickBottom`

这个碰撞副本采用加厚底部和向内收 1 mm 的内壁。其轴对称留存轮廓为：

| z (m) | 内半径 (m) |
|---:|---:|
| `0.015` | `0.0001` |
| `0.016` | `0.0001` |
| `0.020` | `0.0022852` |
| `0.026` | `0.005112` |
| `0.031` | `0.00664` |
| `0.0945` | `0.00664` |
| `0.098` | `0.005555` |
| `0.101` | `0.005555` |

visual tube 保持原形且不参与 PhysX 碰撞；不能再额外叠 Cube、convex 或第二
个活动 SDF。漏斗插入离心管的已验证深度是 `0.015 m`。

## 集成场景运行配置

最终漏斗→离心管 fixture 使用：Z-up、米制、GPU broadphase、GPU dynamics、
TGS、`120 Hz` physics，以及 `gpuMaxParticleContacts = 1048576`。这套运行
配置与 small-v2 recipe 一起构成已验证条件，不能只复制粒子数值而忽略
PhysicsScene。

当前合格产物：

- 漏斗：`outputs/funnel_15ml_small_particle_small_v2_glass_v1_20260825/`
- 离心管：`outputs/tube15_single_mesh_final_small_v2_20260825/package/`
- 组合：`outputs/funnel_tube15_gravity_final_small_v2_r2_20260825/`

选择配方时使用现有 `--liquid-recipe` 接口传入机器真源；不要在 Scenario
Forge、任务 USD 或消费者 adapter 中重新写一份参数。

## 已验证结果与边界

- 漏斗单体三次冷启动：合法出口率 `1.0`，结构漏液 `0`。
- 离心管三次冷启动：静置留存 `0.99237`、运动留存 `0.96004`、倾倒流出
  `0.98801`，结构漏液 `0`。
- 最新漏斗→离心管实拍：合法出口率 `1.0`、离心管接收率
  `0.9921855921855922`、结构漏液 `0`。

这些结果只覆盖 Isaac 4.1、指定几何、small-v2 和已记录轨迹。不声明
robot-policy、benchmark、任意漏斗/容器泛化、真实流体标定或高速操作成功。

## 不要复用的旧配置

- `colleague_small_gpu_pbd_v1` 的粒子间距和视觉宽度相同，但
  `effective_rest_offset_m = 0.005`；实测 9750 个粒子中 `0` 个通过 7 mm
  喉管。
- Task 02 大粒子配方的有效直径约 18 mm，几何上无法进入 7 mm 喉管。
- 降低 `max_velocity_m_s` 不能修复有缝容器、错误SDF或重复碰撞体。

相关记录：

- [small-v2 配方与漏斗资格](../records/2026-08-25-small-particle-conduit-recipe-and-funnel.md)
- [Isaac 实拍证据](../records/2026-08-25-funnel-tube15-live-isaac-video.md)
- [Simple-SDF multi-liquid CLI](simple-sdf-multi-liquid.md)
