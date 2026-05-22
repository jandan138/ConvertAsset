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

The direct-JSON Qwen command is useful only as a response-format diagnostic:

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
  --max-new-tokens 64 \
  --force
```

That run produced 8 parser failures because Qwen emitted malformed JSON with
`addCriterion` fragments. The follow-up usable Qwen command is:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 \
  /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.venv_dlc/bin/python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/pass_only_target_projection_qa_report.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/probes/qwen25_pass_only_structured_predictions.jsonl \
  --model-backend local_hf_qwen \
  --model-path /cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct \
  --attn-implementation eager \
  --coordinate-frame normalized_1000 \
  --response-format structured_text \
  --max-new-tokens 64 \
  --force
```

`structured_text` asks for two plain-text lines rather than direct JSON. The
parser accepts explicit `Point:` / `Answer:` labels, unlabeled two-line
coordinate-answer output, and four-number boxes by converting them to the box
center. It intentionally does not recover a point from ambiguous three-number
lines.

## Qwen Result

The checked-in structured-text Qwen PASS-only probe has 8 predictions over the
same 4 visual-QA PASS pairs as Gemma4.

Summary:

- Direct JSON probe: 8/8 parser failures; zero scored answers or points.
- Structured-text probe: 8/8 rows parsed at least an answer or point.
- Answer accuracy: 3/4 original and 3/4 converted under the current strict
  expected-label matcher. The faucet pair is returned as `fauc`, which the
  matcher does not count as `faucet`.
- Raw point-in-bbox: 2/3 original and 2/4 converted among parsed points.
- Normalized-1000 point-in-bbox: 0/3 original and 0/4 converted among parsed
  points.
- Pair consistency: raw point hit agreement 2/3, one both-hit pair; answer hit
  agreement 4/4.

This is second-backend protocol-sensitivity evidence, not a final robustness
claim. It supports the ACL story by showing why the experiment needs an
explicit coordinate contract, response-format contract, and a larger PASS set.
The returned coordinates are ambiguous and score better under raw image-space
boxes than normalized scaling, but the next Qwen run should freeze the
coordinate prompt and parser policy before treating either interpretation as
controlled evidence.

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
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_prediction_runner.py` later failed with three expected structured-text parser failures on unlabeled Qwen output before parser implementation.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_prediction_runner.py` passed: 15 tests.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_prediction_runner.py tests/test_grscenes_vlm_score_grounding.py tests/test_grscenes_vlm_projection_subset.py` passed: 29 tests.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider` passed: 223 tests.
- Qwen2.5-VL direct-JSON PASS-only probe reran with the current runner commit
  `5ef20a9` and `response_format=json`; score summary still has 0 scored
  answers and 0 scored points.
- Qwen2.5-VL structured-text PASS-only probe ran with the current runner commit
  `5ef20a9` and `response_format=structured_text`; score summary matches the
  3/4 answer, 2/3 original raw point, and 2/4 converted raw point counts above.
- YAML load check passed for `protocol.yaml`, `claims.yaml`, and `results_manifest.yaml`.
- `git diff --check` passed.
