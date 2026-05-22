# 2026-05-22 GRScenes Canonical VLM Model Probes

## Plain Summary

This round moved the ACL VLM experiment one step forward: the four visual-QA
PASS pairs were rerun with real local models under the frozen canonical prompt
contract from `canonical_vlm_run_manifest.json`.

These are still pilot outputs. They prove that the frozen protocol can drive
Gemma4 and Qwen2.5-VL end to end, but they do not make a final GRScenes
benchmark claim because the manifest still has only four PASS pairs and
`final_benchmark_claimable=false`.

## Outputs

New pilot outputs live under:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/canonical_probes/
```

Files:

- `gemma4_canonical_pass_only_predictions.jsonl`
- `gemma4_canonical_pass_only_predictions.jsonl.metadata.json`
- `gemma4_canonical_pass_only_score_summary.json`
- `qwen25_canonical_pass_only_predictions.jsonl`
- `qwen25_canonical_pass_only_predictions.jsonl.metadata.json`
- `qwen25_canonical_pass_only_score_summary.json`

These paths are intentionally not the root `predictions.jsonl` and
`score_summary.json`. Root canonical outputs remain reserved for a future
final-claimable manifest.

## Results

Gemma4 canonical frozen-protocol pilot:

- 8 prediction rows, 4 original and 4 converted.
- Answer accuracy: 4/4 original, 4/4 converted.
- Normalized-1000 point-in-box: 2/4 original, 3/4 converted.
- Raw-pixel point-in-box: 0/4 original, 0/4 converted.

Qwen2.5-VL canonical frozen-protocol pilot:

- 8 prediction rows, 4 original and 4 converted.
- Answer accuracy: 3/4 original, 3/4 converted.
- Parsed point rows: 3/4 original, 4/4 converted.
- Normalized-1000 point-in-box: 0/3 original, 0/4 converted.
- Raw-pixel point-in-box: 2/3 original, 2/4 converted.

Interpretation: Gemma4 is stable on category answers and partly usable for
normalized-1000 points in this tiny pool. Qwen2.5-VL remains useful as a
protocol-sensitivity probe because the frozen structured-text prompt fixes the
JSON parsing failure, but coordinate semantics are still unresolved.

## Design Decisions

- Kept the rerun under `canonical_probes/` instead of root `predictions.jsonl`.
  This prevents a four-pair pilot from looking like the final benchmark run.
- Registered the rerun in `results_manifest.yaml` and `claims.yaml` as
  pilot-only evidence.
- Updated manuscript prose to separate the older initial PASS-only table from
  the new manifest-aligned frozen-protocol rerun.
- Fixed `run_vlm_predictions.py` so model-output rows overwrite any inherited
  input-manifest `claim_boundary` with
  `model_prediction_scores_require_model_provenance_review`.

## Pitfalls

- The new Gemma4 rerun does not match the old historical Gemma4 pilot numbers:
  old normalized-1000 point score was 4/4 original and 3/4 converted; frozen
  rerun is 2/4 original and 3/4 converted. Do not silently replace one with the
  other.
- `canonical_probes/` means "manifest-aligned pilot rerun", not "final canonical
  benchmark".
- The scorer's top-level real-model boundary is generic. Downstream paper
  claims must also consult `canonical_vlm_run_manifest.json`, especially
  `final_benchmark_claimable`.
- Gemma4 runtime warned that Flash Attention 2 is broken and Unsloth fell back
  to Xformers. This is not a result blocker for the small pilot, but it is a
  runtime reproducibility note.
- Qwen runtime warned that the fast image processor is now the default and that
  the `temperature` generation flag may be ignored when deterministic decoding
  is used. Record this before treating future Qwen deltas as model-only effects.

## Commands

Gemma4 prediction:

```bash
CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 \
  /cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py \
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/canonical_vlm_run_manifest.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/canonical_probes/gemma4_canonical_pass_only_predictions.jsonl \
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
  --projection-report paper/shared/evidence/raw/grscene_vlm_grounding/canonical_vlm_run_manifest.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/canonical_probes/qwen25_canonical_pass_only_predictions.jsonl \
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
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/canonical_probes/gemma4_canonical_pass_only_predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/canonical_probes/gemma4_canonical_pass_only_score_summary.json

python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py \
  --predictions paper/shared/evidence/raw/grscene_vlm_grounding/canonical_probes/qwen25_canonical_pass_only_predictions.jsonl \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/canonical_probes/qwen25_canonical_pass_only_score_summary.json
```

## Verification

- TDD red check confirmed that model prediction rows previously inherited
  `canonical_input_manifest_only_not_model_metric_evidence` from the input
  manifest.
- After the runner fix,
  `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_prediction_runner.py`
  passed with 16 tests.
- Post-rerun spot check confirmed all six canonical-probe files exist and
  prediction rows now use
  `model_prediction_scores_require_model_provenance_review`.

## Next Step

Expand the PASS render pool. The current four-pair rerun is enough to validate
the plumbing and protocol, but the paper still needs a larger final-claimable
run before making any VLM robustness claim.
