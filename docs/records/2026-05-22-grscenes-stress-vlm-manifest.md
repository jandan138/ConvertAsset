# 2026-05-22 GRScenes stress VLM manifest

## What changed

- Added `build_stress_vlm_run_manifest.py` for the GRScenes VLM material-shift stress pool.
- Generated `paper/shared/evidence/raw/grscene_vlm_grounding/stress_vlm_run_manifest.json`.
- Registered the manifest in `paper/shared/evidence/results_manifest.yaml`.
- Documented the stress final gate in `protocol.yaml`, the experiment README, and `paper/EXPERIMENT_CHECKLIST.md`.

## Current status

The stress manifest turns the 14 zoom retake pairs into a controlled VLM input set:

- accepts independent visual-QA `PASS` and `WARN` pairs because both are target-visible enough for stress testing;
- excludes `FAIL`, missing-review, unsupported-verdict, or projection-blocked pairs;
- freezes `structured_text` responses, `normalized_1000` coordinates, and `point_in_bbox_normalized_1000_accuracy`;
- marks the set `pilot_only`, `model-run-ready=true`, and `final_benchmark_claimable=false`.

Current blockers for a final stress benchmark claim:

- only 14 stress pairs, below the 30-pair final gate;
- canonical root `stress_predictions.jsonl` is not present;
- canonical root `stress_score_summary.json` is not present.

The current 14-pair pool spans 5 target categories, so category coverage is not the active blocker.

## Why this matters

Before this change, the zoom stress results existed as pilot probes but did not have a machine-readable claim boundary. The new manifest makes the next experiment explicit: run real VLMs against this frozen stress input set, expand the sample count, and only promote claims after the manifest gate allows it.

Plain version: this is the guardrail that keeps the ACL story honest. The stress data is useful and ready for more model runs, but it is still not final benchmark evidence.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_stress_manifest.py`
- `PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/build_stress_vlm_run_manifest.py`
