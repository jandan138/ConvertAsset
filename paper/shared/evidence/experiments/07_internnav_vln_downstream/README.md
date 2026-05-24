# InternNav VLN Downstream Bridge

This directory prepares ConvertAsset-controlled GRScenes original vs no-MDL
inputs for InternNav / VL-LN evaluation.

## What Is Ready

`prepare_minipair.py` converts GRScenes `benchmark/sn_episodes.json` records into
InternNav's expected dataset layout:

```text
<work_root>/datasets/grscene_sn_mini/mini/mini.json.gz
<work_root>/scene_data/original/<scene_id>/fixed.usd
<work_root>/scene_data/converted/<scene_id>/fixed.usd
<work_root>/configs/original_eval_cfg.py
<work_root>/configs/converted_eval_cfg.py
```

The legacy `mini` split keeps `original_eval_cfg.py`, `converted_eval_cfg.py`,
and the existing `convertasset_grscene_sn_nomdl_mini` task name so the recorded
smoke logs remain reproducible. Larger batch splits use task-name-based config
filenames, for example `convertasset_grscene_sn_modified_acl_main_050_eval_cfg.py`.

The default work root is outside git:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523
```

The repo evidence manifest is:

```text
paper/shared/evidence/raw/internnav_vln_downstream/prep_manifest.json
```

The paired real-metric summary is:

```text
paper/shared/evidence/raw/internnav_vln_downstream/internnav_vln_results.json
```

`run_internnav_eval.py` is the ConvertAsset-side wrapper for the real InternNav
eval. It runs InternNav under `./scripts/isaac_python.sh`, adds the external
runtime dependency root to `PYTHONPATH`, pins `HF_HOME`, disables Hugging Face
Xet, and applies the compatibility patches recorded in `prep_manifest.json`.

`runtime_watchdog.py` classifies InternNav progress/common/stdout logs after a
run stalls or during supervised polling. Its narrow purpose is to detect
reset/warm-up hangs before the first navigation action:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/runtime_watchdog.py \
  --log-dir /cpfs/user/zhuzihou/dev/InternNav/logs/<task_name> \
  --result /cpfs/user/zhuzihou/dev/InternNav/logs/<task_name>/result.json \
  --split-name <split_name>
```

It only emits `status=runtime_hang` when the latest episode has
`start sampling`, `WARM UP` / `Env Reset`, no `now action`, no `Env Step`, no
`finish`, and no advanced terminal metric. The emitted `exclude_path_key` can be
passed directly to `prepare_minipair.py --exclude-path-key`. Do not use this
rule for episodes that already produced actions or steps; those are normal
navigation outcomes even if they later fail with `not_reach_goal` or
`exceed_total_max_step`.

`advance_split_from_triage.py` turns a watchdog `runtime_hang` JSON into the
next deterministic candidate split. It reads the previous prep manifest,
validates `status=runtime_hang`, appends the emitted `exclude_path_key`, records
the triage file hash, and calls `prepare_minipair.py` with the same selection
policy:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/advance_split_from_triage.py \
  --previous-manifest paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_v10_prep_manifest.json \
  --triage paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_v10_runtime_hang_triage.json
```

This is the preferred path for v11+ split creation. Avoid hand-assembling long
`--exclude-path-key` command lines after a watchdog triage file exists.
The tool is intentionally strict: the generated manifest must have
`unmatched_excluded_path_keys=[]`, and when the triage key is new the manifest's
`excluded_episode_count` must increase by exactly one. It carries over any
`source.requested_scene_ids` filter from the previous manifest and records the
watchdog reason under `runtime_triage_source` while using a stable manifest-level
exclusion reason.

`audit_episode_height_filter.py` checks a generated InternNav dataset against
the same height-jump rule used by InternNav's `different_height()` filter. Use
it when a split repeatedly hangs at reset/warm-up:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/audit_episode_height_filter.py \
  --dataset /path/to/<split>.json.gz \
  --hang-path-key <runtime_trajectory_id_episode_id> \
  --output paper/shared/evidence/raw/internnav_vln_downstream/<audit>.json
```

The v2-v10 root-cause audit is recorded at:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_runtime_hang_height_filter_audit.json
```

It matched all nine known v2-v10 hang path keys and found that all nine would
be removed by InternNav's official `filter_stairs=True` height gate. The next
split should therefore change the sampling protocol instead of advancing by one
more exclusion.

## Main-Result Goal

To make this route part of the ACL main result, the goal is:

```text
Run paired InternNav / DualVLN evaluation on GRScenes original and
ConvertAsset-modified scenes, produce SR/SPL/NE/TL/OS/StR/FR aggregate metrics,
per-episode paired deltas, failure taxonomy, reproducible manifests, and
selected paper-quality side-by-side videos.
```

The current one-episode smoke is not enough for that claim. It is protocol
evidence and a failure-case seed. The current pilot-main gate is 30 paired
episodes across at least five scenes; the preferred ACL main-result gate is 100+
paired episodes across at least 10 scenes with repeat or seed-control evidence.

## Current Smoke Pair

The first prepared pair uses:

```text
MV7J6NIKTKJZ2AABAAAAADY8_usd
```

Original `fixed.usd` links to the clean GRScenes source tree. Converted
`fixed.usd` links to `start_result_navigation_noMDL.usd` generated only in the
scratch tree:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521
```

Do not run no-MDL conversion inside `/cpfs/user/zhuzihou/assets/zzh-grscenes`.

## Commands

Prepare or refresh the smoke pair:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py \
  --max-episodes 1 \
  --scene-id MV7J6NIKTKJZ2AABAAAAADY8_usd
```

If the converted navigation USD is missing, generate it from the scratch copy:

```bash
./scripts/isaac_python.sh ./main.py no-mdl --only-new-usd \
  /cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes/scenes/MV7J6NIKTKJZ2AABAAAAADY8_usd/start_result_navigation.usd
```

After InternNav produces both `result.json` files, collect paired metrics:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/collect_results.py \
  --original-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_mini/result.json \
  --converted-result /cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_nomdl_mini/result.json
```

`collect_results.py` is intentionally strict: each result path must end with the
expected log suffix recorded in `prep_manifest.json`, and each result split's
`Count` must match the prepared episode count. This prevents stale or unrelated
InternNav runs from becoming paper evidence by accident.

## Main-Result Batch Infrastructure

The current smoke run has been extended with the repository-side infrastructure
needed for a larger ACL main-result benchmark:

- `extract_episode_metrics.py` reads InternNav LMDB `sample_data*.lmdb` outputs
  and writes per-episode JSONL rows. It lazy-imports `lmdb` and `msgpack_numpy`
  so unit tests remain runnable without the full InternNav runtime.
- `analyze_paired_metrics.py` pairs original and modified rows by `path_key`,
  computes means, modified-minus-original deltas, paired win/loss/tie counts,
  paired effect sizes, and a claim gate.
- `select_video_cases.py` chooses a small, storage-bounded set of cases for
  later video reruns. Metric batch runs should keep `vis_output=False`; selected
  video reruns should set `eval_settings.vis_output=True`.

The actual mini smoke LMDBs were extracted into:

```text
paper/shared/evidence/raw/internnav_vln_downstream/original_episode_metrics.jsonl
paper/shared/evidence/raw/internnav_vln_downstream/modified_episode_metrics.jsonl
paper/shared/evidence/raw/internnav_vln_downstream/paired_episode_analysis.json
paper/shared/evidence/raw/internnav_vln_downstream/video_case_manifest.json
```

`video_case_manifest.json` currently selects the one smoke episode as a
`both_failure_divergent` case. This is a rerun target for qualitative video, not
evidence that the benchmark is complete.

The analysis claim gate intentionally separates row-count readiness from paper
readiness. `row_count_acl_ready` can become true after enough paired episodes,
but `acl_main_result_ready` also requires aggregate result provenance and a
video manifest to be explicitly supplied to the analyzer.

## ACL Pilot30 Prepared Batch

The first storage-bounded multi-scene batch input is now prepared, but it has
not been executed through InternNav yet:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_prep_manifest.json
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523_pilot30
```

This manifest uses `--ready-only --selection-strategy round_robin_scenes` so it
only selects scenes with both original and converted navigation USDs and avoids
taking all episodes from the first available scene. The prepared dataset has 30
episodes balanced across six ready scenes, five episodes per scene.

Current ready scene inventory:

| source split | ready scenes | ready episodes |
| --- | ---: | ---: |
| `test` | 5 | 52 |
| `validate` | 1 | 10 |
| total | 6 | 62 |

The pilot30 sample itself contains 25 `test` episodes and 5 `validate`
episodes. It is a custom readiness-bounded split, not a full GRScenes benchmark
claim. The manifest records 24 skipped scenes, currently blocked by
`missing_converted_navigation_usd`.

The five newly prepared `test` scenes were converted only in the scratch tree:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521
```

The clean source tree remains unchanged:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes
```

The prepared work root uses symlinks into those external CPFS trees, so
reproduction currently depends on those paths remaining available. No pilot30
`result.json` exists yet under InternNav logs; this is input-preparation
evidence only.

Run the paired metric batch with the commands recorded in
`internnav_eval_commands.original` and `internnav_eval_commands.converted` in the
pilot manifest. Metric runs should keep `vis_output=False`; paper-video reruns
should be launched later on selected cases only, after paired metrics identify
representative success/failure or trajectory-divergence examples.

The first original pilot30 attempt was stopped and archived after 12 completed
episodes because the prepared scene directories did not expose GRScenes'
`models` and `Materials` dependency sidecars. Isaac therefore emitted missing
asset warnings for references such as `@models/...@`, and episode 13 stalled
after environment warm-up. That partial original-only run is invalid paper
evidence.

`prepare_minipair.py` now installs `models` and `Materials` symlinks beside each
prepared `fixed.usd`, resolving either text sidecar files such as
`../../models`, real symlinks, or real directories. The regenerated pilot30
manifest records the installed sidecars under each scene record.

The modified pilot30 counterpart must finish before any paired metric claim is
made. If a future run stalls, first inspect whether the last scene has complete
dependency sidecars and whether the Isaac kit log contains unresolved asset
warnings.

## Paper Video Workflow

Do not enable video for the full metric batch. Use this storage-bounded flow:

1. Run original and modified metric batches with `vis_output=False`.
2. Extract per-episode metrics and run paired analysis.
3. Use `select_video_cases.py` to choose 2-6 representative cases.
4. Generate selected-only original and modified rerun configs with new task
   names and `eval_settings["vis_output"] = True`.
5. Run those selected-only configs through `run_internnav_eval.py`.
6. Stack matched original and modified mp4s with `ffmpeg`.

InternNav visualization is expected to write:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/<task>/video/<trajectory_id>/frames/*.png
/cpfs/user/zhuzihou/dev/InternNav/logs/<task>/video/<trajectory_id>/<trajectory_id>.mp4
```

Current metric configs intentionally produce no paper video artifacts. The
existing LMDB records contain terminal metrics, not per-step robot trajectory
JSON, so trajectory figures require either selected video reruns or an
InternNav-side pose/action dump patch.

Paper videos should show a matched original/no-MDL episode with the same scene,
instruction, start, and goal. Each clip should label the episode id,
instruction, terminal metrics, failure reason, and step count. If possible,
include the first-person and top-down views that InternNav already composes.

Useful case types are: original-only success, modified-only success,
both-success but trajectory-divergent, both-failure divergent, and neutral
control. If a case type does not occur in the finished batch, record the absence
instead of forcing an example.

## Current Smoke Result

Real InternNav / InternVLA-N1 smoke runs were completed on 2026-05-23 for one
GRScenes SN episode:

| condition | TL | NE | SR | SPL | Count | runtime result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| original | 64.7729 | 8.3585 | 0.0 | 0.0 | 1 | `exceed_total_max_step` |
| no-MDL | 98.2783 | 42.1053 | 0.0 | 0.0 | 1 | `exceed_total_max_step` |
| no-MDL minus original | +33.5054 | +33.7468 | 0.0 | 0.0 | 0 | longer and farther from goal |

Both conditions failed this single navigation episode, so this is not success
evidence. It is a real embodied downstream smoke result showing that the
original vs no-MDL pair can be executed end-to-end and that the material
intervention changes trajectory length and final navigation error. Treat this as
protocol evidence and a failure-case seed; do not use it as a broad InternNav
performance claim.

Persisted InternNav logs:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_original_mini
/cpfs/user/zhuzihou/dev/InternNav/logs/convertasset_grscene_sn_nomdl_mini
```

The current minimal runtime dependency root is external to git and about 17 GiB:

```text
/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523
```

Debug video output remains disabled in the generated configs to avoid extra
`imageio`/`ffmpeg` dependencies and large output files. The canonical evidence
for this smoke run is `result.json`, the progress logs, and
`internnav_vln_results.json`.

Explorer review of the InternNav runtime found that `vis_output=True` should
write rendered visualizations under `logs/<task>/video/<trajectory_id>/`, but the
current mini smoke directories contain no frames or mp4 files because video was
disabled. InternNav can provide failure reasons and terminal metrics through
LMDB; it does not yet emit a clean per-step robot trajectory JSON, so trajectory
figures need either an InternNav-side patch or a selected video rerun with
top-down frames.
