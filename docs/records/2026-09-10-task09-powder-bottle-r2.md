# 2026-09-10 Task09 浅粉瓶与重建称量舟 producer r2

## 背景与记录范围

本轮在新宇原 task09 台面场景中增加可舀取的浅粉瓶，保留原药勺和五颗大固体，
解决细颗粒与原称量舟接触不可靠的问题。用户授权用 Blender 重建外观大致相同的白色浅舟，
最终验收范围收敛为 **Isaac Sim 4.5 ONLY**，采用较慢的规定舀取轨迹。

最终 producer 为 `outputs/task09_powder_bottle_r2_20260910/candidate_r14/`。
`candidate_r1` 至 `candidate_r13` 均只作为诊断候选保留，不获得最终资格。
资格来自下述匹配场景身份的 SF 最终报告，不能由目录编号或构建成功推断。
`candidate_r14/scene_config.json` 仍保留构建时的 `status=candidate`；本文不改写该产物字段。

主会话汇总：[SF 原 task09＋浅粉瓶＋重建称量舟 r2](../../../scenario-forge/docs/records/2026-09-10-task09-powder-bottle-r2.md)。
设计与操作分别见 [SF 设计说明](../../../scenario-forge/docs/design/task09-powder-bottle.md)
和 [SF 操作指南](../../../scenario-forge/docs/operations/task09-powder-bottle-r2-guide.md)。
本文未标 SF 的代码和产物路径以 ConvertAsset 仓库根为基准。

本次文档写入 scope 精确限定为：

- `docs/records/2026-09-10-task09-powder-bottle-r2.md`。
- `docs/records/README.md` 中新增一条本记录链接。

本文记录已发生的研究、设计、代码与验收；本次写作只读核查来源、代码和已有证据，
不修改实现或产物，不运行 GPU，不 commit，保留其他协作者的全部已有改动。

## 资产来源与保留边界

原始来件均在 SF 的 `external_artifacts/incoming/from_xinyu/`：

| 输入 | 身份与用途 |
|---|---|
| `task_09_solid_weighing.zip` | 原 task09 来源；ZIP SHA256 为 `adf898a57146a858d37ca4f4eddfc039cfe41bf78271818cfeee667914a95d5d` |
| 原 task09 场景 | `scene_config.json.source_sha256` 为 `f0cb8161d0d8476c2ffa4b27439bfa90c59bc8a866c0d51da69b1f17405be355` |
| `wide_opening_bottle_two_versions.zip` | ZIP SHA256 为 `5f9bb4584eee04f49b75d35ea5433a6f9daf05f4c968e55a35a80a56b4d2d456`；采用 `bottle_empty` |
| `outputs/rigid_powder_r1_20260909/ico_normalized_480.usda` | 独立 ico 粉粒原型；SHA256 为 `c3c581afb85fdde4ae1bf9431da35b6be15aeee8be3333d62ee01662d7e568c2` |

瓶来件的 `README_variants.md` 记载其按参考照片在 Blender 4.2.1 从零制作，
80×80×140 mm、56 mm 净开口是设计尺寸，150 g 是仿真假设质量；来件本身仅有静态检查，
未做 Isaac runtime 验证。本轮使用空瓶版本，在 USD 中另加假底/浅槽，
没有采用来源中填至 120 mm 的 `bottle_neck_prefilled`。原 ZIP 和此前 r1 输入不因本轮记录改写。

原场景共 19 个 `obj_*`：天平替换为修复版；其余 **18 个旧普通资产中仅称量舟获授权 Blender 重建**。
五颗旧大固体 `/World/obj_grain_01` 至 `obj_grain_05` 全部保留，不属于新粉末通配符。
原勺仍使用原几何，初始仍放在烧杯内；重建舟保留 `obj_weighing_boat` 名称与原初始位置/旋转，
单独声明其 X 尺度烘焙。最终元数据记录其他 **17 个旧对象**的根变换逐一一致；
这里的变换保留不表示其所有物理属性逐字节未变，producer 仍统一设置了相关求解迭代等属性。

天平和桌面引用既有合格闭包，复制到 `deps/balance`、`deps/table`；原 `SubUSDs/` 随场景复制，
MDL 引用复用既有 AAN 本地闭包。天平来源背景见[受力 producer r1](2026-09-09-balance-force-r1.md)，
粉粒原型及此前接触力通道背景见[刚体粉末 fixture 记录](2026-09-09-rigid-powder-fixture.md)。
这些历史资格不自动覆盖本轮细颗粒联合场景；本文不新增资产许可或实物来源认证。

## 研究与诊断

本次核对了两份 producer 脚本、对应测试、瓶来件说明、r14 场景/元数据/舟几何字段，
以及 SF 主记录、设计、操作说明和四份最终证据。以下诊断经过以 SF 主会话记录为依据，
最终结果以原始 JSON 为依据，不把当前脚本默认值回填到早期候选。

1. **原舟 SDF 朝向反例。** 六块旧 hull 存在毫米级接缝；原可见网格虽闭合，三角面整体向内，
   有向体积为负。直接使用 SDF 时曾出现粒心进入底壳实体。隐藏碰撞副本修正绕序后改善了该问题，
   但没有使原舟完整称量稳定。闭合网格和 SDF 分辨率本身不能证明有效的容器内外判定。
2. **重建、尺度、惯量与求解器。** 支撑片、唤醒、CCD 和 SDF 对照都不足以单独宣布解决问题。
   重建舟候选及 TGS 路线仍有动态不稳定；最终选择单位根尺度、明确质心/惯量、封闭凸块和 PGS 的组合，
   重新取得对应场景的验收。不能将结果归结为单一修复，也不能外推为 TGS 普遍不适用或 PGS 普遍更优。
3. **勺腔与区域计数。** 原勺矩形 ROI 曾把勺背下方的床内颗粒计入，床内 `spoon_count` 不能当作装料。
   水平预装 64 粒仅是诊断；最终要求抬离粉床后的持续持料，以及实际倾倒进入舟区域。
   工具轨迹按勺头 anchor 插值再反算根位姿，避免直接插值根 pose 时旋转导致勺头下探撞舟。
4. **4.1 失败。** 早期试跑出现接触差异、CUDA/TGS 内核错误，以及报错后有限但停滞的旧位姿。
   早期标为 `passed` 的不完整判据、阻塞/超时和无完整报告运行均不算资格。
   SF 验收器改为主线程消费日志事件并把引擎错误判失败；4.1/VR 已按用户要求退出最终验收。
5. **校验瞬移与 CCD。** 已知载荷校验在颗粒瞬移前关闭 CCD，推进一个物理步后恢复，
   避免瞬移扫掠影响中间设备。`final_calibration` 明确记录 `calibration_teleport_ccd_reset=true`，
   `final_scoop` 为 `false`。这一夹具处理不能外推为舟不稳定或所有早期故障的底层根因；
   实际舀取过程中粉末由接触驱动，不瞬移粉末。初始化将空舟放到秤盘仍是规定夹具放置。

中间/失败证据保留在两个仓库各自的 `outputs/task09_powder_bottle_r2_20260910/`；
它们解释设计取舍，不替代最终 r14 报告。

## 最终设计与物理配置

| 项目 | r14 实际配置 |
|---|---|
| Runtime/求解 | Isaac Sim 4.5.0；GPU dynamics、GPU broadphase；PGS；480 Hz；32 次位置迭代 |
| 空瓶与固定填充 | 80×80×140 mm 外瓶、56 mm 内口；假底顶高 131 mm，浅槽约 36 mm 直径、槽沿高 139 mm，均为瓶局部高度 |
| 瓶质量 | 瓶和假底/槽壁共用 150 g 工程质量；固定填充不计入可舀粉末 |
| 粉末 | 4096 颗独立 ico；1 mm 等体积球直径，密度 1500 kg/m³；单粒约 0.785398 mg，总量约 3.216991 g |
| 根结构 | `/World/obj_powder_grain_00000` 至 `04095` 是 Xform＋刚体/质量 API；子 `Mesh` 仅有几何/碰撞，无重复刚体或质量 API |
| 原勺 | 原可见几何和初始变换；SDF 512 碰撞；场景初态是普通动态刚体，规定舀取时临时运动学驱动 |
| 新舟 | Blender 白色外扩浅舟；8 块侧壁＋1 块底板，共 9 块封闭凸碰撞体；实际外尺寸 64.8×82×28 mm |
| 新舟质量/尺度 | 显式 0.01 kg；原 root X scale 0.6 烘入视觉和碰撞几何后，root scale 为 `[1,1,1]` |
| 接触与迭代范围 | 粉粒/瓶/勺/舟 32 次位置、4 次速度迭代；天平 articulation 位置迭代 32；场景启用 CCD，舟自身 CCD 关闭 |
| 读数 | `pan_contact_force`；实际 dt 换算接触冲量，1 s 积分窗、既有低通/去皮；显示分度 0.01 g |

粉床不是焊在瓶上的视觉对象。初始化采用有间隙的分层六角排列，代码含 seed 42 的微小位置扰动及颗粒朝向生成，
随后由重力沉降；这不等于任务运行中逐粒独立布局随机化或多 seed 验收。
规定接触段约前推 6 mm / 7 s，先上提原勺离开烧杯，再较陡入粉、停顿、慢推并转平。

新舟质心和惯量由 Blender 闭合模型体积积分得到，而非按读数反调质量。
`source_boat/geometry.json` 中，局部 COM 约为 `(0,0,0.00402146657)` m；
主惯量为 `(4.53971901e-6,6.18594910e-6,9.14689345e-6)` kg·m²，
主轴四元数 wxyz 约为 `(0.70710671,0,0,-0.70710683)`。USD 明确写入这些字段；
最终报告运行时读回舟质量约 `0.009999999776 kg` 及有限惯量。
原视觉、旧 collider 和诊断 SDF 副本作为 inactive 来源参考保留，最终接触使用新舟凸块。

**旧文字与实际字段：** r14 的 `geometry.json.root_scale`、`scene_config.json.boat_root_scale_normalized`
及 USD `xformOp:scale` 均为 `[1,1,1]`。旧版 `geometry.json` 说明或 `.blend` custom `scope` 中若仍有
“0.6”文字，只能作为历史描述，不能据此再施加 0.6 缩放。USD 还继承了旧舟 `weighing:*` 来源属性，
其中 `weighing:visualDimensions_m=(0.108,0.082,0.028)` 描述旧模型，不能替代新舟
`physical_outer_dimensions_m=(0.0648,0.082,0.028)`。本记录按实际字段引用，不修补产物文字。

## 已有代码与脚本调用范围

| 文件 | 已实现职责与调用边界 |
|---|---|
| [scripts/build_task09_powder_bottle.py](../../scripts/build_task09_powder_bottle.py) | 复制原场景/依赖，替换天平，添加瓶内固定填充与根刚体颗粒，配置勺碰撞并接入可选新舟，嵌入 SF 仪器脚本，记录来源/保留变换；`pxr` 在函数内惰性导入 |
| [scripts/model_task09_weighing_boat.py](../../scripts/model_task09_weighing_boat.py) | Blender 内构造闭合白色浅舟、修正法线、应用倒角及 X 缩放，生成 9 凸块、计算 COM/惯量，输出 `geometry.json` 和 `weighing_boat.blend`；不做 Isaac 动力学验收 |
| [tests/test_task09_powder_bottle.py](../../tests/test_task09_powder_bottle.py) | 三个行为测试：浅槽填充间隙/边界/重现及超容量拒绝；Mesh 质量/API 上移到根且不重复；绕序修复不改几何并产生正体积 |

构建脚本通过 `./scripts/isaac_python.sh scripts/build_task09_powder_bottle.py` 调用，
要求带 `pxr` 的 Python；它负责离线 USD 生产，运行资格另由 SF 完成。
必填参数为 `--source` 原场景文件、`--bottle` 空瓶目录、`--balance` 天平闭包目录、
`--table` 桌闭包目录、`--prototype` 粉粒原型 USD、`--controller` SF 脚本目录、`--out` 全新输出目录。
最终组合还需要显式 `--count 4096 --seed 42 --boat-model <geometry.json>`。
默认 `--count 2048` 且不传 `--boat-model` 的调用不是 r14；`--out` 使用 `exist_ok=False` 拒绝已有目录。

Blender 入口形式为 `blender --background --factory-startup --python scripts/model_task09_weighing_boat.py -- --out <全新目录>`。
脚本在当前 Blender 场景中清空对象后构造模型，因此适用于独立工厂初态进程；`--out` 同样拒绝已有目录。
以上说明由当前代码核对，不冒充未保存的历史 shell transcript，也不保证重新生成的字节等于 r14。

构建时 `--controller` 读取 SF 的 `balance_force_state.py`、`balance_force_runtime.py`、
`powder_balance_runtime.py`、`task09_powder_runtime.py`，拼接并编译检查后嵌入场景 FlowController；
仪器运行使用内嵌代码。SF 的 `validate_task09_powder.py`、`task09_powder_protocol.py`、
`task09_powder_evidence.py`、`render_task09_powder.py`、`package_task09_powder.py`
分别承接规定轨迹/测量验证、证据门禁、实际状态回放和打包，操作参数见上文 SF 指南。
ConvertAsset 负责物理生产/修复，SF 消费并验收；没有将转换流水线或 simulator SDK 移入 SF core/schema。

## 最终验收证据

SF 证据根为 `/cpfs/user/zhuzihou/dev/scenario-forge/outputs/task09_powder_bottle_r2_20260910/`。
三份数值报告均 `status=passed`、全部 `checks=true`、`engine_errors=[]`、`runtime=4.5.0`、
`solver=PGS`、`physics_dt=1/480 s`、`robot_grasp_verified=false`。
其 `entry_sha256` 和 `scene_sha256` 与本次只读哈希核验的 r14 `scene.usda` 相同：

`c27fe80c056e5316fc1f0e2266b4ac6e9d81861048f24d7f61a82f4919b82c1a`

| 证据 | 已证实结果 |
|---|---|
| [final_settle/report.json](../../../scenario-forge/outputs/task09_powder_bottle_r2_20260910/final_settle/report.json) | 5 s，自然沉降/重开初态；原勺动态；4096 粒留瓶，采样无假底下/桌下泄漏 |
| [final_scoop/report.json](../../../scenario-forge/outputs/task09_powder_bottle_r2_20260910/final_scoop/report.json) | 50 s，规定慢速舀取；持续携带 45 粒并进入舟区域，末瓶内 4051 粒 |
| [final_calibration/report.json](../../../scenario-forge/outputs/task09_powder_bottle_r2_20260910/final_calibration/report.json) | 43 s，0/128/512/1024/0 粒已知载荷、移舟和仪器 reset 均通过 |
| [final_video/visual_review.json](../../../scenario-forge/outputs/task09_powder_bottle_r2_20260910/final_video/visual_review.json) | 已有独立 image-only 审核 `PASS`；12 张互补帧，无阻塞视觉失败，保留裁切/遮挡 caveats |

最终转移质量为 **0.0353429241 g**；末稳定净重 **0.0353592325 g**（约 0.03536 g），
LCD 为 **0.04 g**，显示分度为 **0.01 g**。末段 1 s、30 样本的力读数/区域质量交叉检查
最大差为 `1.63663560e-5 g`。ROI 仅是独立检查，未用来生成天平读数。

已知载荷每个 case 最后 1 s、30 样本，验收要求 valid/stable，误差阈值为 0.01 g：

| 操作 | 期望净重 g | 最大绝对误差 g |
|---|---:|---:|
| 空舟去皮后，0 粒 | 0 | `8.45311625e-6` |
| 128 粒 | 0.100530968 | `3.10646485e-6` |
| 512 粒 | 0.402123871 | `3.99493040e-5` |
| 1024 粒 | 0.804247742 | `2.78948410e-5` |
| 撤粉回零 | 0 | `1.13945662e-5` |
| 移走已去皮舟 | −10 | `2.50509877e-5` |
| 仪器 reset 后空盘 | 0 | 0（该窗口） |

最大误差 **3.99493e-5 g** 仅属于该离散刚体夹具、指定窗口与条件，
不是实物仪器、任意粉末或毫克级准确度认证。单粒质量和 LCD 位数也不代表测量精度。

SF 主记录记载两段视频均为 1280×800、30 fps、1500 帧、50 s，完整解码通过；
回放恢复实际粒子、普通刚体、天平 links、尺度、LCD/灯状态。
视觉任务 `ses_f748b89a6ffeI0OgBWVOs1ee8i` 初审 WARN，补足初态、持料与下落帧后整组 PASS；
最终 JSON 仍说明部分近景裁切柄/勺缘，搬运全景与背景设备重叠，剂量小、下落颗粒稀疏。
本次仅引用已有审核，没有重新做目视或视频解码，也不以视觉判断力学准确度。

## 验证记录与限制

SF 主会话记录此前先写失败行为测试，并报告 `make check`：982 passed、1 skipped，
Ruff、package/suite/Phase10.x smoke 与 diff-check 通过。这是 SF 的既有检查结果，
不能记成 ConvertAsset 三个 producer 测试的运行结果。
本文已核对 `tests/test_task09_powder_bottle.py` 的覆盖范围，但本次不重跑 pytest、Blender 或仿真，
也不补写没有所读执行证据的 producer 测试通过数。

本次文档核对命令与证据：

- `python -B scripts/build_task09_powder_bottle.py --help`：退出 0；仅核对 CLI，不加载 `pxr` 或启动 SimulationApp。
- `sha256sum`：只读核对两个原 ZIP、r14 场景/配置/舟模型及四份 SF 最终 JSON；场景身份如上。
- `git diff --check -- docs/records/2026-09-10-task09-powder-bottle-r2.md docs/records/README.md`：退出 0；
  新建未跟踪记录另经 `python -B -c '…'` 标准库检查 UTF-8、行尾、末尾换行、标题/围栏及 5 张表格的 38 行结构，均通过。
- 标准库只读检查：本记录 16 个本地 Markdown 链接及 README 新增的 1 个链接目标均存在；
  三份报告状态/全部 checks/场景哈希/runtime/dt/时长、r14 的 4096 个根 Xform、舟字段和已有视觉 JSON 均通过核对。
- README 去掉新增的一条链接后，SHA256 仍为编辑前工作副本的
  `cff8128d7a101f214bcc4f113536ca217addd41aa84d7362b031dd56957aa7ab`，已有索引内容逐字节保留。
  两个 producer 脚本、测试、r14 场景/配置/舟 JSON/BLEND 及 SF 主记录的 SHA256 前后相同；
  排除本次两文件后的其他已跟踪工作树 diff 哈希前后也相同。

限制与后续适用范围：

- 4.5 最终夹具通过不覆盖 4.1、VR loader、Lift2/机器人抓持、真实按钮接触操作或完整策略成功。
- 有限采样无泄漏不意味着连续时间、任意姿态/轨迹都不穿透；改变粒径、密度、工具、求解器或 runtime 后需要匹配的新证据。
- 这是未做实物标定的干颗粒代理，不包含黏聚、湿度、静电等真实粉末资格；早期故障的底层引擎根因仍未由本轮单独确认。
- 50 s 舀取记录墙钟为 517.8036 s，物理步 p50 18.7242 ms、p95 38.3955 ms；未达实时，机器并发负载会影响墙钟结果。
- `TARE`/`reset_requested` 清除测量/去皮/仪器状态，不搬回物体；完整物理重置须重开初始场景并重建 view。
- 最终消费者包、对象清单和 ZIP 身份由 SF 交付 manifest 绑定；本文只绑定已核对的 producer 与验收证据，不生成或改写交付包。

规范依据为当前 SF 工作树的[资产接入 ASSET-001/003/006](../../../scenario-forge/docs/standards/asset-intake.md)、
[状态 STATE-002/003/007](../../../scenario-forge/docs/standards/task-state.md)、
[验证 VAL-001/002/003/005](../../../scenario-forge/docs/standards/validation-and-delivery.md)及
[维护流程](../../../scenario-forge/docs/standards/maintenance.md)。SF 同期记录已说明 SDF 朝向/内外验证、
引擎报错后旧状态不能算通过的同步。本次 producer 文档没有新增通用规则，**规范无需另行变更**；
上述数值只作为该案例事实，核心包/schema/API 契约和历史任务包不由本日期记录重定义。
