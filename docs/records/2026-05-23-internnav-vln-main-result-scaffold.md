# 2026-05-23 InternNav VLN Main-Result Scaffold

## Context

The active ACL goal is to promote the InternNav/DualVLN downstream route from a
one-episode smoke test to a main-result-level paired benchmark over GRScenes
original and ConvertAsset modified scenes.

The previous state had:

- a real one-episode InternNav/InternVLA-N1 smoke run;
- aggregate `result.json` metrics;
- no committed per-episode rows;
- no statistics scaffold for paired deltas;
- no storage-bounded video case manifest.

## What Changed

This iteration added the repository-side scaffold for the larger benchmark:

- `prepare_minipair.py` now supports split-driven InternNav task names for
  larger batches, such as `convertasset_grscene_sn_original_acl_main_050` and
  `convertasset_grscene_sn_modified_acl_main_050`.
- `extract_episode_metrics.py` normalizes InternNav LMDB records into JSONL
  rows with `TL`, `NE`, `OS`, `SR`, `SPL`, and `steps`.
- `analyze_paired_metrics.py` computes paired original-vs-modified deltas,
  win/loss/tie counts, failure-pair counts, effect sizes, and claim gates.
- `select_video_cases.py` selects a small set of representative cases for
  later video reruns while keeping metric batch runs video-free.

The existing mini smoke LMDB outputs were extracted into:

```text
paper/shared/evidence/raw/internnav_vln_downstream/original_episode_metrics.jsonl
paper/shared/evidence/raw/internnav_vln_downstream/modified_episode_metrics.jsonl
paper/shared/evidence/raw/internnav_vln_downstream/paired_episode_analysis.json
paper/shared/evidence/raw/internnav_vln_downstream/video_case_manifest.json
```

## Current Interpretation

The new files do not make the benchmark complete. They make the benchmark
scalable and auditable. The current `paired_episode_analysis.json` still has
`episode_count=1`, `row_count_acl_ready=false`, and
`acl_main_result_ready=false`. The final claim gate also requires aggregate
result provenance and a video manifest, so it cannot open from row counts alone.

The video manifest currently selects the one smoke episode as a
`both_failure_divergent` rerun candidate. InternNav can write visualization
frames and mp4 files when `eval_settings.vis_output=True`, but the current smoke
run disabled video and therefore produced no paper video yet.

## Next Evidence Gate

The next hard gate is a real multi-episode paired batch:

- minimum pilot-main gate: 30 paired episodes across at least five scenes;
- preferred ACL main-result gate: 100+ paired episodes across at least 10
  scenes;
- metric batch runs should keep `vis_output=False`;
- selected qualitative reruns should enable video only for cases listed in the
  video manifest.

## Pilot30 Prep Update

The first pilot-main input batch is now prepared:

```text
paper/shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_prep_manifest.json
/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523_pilot30
```

Current external readiness for `/cpfs/user/zhuzihou/assets/zzh-grscenes` is 6
ready scenes and 62 ready SN episodes across the `test` and `validate` splits.
The pilot manifest selects 30 episodes with `ready_only=true`,
`selection_strategy=round_robin_scenes`, and `min_scenes=5`; the generated claim
gate is:

```json
{"blocked_by": [], "can_run_paired_eval": true, "min_scenes": 5, "selected_scene_count": 6, "status": "ready_for_internnav_runtime"}
```

The selected scenes are balanced at five episodes each:

```text
MVUCSQAKTKJ5EAABAAAAABQ8_usd
MVUCSQAKTKJ5EAABAAAAADY8_usd
MVUCSQAKTKJ5EAABAAAAACY8_usd
MVUCSQAKTKJ5EAABAAAAABA8_usd
MVUCSQAKTKJ5EAABAAAAACA8_usd
MV7J6NIKTKJZ2AABAAAAADY8_usd
```

The selected sample is 25 `test` episodes plus 5 `validate` episodes. The
manifest also records 24 skipped scene records, all blocked by
`missing_converted_navigation_usd`. That makes this a readiness-bounded pilot
split, not a claim about full GRScenes coverage.

The five `MVUCS...` navigation no-MDL files were generated only under the
scratch modified tree:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521
```

The clean source tree was not modified:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes
```

The clean source check found no `start_result_navigation_noMDL.usd` under the
selected source scene directories. The prepared work root uses symlinks into the
clean and scratch CPFS trees, so exact reproduction currently depends on those
external paths. The pilot30 InternNav `result.json` files are intentionally
absent at this stage; no SR/SPL/NE/TL claim should be made from the manifest
alone.

This update still does not complete the ACL main result. It only proves the next
real InternNav paired batch can be launched from an auditable manifest. The
remaining paper-level deliverables are: original and modified batch runs,
per-episode metric extraction, paired statistics/effect sizes, selected
paper-video reruns, trajectory or frame-level qualitative figures, and final
paper text.

## Verification

Focused tests:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py -q
```

Result:

```text
24 passed
```

Full tests after the pilot30 prep changes:

```bash
python -m pytest -q
```

Result:

```text
287 passed
```

Actual smoke LMDB extraction used the external InternNav runtime dependency
root on `PYTHONPATH` so `lmdb` and `msgpack_numpy` were available without adding
those packages to ConvertAsset.
