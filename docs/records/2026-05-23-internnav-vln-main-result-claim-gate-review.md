# 2026-05-23 InternNav VLN Main-Result Claim Gate Review

## Context

The active ACL goal is to turn the InternNav / DualVLN downstream route into a
main-result-level experiment, not just a protocol smoke test. This review
records the current claim boundary, the evidence required to promote the result,
and the video policy for paper-quality qualitative comparisons.

## Current Story

ConvertAsset is not only an asset conversion tool in the paper story. The ACL
question is whether a material/texture conversion that preserves scene geometry
still preserves the visual conditions that embodied language agents rely on.

The current VLM grounding results support the first half of that story:
target-centered image pairs can remain task-readable while still exposing
material and coordinate-protocol sensitivity. InternNav extends the same concern
to embodied downstream behavior: for the same scene, instruction, start, and
goal, changing the material representation may change how the navigation agent
acts.

The one-episode InternNav smoke already proves the route is executable and
produces real embodied metrics. It does not yet prove a statistically stable
navigation-performance claim.

## Current Gate Status

The main-result gate is not open yet.

The repository currently has:

- one real paired InternNav smoke episode;
- a prepared `acl_main_pilot30` dataset with 30 episodes across six ready
  scenes;
- a repaired `acl_main_pilot30` work root with scene dependency sidecars;
- no modified-side `acl_main_pilot30` result yet;
- no pilot30 per-episode JSONL extraction or paired analysis yet;
- no paper video frames or mp4 artifacts yet.

The current one-episode smoke supports only a downstream sensitivity example:
both original and no-MDL failed with `SR=0` and `SPL=0`, while the no-MDL run had
larger `TL` and `NE`. That can be written as a failure-case seed, not as a broad
benchmark conclusion.

本轮 `acl_main_pilot30` 的运行记录里也出现过两类无效实验启动：
第一类是资源准备失败，第二类是旧 LMDB 断点污染。它们都不能被写成
downstream 结论，只能作为工程踩坑和运行门禁记录。

## Promotion Criteria

Minimum pilot-main criteria:

- at least 30 paired episodes;
- at least five scenes;
- completed original and modified aggregate `result.json` files;
- per-episode JSONL for both conditions;
- paired statistics with SR/SPL/NE/TL/OS/StR/FR deltas;
- failure-pair taxonomy;
- selected-case video reruns or a documented reason that video failed;
- manifest-level proof that original and modified conditions share the same
  instruction, start, goal, and navigation geometry.

Preferred ACL main-result criteria:

- 100+ paired episodes;
- 10+ scenes;
- repeat or seed-control check for representative episodes;
- representative qualitative videos covering multiple case types;
- explicit limitations if success metrics remain all-zero.

If pilot30 still has nearly all failures, the paper claim should be phrased as
embodied trajectory/failure sensitivity, not as a success-rate or SPL benchmark.

## Video Policy

Metric runs should keep video disabled:

```text
eval_settings["vis_output"] = False
agent.model_settings["vis_debug"] = False
```

This keeps 30+ episode runs storage-bounded and avoids requiring video codecs in
the main metric loop.

Paper videos should be produced only after metrics identify representative
cases. The selected rerun configs should use a new task name and enable:

```text
eval_settings["vis_output"] = True
agent.model_settings["vis_debug"] = False
```

InternNav's visualization path is expected to write under:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/<task>/video/<trajectory_id>/frames/*.png
/cpfs/user/zhuzihou/dev/InternNav/logs/<task>/video/<trajectory_id>/<trajectory_id>.mp4
```

Side-by-side paper videos should be created from matched original and modified
selected reruns, then stacked with `ffmpeg`. Different episode lengths must be
handled explicitly by truncating, padding, or leaving a visible blank segment.

The video should show the same instruction, scene id, episode id, terminal
metrics, failure reason, and a synchronized first-person/top-down view when
available. It should emphasize behavior changes such as the first divergent
turn, a stuck loop, moving away from the goal, or reaching a different terminal
state.

## Case Checklist

Try to cover these case types in the final video set:

- original-only success;
- modified-only success;
- both-success but trajectory-divergent;
- both-failure and trajectory-divergent;
- neutral control with similar behavior.

If one of these case types does not appear in the completed batch, record that
absence instead of forcing a hand-picked example.

## Render Boundary

Do not migrate the separate `render-usd` runtime wholesale. ConvertAsset already
has the relevant local render capabilities for static paper figures:

- target-centered render manifests and camera-stage authoring under
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/`;
- authored-camera viewport capture through
  `scripts/render_with_viewport_capture.py`;
- single-object render callouts through `convert_asset/render/single.py`.

Use InternNav `vis_output=True` for navigation videos. Use the existing
ConvertAsset target-centered render pipeline for static close-ups, bbox
projection QA, and paper figures. Keep no-MDL generation in scratch trees, not
inside `/cpfs/user/zhuzihou/assets/zzh-grscenes`.

## Runtime Observation And Sidecar Fix

The first original-side `acl_main_pilot30` run was stopped and archived because
it was not a valid paper run. It reached 12 completed episodes, then stalled
after starting episode 13:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_acl_main_pilot30_invalid_broken_sidecars_20260523235649
```

The root cause was the prepared work root. It installed only `fixed.usd` and
`fixed_docker.usd` into each scene directory. GRScenes `fixed.usd` files contain
relative references such as `models/...` and `Materials/...`; the clean source
tree stores per-scene `models` and `Materials` entries as small text files
pointing to `../../models` and `../../Materials`, while the no-MDL scratch tree
uses real symlinks. Without recreating those sidecar entries in the InternNav
work root, Isaac resolved the references relative to:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523_pilot30/scene_data/<condition>/<scene_id>/
```

and logged many `Could not open asset @models/...@` warnings.

The fix in `prepare_minipair.py` now resolves text sidecars, symlinks, and real
directories, then installs `models` and `Materials` symlinks beside every
prepared `fixed.usd`. The regenerated pilot30 manifest records those sidecars in
each `scene_records[*].original_dependency_sidecars` and
`scene_records[*].converted_dependency_sidecars` field.

The invalid original-only partial metrics at `Count=12` were:

```json
{
  "TL": 30.3341,
  "NE": 11.6283,
  "FR": 0.0,
  "StR": 0.0,
  "OS": 0.25,
  "SR": 0.0,
  "SPL": 0.0,
  "Count": 12
}
```

This artifact must not be used as paper evidence.

这次归档对应 `invalid_broken_sidecars`：`@models/...@` 和
`@Materials/...@` sidecar 缺失导致 USD 引用解析坏掉。它是工程准备失败，
不能说明导航 agent 因为 original 或 converted 材质而失败；只能说明输入场景
包本身无效。

## Runtime Observation And LMDB Resume Trap

sidecar 修复后，第二次 original-side pilot30 启动仍然不是干净的 30 条任务。
它的第一行 progress 输出是：

```text
total_path: 18
```

根因是 InternNav 的断点/已完成状态没有一起清掉。上一轮只归档了
`InternNav/logs/...` 里的任务目录，但 completed/resume 状态仍然留在：

```text
/cpfs/user/zhuzihou/dev/InternNav/data/sample_episodes/<task_name>/sample_data0.lmdb
```

这个 LMDB 仍然带着 broken-sidecar run 已完成的 12 条记录，所以 InternNav
把重启后的任务当成 resume，只暴露剩余 18 条 path。第二次启动也已归档为
invalid `resumed_lmdb` / `invalid_resumed_lmdb`，同样只是工程运行 artifact，
不能作为 paper evidence。

有效的 clean pilot30 rerun 必须同时清理或归档两个状态根：

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/<task_name>
/cpfs/user/zhuzihou/dev/InternNav/data/sample_episodes/<task_name>
```

第一行 progress 现在是硬门禁，必须严格等于：

```text
total_path: 30
```

只要不是这个值，就说明 run 继承了旧状态，或者 episode set 准备错了，不能当作
有效 pilot30 结果使用。

## Current Clean Original Run

当前 clean original-side `acl_main_pilot30` 已在同时清理 log 目录和
`data/sample_episodes` 状态后启动。它已经通过 run-shape gate：第一行 progress
输出确认是 `total_path: 30`。

主会话观察窗口里，已有若干 episode 以这些 terminal status 结束：

```text
not_reach_goal
exceed_total_max_step
```

这些状态表示对应 episode 的导航任务失败，但程序协议是有效的：场景包能加载，
任务数是干净的，InternNav 也正常执行到 episode terminal state。它们必须和
broken sidecars、旧 LMDB 污染这类工程失败分开解释。

最终 paper-facing 指标仍在等待。只有完整 30 条 clean original 和匹配的 30 条
modified 都完成，并能做 paired analysis 后，claim gate 才能打开。

## Runtime Hang Exclusions And V4 Split

`acl_main_pilot30_v2` 进一步暴露了两条 simulator/runtime hang，而不是有效导航
失败：

- `MVUCSQAKTKJ5EAABAAAAACA8_usd_electriccooker_model_6dcff0778b2c8c7614949fa7f4d8a8bd_0_0_16`
- `MVUCSQAKTKJ5EAABAAAAACA8_usd_refrigerator_model_b40856029554f6e152f24a267738f99f_0_0_10`

这两条都没有 episode terminal metric，不能记成 `not_reach_goal`。其中
refrigerator case 的 v2 evidence 是：progress 只有 `start sampling`，common
log 进入 `WARM UP` 并记录 `Env Reset time: 9.35s`、`agent step time: 0.0s`，
之后没有 `now action`、没有 `Env Step`、没有 `finish`。进程仍高 CPU，但日志
长时间不再更新。

v2 partial run 已归档为工程排障材料，不进 paper result：

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_acl_main_pilot30_v2_invalid_refrigerator_warmup_hang_20260524052033
/cpfs/user/zhuzihou/dev/InternNav/data/sample_episodes/convertasset_grscene_sn_original_acl_main_pilot30_v2_invalid_refrigerator_warmup_hang_20260524052033
```

v2 停止前的 partial aggregate 是 `Count=12`，只能说明前 12 条有 terminal
metrics，不能作为论文主结果。

`acl_main_pilot30_v3` supersedes v2，
保留 30 条、6 个场景，并用 deterministic replacement policy 从 ready
candidate 顺序中补入：

- `MVUCSQAKTKJ5EAABAAAAABQ8_usd_sofa_chair_model_d5f1d04da565644d5b370cb39f1ea6bb_0_0_30`
- `MVUCSQAKTKJ5EAABAAAAADY8_usd_toilet_model_9b773fd00bc7a69cb9fd954d0c2a48d9_0_0_31`

v3 manifest:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_v3_prep_manifest.json
```

The v3 original clean run passed the run-shape gate:

```text
start eval dataset: convertasset_grscene_sn_original_acl_main_pilot30_v3, total_path: 30
```

但 v3 original 在第 13 个 task 暴露了第三条 simulator/runtime hang：

```text
MVUCSQAKTKJ5EAABAAAAACA8_usd_microwave_model_699bb196fbcad1de3f017f4e61fb5a50_0_0_20
```

它停在 `WARM UP`、`Env Reset time: 10.84s`、`agent step time: 0.0s`，
之后没有 `now action`、没有 `Env Step`、没有 `finish`、没有 terminal
metrics。`result.json` 停在 `Count=12`，因此它不是导航失败，而是无效
runtime artifact。v3 partial run 已归档：

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_acl_main_pilot30_v3_invalid_microwave_warmup_hang_20260524070839
/cpfs/user/zhuzihou/dev/InternNav/data/sample_episodes/convertasset_grscene_sn_original_acl_main_pilot30_v3_invalid_microwave_warmup_hang_20260524070839
```

`acl_main_pilot30_v4` 是当前 paper-main candidate split。它 supersedes v3，
继续保持 30 条、6 个场景，三条 runtime hang 都在 manifest 中显式排除，
`unmatched_excluded_path_keys=[]`。第三条 microwave hang 的日志显示 ID 使用
InternNav runtime 的 episode index `_20`，而 source selection path key 是
`_22`；`prepare_minipair.py` 现在同时接受 raw `trajectory_id`、source
`path_key` 和 `trajectory_id_<number>` 形式，避免从日志复制 exclusion key 时漏排。

v4 deterministic replacements are:

```text
MVUCSQAKTKJ5EAABAAAAABQ8_usd_sofa_chair_model_d5f1d04da565644d5b370cb39f1ea6bb_0_0_30
MVUCSQAKTKJ5EAABAAAAADY8_usd_toilet_model_9b773fd00bc7a69cb9fd954d0c2a48d9_0_0_31
MVUCSQAKTKJ5EAABAAAAACY8_usd_couch_model_676b88959789c12273e483c196b28191_0_0_32
```

v4 manifest:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_v4_prep_manifest.json
```

For paper statistics, include only paired episodes where both original and
modified produce terminal metrics. Runtime hangs are reported as exclusions and
limitations, not silently counted as navigation failures.

## Failure Boundary

后续 triage InternNav run 时使用这个边界：

| 类别 | 例子 | 论文状态 |
|---|---|---|
| 工程失败 | 缺 `@models/...@` 或 `@Materials/...@` sidecar；旧 `data/sample_episodes/<task_name>/sample_data0.lmdb` 污染；第一行不是 `total_path: 30` | 无效 run artifact。归档，但不要用于 downstream claims。 |
| runtime hang | reset/warm-up 后无 `now action`、无 `Env Step`、无 `finish`、无 terminal metric；进程仍高 CPU | 无效 episode artifact。按 deterministic policy 排除并替换，记录 exclusion count/rate。 |
| 任务失败 | `not_reach_goal`；`exceed_total_max_step`；episode 数符合预期且有正常 terminal metrics | 有效 episode outcome。只有 original 和 modified 两侧都完整并配对后再纳入分析。 |

## Next Work

1. Let the clean original v4 pilot30 complete and inspect its final result and
   logs.
2. Run the modified v4 pilot30 counterpart from equally clean logs and
   `data/sample_episodes` state, with stdout redirected to a log file.
3. Extract aggregate and per-episode metrics for both conditions.
4. Run paired analysis and select video cases.
5. Generate selected-only video reruns and side-by-side mp4s.
6. Update the ACL paper only after the claim gate records real paired results.
