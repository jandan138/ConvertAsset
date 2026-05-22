# 2026-05-22 GRScenes Scoring Smoke Baseline

## Scope

This record documents the first runnable scoring gate for the GRScenes VLM
grounding pilot after target projection QA. It validates the scoring schema and
original/converted aggregation, but it does not provide VLM model evidence.

## Changes

- Added
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/generate_projection_center_baseline_predictions.py`.
- Extended
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py`
  with paired original/converted consistency metrics, prediction backend
  provenance, model checkpoint provenance, score input/scorer hashes, and an
  explicit claim boundary.
- Consulted
  `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator` as a read-only
  reference for real model backend organization. Its useful pattern is the
  backend split between local Hugging Face/Qwen-VL, local Gemma4 multimodal,
  and OpenAI-compatible remote multimodal API inference. This repo should reuse
  that idea for a future `predictions.jsonl` runner, not run the annotation CLI
  directly on the paper evidence directory.
- Added tests:
  - `tests/test_grscenes_vlm_projection_center_baseline.py`
  - `tests/test_grscenes_vlm_score_grounding.py`
- Generated:
  - `paper/shared/evidence/raw/grscene_vlm_grounding/projection_center_baseline_predictions.jsonl`
  - `paper/shared/evidence/raw/grscene_vlm_grounding/projection_center_baseline_predictions.jsonl.metadata.json`
  - `paper/shared/evidence/raw/grscene_vlm_grounding/projection_center_baseline_score_summary.json`

## Current Result

The deterministic baseline uses each projected target bbox center as the
predicted point and the target category as the predicted answer. The current
score summary records 20 scoring records across 10 original/converted pairs.

| Field | Value |
|---|---:|
| `num_records` | 20 |
| `pair_consistency.pair_count` | 10 |
| `pair_consistency.point_hit_agreement` | 1.0 |
| `pair_consistency.both_point_hit_count` | 10 |
| `pair_consistency.mean_prediction_point_delta_px` | 0.0 |
| `pair_consistency.answer_match_agreement` | 1.0 |
| `pair_consistency.duplicate_pair_version_count` | 0 |

The current score output uses `schema_version=3` and records:

- `prediction_backends=["projection_center_smoke_baseline"]`
- `model_checkpoints=["projection_center_smoke_baseline_no_vlm"]`
- `claim_boundary="scoring_smoke_only_not_vlm_evidence"`
- `score_provenance.input_predictions.hash_sha256`
- `score_provenance.scorer.script_hash_sha256`

If a future `predictions.jsonl` accidentally mixes
`projection_center_smoke_baseline` rows with real model rows, the scorer reports
`claim_boundary="mixed_projection_baseline_and_model_predictions_not_claimable"`.
If a future run accidentally contains duplicate rows for the same
`pair_id/task/version`, the scorer reports them in
`pair_consistency.duplicate_pair_version_count`.
Malformed coordinate fields, string-valued coordinate arrays, and non-dict
`target` or `prediction` objects are treated as unscored rows instead of
crashing the scorer.

## Claim Boundary

This is a scorer-smoke baseline only. It proves that the labels, JSONL schema,
point-in-box scoring, answer matching, and original/converted pair aggregation
are wired together. The 1.0 scores are expected by construction and must not be
cited as VLM accuracy, VLM robustness, downstream task performance, or paper
evidence that no-MDL improves model behavior.

The environment did not provide a ready non-interactive VLM backend during this
pass. No OpenAI/Anthropic-style API keys were present, local `torch`,
`transformers`, `openai`, and `anthropic` modules were unavailable, and the
`qwen` CLI failed in non-interactive mode because no auth type was configured.

The Auto-Asset-Annotator reference shows that a real local route likely exists
outside the default Python environment:

- Qwen2.5-VL local weights:
  `/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct`
- Gemma4 local multimodal runtime:
  `/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python`
- Gemma4 release:
  `/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8`

Those are candidates for the next real VLM runner, but they were not loaded or
run during this scoring-smoke pass.

The current answer metric remains smoke-grade: `_answer_matches()` uses
case-insensitive substring containment. That is acceptable for deterministic
category echo, but final ACL/AAAI claims need stricter category normalization,
an ontology map, or adjudicated semantic matching.

## Verification

Targeted scoring tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_grscenes_vlm_score_grounding.py \
  tests/test_grscenes_vlm_projection_center_baseline.py
```

Latest local result: `10 passed in 0.58s`.

Generation commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/generate_projection_center_baseline_predictions.py \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/projection_center_baseline_predictions.jsonl

PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/projection_center_baseline_predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/projection_center_baseline_score_summary.json
```

Latest local outputs:

- `Wrote .../projection_center_baseline_predictions.jsonl predictions=20`
- `Wrote .../projection_center_baseline_score_summary.json with 20 records`

## Next

- Run visual or depth QA over the 10 recommended render pairs.
- Replace the deterministic baseline with model-generated `predictions.jsonl`
  from a reproducible VLM backend.
- Use the same scorer to produce the first real `score_summary.json`.
