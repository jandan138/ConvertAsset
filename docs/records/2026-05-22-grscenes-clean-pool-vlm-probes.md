# 2026-05-22 GRScenes Clean-Pool VLM Probes

This record documents the first real-model run over the expanded clean visual-QA
pool after the retake pass.

## Scope

The selected projection subset is:

- `paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_pass15_projection_qa_report.json`
- 15 original/converted pairs.
- 30 scoring records.
- 4 older PASS pairs from `pass_only_target_projection_qa_report.json`.
- 11 retake PASS pairs from `retake_visual_review_batch.json`.
- All selected pairs are `projection_ok`.

This is still a pilot pool. It expands the clean preservation evidence from 4
to 15 pairs, but it remains below the 20-pair final benchmark gate.

## Dependency And Conversion Gate

The full-route data gate was rechecked before this probe:

- `full_dependency_closure_report.json` records `scan_truncated=false`,
  `usd_layer_scan_limit=null`, `reachable_source_usd_count=85705`, and
  `unscanned_usd_queue_count=0`.
- `full_nomdl_scratch_materialization_report.json` records `dry_run=false` and
  99 top-level scratch inputs present.
- `full_nomdl_multi_root_run_report.json` records a completed full GRScenes
  single-process multi-root no-MDL run.
- `full_nomdl_apply_verification_report.json` records 99 top-level outputs,
  `source_pollution_count=0`, and `source_pollution_scan_truncated=false`.

If the full dependency scan is rerun, the command must pass
`--max-usd-layers 0`; the script CLI default remains 5000 for bounded dry-run
checks.

## Real-Model Results

Gemma4 local, structured text, normalized-1000 prompt:

- Predictions:
  `paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/gemma4_clean_pool_pass15_predictions.jsonl`
- Score:
  `paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/gemma4_clean_pool_pass15_score_summary.json`
- 30/30 records parsed.
- Answer accuracy: 15/15 original and 15/15 converted.
- Normalized-1000 point-in-bbox: 8/15 original and 6/15 converted.
- Normalized-1000 pair hit agreement: 11/15; both-hit pairs: 5/15.

Qwen2.5-VL structured text, normalized-1000 prompt:

- Predictions:
  `paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/qwen25_clean_pool_pass15_structured_predictions.jsonl`
- Score:
  `paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/qwen25_clean_pool_pass15_structured_score_summary.json`
- 30/30 records parsed, but only 23/30 have scorable answer strings under the
  current parser.
- Answer accuracy: 8/11 original and 9/12 converted.
- Raw point-in-bbox: 5/14 original and 5/15 converted.
- Normalized-1000 point-in-bbox: 0/14 original and 0/15 converted.
- Normalized-1000 hit agreement is 14/14 only because all comparable
  normalized points miss; coordinate semantics are still unresolved.

The table artifacts are:

- `paper/shared/tables/grscenes_vlm_clean_pool_pass15.csv`
- `paper/shared/tables/tab_grscenes_vlm_clean_pool_pass15.tex`

## Commands

Projection subset:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/select_projection_subset.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/pass_only_target_projection_qa_report.json \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/retake_target_projection_qa_report.json \
  --selection-id clean_pool_pass15_v1 \
  --claim-boundary clean_pool_projection_labels_only_not_final_vlm_metric_evidence \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_pass15_projection_qa_report.json \
  --pair-id c27086f557d316584264.view_001 \
  --pair-id e2ec085d524d5df4455d.view_001 \
  --pair-id e2ec085d524d5df4455d.view_003 \
  --pair-id c8ee4b66274b05d242c2.view_003 \
  --pair-id 47aa36277a54f6ca90cc.retake_011 \
  --pair-id 47aa36277a54f6ca90cc.retake_012 \
  --pair-id e1cf9f0feb81aa92d8a1.retake_008 \
  --pair-id 1e397951c1926c7f0a0b.retake_008 \
  --pair-id 1e397951c1926c7f0a0b.retake_009 \
  --pair-id ef6a4fe9448f672c2ecc.retake_008 \
  --pair-id ef6a4fe9448f672c2ecc.retake_009 \
  --pair-id 21dde4a14ca93f539a47.retake_008 \
  --pair-id f35ef3d86c42446b7ddf.retake_011 \
  --pair-id c8ee4b66274b05d242c2.retake_008 \
  --pair-id c8ee4b66274b05d242c2.retake_014
```

Gemma4 prediction:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 \
UNSLOTH_COMPILE_LOCATION=/tmp/convertasset_vlm_unsloth_cache \
  /cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_pass15_projection_qa_report.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/gemma4_clean_pool_pass15_predictions.jsonl \
  --model-backend local_gemma4_multimodal \
  --model-path /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8 \
  --coordinate-frame normalized_1000 \
  --response-format structured_text \
  --max-new-tokens 64 \
  --force
```

Qwen2.5-VL prediction:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 \
  /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.venv_dlc/bin/python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_pass15_projection_qa_report.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/qwen25_clean_pool_pass15_structured_predictions.jsonl \
  --model-backend local_hf_qwen \
  --model-path /cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct \
  --attn-implementation eager \
  --coordinate-frame normalized_1000 \
  --response-format structured_text \
  --max-new-tokens 64 \
  --force
```

Scoring:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/gemma4_clean_pool_pass15_predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/gemma4_clean_pool_pass15_score_summary.json

PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/qwen25_clean_pool_pass15_structured_predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/qwen25_clean_pool_pass15_structured_score_summary.json
```

## Interpretation

The expanded pool gives a useful ACL pilot signal: Gemma4 is robust on object
category answers across original/no-MDL renders, while point localization drops
from 8/15 to 6/15 under the normalized-1000 primary point metric. Qwen remains
useful as a second-backend stress test, but its coordinate protocol is not yet
stable enough for final performance claims.

The next highest-value step is to run the zoom/material-shift stress pool as a
separate experiment, because it directly tests whether target-visible but
material-shifted renders perturb VLM grounding.
