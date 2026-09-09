# 2026-09-09 Task 09 天平受力 producer r1 记录

## 背景与当前状态

本次工作修复 Task 09 来料天平的物理称量基础，将独立秤盘、承力关节和实时显示附件制作在 ConvertAsset producer 中，供 Scenario Forge 消费。原始 ZIP 保持不变；本记录覆盖调查、producer 实现、正式晋级和下游任务报告；各项结论均限定到具体报告及构型。

正式 producer 包已晋级为 `outputs/balance_force_r1_20260909/packages/analytical_balance_force_r1/`，旁置 `analytical_balance_force_r1.zip`。包内 `manifest.json` 的 `status=promoted`、`overall_status=pass`，`evidence/manifest.json` 的 `overall_status=pass`。准入范围限定为 GPU TGS、水平支撑上的自由基座、独立 load-cell 链的受力称量。选定配置为 **0.1 g 分度、200 g 容量、30 ± 0.2 g 目标**。早期 0.01 g 配置虽然在简单标准质量夹具中读数良好，却未满足原任务颗粒的稳定称量要求，因此不作为交付精度声明。该选定配置已得到下述任务报告支持；更广泛的真实仪器精度和量程不在证据范围内。

正式包 manifest 绑定：

| 内容 | SHA-256 |
|---|---|
| `asset.usda` | `56ef7fbe5d9313c3f33a9bf9777aab13ba42e3d47589f2c7e90ca486d8f93a0b` |
| 嵌入控制器 | `74dd26ee7837ac55b6e4085854aa813182cff4f12385fbd7979910ce797aea3c` |
| `scene_support.usda` | `aaf7a19c9f00e132d7de1dcf5f54fd3536200a3302b06d45000f46135d021c59` |

本资产来源与此前 [LICHEN r1 四扇滑动门记录](2026-08-18-analytical-balance-lichen-r1-doors.md) 不同，旧资产的固定基座开关门证据不能继承到本次可移动称量资产。

## 来料与调查

原始来源：

`/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/from_xinyu/task_09_solid_weighing.zip`

manifest 记录的来源 SHA-256：

| 来源 | SHA-256 |
|---|---|
| ZIP | `adf898a57146a858d37ca4f4eddfc039cfe41bf78271818cfeee667914a95d5d` |
| 包内 `task_09_solid_weighing/scene.usd` | `f0cb8161d0d8476c2ffa4b27439bfa90c59bc8a866c0d51da69b1f17405be355` |

调查发现原天平 LCD 是静态字形，只有一个可动去皮自由度 `RightTarePress`；原秤盘位于机身下，不具备独立 load-cell 受力链。`Chassis` 的 `physics:mass` 为 1,000,000 kg，与其 `balance:mass_kg=6.8` 声明不一致。本次按声明修复机身质量，不使用超大质量稳定机身，也不按观察到的读数衰减添加质量倍率。

已读取的实现和验证入口为 `scripts/build_balance_force_asset.py`、`scripts/attach_balance_runtime.py`、`scripts/qualify_balance_force.py`、`scripts/probe_balance_initialization.py`、`scripts/probe_balance_force.py` 与 `tests/test_balance_force_asset.py`。

## Producer 实现

公共入口仍为 `/World/obj_analytical_balance`。`scripts/build_balance_force_asset.py` 解包经过路径安全检查的 ZIP，复制 `SubUSDs` 依赖，生成独立 `asset.usda` 和全场景支持层 `scene_support.usda`，并记录来源、输出哈希及路径迁移。

| 修改 | 行为与原因 |
|---|---|
| `Instance/Chassis` → `Instance/Body` | 将机身质量恢复为 6.8 kg，保留局部装配位置；默认移除旧固定基座，形成可移动 articulation |
| `Instance/Chassis/Pan` → `Instance/WeighingPan` | 独立秤盘刚体质量 0.05 kg，以 `Instance/Joints/LoadCell` 固定关节连接机身，提供关节反力测量链 |
| 重建 `Instance/Joints/RightTarePress` | 对齐按钮刚体和关节两侧局部框架；保留 0–0.0015 m 行程与回弹 drive |
| 清理保存态 | 修正装配四元数，归零刚体线速度和角速度，取消 kinematic，避免来料保存态影响启动 |
| 物理配置 | 关闭 articulation 自碰撞、睡眠及 stabilization；相关刚体保持 awake，设置明确 solver iterations |
| 场景支持层 | 对天平外的原场景刚体设置 `sleepThreshold=0`、`stabilizationThreshold=0`，在 manifest 列出 `awake_loads` |
| 依赖与碰撞 | 重写 `SubUSDs` 资产引用；碰撞 mesh 的空或 `none` approximation 转为 `convexHull` |

`--fixed` 是独立诊断构型选项；正式包 manifest 的 `movable=true`。固定构型结果不应外推为可移动构型资格。

根元数据更新为 `balance:asset_id=analytical_balance_force_r1`、`balance:revision=force_weighing_r1`；原值保存在 `balance:source_asset_id`、`balance:source_revision`。按钮角色更新为 `spring_return_tare_button`。场景支持层保留原道具碰撞参数：曾尝试减小颗粒和称量舟 contact offset，稳定性变差后已回退到原 `contactOffset=0.005 m`、`restOffset=0.001 m`。当前构型的睡眠与 stabilization 修复保留；producer 另允许通过 `--grain-mass-g` 配置颗粒质量，当前为每颗 10 g。

`scripts/attach_balance_runtime.py` 隐藏原静态 `Digits`，复用字形 mesh 制作八位 `LiveDigits` 及球形小数点，附加传入的 policy 和 bridge 代码，并对嵌入控制器内容做 SHA-256。控制器随 producer artifact 保存，不在运行时导入消费仓库脚本。离线目标校验函数从嵌入 policy 中排除，避免把编译阶段职责带入设备运行脚本。该脚本设置 `balance:*` 状态属性和 `container`、`spoon`、`samples` 关系，并生成 `asset_isaac41.usda` 以适配 4.1 的 `OnPhysicsStep` 节点类型。附件是否工作以实际任务报告和图像为准，当前结果见下一节。

## 已有测量证据及适用范围

证据根目录：`outputs/balance_force_r1_20260909/`。各报告的 runtime、PID、资产哈希和构型共同限定结论，文件名尾缀不代表准入版本。

| 文件或文件族 | 已观察结果 | 结论边界 |
|---|---|---|
| `probe41.json`、`probe45.json` | 独立简化三刚体夹具产生关节反力采样，构型为可移动 | 验证力读取路线可行；不是原天平或任务准入 |
| `original41_zero.json`、`original45_zero.json` | `passed_this_reproduction`，DOF 为 `RightTarePress` | 仅当前高层 API 显式零初始化复现通过 |
| `measure41a.json`、`measure45a.json` 等早期迭代 | 30 g 载荷稳态仅约 3.75 g，200 g 约 25 g | 留作读数衰减失败证据，`measured` 不等于通过 |
| `measure41e.json`、`measure45e.json` | awake/stabilization 配置修复后，30 g 均值分别约 30.000008、30.000601 g | 证明本夹具中不需要质量倍率补偿，不能替代最终任务测试 |
| `measure41f.json`、`measure45f.json` | 进一步记录空载、分档载荷、偏载、卸载及规定搬移后的恢复 | 历史构型测量，绑定报告内哈希 |
| `measure41gpu.json`、`measure45gpu.json` | GPU 下各 11 个 case 已完成测量，状态 `measured` | 单资产已知刚体载荷夹具，非完整场景任务 |

早期衰减与载荷进入睡眠及 stabilization 配置相关；修复在物理状态配置层保持载荷 awake，并关闭相应 stabilization，没有将 1/8 的读数乘八来冒充校准。当前测量公式直接使用秤盘关节 Z 向反力：`raw_g = force_z / 9.81 * 1000 - 50`，随后用 0.25 s 时间常数滤波。50 g 是显式秤盘自重。

`qualify_balance_force.py` 在 120 Hz 下依次测量空载、1/10/30/50/100/200 g、30 g 偏移 0.035 m、卸载、规定 articulation 搬移恢复空载和恢复后 30 g。每项统计采样尾部 30 点的均值、最大绝对误差和范围。最后重复三次零位设置。脚本写出的 `status='measured'` 表示过程完成，不执行最终任务精度或准入门禁。

GPU 报告中，4.1 的 200 g case 尾窗最大误差为约 0.010341 g，4.5 各 case 最大误差约 0.006557 g。因此不能仅凭均值接近标称值宣称所有采样达到 0.01 g 精度。这两份历史 GPU 报告绑定资产哈希 `e539fb2d2d5d7978194171e1f1e5cd19de446aad53b69324fdea532cfded6763`；该哈希早于最终材质闭包版本。最终晋级使用下述 `bundle*` 报告，未沿用历史测量作为最终字节的资格证据。

原始显式零初始化复现使用 `World`/`Articulation` 高层 API，每次 reset 后设置零位并步进 120 步，重复三轮。4.1 报告 runtime 为 `4.1.0-rc.7+4.1.14801.71533b68.gl`，4.5 为 `4.5.0`。这只说明本机这段复现没有触发问题，不能证明同事原环境的崩溃不存在或已经修复；未据此声称 omitted、pressed 或其他初始化路径均通过。

主实现者另已报告：CPU 单资产受力夹具可工作，但包含原始 SDF 任务道具的完整场景在 Isaac 4.1 CPU 路径失败；该完整场景需要 GPU dynamics。CPU 失败诊断已从临时路径持久化至 `outputs/balance_force_r1_20260909/diagnostics/weighing-live41.log`；GPU 任务报告见下节，不把此限制泛化为“所有天平受力测量必须 GPU”。

## 最终闭包、报告与视觉状态

`scripts/localize_balance_materials.py` 调用已有 AAN `build_material_runtime_closure`，分别闭合 Isaac 4.1/4.5 的 SDK MDL 依赖，重写本地资产引用，保留模块版权头；没有另行实现 MDL 转换。正式包共保留 48 个 `.mdl` 文件，其中 43 个位于 `materials/`，另有 5 个原始文件保留在 `SubUSDs/`；两版 USD 与 MDL 均闭合。`material_closure.json` 两版状态均为 pass；主实现者确认材质编译日志无错误、缺失纹理或缺失模块。该处理改变了资产和支持层哈希，故最终测量改用 `bundle*`，历史 `release*` 只保留为诊断。

正式 ZIP SHA-256：`91927b1d2cfa1db9e8d2488b2a46e3ec0f6a822498047bca4f74d4c5f1f4fac0`。

Scenario Forge 任务证据目录：

`/cpfs/user/zhuzihou/dev/scenario-forge/outputs/scientific_workbench_solid_sample_weighing_vr_r1_20260909/evidence/`

最终六份任务 `bundle{41,45}_{zero,omitted,pressed}.json` 通过；六份 producer 同名报告位于 `outputs/balance_force_r1_20260909/`，已收入正式包 `evidence/cold_start_1.json` 至 `cold_start_6.json`。六份 producer 原始报告状态为 `measured`，晋级汇总为 pass，全部绑定正式 asset SHA。Scenario Forge `bundle_processes41.json`、`bundle_processes45.json` 记录六次任务与六次 producer 独立子进程全部退出 0。

任务检查覆盖空载、容器、去皮、目标、负数、reset、抬离失效、超载、外加压力响应、撤压恢复、搬移恢复。协议为 `prescribed_live_body_placement_and_joint_press`，包括规定位置摆放任务颗粒、按钮关节按压，以及整机搬移并绕竖直轴转动 30° 后恢复。去皮属于关节按压流程证据，不能外推为机器人真实接触按钮成功；报告明确 `robot_policy_success=false`。

下游最终任务 source SHA 为 `ca7410b8810de82a92a9fda06ffbc4a4cbd1d627b21086d8aa3894bc198f8335`，closure SHA 为 `46c7239bcd1352d4ecc3b4a4711e3c283c9f684a748d0dade051eded5cd5cde1`。此处不记录仍在刷新便携截图内容的任务 ZIP 哈希。

主实现者已本地复核跟随机位 `bundle*zero*.png`，数字、小数点和负数读数可见，解决了历史固定机位搬移后裁切负数的问题。视觉结论保留 **WARN**：两版全景背景塑料色调和阴影有差异，近景裁切了碗沿；这是本地查看，不是独立视觉评审，也不声明跨版本像素一致。manifest 的视觉保留 fingerprint 比较基准是 producer 修复后 candidate，而非原始来料，不应据此声称全部原始视觉和物理未经修改。

## 验证入口与结果

以下是当前脚本可执行入口模板，不是本次已执行命令的追认；每次需选定正确的 Isaac Sim 环境，并使用独立输出路径保留证据。

```bash
./scripts/isaac_python.sh scripts/build_balance_force_asset.py --source /path/to/task_09_solid_weighing.zip --out /path/to/candidate --grain-mass-g 10
./scripts/isaac_python.sh scripts/probe_balance_initialization.py --scene /path/to/original/scene.usd --init zero --out /path/to/original_zero.json
./scripts/isaac_python.sh scripts/qualify_balance_force.py --asset /path/to/candidate/asset.usda --init zero --gpu --out /path/to/measurement.json
python -m pytest tests/test_balance_force_asset.py -q
```

主实现者报告 ConvertAsset focused tests **3 passed**（`tests/test_balance_force_asset.py` 和 `tests/test_promote_balance_force.py`），source Ruff 通过；Scenario Forge `make check` **973 passed, 1 skipped**，phase10x 与 package-smoke 通过。随后执行 `python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py tests/test_balance_force_asset.py tests/test_promote_balance_force.py -q`，联合验证结果为 **24 passed in 0.70s**。本记录编写者核对了当前脚本、正式包 manifest、材质闭包和包内六份冷启动报告，未重跑测试或仿真。

仍保留的限制是原始同事崩溃环境未完整复现、上述视觉 WARN，以及 GPU/水平支撑/awake-load 的准入适用范围。本次测量和任务流程不声明真实仪器计量校准、真实粉末测量或机器人策略成功。0.1 g 分度是选定软件显示与任务验证配置，不等同于真实硬件校准证书。

本次是特定来料的 producer 修复，没有建立可推广的新通用准入规则；原有历史 LICHEN 记录保持原适用范围。文档记录和两个索引已同步；本次文档编辑保留无关论文与索引的既有改动，不触及代码或记忆文件。
