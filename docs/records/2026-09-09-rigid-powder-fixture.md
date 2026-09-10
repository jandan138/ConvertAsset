# 2026-09-09 刚体粉末 producer fixture 与天平联合夹具

## 背景与本次完成范围

本次工作以 `labmius` 来件为工程起点，在 ConvertAsset 制作可供 Scenario Forge（SF）消费的独立刚体粉末、开口工具和天平联合夹具。目标是规定工具轨迹下的物理转移与受力称量；精度按实测报告说明。

当前选定 producer 输出为 `outputs/rigid_powder_r1_20260909/balance_fixture_r6/`：4096 粒、1 mm 等体积球直径的 ico、1500 kg/m³、GPU PhysX/TGS、480 Hz、粉粒/舟/articulation 64 次位置迭代与 4 次速度迭代；10 g 动态舟、运动学诊断勺、原 force r1 自由基座天平。SF 提供新的秤盘接触力 controller，producer 将其嵌入顶层场景。

本记录核对完成的 producer 职责及三份消费者数值报告。消费者视频、独立视觉审核、多 seed 汇总和最终 ZIP 身份仍由其收尾记录确认，不在这里追认完成。`scene.json` 的 `validation` 仍为构建时的 `candidate; integrated runtime pending`；本记录不改写产物或将它冒称为已正式晋级的 manifest。

文档核对日期为 2026-09-10；工作与证据批次为 2026-09-09。本文中的相对代码及产物路径以 ConvertAsset 仓库根为基准；SF 路径另行标明。

## 来件、来源身份与调研

原始输入目录：

`/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/from_zzh/labmius/`

包含 `Labimus_Rigid_Powder_Reproduction.zip` 和 `Labimus_Rigid_Powder_Reproduction_Guide.md`。ZIP 已解压到 `outputs/rigid_powder_r1_20260909/source/`；构建输入根是其下的 `Labimus_Rigid_Powder_Reproduction/`。原 ZIP 和解压来源文件保持不可变，适配另写 producer 脚本和输出。本次只读比对 ZIP 内全部 **13 个文件**与解压文件，字节一致；目录内额外的 `__pycache__/` 不是 ZIP 来源成员，不纳入原始来源身份。

| 来源 | SHA256 |
|---|---|
| 原始 ZIP | `f0207b40e95e69fa50aff51f82bed430e6b7cf6f1436ad69be1c12e7da6910fe` |
| 来源 `build_scene.py` | `1d58d2ed5969359f5e78a16de21467fc25787ea3aa7f0896749aafae7d1b8328` |
| 来源 `config.json` | `4b9d7a9fc0bfe899a6ad4a6bffaed9235ac09a637ec2b2e4a3f0aa6d94fb2bdd` |
| 原 force r1 `asset.usda` | `56ef7fbe5d9313c3f33a9bf9777aab13ba42e3d47589f2c7e90ca486d8f93a0b` |

天平输入为 `outputs/balance_force_r1_20260909/packages/analytical_balance_force_r1/`，来历与原资格见[天平 producer r1 记录](2026-09-09-balance-force-r1.md)。其既有 Isaac 4.1/4.5 规则载荷资格不自动覆盖毫米级粉粒接触机身的联合场景。

调查依据包括来件 `README_复现说明.md`、`provenance.json`、`config.json`、`build_scene.py`、`run_isaac.py`、`validate_usd.py`、`validation.json`，本次五个代码文件、r6 元数据，以及下述 SF 实现和原始报告。

- [Labimus 论文 §3.1](https://arxiv.org/html/2606.31037v1#S3.SS1)支持“小刚体与 PhysX 接触”的路线。来件调研未找到可恢复作者配置的完整参数表；不能由论文的累计质量描述断言作者使用了承重关节反力。
- [官方项目页](https://labimus.github.io/)与[task06 视频](https://labimus.github.io/videos/task06_scoopweigh.mp4)作为动作和外观参考。来源记录给出 960×540、30 fps、7 s；参考帧属于官方视频，不是本 fixture 的运行结果。本次文档编写没有重新执行视觉审核。
- 来件两组 USD 都是 8192 粒、0.6 mm 等体积直径的 sphere/ico 工程初值，只有静态检查。作者数值参数、实物粉末标定、官方目标 0.850 ± 0.001 g 的达成均未由本次来源证明。
- 开口容器使用底板、侧壁组成的复合凸块，避免整个容器单凸包封口。抬高柄勺是诊断工具，不是从视频恢复的原药勺或已获机器人抓持资格的资产。

## 诊断与设计决策

### USD 接口兼容与运行记录

`baseline_probe.log` 保留来件 `TokenListOp.GetAppliedItems` 的 `AttributeError`；`sphere_probe_r1/report.json` 保留 `PrimDefinition.GetAttributeDefinition` 不存在的异常。producer 独立 probe 改用 `prim.GetAppliedSchemas()` 和 `GetSchemaAttributeSpec()`，核对 PhysX schema 属性及类型，未修改来源脚本。

来件关闭应用的路径可能在没有报告时结束，不能仅凭退出码判定成功。新 probe 对进入其 `try` 区间后的异常保存 traceback，在 `finally` 中先写 `report.json` 再关闭应用；应用构造本身在该区间之前，因此不能声称覆盖启动失败的所有异常。

数千刚体逐物理步写回 USD 造成明显开销。probe 在 reset 后关闭 `/physics/updateToUsd` 与 `/physics/updateVelocitiesToUsd`，从 tensor/刚体 view 读取实际位姿、速度、质量和惯量，以 `set_kinematic_targets` 驱动药勺。`World` 初始化后显式恢复 GPU dynamics 与 GPU broadphase。关闭写回后，静态 USD xform 不能用作 live 物理观察。

### 单位 ico cooking 与跨尺度接触

producer 对 ico 先把 mesh 点除以等体积半径，在单位尺寸上保留形状，再在 collider 加半径 scale；相对直接使用微小坐标 cooking 的版本进行对照。物理质量仍按 `m = ρ × 4πr³/3`，ico 惯量沿用封闭多面体体积积分，没有按称重结果放大质量或惯量。`ico_probe_r3/report.json` 读得单粒惯量对角约 `7.94087154e-14 kg·m²`。这是该对照与后续联合配置的证据，不足以确定某一个 PhysX cooking 内部阈值就是根因。

粒子接触与宏观天平支脚不能共用一个微尺度摩擦激活范围：30 μm 的 `frictionOffsetThreshold` 会抑制较大接触间距处的支脚摩擦，引发漂移。联合夹具采用 **5 mm 摩擦激活阈值**，颗粒和工具保留 30 μm contact offset；地面另用 5 mm contact offset 和 40 mm 厚度。场景及粉粒启用 CCD，以处理从抬高料盘落下的较快颗粒。

24 次位置迭代在联合称量中仍有明显偏差，最终粉粒、舟与天平 articulation 设为 64/4、480 Hz，无 stabilization、保持相关载荷 awake。药勺仍是诊断运动学体，继承基础夹具的 24/4；“64/4”不表示所有 prim 均被改为同一迭代数。具体数值属于本夹具，不能提升为通用默认配置。

### 机身单粒接触暴露原称量通道漏项

SF 完整转移诊断中，舟仍在秤盘上，去皮净重却降到约 −10 g。其离线几何检查将持续失重开始与 `g_02469` 落到 `Body/Chamber/Deck` 联系起来；随后远置药勺，仅在机身放置一颗、移走并重复：

- 原 incoming joint-force 毛重约为 `10 → 0 → 10 g`；post-fetch 独立读取也出现相同问题，排除“仅 callback 读取相位错误”的解释。
- 同时读取的秤盘接触力毛重持续约 10 g；额外唤醒 articulation 与舟没有修复原关节通道。
- 因而这是当前组合中测量通道遗漏舟载荷的反例，不是舟实际卸载；底层 PhysX 内部根因仍未确定。

新 controller 由 SF 的 `scripts/powder_balance_runtime.py` 提供，producer 连同 `balance_force_state.py`、`balance_force_runtime.py` 编译检查后嵌入 `/World/obj_analytical_balance/BalanceRuntime/Graph/FlowController`。构建时需要 SF 源文件，场景运行时使用内嵌代码。原 `balance/asset.usda` 保持原字节，覆盖写在顶层 `scene.usda`。

新读数固定为秤盘实际接触力的世界竖直分量：`gross_contact_g = -F_contact_world_z / 9.81 × 1000`。tensor API 使用实际物理 `dt` 将接触冲量转换为力，再作 1 s 仿真时间积分窗，复用 0.25 s 低通、0.6 s 稳定判断、按钮去皮及 0.1 g 显示。根属性 `balance:measurement_source=pan_contact_force`；`joint_gross_g`、`contact_raw_gross_g`、`channel_disagreement_g` 保留诊断。没有补常数“找回”舟重，也没有把区域计数接入仪器读数。

## Producer 代码与输出

| 新增文件 | 实际职责 |
|---|---|
| `scripts/build_powder_fixture.py` | 惰性导入 pxr；显式加载并哈希来件生成器/配置；以几何质量、带 seed 抖动及间隙的初始填充、单位 ico + scale、UsdPreviewSurface 外观形成新 USD/JSON；拒绝已存在的 USD 输出 |
| `scripts/build_powder_balance_fixture.py` | 复制既有天平闭包、引用原自由基座设备、抬高工作区、添加料盘支撑、把接收盘改成 10 g 动态舟；设置跨尺度接触/CCD/迭代；可选嵌入 SF controller 并记录哈希；要求全新输出目录 |
| `scripts/run_powder_probe.py` | Isaac 4.5 有限时长 settle/scoop 诊断、schema/质量检查、真实粒子状态采样、耗时及异常报告；判据是有限状态、采样无地下颗粒、scoop 末帧接收区超过 50 粒 |
| `scripts/powder_tools_blender.py` | Blender 中生成源料盘、开口勺斗/抬高柄和舟的可编辑几何；采用米制；已存在的 `.blend` 输出会被拒绝；动力学权威仍为 USD |
| `tests/test_powder_fixture.py` | 两个纯 Python 行为测试：几何质量/半径立方关系及非法值；填充间隙、边界、seed 重现性与超容量拒绝 |

基础粉末入口为 `outputs/rigid_powder_r1_20260909/ico_normalized_480.usda`，联合入口为 `outputs/rigid_powder_r1_20260909/balance_fixture_r6/scene.usda`。r6 的 `balance/` 复制既有设备与本地材质闭包，不另行实现 USD/MDL 转换，也不将来件生成器变成 ConvertAsset 核心包依赖。

| r6 配置 | 值/范围 |
|---|---|
| 单位、轴向、重力 | m、kg、s；Z up；9.81 m/s² |
| 粉粒 | 4096 个独立 ico 凸刚体；seed 42；等体积半径 0.0005 m；外接半径约 0.000591028 m |
| 固体密度、质量 | 1500 kg/m³；单粒 `7.853981633974482e-7 kg`，约 0.785398 mg；总量约 3.216990877 g |
| 摩擦/恢复系数 | 粉粒静/动摩擦 0.65/0.5；工具 0.4/0.3；restitution 0 |
| 小尺度接触 | 粉粒/工具 contact offset 30 μm、rest offset 0；friction correlation distance 30 μm |
| 宏观支撑 | 场景 friction offset threshold 5 mm；地面 850×650×40 mm、contact offset 5 mm |
| 工具空腔 | 源料盘 30×24×20 mm；舟 34×30×10 mm；勺斗 12×8×4 mm，+X 开口 |
| 物理身份 | 源料盘静态；舟动态 0.01 kg；药勺运动学（声明质量 0.02 kg）；天平自由基座 |
| 联合摆放 | 舟中心 X=0.18 m；工作区 Z offset=`0.1634000000366941 m`；秤盘顶面 Z=`0.1664000000366941 m` |
| 求解 | Isaac 4.5.0、GPU dynamics/broadphase、TGS、480 Hz；粉粒/舟/articulation 64/4；CCD 与上述阈值按联合构型生效 |

`scene.json` 有继承的旧字段：`config.note` 仍写 fixed pan，`pan_center_m`/`source_floor_z_m` 是抬高前基础夹具坐标，`initial_spacing_m`/`grid` 是来件生成器改写初始填充前的值。它们不能覆盖最终 USD 的动态舟、摆放和实际粒子位置；联合位置使用 `workspace_offset`、`receiver_x` 等新增字段。实际填充函数使用 `2 × bound + 2 × contact_offset + 60 μm` 的格距及每轴 ±10 μm 抖动。后续实现者如修正元数据，应另作对应版本与验证；本次文档仅记录差异。

产物身份（本次只读复核）：

| 文件/内容 | SHA256 |
|---|---|
| `ico_normalized_480.usda` | `c3c581afb85fdde4ae1bf9431da35b6be15aeee8be3333d62ee01662d7e568c2` |
| `balance_fixture_r6/scene.usda` | `fcb2db7e269f9aa946a880c50352e65f8baa968a736841a8d98ab76d93778d13` |
| `balance_fixture_r6/scene.json` | `eb912e47ff92d795b54c7f28c0f8e79833eff5a98560e06b3624c21d2b868bdc` |
| r6 嵌入 controller（元数据记录） | `4fcd54570ad3b9facc00a67dba8769efbbd3d4be4c5365fe4291bc0f348d37b0` |
| `powder_tools.blend` | `969d53fd3d1e3f32d3fe4881f5957ba5975e2266f60893f6ba551175f6c4a7f0` |

上述相对产物均位于 `outputs/rigid_powder_r1_20260909/`。Blender 4.4.3 成功生成 `powder_tools.blend` 为生产者 handoff 所报事实；文件存在和哈希已核对。它保存基础工具几何，而非完整 r6 天平布置；未在 Blender 做动力学资格验证。

## 已完成证据及其边界

### Producer 探针

以下均位于 `outputs/rigid_powder_r1_20260909/`，历史配置以每份报告内部字段和哈希为准，不以当前脚本默认值回填：

| 报告 | 已观察结果 | 限定范围 |
|---|---|---|
| `sphere_probe_r1/report.json` | failed，USD 属性定义查询 API 异常 | 接口兼容诊断 |
| `sphere_probe_r3/report.json` | failed，采样期出现地下颗粒，未完成转移 | 8192 粒、0.6 mm 球形的早期短运行 |
| `ico_probe_r1/report.json` | failed；末采样地下 14 粒，接收区 93 粒 | 4096 粒、1 mm、240 Hz 的历史配置 |
| `ico_probe_r2/report.json` | passed，3 s settle，惯量读回 | 2048 粒、480 Hz；settle 模式的 `transfer=true` 是该检查不要求转移，不是舀取成功 |
| `ico_probe_r3/report.json` | passed，22 s scoop；末接收区 406 粒、源区 3580 粒、地下 0；墙钟约 63.79 s | 基础粉末 24/4、480 Hz；不是联合天平称量资格 |

早期 producer probe 的 `states.npz` 中粒子 pose 来自物理 view，但 `tools` 写入的是药勺控制目标，不能作为实际药勺接触轨迹的完整证据。SF 最终 `scripts/validate_powder_weighing.py` 改为记录 `spoon.get_transforms()` 的实际位姿，并记录舟与天平 link；最终回放应使用消费者记录。采样时无地下颗粒也不等于连续时间、任意轨迹下永不穿透；没有由这些检查宣称粉床完全静止。

收尾时 producer probe 的后续记录路径也改为读取 `spoon_view.get_transforms()`，并保持 wxyz 记录格式。
该处仅通过 Python 语法及定向测试检查，未重跑早期 GPU probe；历史 NPZ 不因此被改写。

### r6 对应的消费者联合报告

权威消费者记录：[刚体粉末与真实受力称重 r1](../../../scenario-forge/docs/records/2026-09-09-rigid-powder-force-weighing-r1.md)；运行与测量语义见[操作指南](../../../scenario-forge/docs/operations/powder-weighing-r1-guide.md)。

SF 证据根：`/cpfs/user/zhuzihou/dev/scenario-forge/outputs/powder_weighing_r1_20260909/`。
三份报告的 `status=passed`、全部 `checks=true`、`runtime=4.5.0`、`physics_dt=1/480 s`、`robot_grasp_verified=false`。它们的场景哈希与 producer r6 相同；`handoff/powder_weighing_r1/scene.usda` 也经本次只读比对确认同字节。

| 报告 | 结果 | 报告 SHA256 |
|---|---|---|
| `weighing_contact_r3/report.json` | seed 42、28 s 完整舀取/倾倒；末舟区域 406 粒、0.318871607 g；末净重 0.327405172 g；尾窗区域交叉检查最大误差 0.010654602 g | `8d2c66abcc6454d410d488c93d607630987606806b6ebe89d64bbd41e5d9518b` |
| `calibration_final/report.json` | 32 s 已知载荷、撤载、移舟、reset；在已打包场景上运行 | `06ea654a2fcb492f5911fd47c8313f29e40cb413488f7efad397fae9c121ac4e` |
| `body_contact_qualified/report.json` | 25 s 机身单粒放置/移走/重复，新接触力通道保持舟载荷，旧关节读数保留诊断 | `0380aa89b14970952dbf3032bb5e6f43c04863d712904a0ab3c56deef3d1358b` |

已知载荷每个 case 最后 1 s、30 个采样点的滤波净重最大绝对误差，直接据 `calibration_final/report.json`（下表作小数舍入）：

| 载荷/操作 | 期望净重 g | 最大绝对误差 g |
|---|---:|---:|
| 0 粒 | 0 | 0.000057774 |
| 128 粒 | 0.100530968 | 0.000185395 |
| 512 粒 | 0.402123871 | 0.015175666 |
| 1024 粒 | 0.804247742 | 0.047734660 |
| 撤去粉末 | 0 | 0.000116071 |
| 移走已去皮空舟 | −10 | 0.000868806 |
| reset 后空盘 | 0 | 0（该窗口） |

通过阈值为 0.1 g，并要求窗口内 valid/stable。较小载荷的低误差不能外推为毫克级精度；单粒质量约 0.785 mg 也不等于测量精度。舟外但仍在秤盘上的洒粉也会被测到，因此 ROI 质量只是独立交叉检查，不是秤盘所有荷载的精确替代。直接施加到秤盘上的非接触外力不属于该接触传感器输入。

28 s 联合记录用时 `247.063936 s`，物理步 p50=`17.178351 ms`、p95=`27.193203 ms`。它反映该机器负载与采样条件，未达到实时运行；按仿真时间播放状态回放视频不能证明 RTF≥1。

## 命令与验证记录

### 已有执行结果

- 生产者 handoff 与 SF 日期记录均记载 `python -m pytest -q tests/test_powder_fixture.py`：**2 passed**。覆盖上表两项纯 Python 行为，不能称为完整 USD、Blender 或 GPU 集成测试。
- 生产者 handoff 记载 Blender **4.4.3** 运行 `scripts/powder_tools_blender.py` 生成 `outputs/rigid_powder_r1_20260909/powder_tools.blend`。本次文档任务仅核验已存在文件。
- GPU 运行结果复用上述历史原始报告；本次 docs-writer 不运行 GPU。历史构建/Blender 的完整 shell 调用没有在所读报告中保存，以下给出按当前 CLI 与产物配置核对的确切复现命令，不冒充历史 shell transcript。

### Producer 复现命令（本次未执行）

工作目录为 `/cpfs/user/zhuzihou/dev/ConvertAsset`；要求本机 `/isaac-sim` 为 Isaac 4.5.0，`blender` 为 4.4.3。使用全新 `doc_repro` 路径保留既有证据；这些是新运行，不保证与旧输出逐字节一致。必须先确认该目录不存在，且 SF controller 源内容仍与记录身份一致。

```bash
ROOT=/cpfs/user/zhuzihou/dev/ConvertAsset
SF=/cpfs/user/zhuzihou/dev/scenario-forge
SOURCE="$ROOT/outputs/rigid_powder_r1_20260909/source/Labimus_Rigid_Powder_Reproduction"
OUT="$ROOT/outputs/rigid_powder_r1_20260909/doc_repro"

ISAAC_SIM_ROOT=/isaac-sim ./scripts/isaac_python.sh scripts/build_powder_fixture.py \
  --source "$SOURCE" --out "$OUT/ico_normalized_480.usda" \
  --count 4096 --radius 0.0005 --shape ico --seed 42 --hz 480

ISAAC_SIM_ROOT=/isaac-sim ./scripts/isaac_python.sh scripts/build_powder_balance_fixture.py \
  --powder "$OUT/ico_normalized_480.usda" \
  --balance "$ROOT/outputs/balance_force_r1_20260909/packages/analytical_balance_force_r1" \
  --out "$OUT/balance_fixture_r6" --controller-source "$SF/scripts" --iterations 64

ISAAC_SIM_ROOT=/isaac-sim ./scripts/isaac_python.sh scripts/run_powder_probe.py \
  --scene "$OUT/ico_normalized_480.usda" --out "$OUT/ico_probe" --mode scoop --seconds 22

blender --background --factory-startup --python scripts/powder_tools_blender.py \
  -- --out "$OUT/powder_tools.blend"
```

必须显式传 `--hz 480`、`--iterations 64`、`--controller-source`：当前默认分别为 240 Hz、24 次，以及沿用 `incoming_joint_force`，默认调用不是 r6。producer probe 的轨迹/ROI 是基础夹具坐标，不应直接拿它验证抬高后的天平联合夹具。

### 对应消费者验证入口（本次未执行）

工作目录为 `/cpfs/user/zhuzihou/dev/scenario-forge`；下面以已记录的 handoff 场景建立三份新报告。参数分别对应已完成的 28/32/25 s 试验；输出名追加 `_doc_repro`，不覆盖原报告。

```bash
SCENE=/cpfs/user/zhuzihou/dev/scenario-forge/outputs/powder_weighing_r1_20260909/handoff/powder_weighing_r1/scene.usda
EVIDENCE=/cpfs/user/zhuzihou/dev/scenario-forge/outputs/powder_weighing_r1_20260909

/isaac-sim/python.sh scripts/validate_powder_weighing.py \
  --scene "$SCENE" --out "$EVIDENCE/weighing_contact_r3_doc_repro" --mode scoop --seconds 28
/isaac-sim/python.sh scripts/validate_powder_weighing.py \
  --scene "$SCENE" --out "$EVIDENCE/calibration_final_doc_repro" --mode calibration --seconds 32
/isaac-sim/python.sh scripts/validate_powder_weighing.py \
  --scene "$SCENE" --out "$EVIDENCE/body_contact_qualified_doc_repro" --mode body_contact --seconds 25
```

检查 `report.json` 的状态、checks、异常与场景哈希，而非只看进程退出码。GUI 打开场景并播放不自动运行舀取轨迹；规定轨迹由验证脚本驱动。

### 本次文档验证（2026-09-10，无 GPU）

- `git diff --check -- docs/records/README.md docs/records/2026-09-09-rigid-powder-fixture.md`：通过；新建未跟踪文件另由 Python 检查行尾空白、末尾换行和代码围栏。
- `python -B scripts/build_powder_fixture.py --help`、`python -B scripts/build_powder_balance_fixture.py --help`、`python -B scripts/run_powder_probe.py --help`：均退出 0，只验证 CLI 入口，不启动 SimulationApp。
- `python -B -c '…'` 标准库只读核对：7 个本地 Markdown 链接存在；2 段 Bash 代码通过 `bash -n`；原 ZIP 的 13 个来源文件同字节；r6/消费者场景身份一致；三份报告的哈希、状态、checks、runtime 及机器人未验证标记符合正文。
- SHA256 前后对比：本次所述五个 producer 代码/测试文件未变；从 README 去掉新增的一条链接后，与编辑前工作副本逐字节一致，保留了他人已有索引改动。
- 未重跑历史 pytest、Blender、仿真或视觉检查；2 passed 和 Blender 4.4.3 生成结果按已有 handoff 与上述文件证据引用。

## 限制与文档同步边界

- 已验证范围是 Isaac 4.5.0 下该自由基座联合夹具、指定参数和有限轨迹。Isaac 4.1 粉末组合、VR loader、Lift2/真实机器人动态抓持、按钮真实接触操作及完整机器人策略均未获本记录资格。
- 这是无实物标定的干颗粒代理；黏聚、湿度、静电、任意化学粉末真实性、作者原始配置、毫克级准确度和实时性能均不能称为已验证。
- 单粒机身接触反例说明原关节力通道有范围缺口；新通道通过特定回归不等于解释或修复了底层引擎全部问题。改变粒径、密度、形状、工具、求解器或 runtime 后须重新取得匹配证据。
- 仪器 `reset_requested` 清除测量滤波、去皮及仪器状态，不会自动搬回粉粒、舟或药勺。完整重现实验需重开初始场景并重建物理 view。
- 已有旧元数据和早期 probe 的目标位姿记录限制见上文；原输入、旧 fixture 和原 force r1 资格不因本记录而被改写。

规范依据为本次读取的 SF 当前工作树：[资产接入 ASSET-001/003/006](../../../scenario-forge/docs/standards/asset-intake.md)、[状态 STATE-002/003/005/007](../../../scenario-forge/docs/standards/task-state.md)、[验证 VAL-001/002/003/005](../../../scenario-forge/docs/standards/validation-and-delivery.md)及[维护流程](../../../scenario-forge/docs/standards/maintenance.md)。消费者同期记录已说明 ASSET-003 颗粒尺度、STATE-007 多 link 接触、VAL-003 实际工具位姿的同步；本次 producer 文档没有新增通用规则，**规范无需另行变更**，参数只作为具体夹具事实。核心包/schema/API 契约不由本日期记录重新定义。

本次写入限定为本记录及 `docs/records/README.md` 的一条日期链接；保留其他协作者既有工作。文档验证采用来源字节比对、场景/报告哈希与状态核对、局部链接/Markdown 结构和 diff 空白检查；不以文档同步重新运行 GPU 或声明消费者视觉/多 seed 收尾完成。
