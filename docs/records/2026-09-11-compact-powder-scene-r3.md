# Task09 r3：Blender 紧凑粉末瓶集成与生产者场景验证

Git 收尾补充（2026-09-11）：用户授权提交 r2/r3 基线。仅含拟提交源码的独立 index 快照执行
`python -m pytest -q tests/test_task09_powder_bottle.py tests/test_compact_powder_bottle.py tests/test_compact_powder_scene.py`，
16 passed，七个相关源码/测试文件 Ruff 通过。详情见
[跨仓收尾记录](../../../scenario-forge/docs/records/2026-09-11-task09-r3-git-closeout.md)。

日期：2026-09-11；产物目录沿用任务开始日 `20260910`。
本记录补齐 [Blender 源模型 model_r1/model_r2 记录](2026-09-10-compact-powder-bottle-model.md)
之后的生产者集成证据：将紧凑薄口瓶 `model_r2` 和更深的独立刚体粉床接入原 task09 场景。
**生产者集成、静态审计和 Isaac Sim 4.5 规定工具轨迹验证已通过**；本记录不宣布最终视频或 handoff 完成。

## 调查、分工与规范依据

文档核对了 ConvertAsset `AGENTS.md`、`CLAUDE.md`、`.codex/file-ownership.md`、
`.codex/agents/docs-writer.md`、对应 `.claude` 角色及 `.codex` memory，随后读取
[`scripts/build_compact_powder_scene.py`](../../scripts/build_compact_powder_scene.py)、
[`tests/test_compact_powder_scene.py`](../../tests/test_compact_powder_scene.py)、原模型记录、候选配置、静态检查、重建日志及运行汇总。
Scenario Forge 的 [r3 任务记录](../../../scenario-forge/docs/records/2026-09-11-task09-powder-bottle-r3.md)
只作为集成上下文；其中尚待回填的运行/检查结果以本次读取的实际 JSON 和完成日志为依据。

ConvertAsset 生产者负责模型几何、局部凸碰撞、质量/惯量、USD 场景及独立颗粒配置；
Scenario Forge 主实现者负责规定工具动作、仪器受力逻辑、运行验证、视觉与最终打包。
本次 docs-writer 仅新增本记录、最小导航和旧模型记录末尾的前向链接；源码、配置、输出及其他工作树修改均由原所有者维护。
本次未启动 Isaac、未派生 agent、未提交或推送；用户精确写入范围优先于默认 memory 更新与提交要求。

规范依据：Scenario Forge 基线 `90bfc13d578769b1061d3ba7984735d872814593`（`90bfc13`），
规范库初始整理基线 `2a61514`；ConvertAsset 调查基线 `3240ca3e4a445b2c241629a6dc93345b98951048`。
已读规范入口、资产接入、验证与交付和维护流程，适用：

- [ASSET-001](../../../scenario-forge/docs/standards/asset-intake.md#asset-001)：生产者与消费者职责分离。
- [ASSET-003](../../../scenario-forge/docs/standards/asset-intake.md#asset-003)：粒径、碰撞、惯量和运行时变更须按新组合验证。
- [VAL-001](../../../scenario-forge/docs/standards/validation-and-delivery.md#val-001)、
  [VAL-002](../../../scenario-forge/docs/standards/validation-and-delivery.md#val-002)、
  [VAL-003](../../../scenario-forge/docs/standards/validation-and-delivery.md#val-003)：分别声明静态/运行时/视觉层，按变更验证并绑定实际字节。

**规范无需变更**：本次仅增加任务专属尺寸、粒数、240 Hz 配置与实测证据，不形成任意容器或粉末的通用规则。
按 [维护流程](../../../scenario-forge/docs/standards/maintenance.md)，本记录同步生产者设计理由、操作命令和日期证据；
消费者设计、操作与视觉/交付说明由主实现者同步。历史模型记录的原有声明和哈希不追写成新运行资格。

## 来源与目录身份

以下缩写均为本机外部证据定位，不是可分发包内路径：

| 缩写 | 精确绝对路径 |
|---|---|
| `CA` | `/cpfs/user/zhuzihou/dev/ConvertAsset` |
| `SF` | `/cpfs/user/zhuzihou/dev/scenario-forge` |
| `P`（生产者输出根） | `/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910` |
| `E`（运行证据根） | `/cpfs/user/zhuzihou/dev/scenario-forge/outputs/task09_powder_bottle_r3_20260910` |
| `B`（不可变 r2 基础） | `/cpfs/user/zhuzihou/dev/scenario-forge/outputs/task09_powder_bottle_r2_20260910/handoff/task09_powder_bottle_r2` |

最终被验证的候选入口为 `P/candidate_r2/scene.usda`，配置为同目录 `scene_config.json`；
模型入口为 `P/model_r2/geometry.json`，可编辑源为同目录 `bottle.blend`。
`candidate_r2` 是 r3 任务内的第二个候选，不能与不可变 r2 handoff `B` 混淆。
候选配置仍保留 `status="candidate"`，运行通过不自动将其改为最终交付包。

`P/model_r1`、`P/model_r2`、`P/candidate_r1`、`P/candidate_r2`、`P/rebuild_check` 及
`E/settle_r1`、`E/final_settle`、`E/scoop_r1`、`E/final_calibration` 分别保留各轮文件输出；
原 r2 handoff 和历史产物字节保留，不以新结果覆盖失败证据或旧模型。

## 生产者实现与三维度审核

### 架构：新模型接入原场景

`scripts/build_compact_powder_scene.py` 从 `B/scene.usda` 克隆根层，仅替换瓶与粉粒根，
复制 `SubUSDs/`、`source_boat/`、`deps/balance/`、`deps/table/`，并把模型目录复制为 `source_bottle/`。
它使用模型 JSON 的 `visual_meshes`、`colliders`、`inner_profile` 和质量属性；`pxr`、NumPy 在 `build()` 内加载。
原勺、原场景五颗大固体、台面资产、修复天平和 r2 称量舟沿用来源；原勺初态仍在烧杯内。
保存原对象变换，并从原勺实际网格计算 `spoon_floor_envelope`，供消费者深瓶动作使用。
没有把模拟器 SDK 引入 Scenario Forge 纯包层，也没有复制通用 USD/MDL/mesh 转换实现。

| 项目 | 最终生产者配置 |
|---|---|
| 外形/通口 | 60×60×100 mm；最小通口 ID 48 mm，口沿最大 OD 54 mm |
| 薄壁/顶冠 | 直身壁厚 1.8 mm、颈壁约 2.2 mm；顶冠 ID/OD 49.8/51.4 mm |
| 固定内托 | 瓶局部 z=57–59 mm，厚 2 mm；下部保留空腔 |
| 瓶根 | `/World/obj_powder_bottle`，唯一动态 RB + MassAPI，scale=1 |
| 瓶壳和内托质量 | 共用根质量 `0.04851802575359416 kg`，约 48.518 g |
| 瓶碰撞 | 258 个独立 child Mesh 凸片：256 壁块、底板、内托；各自 `convexHull` |
| 瓶接触 | 每凸片 contact offset 0.05 mm、rest offset 0；绑定粉末接触材质 |
| 粒子根 | `/World/obj_powder_grain_00000` 至 `/World/obj_powder_grain_16383`；每个独立 `obj_*` Xform 上唯一 RB + MassAPI，子 `Mesh` 承担碰撞 |
| 默认粒数/粒径 | 16,384；等体积球直径 1.4 mm（`radius=0.0007 m`），ico 外包半径约 0.8274 mm |
| 密度/质量 | 1500 kg/m³ 工程代理；每粒生产者质量 `2.155132560362598e-06 kg`，总量约 35.3097 g |
| 物理/随机种子 | PGS、240 Hz、32 次位置迭代；seed=42 |

视觉薄壳与内托保留独立网格，各凸片保持同一瓶根的子形状，不能把整瓶合成一个凸包或给凸片另加刚体。
USD 生产者为壳体写 vertex normals 和任务用 UsdPreviewSurface 材质；Blender 静态预览仅证明其原模型范围，
不能替代新 USD 全场景的视觉验收。

### 完整性：尺度、填充和来源保留

质量由 `1500 × 4πr³/3` 计算；基准半径 0.5 mm 的惯量按 `(r/0.0005)^5` 缩放。
即根质量按 `r³`、根惯量按 `r⁵` 随几何尺度变化，不能只放大子 Mesh。
运行报告最小对角惯量为 `4.270791348608832e-13 kg·m²`。
瓶质量、质心与主惯量来自模型视觉实体积分，避免重复计算重叠凸片质量。

填充使用内轮廓插值和 HCP 风格排列，间距为 `2 × grain_bound + 0.14 mm`，
壁面初始化余量为 `0.75 mm + grain_bound + 0.12 mm`，并施加每轴 ±0.01 mm 的确定性抖动。
0.75 mm 是几何初始化余量，不是 contact offset；容量不足显式失败。
最终床深由沉降状态量测，不把初始化层高当作通过证据。

`E/static_validation.json` 为 PASS：16,384 个颗粒根结构、粒质量/尺度及 258 瓶凸片通过；
**19 个未替换原对象的 authored 根层子树及全部复制依赖文件字节与来源一致**，不止是位姿一致。
闭包检查为 **5 个 USD layers、19 个 assets，无缺失或包外依赖**。
这属于候选场景静态闭包，不等同于最终 ZIP、视频或异目录解压验证。

### 风险：重新验证与确定性重建

首个 `P/candidate_r1` 为 14,336 粒，8 s 沉降后约 9.6 mm，未满足 10–12 mm 深度要求；
保留 `E/settle_r1/report.json` 失败证据。第二候选只把粒数提升至 16,384 后获得最终床深结果，
不继承旧 r2 的 480 Hz 细粒资格。

早期 builder 在打开输出 Stage 时，先尝试解析稍后才删除的旧瓶引用，产生短暂 missing-old-bottle warning。
最终源码改为在打开输出 Stage **之前**通过 `Sdf.BatchNamespaceEdit` 删除旧瓶和旧颗粒的 prim specs；
删除失败显式抛错。`E/rebuild.log` 记录用最终默认参数独立生成 `P/rebuild_check`，旧瓶警告已消失。
只读 SHA 核对确认重建与被验证候选的 `scene.usda` 字节相同，均为
`ec3cffc76cf32dabc714dd3b893c9a82cb32aac0715d690433188a0c6c9b3141`。
这里的确定性结论针对场景文件；不宣称所有配置或日志文件也逐字节相同。

## 已完成的联合运行证据

权威汇总为 `E/qualification_summary.json`，状态 `passed`。
三份原始报告均由 `scripts/task09_powder_evidence.py::validate_report(report, scene_hash, mode, cfg)`
使用 `P/candidate_r2/scene_config.json` 验证，分别为 settle **8 s**、scoop **50 s**、calibration **43 s**。
本次文档核对又以普通 Python 只读验证了这三份报告；没有重跑模拟器。
汇总省略原始 `rows` 和 `observed_body_paths`，以 `last_row` 保留最后一行；其所列字段与原报告一致。

共同条件：Isaac Sim **4.5.0**（requested runtime `45`），PGS，`physics_dt=1/240 s`，
authored 240 Hz；World manager dt 为 1/60 s，两者不能混用。
无 position-iteration override、无 wake-all override；全部 checks 为 true，`engine_errors=[]`，
`robot_grasp_verified=false`，场景与入口哈希均绑定上述最终候选。

### 沉降与舀取

- `E/final_settle/report.json`：184 个有效列，粉床深度 median **10.5604757181 mm**，
  p10 **10.2350880018 mm**、p90 **10.8623792043 mm**；16,384 粒全部留在瓶内，内托下/桌下均 0。
  床深是瓶局部 XY 的 4 mm 网格列（避开壁边、每列至少 5 粒）最高粒心加外包半径相对内托顶面的统计，
  不表示粉面处处等厚。
- `E/scoop_r1/report.json`：原勺规定动作在 33–35 s 搬运窗口有持续留料，最终舟内 **54 粒**、瓶内 **16,330 粒**，
  内托下/桌下均 0。舟内区域核验质量 `0.1163771448773332 g`；受力净读数
  `0.11639796889062026 g`（约 **0.116398 g**），LCD **0.12 g**，valid/stable/tared 均 true。
  最后稳定核验窗口 30 samples，最大绝对误差 `2.082401328706851e-05 g`，读数范围 `3.944506815400928e-06 g`。

仪器读数来自秤盘世界竖直接触力/冲量，使用实际物理步长、1 s 积分窗、0.25 s 低通和去皮；
**区域粒数只用于独立质量核验，不驱动读数**。初始床内的 spoon-region count 不能证明搬运，
必须同时看抬离后的持续留料与舟内转移。显示分度 0.01 g 不等于实物计量精度资格。

### 完整校准、卸载与重置

`E/final_calibration/report.json` 独立运行 43 s，载荷序列为 **0、46、186、371、0 粒**，
随后移走已去皮的 10 g 舟并重置仪器。所有窗口均 30 samples，全部 passed：

| 窗口 | 期望净质量（g） | 最大绝对误差（g） | 读数范围（g） |
|---|---:|---:|---:|
| 初始空载，0 粒 | 0 | 5.670474848784579e-06 | 5.973976211492982e-07 |
| 46 粒 | 0.09913609528666711 | 1.916866455431432e-05 | 2.7695261017868233e-07 |
| 186 粒 | 0.40085464615913224 | 1.4194814934143096e-05 | 1.118399350019672e-06 |
| 371 粒 | 0.7995541598120326 | 5.792663507797613e-05 | 2.2202899593537495e-05 |
| 再次空载，0 粒 | 0 | 5.717125256765598e-06 | 1.3971375771859584e-06 |
| 移走已去皮称量舟 | -10.0 | 2.019991821811118e-05 | 1.439892249699426e-05 |
| 仪器重置 | 0 | 0 | 0 |

校准使用显式位置变更，`calibration_teleport_ccd_reset=true`；它验证已知载荷与仪器状态，不提供额外舀取证据。
最终 16,384 粒回到瓶内，内托下/桌下均 0；gross/net/tare 均 0，valid/stable=true、tared=false，LCD `0.00 g`。

报告保留实际执行时的 validator 身份：settle/calibration 为
`f3b88e5fe791644e39caeb511fe6a6328d837c46a002f37fd171698e7b33d8b3`，scoop 为
`8e5ffaade559b144150484c0b4a9a083396927418d5c68d92da5b76deb4e54fe`；
共同 protocol SHA 为 `a8ddb3bde049fa4c5ff481691741d74a9a01a237392b5935a8319654730aac16`。
舀取后仅收紧独立 settle 的床深上限至 12 mm，该改动不进入 scoop 路径；没有回写旧运行报告的 validator 哈希。

### 测得的离线性能范围

| 模式 | 仿真时间（s） | 记录循环 wall seconds | step p50（ms） | step p95（ms） |
|---|---:|---:|---:|---:|
| settle | 8 | 179.09656 | 40.24052 | 62.02488 |
| scoop | 50 | 677.97716 | 44.39785 | 61.01928 |
| calibration | 43 | 669.99784 | 50.55081 | 72.29892 |

这些是当前场景、机器及验证循环的测量，wall 时间不含全部启动和保存成本；step 统计也不能替代端到端耗时。
50 s 仿真约需 678 s 记录循环墙钟时间，明确为**非实时**。性能不能外推至其他硬件、粒数、连续多勺或交互式 VR。

## 命令与测试证据

以下为生产者/主实现者已执行命令的复现形式，本次文档任务没有执行构建或模拟器。
在 `CA` 根目录，用提供 `pxr` 的 Python 运行；`rebuild_check` 已有独立重建证据，
复跑须把 `--out` 换为新的目录，脚本 `exist_ok=False`，不删除既有输出：

```bash
./scripts/isaac_python.sh scripts/build_compact_powder_scene.py \
  --base /cpfs/user/zhuzihou/dev/scenario-forge/outputs/task09_powder_bottle_r2_20260910/handoff/task09_powder_bottle_r2 \
  --model /cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910/model_r2/geometry.json \
  --out /cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910/rebuild_check

python -m pytest -q tests/test_compact_powder_bottle.py tests/test_compact_powder_scene.py
python -m ruff check scripts/model_compact_powder_bottle.py scripts/build_compact_powder_scene.py \
  tests/test_compact_powder_bottle.py tests/test_compact_powder_scene.py
```

生产者测试 **13 passed**，四个源码/测试文件 Ruff 通过（主实现者交接结果）。
新增场景测试覆盖确定性内腔填充、间距/余量、容量拒绝及质量/惯量尺度；
模型/LOD 测试覆盖闭合凸性、薄壁空腔、质量、clearance 和 model_r1 不变量，红阶段见原模型记录。
这些普通 Python 测试不替代实际 USD 结构与联合运行检查。
ConvertAsset 没有 `Makefile`，没有本仓 `make check` 目标。

在 `SF` 根目录，目标 Isaac Sim 4.5 Python 安装位置按本机调整；运行输出同样选择新目录：

```bash
/isaac-sim/python.sh scripts/validate_task09_powder.py \
  --root /cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910/candidate_r2 \
  --out outputs/task09_powder_bottle_r3_20260910/final_settle --mode settle --seconds 8
/isaac-sim/python.sh scripts/validate_task09_powder.py \
  --root /cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910/candidate_r2 \
  --out outputs/task09_powder_bottle_r3_20260910/scoop_r1 --mode scoop --seconds 50
/isaac-sim/python.sh scripts/validate_task09_powder.py \
  --root /cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r3_20260910/candidate_r2 \
  --out outputs/task09_powder_bottle_r3_20260910/final_calibration --mode calibration --seconds 43
```

Scenario Forge 已完成 `make check`：**986 passed, 1 skipped in 392.98s**，
Ruff、package smoke、suite quality、strict phase10x 和 `git diff --check` 均通过，
依据 `E/make_check_retry.log`。首轮受工具 240 s 时限中断，完成结果来自增加时间预算后的重跑，非首轮成功声明。

## 文件哈希

下表为本次只读 `sha256sum` 核对的 SHA-256，路径缩写按前文绝对根展开：

| 文件 | SHA-256 |
|---|---|
| `CA/scripts/build_compact_powder_scene.py` | `8130efce38f3f391a6ae8146c1bcb6a7ba3120d09b249db511b825d5b5d20865` |
| `CA/tests/test_compact_powder_scene.py` | `be387180e36883b7710a98767526cb77dc54e571fcf0def77caeb5f89a04518f` |
| `CA/scripts/model_compact_powder_bottle.py` | `ffcd794d4ef7b05682d7148736649d328668fa29b60556f30e1d52fdfa75e118` |
| `CA/tests/test_compact_powder_bottle.py` | `f5f5ccbba21dc9de09c4a35d33cf52d1098b0ca4f9dbb8450a6584e22acbba06` |
| `P/model_r2/geometry.json` | `1faef532b41c1eddbe629ced7ca52109c5211b1d7996aaba507d3be9fb8a70a9` |
| `P/model_r2/bottle.blend` | `ef3f1bce668874d85ab9f4460f501ad28a5294fbaa139fbad5a8c702d6fbeeaf` |
| `B/scene.usda` | `c27fe80c056e5316fc1f0e2266b4ac6e9d81861048f24d7f61a82f4919b82c1a` |
| `P/candidate_r2/scene.usda` | `ec3cffc76cf32dabc714dd3b893c9a82cb32aac0715d690433188a0c6c9b3141` |
| `P/candidate_r2/scene_config.json` | `86762d8b8ef6af352373d7daa94d9fc4ad94dea38d5fdd982c9ce30912d952eb` |
| `P/rebuild_check/scene.usda` | `ec3cffc76cf32dabc714dd3b893c9a82cb32aac0715d690433188a0c6c9b3141` |
| `E/static_validation.json` | `d0635305f71008bb6b42803dca9525da346aae97e786a91d9ce6616d2c9757b6` |
| `E/rebuild.log` | `d852222b8d3f3c9caf9bd85184a31b810ae4c5ab0290e17906645d8c98dcea5e` |
| `E/qualification_summary.json` | `58abb0cef105b1e3cfa3e8c8f50cba1fbcc184b6e188f27e6366ae44d95aadba` |
| `E/final_settle/report.json` | `8626ec7ad057cea4e759b457f2a8670dc51e58efa6f45c1d3b4e1f4e181eb5b7` |
| `E/scoop_r1/report.json` | `74f43055713886e66b092ea1b2bcc89e3df65949d48e1d1bbbf3a8dda58803ff` |
| `E/final_calibration/report.json` | `600899851bcc198bf14efcc276ff5ccaa2071a40e4dc9391f2f5f1399395b866` |

生产者双精度总质量为 `35.309691868980806 g`，运行张量报告为 `35.309694707393646 g`；
保留各自原数值及浮点表示范围，不把微小差别改写成统一的历史数值。

## 剩余限制与文档验收

本轮资格仅为 **kinematic prescribed-tool scene fixture**：颗粒接触转移和仪器受力均在该规定动作中验证，
不包含真实粉末黏聚物性、机器人抓持/策略、VR、Isaac 4.1 或连续多次舀取的一般资格。
1500 kg/m³ 是工程密度代理，不能据此声明实物粉末一致性。
静态空瓶预览、数值运行与最终场景视频/交付为不同证据；最终视频、视觉逐阶段审查及 handoff 包仍由主实现者完成。

本次文档验收采用源依据核对、三份报告的 cfg-aware 只读校验、所列文件 SHA 核验、
新增 Markdown 链接/显式规则锚点检查，以及 scoped `git diff --check`。
结果：13 个新增链接与 5 个显式规则锚点全部有效，16 项文件 SHA-256 全部匹配；
三份报告与汇总所列字段逐项一致（`last_row` 对应原报告最后一行）。
旧模型记录仅追加前向链接，原正文前缀 SHA-256 保持
`993da5275cd9bdb7aae54854b19de4ca9ae393ce16c6378c7745e37c609eef27`；
索引只插入本记录导航，保留已有其他任务条目。文档任务无阻塞；最终包装完成状态不在本记录验收范围内。

## 最终交付后续同步（2026-09-11）

主实现者现已完成 Scenario Forge 交付，详情及视觉限制见
[SF r3 正式日期记录](../../../scenario-forge/docs/records/2026-09-11-task09-powder-bottle-r3.md)。
本节仅追加最终阶段结果；前文“待完成”等阶段性陈述、历史证据及哈希原样保留，资格边界不扩大。

- 回放快照载入优化后的最终 `make check`：**987 passed、1 skipped，295.63 s**；Ruff、smokes、phase10x、diff 检查通过。
- 独立选帧审查 **21 张图片，WARN、无阻塞问题**；两路视频均为 **1280×800、1500 帧、30 fps、50 s**，完整解码通过。
  选帧审查不等于逐帧人工审核。
- canonical ZIP：`/cpfs/user/zhuzihou/dev/scenario-forge/outputs/task09_powder_bottle_r3_20260910/handoff/task09_powder_bottle_r3.zip`，
  **703,547,355 bytes**，SHA-256 `e1ac66ae061a1706951f70e3364e3d5c30c6e94f44ffcdae59f6a90d3dd0235b`。
  包资格为 `scene_fixture_verified`，清单含 **199 个文件哈希**；scene SHA 保持前文
  `ec3cffc76cf32dabc714dd3b893c9a82cb32aac0715d690433188a0c6c9b3141`。
- 异目录 `/tmp/opencode/task09-r3-delivery-check/task09_powder_bottle_r3` 的哈希与闭包检查通过；
  移除继承的 `PYTHONPATH` 后，用包内验证器执行 Isaac 4.5 **8 s settle** 通过：median **10.56048 mm**、
  **16,384 粒全部保留、无引擎错误**。证据为 `E/relocated_static_check.json` 和 `E/relocated_settle/report.json`。
- 原 r2 的 **181 个文件哈希**复核通过，见 `E/r2_preservation_check.json`；历史 r2 字节保留。
