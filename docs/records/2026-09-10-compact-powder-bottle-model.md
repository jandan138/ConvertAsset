# Task09 r3：紧凑薄壁粉末瓶 Blender 源模型 model_r1

日期：2026-09-10。状态：模型、静态几何和 CPU 预览完成；等待主会话集成 USD、真实颗粒和 Isaac 验证。

后续更新：本记录末尾追加 **model_r2 collision LOD**，当前推荐几何入口为 `model_r2/geometry.json`。
以下原有 model_r1 记录及哈希作为历史证据保留；model_r1 产物所有字节未修改。

## 授权范围与调查

本次实现者只写以下三个源文件及指定产物目录，不提交，不覆盖其他会话的修改：

- `scripts/model_compact_powder_bottle.py`
- `tests/test_compact_powder_bottle.py`
- 本记录 `docs/records/2026-09-10-compact-powder-bottle-model.md`
- `/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910/model_r1/`

开始时已读 `AGENTS.md`、`CLAUDE.md`、`.codex/file-ownership.md`、
`.codex/agents/feature-implementer.md`、对应 `.claude/agents/feature-implementer.md`
和角色 memory；参考 `scripts/model_task09_weighing_boat.py` 的 Blender/JSON 分工及现有粉末瓶测试风格。
工作树已有其他会话的论文、task09 r2、滴定和称量舟改动，保留原状。
用户精确 scope 优先于仓库默认的索引、memory 更新及文档提交要求，索引集成由主会话决定。

ConvertAsset 调查基线 HEAD：`3240ca3e4a445b2c241629a6dc93345b98951048`。
Scenario Forge 规范基线 HEAD：`90bfc13d578769b1061d3ba7984735d872814593`；阅读了
`docs/standards/README.md`、`asset-intake.md`、`validation-and-delivery.md`、`maintenance.md`。
适用规则为 ASSET-001/003、VAL-001/002/003/004/005/007：生产者提供几何，静态/视觉证据不扩展成颗粒运行时资格。
**规范无需变更**：本次是任务专属瓶体参数及造型实现，没有新的通用契约或运行时结论；本记录同步参数、操作和证据。

## 设计与范围审核

用户选定“紧凑瓶 + 更深真实粉床”，针对 r2 的过厚瓶口和薄粉床：

- 白色圆角方身，外轮廓 superellipse `p=5`；66–90 mm 高度内平滑收肩，过渡到圆形颈口。
- 内外肩部同源变化，直身轴向壁厚 1.8 mm，颈部径向壁厚 2.2 mm。
- 喉口内径 48 mm，圆润口沿最大外径 54 mm，最大径向厚度 3 mm。
  顶冠在 z=100 mm 处向内外圆润收拢，顶冠 ID/OD 为 49.8/51.4 mm，冠部径向宽度 0.8 mm。
  48/54 mm 分别指最小通孔和口沿最大外径，不是要求顶冠同一切片仍为 48/54 mm。
- 固定假底仅 z=57–59 mm 的 2 mm 板，下方保留 z=2–57 mm 空腔。
  计划粉床 z=59–70 mm，深 11 mm，约 30 mm 瓶口上部操作空间。模型内未生成颗粒或假粉末面。
- 视觉按 128 个角向点生成；碰撞按 32 个角向分段 × 15 个高度层生成局部闭合凸块。
  每个壁块仅 8 点；底板和假底各为 64 点的闭合凸片。
  假底与内壁半径重叠 0.15 mm，保证静态几何接缝重合；不宣称已验证动态防漏。

三维度审核：

- 架构：新增任务专用轮廓生成脚本，不修改通用 USD/MDL/mesh 转换层；`build_geometry()` 仅标准库，`bpy/bmesh` 懒加载。
- 完整性：内外壁、底面、唇部与假底均提供闭合、朝外、正体积几何；给出 SI 单位、内腔轮廓、质量及惯量。
  普通 Python 测试与 Blender 生成相互独立，且重新打开保存文件验证 JSON 一致性。
- 风险：32 分段凸碰撞相对光滑内形产生内缩，显式给出初始化余量；482 个凸块的运行时成本、cooking、contact offset 和粒子防漏由主会话联合测试。

## JSON 协作接口

入口 `geometry.json`，schema 标识 `compact-powder-bottle-geometry-v1`。

| 字段/几何 | 值 |
|---|---|
| `visual_meshes` | 2 项：`BottleShell`（`material='bottle'`）、`FalseBottom`（`material='insert'`） |
| 视觉网格内容 | `name`, `points: [[x,y,z],…]`, `faces: [[index,…],…]`, `material` |
| `colliders` | 482 项：480 个 `Wall_LL_SS` + `Base` + `Insert`，各具 `name/points/faces` |
| `inner_profile` | 升序 `list{z,radius,exponent}`，同尺寸 x/y superellipse |
| `outer_profile` | 额外输出同样格式的外形轮廓，供诊断 |
| 坐标 | `meters_per_unit=1`、`up_axis='Z'`、`root_scale=[1,1,1]`，底部 z=0 |
| `metadata.height_m` | `0.1` |
| `metadata.outer_dimensions_m` | `[0.06,0.06,0.1]` |
| `metadata.mouth_inner_diameter_m` | `0.048` |
| `metadata.mouth_outer_diameter_m` | `0.054` |
| `metadata.insert_top_m` / `insert_thickness_m` | `0.059` / `0.002` |
| `metadata.suggested_powder_surface_m` / `suggested_powder_depth_m` | `0.070` / `0.011` |
| `metadata.collider_segments` / `collider_wall_layers` | `32` / `15` |
| `metadata.recommended_clearance_m` | `0.00075` |

### 颗粒初始化注意点

`inner_profile` 是几何内腔，不代表所有高度均允许放颗粒；本任务粉床从假底顶面 z=0.059 m 起。
在相邻 z 样本间线性插值 `radius` 和 `exponent`。以角度 θ 的极径形式计算边界：

```text
R(theta,z) = radius(z) / (abs(cos(theta))^p + abs(sin(theta))^p)^(1/p)
```

从该极径减去 0.75 mm 作为分段几何余量；颗粒半径和 contact margin 另计。
这是点初始化余量，不是接触偏移，也不是任意粒径球体的碰撞证书；尤其在倾斜肩部，应再对实际凸片做球体间隙检查。
独立 Qhull 半空间扫描得到最大采样径向内缩 `0.000542788918362 m`，低于声明余量；采样不等于连续域严格上界证明。

每个 collider 单独应用 convexHull；**不能合并 482 个块后对整瓶求 convexHull**。
所有 collider 都是同一个瓶根刚体的子形状，源 Blender/JSON 未添加独立 Rigidbody。
主会话在瓶根添加唯一 RB 和下述质量属性。

### 质量与惯量

HDPE 密度 950 kg/m³。使用有向四面体积分计算闭合视觉壳体及内腔内的假底。
插入板与壳体的 0.15 mm 重叠接缝不重复计质量：计算时只加半径 28.2 mm 的有效内板。
该高度段是直壁，所以这是当前离散网格实体并集的精确体积计算（除浮点误差）。

```json
{
  "volume_m3": 0.000051071606056414905,
  "mass_kg": 0.04851802575359416,
  "center_of_mass_m": [1.0869164276686112e-17, -3.714645609830453e-18, 0.04480371688340645],
  "diagonal_inertia_kg_m2": [0.00006364368244619421, 0.00006364368244619424, 0.00004130195547250814],
  "principal_axes_wxyz": [1, 0, 0, 0]
}
```

约 48.52 g；惯量为质心坐标下的主惯量，root XYZ 因四重对称就是主轴，无需排序重排。
不要按相互重叠的 collider 体积简单相加求质量。

## Blender 编辑与预览

`bottle.blend` 使用 Blender 4.4.3，scene `scale_length=1`，所有资产几何及瓶根 scale 均为 1。

- `ASSET_Visuals`：瓶根 `Bottle`、闭合薄壁 `BottleShell` 和薄板 `FalseBottom`。
- `ASSET_ConvexColliders`：默认隐藏显示/渲染，父级仍是 `Bottle`；482 个可单独编辑的凸片。
- `PREVIEW_Studio_not_asset`：摄影地面、灯光、相机。
- `PREVIEW_Section_not_asset`：源网格真实二分剖切副本，默认隐藏；切面诊断色为陶土色。

主资产材质为温白 HDPE 风格：瓶身 Principled Base Color 线性 RGBA `(0.82,0.805,0.75,1)`，
roughness 0.32，IOR 1.46；假底 `(0.79,0.775,0.72,1)`，roughness 0.44。
无纹理或外部文件依赖。剖切面诊断着色不在导出的 `visual_meshes` 中。
JSON 是几何 handoff；整体导出 Blender 摄影场景会夹带诊断物体，集成应使用资产集合/JSON。

最终三张 900×1000 PNG 均为 Cycles CPU、8 线程、40 samples、去噪静态预览：

| 文件 | 实现者目视结论 | 证据与限制 |
|---|---|---|
| `preview_overall.png` | PASS | 完整温白圆角方身、平滑肩部及轻薄口沿；普通视角看不到全部内腔 |
| `preview_mouth.png` | PASS | 近看圆形通口和圆润薄唇，没有窄孔厚圈；下部瓶身为近景有意裁切 |
| `preview_section.png` | PASS | 实际半剖，薄壳/底板/高位薄假底和下方空腔可辨；陶土色只标记截面 |

首轮照明使白色高光过强，降低灯光功率后重新渲染，最终文件再次逐张查看。
按 render-visual-reviewer 流程进行本地目视，**并非独立 reviewer 审查**；只支撑静态造型与剖面可读性，不支撑物理表现。

## 可重复命令与验证结果

在 `/cpfs/user/zhuzihou/dev/ConvertAsset` 执行：

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python -m pytest \
  -p no:cacheprovider tests/test_compact_powder_bottle.py -q -rP

PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HIP_VISIBLE_DEVICES='' \
  /cpfs/shared/simulation/zhuzihou/tools/blender-4.4.3-linux-x64/blender \
  -b -t 8 --python-exit-code 1 --python scripts/model_compact_powder_bottle.py -- \
  --out outputs/task09_powder_bottle_r3_20260910/model_r1 --render --samples 40
```

验证过程：

1. 先写几何行为测试，脚本尚不存在时运行：**1 failed, 7 errors**，原因是缺少实现文件，明确记录红阶段。
2. 实现后最初 8 项通过；补充独立径向内缩量化测试，最终 **9 passed in 2.38s**。
3. 覆盖普通 Python `-I -S -B` 无第三方依赖导入/构造、SI 尺寸、48/54 mm 唇径、假底位置/厚度、
   全部视觉及碰撞片闭合/反向边配对/正体积、独立 Qhull 凸性、开口与下部空腔不封堵、粉床和 clearance、
   插入板接缝重叠、质量惯量正值及 JSON 序列化。
4. 内缩扫描：每个壁块 32 条角向采样 × 17 个高度，共 **261,120 条射线**；最坏采样值约 0.543 mm。
5. Blender CPU 建模/渲染退出码 0，全部 484 个资产网格通过 `bmesh` manifold 与有向正体积检查，真实剖面亦闭合且正体积。
6. 新 Blender 进程重新打开最终 `bottle.blend`，逐资产比对 JSON 的点/面数量、面索引、顶点坐标、父级、单位 scale 与无 RB，
   输出 `BLEND_REOPEN_PARITY_PASS 484 max_vertex_error_m 3.5762786898541066e-09`。
7. 最终三张图实际查看通过；未启动 Isaac，渲染引擎明确 `CPU`，CUDA/HIP 设备环境变量为空。

ConvertAsset 根目录没有 `Makefile` / `make check` 目标；未运行其他项目的全量检查，采用本任务普通 Python 测试、Blender 重开比对和实际渲染验证。
运行测试禁用 bytecode 与 pytest cache，生成数据均在授权 `model_r1/`。

## 最终文件身份

完整产物目录：`/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910/model_r1/`。
附 `blender_validation.json` 和 `validation_summary.json` 供机器/主会话定位验证范围。

| 文件 | SHA-256 |
|---|---|
| `scripts/model_compact_powder_bottle.py` | `3ee9c11ca909d7d9dfd296c3f6b1af2f685cd3ff8de8174719aab9ca7ad396a5` |
| `tests/test_compact_powder_bottle.py` | `b69965a395f6bf043349f378b67e4220fd63109495517de864b74c890558d92c` |
| `geometry.json` | `19286782a6a548806648b6f67dfacc4d967318857aa03f791c7c937411cb867b` |
| `bottle.blend` | `e54035360a14d606915401ead2cf3a137f5f1c1a61940c3e4cbb2ff10bcb847b` |
| `preview_overall.png` | `aa1b2408249c1e9fb632cde4e849aebfd2b5e25e09e6682f86eef27cde0d9467` |
| `preview_mouth.png` | `8ff6dd90fd537b823ead740f9e1a465d6251c6d88dac4ad659843ba7d8fb365b` |
| `preview_section.png` | `e50e56606b65f89acb7565501843c0deff60e7455718dc249e43f52ce33a6b57` |

## 主会话交接与剩余限制

- 集成上述 JSON，按材料键赋材质；保留每个独立凸片，在瓶根应用唯一 RB 与质量/惯量。
- 依据内轮廓和假底高度布置真实 10–12 mm 粉床，联合粒径、contact offset 与球-凸片间隙复核。
- 验证 USD 法向/尺度/碰撞 cooking、Isaac 颗粒保持与操作轨迹、运行性能及视频。
- 482 个局部凸块尚无 Isaac 性能、抗漏或动态资格；没有将静态闭合性当作运行时通过。
- 视觉壳体与假底是两个分别闭合且微量重叠的固体；若下游另走单一 SDF，需处理实体并集语义，不能直接把整个容器凸包化。
- 预览未展示实际颗粒、抓取或舀取，未包含螺纹/瓶盖配合的制造资格。
- 本记录可由主会话集成进文档导航；本次按授权未 commit。

## model_r2 collision LOD（2026-09-10）

### 本轮授权与不变量

用户要求沿用原三个源文件的精确 write scope，新增产物仅放到：

`/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910/model_r2/`

本轮仅精简碰撞高度层。`visual_meshes`、`inner_profile`、`outer_profile`、底板/假底凸片、
`volume_m3`、`mass_kg`、质心、主惯量与主轴保持 r1 精确值；使用冻结的规范化 JSON SHA-256 回归测试：
`959d44d812ef7ee9df976bd22140ba8d0f72436fa0a30afdb68d53828dc688f5`。
假底仍为 z=57–59 mm、厚 2 mm；建议粉床仍为 z=59–70 mm。
本轮无 USD、Isaac、GPU 或提交操作。

架构审核：LOD 仅抽取已有轮廓关键高度，视觉与质量积分路径不变；没有引入通用转换层。
完整性审核：射线测试必须按 collider **实际高度范围**插值原视觉内轮廓，不能用粗化碰撞轮廓替代真值。
风险审核：减少薄小凸片有利于后续 cooking，但静态几何验证不等同于 PhysX cooking/性能通过。
规范无需变更：仍遵循 ASSET-003 与 VAL-001/002/003/004 的资格、证据范围，未新增运行时结论。

### 高度选择与依据

用户建议的首轮 9 个高度：

```text
0.002, 0.004, 0.066, 0.074, 0.082, 0.090, 0.096, 0.0985, 0.100
```

确实生成 258 片，但 66–74 mm 肩部层的最大采样内缩 **1.0254608 mm**，发生在 z=70 mm，
会侵占声明的 0.75 mm 初始化余量；该候选未作为交付输出。

| 只读候选探测 | 最大采样内缩 | 决定 |
|---|---:|---|
| 原建议 9 高度 | 1.025461 mm | 不满足 clearance |
| 增加 `.078` | 1.025461 mm | 未解决 66–74 mm 层 |
| 增加 `.070` | 0.688760 mm | 肩部通过，但 290 片 |
| 增加 `.070,.078` | 0.543325 mm | 322 片，精度提升非必要 |
| 258 片、肩部中间高度换为 `.070,.078` | 0.888323 mm | 仍超余量 |
| 258 片、肩部中间高度换为 `.070,.082` | 1.148170 mm | 仍超余量 |
| 258 片、肩部中间高度换为 `.070,.086` | 1.281178 mm | 仍超余量 |

最终在肩部增加 `.070`，同时将**等内径**的 `.090–.096–.0985` 颈部合并，省去 `.096`。
最终高度为：

```text
0.002, 0.004, 0.066, 0.070, 0.074, 0.082, 0.090, 0.0985, 0.100
```

共 **32 × 8 + 2 = 258 个闭合凸片**：256 壁块、1 底板、1 假底，较 r1 的 482 片减少 224 片（46.47%）。
所有壁块仍只有 8 个角点，底板/假底各 64 点，保持独立凸性和闭合朝外面序。
最小碰撞高度层为 98.5–100 mm 的 **1.5 mm**；移除了原 0.4–0.6 mm 量级的口沿细层。

颈部 90–98.5 mm 的内半径恒为 24 mm，合并不改变内侧通孔。
外侧近似将原 96 mm 前等径段和末端轻微唇凸合并为直线斜率；相对视觉外轮廓的
径向外扩最大采样值 **0.5567468 mm**，轴向方向的线性包络上界为 **0.5647059 mm**（z=96 mm）。
该差异已写入 `metadata.collider_lod_note`，只描述局部碰撞近似，不能读作视觉颈壁增厚。

### 内缩审计结果

最终每段 32 个角向方向，65 个等距高度并补入所有被省略的原内外轮廓高度，合计 **537,600 条射线**。
采用 SciPy/Qhull 独立半空间求射线进入凸块位置，参照原 `inner_profile` 的线性 radius/exponent 插值。

| 碰撞层高度（mm） | 最大采样径向内缩（mm） |
|---|---:|
| 2–4 | 0.531298 |
| 4–66 | 0.531298 |
| 66–70 | 0.542789 |
| 70–74 | 0.543325 |
| 74–82 | **0.688760** |
| 82–90 | 0.225699 |
| 90–98.5 | 0.115454 |
| 98.5–100 | 0.119784 |

全局最大值 `0.0006887598741318439 m`，位置 `Wall_04_03`、z=`0.078125 m`。
建议几何 clearance 仍为 **0.00075 m**，颗粒半径及 contact margin 另计。
这些是密集采样证据，不宣称连续域严格最大值或任意球体/运行时接触资格。

### 测试、Blender 重开与预览复用

先新增 LOD 数量/最小层高及 r1 不变量回归：旧实现运行结果 **1 failed, 10 passed**，失败明确为 `482 > 258`。
初始 258 片候选随后因 clearance 失败；按上述依据调整后，最终测试：

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python -m pytest \
  -p no:cacheprovider tests/test_compact_powder_bottle.py -q -rP
```

结果：**11 passed in 2.08s**，包含凸性、朝外闭合/正体积、口部不封闭、下部空腔、薄假底及重叠、
新 LOD 预算/层高、冻结视觉/质量数据、clearance 点检查和独立射线内缩/颈外扩检查。

新模型仅做 CPU 建模/保存，不重新渲染：

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HIP_VISIBLE_DEVICES='' \
  /cpfs/shared/simulation/zhuzihou/tools/blender-4.4.3-linux-x64/blender \
  -b -t 8 --python-exit-code 1 --python scripts/model_compact_powder_bottle.py -- \
  --out outputs/task09_powder_bottle_r3_20260910/model_r2
```

退出码 0，`bottle.blend`、`geometry.json` 与本次建模 `blender_validation.json` 已生成。
独立 Blender 新进程重开输出 **260 个资产网格**（2 visual + 258 collider）验证：

- 点/面数、面索引与 JSON 精确一致；最大顶点坐标误差 `3.5762786898541066e-09 m`。
- 所有网格 bmesh manifold、有向正体积；scale 1、米制、瓶根父级；瓶根/子网格均未添加 RB。
- 输出 `R2_BLEND_REOPEN_PARITY_MANIFOLD_POSITIVE_PASS 260`，退出码 0。

另一次 Blender 进程分别重开 r2/r1，比对瓶壳、假底、剖切副本和摄影地面的顶点/面/平滑标志、
材质/节点参数、灯光、相机、World、色彩管理、分辨率、samples/去噪和集合可见性，
输出 `R1_R2_RENDER_RELEVANT_GEOMETRY_MATERIAL_LIGHT_CAMERA_PARITY_PASS`，退出码 0。
首次临时比较命令有 shell 引号丢失导致的 `NameError`；修正后上述两项检查均重新成功执行，未保存或修改 r1。

因此 `preview_overall.png`、`preview_mouth.png`、`preview_section.png` 从 r1 **逐字节复制**到 r2，
三个 SHA-256 均与前文 r1 一致。复用范围仅为不变的视觉几何/材质/摄影和真实剖面，**不提供新碰撞 LOD 的运行时或碰撞覆盖可视证据**。
复用前轮实现者目视结论，不声称新渲染或独立审查；本轮 `blender_validation.json.previews=[]` 正确表示未新渲染，
复用来源及范围在 `model_r2/validation_summary.json` 中单独声明。

### r2 文件与保留证据

当前模型：`/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910/model_r2/bottle.blend`。
当前接口：同目录 `geometry.json`；同目录另有三张复用 PNG、`blender_validation.json`、`validation_summary.json`。

| r2 文件 | SHA-256 |
|---|---|
| `scripts/model_compact_powder_bottle.py` | `ffcd794d4ef7b05682d7148736649d328668fa29b60556f30e1d52fdfa75e118` |
| `tests/test_compact_powder_bottle.py` | `f5f5ccbba21dc9de09c4a35d33cf52d1098b0ca4f9dbb8450a6584e22acbba06` |
| `model_r2/geometry.json` | `1faef532b41c1eddbe629ced7ca52109c5211b1d7996aaba507d3be9fb8a70a9` |
| `model_r2/bottle.blend` | `ef3f1bce668874d85ab9f4460f501ad28a5294fbaa139fbad5a8c702d6fbeeaf` |
| `model_r2/blender_validation.json` | `8cc9370499b3b80268a162351d0bfaee834be9e9313f8fe55df2fe9aa982b7bb` |

开始与结束均检查 model_r1 全部 7 个文件 SHA-256；原 blend、geometry、三个 PNG 和两份 JSON 所有字节保持一致。
完整 r1 字节基线保存在 r2 `validation_summary.json`。r1 的旧记录仍对应当时源码，不追写成新 LOD 结果。

集成约束仍为：各 collider **分别** convexHull，唯一 RB/质量属性由主会话加到瓶根；
保持 `inner_profile` 与假底高度初始化真实粉床；0.75 mm 为几何余量而非 contact offset。
本轮没有 PhysX cooking、Isaac 颗粒防漏或性能结果，不能因为片数减少就宣称这些资格已通过。

后续集成（2026-09-11）：见 [Task09 r3 生产者场景集成与运行证据](2026-09-11-compact-powder-scene-r3.md)。
该记录新增 model_r2 接入原场景后的静态、沉降、舀取及校准结果；本页历史声明、哈希与对应产物字节保持原样。
