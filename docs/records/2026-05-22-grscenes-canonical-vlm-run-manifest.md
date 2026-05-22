# 2026-05-22 GRScenes Canonical VLM Run Manifest

## Scope

This record documents the canonical VLM input/protocol manifest added after the
four-pair GRScenes PASS-only pilot table. It does not add new model
predictions. It turns the current visual-QA PASS/WARN/FAIL evidence into a
machine-readable run gate for the next frozen-protocol VLM pass.

## What Changed

- Added
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/build_canonical_vlm_run_manifest.py`.
- Generated
  `paper/shared/evidence/raw/grscene_vlm_grounding/canonical_vlm_run_manifest.json`.
- Added `tests/test_grscenes_vlm_canonical_manifest.py`.
- Registered the manifest in `paper/shared/evidence/results_manifest.yaml`.
- Updated `claims.yaml`, `paper/EXPERIMENT_CHECKLIST.md`, the raw-output
  README, the experiment README, and the Experiments section wording.

## Manifest Semantics

The manifest is input/protocol evidence, not model-result evidence. It verifies
that the selected PASS-only projection records are backed by independent blind
visual review, then separates the available image pairs into:

- 4 PASS pairs and 8 runner-compatible scoring records.
- 11 WARN retake candidates.
- 6 FAIL exclusions.

The next-run protocol is fixed as:

- `coordinate_frame=normalized_1000`
- `response_format=structured_text`
- primary point metric: `point_in_bbox_normalized_1000_accuracy`

The manifest records both top-level and nested claim-gate fields:

- `claim_status=pilot_only`
- `final_benchmark_claimable=false`
- blocked by the small PASS pool, missing canonical `predictions.jsonl`,
  missing canonical `score_summary.json`, legacy Gemma4 probe protocol, and
  unresolved Qwen coordinate semantics.

Plain version: the current four-pair pilot can keep driving protocol debugging,
but it still cannot become the final ACL VLM benchmark result.

## Review Input

Two read-only review agents agreed that the manifest is the right next step.
Their main points were:

- `pass_only_target_projection_qa_report.json` proves projection labels, but
  the PASS status must be traced back to the blind visual-review reports.
- Existing Gemma4 PASS-only output is a historical pixel-prompt probe with a
  normalized-1000 diagnostic, not a frozen canonical protocol run.
- Existing Qwen structured output uses normalized-1000 + structured text, but
  its coordinate semantics remain unresolved, so it remains
  protocol-sensitivity evidence.
- Final VLM tables must not be generated from runs whose canonical manifest
  has `final_benchmark_claimable=false`.

## Next Step

Use `canonical_vlm_run_manifest.json` as the audit source for the next
frozen-protocol model pass. For final paper results, first expand the PASS pool
by retaking WARN views or adding clearer views, then rerun Gemma4 and Qwen under
the same frozen protocol and score canonical `predictions.jsonl`.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_canonical_manifest.py` failed first because the generator did not exist.
- After implementation and review-driven gate fields, the same test passed:
  3 tests.
- `python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/build_canonical_vlm_run_manifest.py` generated the checked-in manifest with 4 PASS pairs, 11 WARN retake candidates, 6 FAIL exclusions, `pilot_ready=true`, and `final_ready=false`.
