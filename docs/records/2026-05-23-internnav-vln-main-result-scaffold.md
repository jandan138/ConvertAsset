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

## Verification

Focused tests:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py -q
```

Result:

```text
23 passed
```

Actual smoke LMDB extraction used the external InternNav runtime dependency
root on `PYTHONPATH` so `lmdb` and `msgpack_numpy` were available without adding
those packages to ConvertAsset.
