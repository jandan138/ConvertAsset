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
