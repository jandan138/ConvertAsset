# 2026-05-22 GRScenes Zoom Stress VLM Probes

This record documents the first real-model run over the zoom/material-shift
stress pool.

## Scope

The input projection report is:

- `paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_target_projection_qa_report.json`

It contains:

- 14 original/converted pairs.
- 28 scoring records.
- 14/14 pairs with `projection_ok`.
- 2 visual-review PASS pairs and 12 WARN pairs.

The zoom pool is not a clean material-preservation set. It is a target-visible
stress set: visual QA found that targets are identifiable enough for grounding
experiments, but many pairs have large material/color/lighting shifts after
no-MDL conversion.

## Results

Gemma4 local, structured text, normalized-1000 prompt:

- Predictions:
  `paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/gemma4_zoom_stress_predictions.jsonl`
- Score:
  `paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/gemma4_zoom_stress_score_summary.json`
- 28/28 rows parsed.
- Answer accuracy: 14/14 original and 14/14 converted.
- Raw point-in-bbox: 1/14 original and 1/14 converted.
- Normalized-1000 point-in-bbox: 11/14 original and 13/14 converted.
- Normalized-1000 pair hit agreement: 12/14; both-hit pairs: 11/14.

Qwen2.5-VL structured text, normalized-1000 prompt:

- Predictions:
  `paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/qwen25_zoom_stress_structured_predictions.jsonl`
- Score:
  `paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/qwen25_zoom_stress_structured_score_summary.json`
- 28/28 rows parsed.
- 26/28 rows have scorable answer strings.
- Answer accuracy: 12/14 original and 10/12 converted.
- Raw point-in-bbox: 9/14 original and 6/13 converted.
- Normalized-1000 point-in-bbox: 3/14 original and 3/13 converted.
- Raw point hit agreement: 8/13; both-hit pairs: 5/13.

The table artifacts are:

- `paper/shared/tables/grscenes_vlm_zoom_stress.csv`
- `paper/shared/tables/tab_grscenes_vlm_zoom_stress.tex`

## Commands

Gemma4 prediction:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 \
UNSLOTH_COMPILE_LOCATION=/tmp/convertasset_vlm_unsloth_cache \
  /cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_target_projection_qa_report.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/gemma4_zoom_stress_predictions.jsonl \
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
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_target_projection_qa_report.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/qwen25_zoom_stress_structured_predictions.jsonl \
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
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/gemma4_zoom_stress_predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/gemma4_zoom_stress_score_summary.json

PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/qwen25_zoom_stress_structured_predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/qwen25_zoom_stress_structured_score_summary.json
```

## Interpretation

The stress pool gives the first evidence for the ACL material-shift story. In
these target-visible zoom views, Gemma4 keeps category answers stable and scores
well under the normalized-1000 point metric. Qwen still shows response and
coordinate-protocol sensitivity, with a visible drop in raw point hits from
original to converted.

This should be written as a pilot result about material-shift sensitivity and
protocol dependence, not as a final GRScenes benchmark.
