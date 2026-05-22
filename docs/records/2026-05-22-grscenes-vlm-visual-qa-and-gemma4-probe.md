# 2026-05-22 GRScenes VLM Visual QA And Gemma4 Probe

## Scope

This record documents the first full visual QA gate over the 10 recommended
GRScenes render-smoke pairs, plus the first real local VLM probe. It is a pilot
gate for the ACL-oriented object material/texture generalization story, not a
final benchmark result.

## Visual QA Result

The 10 recommended render-smoke pairs were reviewed in parallel by independent
clean-room visual reviewers using blind A/B labels. Reviewers saw only the image
paths and target category, not code, manifests, or original/converted labels.

Durable artifact:

- `paper/shared/evidence/raw/grscene_vlm_grounding/paired_render_visual_review_batch.json`

Outcome:

- `PASS`: 1 pair, `c27086f557d316584264.view_001` (`bottle`).
- `WARN`: 5 pairs, usable only with caveats or retakes.
- `FAIL`: 4 pairs, excluded from VLM metrics until rerendered.

Interpretation: the render stack works, but render-smoke is not enough for
paper metrics. Final VLM evaluation must filter or retake scenes based on human
or depth/visibility QA before scoring.

## Real Model Probe

The first live model run used local Gemma4 under the Genesis-LLM QLoRA Python
environment. It ran only on the visually accepted P01 bottle pair and wrote to
an isolated probe output, not canonical `predictions.jsonl`.

Command:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 \
  /cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/target_projection_qa_report.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_p01_predictions.jsonl \
  --model-backend local_gemma4_multimodal \
  --model-path /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8 \
  --sample-id c27086f557d316584264.view_001.original \
  --sample-id c27086f557d316584264.view_001.converted \
  --max-new-tokens 64 \
  --force
```

Artifacts:

- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_p01_predictions.jsonl`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_p01_predictions.jsonl.metadata.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_p01_score_summary.json`

Result:

- The model produced parseable JSON for both original and converted images.
- The answer string matched `bottle` for both images.
- Both predicted points were outside the 600x450 image and outside the target
  bbox.
- The score summary reports `point_in_bbox_accuracy=0.0`,
  `point_in_image_accuracy=0.0`, and `answer_accuracy=1.0` for both material
  conditions.

Interpretation: this is useful real-model evidence because it proves the
prediction runner and scorer can run end-to-end on local VLM output. It is not
positive grounding evidence. It shows that coordinate grounding must be analyzed
separately from category text answers.

## Code Change

`score_grounding.py` now emits score `schema_version=3` and reports
`point_in_image` per record plus `point_in_image_accuracy` in aggregate
summaries. This was added because the first real model generated
image-out-of-bounds coordinates; treating those only as bbox misses would hide
an important failure mode.

Tests:

- Added
  `test_score_reports_out_of_frame_points_separately_from_bbox_misses`.
- Targeted scorer tests pass: `9 passed`.

## Runtime Notes

- The Qwen route is not currently first-choice in this repo because the checked
  Python environments do not provide `qwen_vl_utils`.
- The Gemma4 environment has `torch`, `transformers`, `unsloth`, and `PIL`, and
  loaded successfully on the RTX 4090.
- Unsloth may create `unsloth_compiled_cache/` under the repo root. It is a
  disposable runtime cache and is now ignored by git.

## Claim Boundary

Do not cite this as final VLM performance. It supports only:

- render candidate filtering exists and has concrete accept/reject results,
- local Gemma4 inference can run on the generated renders,
- the scorer can evaluate real model predictions,
- the first probe found a coordinate-grounding failure.

The next publishable experiment step is to run the real model on the visually
accepted/caution subset, retake failed views, and aggregate metrics only over
QA-accepted pairs.
