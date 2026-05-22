# 2026-05-22 GRScenes Gemma4 PASS-Only Probe

## Scope

This record documents the first Gemma4 run restricted to visual-QA PASS pairs
only. It replaces the earlier WARN-heavy PASS/WARN pilot as the strongest
current real-model pilot for the ACL material-generalization story, but it is
still not final benchmark evidence.

## Selection

Input label artifacts:

- `paper/shared/evidence/raw/grscene_vlm_grounding/target_projection_qa_report.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/alternative_centerline_target_projection_qa_report.json`

Combined PASS-only artifact:

- `paper/shared/evidence/raw/grscene_vlm_grounding/pass_only_target_projection_qa_report.json`

Selected pairs:

- `c27086f557d316584264.view_001` (`bottle`)
- `e2ec085d524d5df4455d.view_001` (`cup`)
- `e2ec085d524d5df4455d.view_003` (`cup`)
- `c8ee4b66274b05d242c2.view_003` (`faucet`)

The helper `select_projection_subset.py` was added so this combined projection
artifact is reproducible and records source report hashes.

## Artifacts

- `paper/shared/evidence/raw/grscene_vlm_grounding/pass_only_target_projection_qa_report.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_pass_only_predictions.jsonl`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_pass_only_predictions.jsonl.metadata.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_pass_only_selection.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_pass_only_score_summary.json`

## Result

The run produced 8 predictions across 4 original/converted pairs.

Score summary:

- `schema_version=5`
- Raw pixel `point_in_bbox_accuracy`: original 0/4, converted 0/4
- Normalized-1000 `point_in_bbox_normalized_1000_accuracy`: original 4/4,
  converted 3/4
- `answer_accuracy`: original 4/4, converted 4/4
- Normalized-1000 pair hit agreement: 3/4
- Normalized-1000 both-hit pair count: 3/4
- Normalized-1000 mean pair point delta: 27.047455 px

The only normalized-1000 miss is the converted faucet sample
`c8ee4b66274b05d242c2.view_003.converted`.

## Interpretation

This is cleaner than the PASS/WARN probe because all four pairs passed blind
visual QA. It supports the current direction of the paper story: no-MDL
conversion can preserve enough visual semantics for a real VLM to answer target
categories and often ground the object under normalized coordinates, while
material changes can still shift localization on some samples.

Do not cite this as final VLM performance. It is a small pilot with four pairs,
and Gemma4 continues to use normalized visual coordinates even though the prompt
asks for pixel coordinates. Final paper claims still need a frozen coordinate
protocol, a larger PASS set or retakes, and preferably at least one additional
VLM backend.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_projection_subset.py` passed: 3 tests.
- The prediction runner wrote 8 records with local Gemma4.
- The scorer wrote `gemma4_pass_only_score_summary.json` with 8 records.
