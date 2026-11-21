# EBench 齿轮下缘入齿几何

EEOS 的固定动作诊断发现，排除目标与邻齿碰撞后目标下降约 10 mm。为继续区分真实
接触下的落位原因，本次用 Blender 制作目标齿轮下缘退让几何及同流程原尺寸对照。

## 实现

`scripts/build_ebench_gear_leadin.py` 读取原生 `install_gear/scene.usd` 中 `obj_04` 的
视觉和碰撞网格，要求两者拓扑、点坐标一致且无需 UV 重映射。Blender 先在局部 Z =
9 mm 处切分并三角化，再对干预分支施加下缘径向退让；对照采用同一切分但零退让。
局部 Z >= 9 mm、半径 <= 15 mm 的区域和全部 Z 坐标保持不变。
最大退让为 2 mm；局部径向中心使用源网格的 `(20.25 mm, 0)`。

生成 USD 叠加层同时更新视觉和碰撞网格及法线；不改源资产、材质、原物理属性或
邻齿碰撞。保留 `.blend`、中间网格 JSON、日志和来源哈希。
这是依赖外部源资产的原生原型，不是可移植资产包。

## 验证与产物

命令：

```bash
/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-py310/bin/python \
  scripts/build_ebench_gear_leadin.py \
  --source /cpfs/shared/simulation/zhuzihou/dev/GenManip/saved/assets/scene_usds/ebench/teleop_tasks/install_gear/scene.usd \
  --blender /cpfs/shared/simulation/zhuzihou/tools/blender-4.4.3-linux-x64/blender \
  --output outputs/ebench_gear_leadin_20260912_r2
```

- Blender 4.4.3 实际完成两分支生成，两者均为 10,580 个顶点、12,856 个三角面。
- 两个实体均 watertight、绕序一致、体积为正；上部与孔区顶点保持一致。
- 干预改变 3,951 个顶点，最大径向位移约 0.002000002 m。
- 对照体积相对源资产差 `4.5698e-11`，包围盒差为零；这不等价于已证明仿真轨迹相同。
- 原尺寸对照体积 `2.1066671125e-5 m³`，干预体积 `2.0584430565e-5 m³`。
- `tests/test_ebench_gear_leadin.py` 两项测试通过，Ruff 通过。

首版 r1 在“变形后再三角化”时生成不同拓扑，被检查拒绝。失败产物与当时脚本
`producer_failed.py` 保留；r2 改成先共同三角化，再变形，未覆盖历史输出。

## 待完成与交接

资产继承密度，体积变化会影响自动计算的质量和惯性。EEOS 已启动原始目标的运行时
质量读回，后续必须测量并按需要匹配两分支惯性，才能进行几何归因。
还需场景任务编译、最终资产渲染检查和真实接触回放；本记录不报告策略成功。
Scenario Forge 负责接入生成内容与任务语义，EEOS 负责运行和记录结果。

### 运行时参照已取得，r3 已生成

EEOS 的原始齿轮读回完成，质量 `0.02106667123734951 kg`，重心约
`(0.02025, 0, 0.0155813) m`，惯性张量为对角阵。读取来源已通过目标源层哈希绑定。
生产脚本新增可选 `--mass-readback`，要求 `obj_04`、米／千克单位、单位惯性姿态及
正对角惯性。两分支都显式写入同一质量、重心、对角惯性和主轴，保持其他源属性。

在上述命令中增加：

```text
--mass-readback /cpfs/user/zhuzihou/dev/embodied-eval-os/outputs/ebench_evolution/gear_source_mass_20260912_r1/mass_properties.json
--output outputs/ebench_gear_leadin_20260912_r3
```

实际 r3 已生成，网格数量、体积和退让量与 r2 一致；两项测试及 Ruff 通过。
源参照 SHA-256 为 `b89b53c58300708e280c16f3b316c558fa1c0b70a0ed9dcba1ada6f7d87d66c0`。
当前任务集成入口使用 r3；r2 保留为未固定物理属性的几何产物。
新资产中写入参照值不等于运行时匹配已经验证，仍需对两条件分别执行读回。

后续 EEOS 已完成 r3 两条件读回，全部惯性属性与原始参照逐项精确匹配；
实际组合层哈希包含各自生产者层。汇总路径为 EEOS
`outputs/ebench_evolution/gear_leadin_mass_comparison_20260912.json`。
两次重置仍有亚微米位置差，最终轨迹结果待检查。

同会话检查了 Blender CPU 输出的 `control_geometry_inspection.png` 与
`leadin_geometry_inspection.png`：下缘退让可见，没有明显裂面，上部外观未见明显变形。
它们只显示灰色几何，不是源材质或仿真运行证据；图像、脚本和 blend 哈希保存在
`geometry_visual_review.json`。精确保留范围仍以数值检查为准。

### 原尺寸对照没有保持原回放结果

EEOS 的原尺寸对照在 step 561 已触发几何终止判据，故不能将后续改善归功于下缘
退让。为分离重新切分网格与显式惯性属性的影响，另生成
`outputs/ebench_gear_native_mass_20260912_r1/`，其 `build.py` 只在目标刚体上写入
同一质量、重心、对角惯性及主轴，逐项检查视觉与碰撞网格的全部属性保持不变。
生产脚本、源参照、内容层 SHA-256 保存在 manifest。Scenario Forge 已编译对应
配对任务；这一诊断变体的运行时及回放验证尚未完成。

斜面条件随后执行满 900 步回放窗口，未取得几何终止结果，最终持续判据 `[0, 0]`。
本配对不支持入齿斜面的改善；两条件在接近阶段就出现姿态差异，不能将结果只归于
最终入齿接触。EEOS 汇总为 `outputs/ebench_evolution/gear_leadin_pair_result_20260912.json`。

原网格、仅显式惯性写入变体随后通过运行时属性匹配，并在 900 步回放中精确复现
原始对象、机器人状态及目标标志（901 个观测），最终 `[1, 0]`。
该结果不支持仅惯性写入导致原尺寸对照改变结果；网格处理及初始化影响仍待检查。
证据见 EEOS `outputs/ebench_evolution/gear_native_mass_authored_replay_20260912_r1/source_comparison.json`。

### 表面距离的数值尺度检查

在 r3 输出目录新增可复算的 `check_control_surface.py`，双向检查全部顶点及各 4096
个面积采样点。以毫米计算并转回米，最大点到面距离分别为 `1.5124e-9 m` 与
`1.8449e-9 m`；改用 0.1 毫米单位得到一致结果。
原米单位计算曾产生约 0.19 mm 的结果，具有明显尺度依赖，不用于判断实际形变。
旧脚本和结果以 `_meters` 后缀保留。当前报告为 `control_surface_check.json`，
尺度复算为 `control_surface_check_scale10000.json`，均绑定源网格和脚本哈希。
本检查不证明全表面的严格距离界，也不证明 PhysX 烹制碰撞或动态轨迹等价。

额外 Open3D 0.19 自交检查未在斜面上报告自交；对照出现几个随计算尺度变化的
候选。其三角形 Z 区间只共享切分平面，每边仅一个顶点处于该平面，顶点又不同，
因此逐对排除了这些报告。记录为 `self_intersection_check.json` 和
`intersection_candidate_check.json`。这不是完整几何正确性或烹制 SDF 等价性证明。
