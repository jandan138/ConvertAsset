# 2026-05-22 GRScenes Coordinate Protocol And Qwen Route

## Scope

This record documents the protocol cleanup after the Gemma4 PASS-only pilot.
The goal is to make the next real-model probes comparable across Gemma4 and
Qwen2.5-VL without mixing pixel-coordinate prompts with normalized-coordinate
scoring.

## Decision

New VLM probes should request normalized 0-1000 visual coordinates by default.
The prediction runner now exposes:

```bash
--coordinate-frame normalized_1000
--coordinate-frame pixel
```

The default is `normalized_1000`. Prediction rows record the requested frame in
both `prompt.coordinate_frame` and `prediction.coordinate_frame_requested`, and
the metadata sidecar records `coordinate_frame`.

Raw pixel scoring is still retained as a diagnostic because earlier probes
asked for pixels and because a future model may actually emit raw pixel
coordinates. For the current small PASS-only real-model probes, the primary
point metric should be the existing normalized-1000 point-in-box field.

## Why

Gemma4 repeatedly emitted points in a visual 0-1000 style frame during the
historical pixel-prompt probes. That made raw pixel point-in-box 0/4 for both
material conditions on the PASS-only pilot, while normalized-1000 scoring gave
4/4 for original and 3/4 for converted. Historical Gemma4 commands should be
rerun with `--coordinate-frame pixel` if the goal is to reproduce the old prompt
semantics; script hashes, metadata sidecars, and stochastic model output may
still differ. New cross-backend probes should use `--coordinate-frame
normalized_1000` so Qwen and Gemma4 comparisons do not depend on an avoidable
coordinate ambiguity.

## Qwen Route

The most feasible second backend is Qwen2.5-VL:

- Model: `/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct`
- Runtime: `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.venv_dlc/bin/python`
- Required packages confirmed there: `torch`, `transformers`, `qwen_vl_utils`

The Genesis-LLM Gemma4 environment has recent `transformers`, `torch`, and
`unsloth`, but not `qwen_vl_utils`, so it remains the Gemma4 runtime rather
than the Qwen runtime.

Recommended next Qwen command on a clean commit:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 \
  /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.venv_dlc/bin/python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/pass_only_target_projection_qa_report.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/probes/qwen25_pass_only_predictions.jsonl \
  --model-backend local_hf_qwen \
  --model-path /cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct \
  --attn-implementation eager \
  --coordinate-frame normalized_1000 \
  --max-new-tokens 64
```

## PASS Pool Expansion

All 21 current `centerline_clear` candidates from
`visibility_preflight_report.json` have already been rendered and visually
reviewed. Only four are visual-QA PASS. The lowest-risk way to expand the PASS
pool is not to overwrite existing renders, but to generate a retake render
manifest with a new render root and different camera sampling, then run the
same preflight, render-smoke, projection, and visual-QA gates.

The retake should stay separate, for example:

- `paper/shared/evidence/raw/grscene_vlm_grounding/retake_render_manifest.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/retake_renders/`
- `paper/shared/evidence/raw/grscene_vlm_grounding/retake_visibility_preflight_report.json`

Existing artifacts suggest storage is modest for targeted retakes: roughly
2 MB per original/converted pair including PNGs, logs, and paired reports.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_prediction_runner.py` failed first with three expected `coordinate_frame` API failures before implementation.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_prediction_runner.py` passed: 10 tests.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_prediction_runner.py tests/test_grscenes_vlm_score_grounding.py tests/test_grscenes_vlm_projection_subset.py` passed: 24 tests.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider` passed: 218 tests.
- YAML load check passed for `protocol.yaml`, `claims.yaml`, and `results_manifest.yaml`.
- `git diff --check` passed.
