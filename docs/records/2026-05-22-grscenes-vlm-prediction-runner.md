# 2026-05-22 GRScenes VLM Prediction Runner

## Scope

This record documents the first real-model prediction runner for the GRScenes
VLM grounding pilot. It creates the bridge between projected scoring records and
future model-generated `predictions.jsonl` files.

No live VLM inference was run in this pass. The later first live Gemma4 probe is
recorded in
`docs/records/2026-05-22-grscenes-vlm-visual-qa-and-gemma4-probe.md`.

## Changes

- Added
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py`.
- Added `tests/test_grscenes_vlm_prediction_runner.py`.
- Updated the experiment runbook and raw evidence README with the real-model
  route and claim boundary.

The runner reads `target_projection_qa_report.json`, builds one S1 pointing
prompt per scoring record, sends the prompt plus rendered image to an explicit
backend, parses JSON-shaped model output, and writes `predictions.jsonl` plus a
metadata sidecar.

## Backend Route

The runner borrows the backend split from the read-only
`/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator` reference:

- `local_hf_qwen`: local Hugging Face Qwen2.5-VL style inference.
- `local_gemma4_multimodal`: local Gemma4 image-text inference, intended for
  the Genesis-LLM QLoRA Python environment.
- `openai_compatible`: remote multimodal Chat Completions-compatible API.

All heavy model imports are lazy. Importing the runner or running unit tests
does not load Qwen, Gemma4, Torch, Transformers, or remote API clients.

The runner performs preflight before constructing a backend. It rejects empty
record selections, missing image files, existing output files without `--force`,
and limited `--limit` probes that would write to canonical `predictions.jsonl`
without `--force`.

## Output Contract

Each output row preserves the original scoring record fields and adds:

- `prompt`: prompt type and text.
- `image.hash_sha256`: hash of the rendered PNG when available.
- `prediction.backend`: selected backend.
- `prediction.point_xy`: parsed model point, or `null`.
- `prediction.answer`: parsed model answer, or `null`.
- `prediction.parse_status`: `parsed`, `parsed_empty`, or `parse_failed`.
- `prediction.raw_text`: raw model output.
- `model_checkpoint`: local model path or API model name.
- `decoding`: temperature and max-new-token settings.
- `prediction_generated_at_utc`.

The metadata sidecar records input projection-report hash, output JSONL hash,
runner script hash, git commit, git status, backend, model checkpoint, and
`claim_boundary="model_prediction_scores_require_model_provenance_review"`.

## Claim Boundary

This runner enables real VLM evidence, but the script alone is not evidence.
Paper claims require all of the following:

- visual or depth QA accepts the rendered candidate pair,
- a real backend generates `predictions.jsonl`,
- `score_grounding.py` produces `score_summary.json`,
- the resulting artifacts are registered in
  `paper/shared/evidence/results_manifest.yaml`,
- the answer metric is upgraded beyond smoke-grade substring matching before
  final ACL/AAAI claims.

## Verification

Targeted tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_grscenes_vlm_prediction_runner.py
```

Latest local result: `9 passed in 0.61s`.

No live model command was executed. The safe first live probe should use
`--limit 1` and an isolated output path such as
`paper/shared/evidence/raw/grscene_vlm_grounding/probes/qwen_limit1_predictions.jsonl`.
