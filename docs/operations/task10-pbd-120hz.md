# Task10 原生 120 Hz PBD 冻结产物操作说明

本说明用于消费 Task10 revision16 冻结产物及复核生产者静态冷启动资格。
Isaac Sim 4.1、4.5 各自独立运行 30 秒通过；该证据不包含完整滴定、VR 操作或视频验收。
实验历程、最终参数、哈希和完整重建命令以
[2026-10-10 生产者记录](../records/2026-10-10-task10-pbd-120hz.md)为准。

## 产物入口与不可变边界

以下路径均相对 ConvertAsset 根目录：

| 内容 | 路径 |
| --- | --- |
| 冻结目录 | `outputs/task10_pbd_120hz_motion_20261010/snapshots/native120_prebalanced_16/` |
| Isaac Sim 4.1 入口 | 冻结目录下 `package/isaac41.usda` |
| Isaac Sim 4.5 入口 | 冻结目录下 `package/isaac45.usda` |
| 参数与运行契约 | 冻结目录下 `manifest.json` |
| 90 个 payload 文件清单 | 冻结目录下 `snapshot_hashes.json` |
| 封存回执 | `outputs/task10_pbd_120hz_motion_20261010/frozen16_receipt.json` |
| 外部冷启动回执 | `outputs/task10_pbd_120hz_motion_20261010/cold16_receipt.json` |
| 运行环境与已执行冷启动命令 | `outputs/task10_pbd_120hz_motion_20261010/HANDOFF_120_motion_final.md` |

引用匹配运行时的入口及其 `/World`，保持完整相对依赖树。不要只抽取可见液面或重新采样。
源绑定是 `/mnt/data/chenjiantong/scene_usd/task_10_titration_experiment/scene.usd`
及其本地依赖；使用 manifest 的源哈希、物理签名和运行契约签名检查身份。
`runtime_configuration_sha256` 绑定物理配置与完整运行契约，不能用旧 240 Hz 证据替代。
原始源场景、旧 `outputs/task10_pbd_20261009/` 和本次 91 文件冻结内容均保持不可变。
新实验写入新目录，外部验证回执不回写已冻结 manifest。

旧 revision09 的静态资格与失败历史保留在生产者记录和旧输出树；它没有通过后续运动要求。
当前 revision16 共 90 个 payload 文件加清单，合计 91 文件。旧 revision09 共 93 文件
（92 个 payload 加清单），计数口径不能混用。

## 必须消费的运行条件

主配方从冻结 manifest 读取，不在 consumer 手写第二份参数。关键检查条件如下：

- 真实原生物理步长为 `1/120 s`，PhysicsScene 为 `120 Hz`；记录原生 callback 的
  count/min/max/sum、World dt 和 Scene Hz。仅传入 `simulate(dt)` 不是时钟证据。
- GPU dynamics、GPU broadphase、TGS 与粒子 CCD 按 manifest 启用。
  各系统保持 64 次 position iterations，Scene min/max 均为 64。
- Scene 的 `gpuFoundLostAggregatePairsCapacity` 和 `gpuTotalAggregatePairsCapacity`
  都设为 8192，并读回实际值。对应 manifest 字段为
  `scene_gpu_found_lost_aggregate_pairs_capacity` 和
  `scene_gpu_total_aggregate_pairs_capacity`。
- 干净入口的 simulation owner 未绑定；host 创建实际 PhysicsScene 后绑定所有粒子系统，
  保留 `/World` 下的粒子、完整碰撞与材质依赖。不能增加重复场景或遗漏液体 owner。
- 保留全部 **155,658** 粒子：Source 9,281、Receiver 85,247、DeadPrecharge 61,130，
  Falling 初始为空。冻结回执确认三组所有粒子均保留实测非零速度。
  不删点、搬回越界点、清零速度或冻结液面；重表达容器姿态只能对整组做同一刚体映射并旋转速度。
- `physics:mass` 表示整组总质量。受控转移变更粒子数时，按 manifest 的质量量子同步更新，
  points、velocities、widths、ids 一起维护。静态资格不证明动态转移已合格。
- 读取实际粒子位置；producer 不作者 SDK 只读的 `simulationPoints`。
  保持 USD/particle/velocity readback 开启、`suppressReadback=false`，并记录 getters。
  历史 4.1 bootstrap 故障没有被唯一归因于这些设置。

夹具开口碰撞修复、Source 短凸壁、原阀座区间内解析 cap 都属于已冻结物理配置。
不要删除修复或通过 fluid collision filtering 绕过接触，也不要降低 64 次迭代或容量来
迁就 host 默认值。Receiver 另有 1,600 个沿原腔体轮廓的凸壁分块及原平底高度 3.684 mm 的盘形碰撞；
壁 rest/contact 为 1.5/1.75 mm，底盘为 0.6/1.6 mm，Receiver fluidRest 为 838 µm，
Source 保持 933.5 µm。Source/Fine recipe 保持，原 SDF 和可见几何保持。
这些是冻结 manifest 的消费检查摘要；完整参数和精确重建命令以记录为准。

## 全程验收与回执复核

冷启动使用同一份冻结初态，两版本分别新进程运行，不传 `--seed-state`、不做逐版本粒子修正。
当前资格包含每版本 3,602 个原生步（包括两步 reset/bootstrap）、每步三组零越界、
零 PhysX 错误，以及每组 902 个液面采样全部通过。Source/Receiver 液面容差 ±2 mm，
DeadPrecharge ±0.5 mm；腔体容差分别为 150 µm 和 50 µm。不能只检查最后一帧或尾部零越界。
每版本 3,600 次 post-step/post-fetch 粒子和真实 body pose 比较完全一致。
全程液面范围与尾 10/20 秒漂移均保存在回执，不能把有限窗口结论写成无限时稳态保证。

在 ConvertAsset 根目录执行下面的 CPU 只读检查，可复核当前落盘资产与回执绑定；
输出树迁移后应使用迁移后的根目录，并继续按相对路径匹配文件：

```python
import hashlib
import json
from pathlib import Path

root = Path("outputs/task10_pbd_120hz_motion_20261010")
receipt = json.loads((root / "cold16_receipt.json").read_text())
snapshot = root / "snapshots/native120_prebalanced_16"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

inventory = json.loads((snapshot / "snapshot_hashes.json").read_text())
assert len(inventory) == 90
full_hashes = receipt["snapshot_hashes"]
assert receipt["snapshot_file_count"] == len(full_hashes) == 91
actual = {
    str(path.relative_to(snapshot))
    for path in snapshot.rglob("*")
    if path.is_file()
}
assert actual == set(full_hashes)
assert set(inventory) == actual - {"snapshot_hashes.json"}
for relative, digest in full_hashes.items():
    assert sha(snapshot / relative) == digest, relative
for relative, digest in inventory.items():
    assert full_hashes[relative] == digest
assert sha(snapshot / "manifest.json") == receipt["manifest_sha256"]
assert sha(snapshot / "package/pbd.usda") == receipt["pbd_sha256"]
for runtime, evidence in receipt["cold"].items():
    report = root / "probes" / f"cold{runtime}_prebalanced16" / "report.json"
    assert sha(report) == evidence["report_sha256"]
    assert evidence["all_native_step_containment_zero"]
    assert all(item["all_within_unchanged_tolerance"]
               for item in evidence["all_static_surfaces"].values())
    assert not json.loads(report.read_text())["physx_errors"]
assert receipt["status"] == "qualified_static_cold_native120_sdk41_sdk45"
print("91 frozen files and both cold reports verified")
```

哈希检查证明当前文件与该回执一致；重跑物理验证需要对应 Isaac SDK 和 GPU。
复核外部回执本身的预期哈希时，使用生产者记录中的最终哈希表。

## 重建与资格边界

精确重建命令在
[生产者记录的 Current immutable identities and rebuild command](../records/2026-10-10-task10-pbd-120hz.md#current-immutable-identities-and-rebuild-command)。
该命令同时指定源、native 120 Hz、碰撞修复、参数 profile、完整实测 state 和配对 settling
report。本说明不再复制一套标量参数或重建命令。执行重建时必须改用新的输出目录，
不得覆盖已封存 revision16；导入成功后仍需两版本独立冷启动与新回执。

wall14 使用 Receiver 848 µm 和另一初态，通过了独立运动探针；该结果不能替代
revision16（838 µm）的完整运动验证。revision16 当前仅双版静态 cold 通过；
`main41_full16`、`main45_full16` 在运行，未在此宣称通过。

完整滴定、目标外滴落、入瓶承认、停流/复位/过量、受限 VR 搬动（固定 2 秒晃动后沉降）、
可移植交付与最终视频由 consumer 另行实证。生产者静态通过不代表上述资格。

无需修改全库通用设计契约：本次扩展的是 Task10 专用 producer 脚本及其任务运行契约，
`--physics-hz` 的历史默认仍为 240，全库资产接口和通用液体 recipe 未被改写。
本操作说明和日期化记录共同保存任务范围；不能把该资产的 4.1/4.5 静态证据推广到其他几何。
