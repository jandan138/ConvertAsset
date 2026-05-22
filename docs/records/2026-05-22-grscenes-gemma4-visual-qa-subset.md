# 2026-05-22 GRScenes Gemma4 Visual-QA Subset Probe

## Scope

This record documents the first Gemma4 run beyond the single P01 smoke probe.
It uses only the render pairs accepted by the independent visual-QA filter as
`PASS` or `WARN`, while keeping `FAIL` pairs excluded.

## Selection

Input visual-QA artifact:

- `paper/shared/evidence/raw/grscene_vlm_grounding/paired_render_visual_review_batch.json`

Selected pairs:

- PASS: `c27086f557d316584264.view_001` (`bottle`)
- WARN: `32ba3ade1a8e63c981af.view_002` (`plate`)
- WARN: `bb985fd4504a1afe8516.view_000` (`cup`)
- WARN: `e2ec085d524d5df4455d.view_000` (`cup`)
- WARN: `c8ee4b66274b05d242c2.view_000` (`faucet`)
- WARN: `90e105daa7e6ff59da38.view_002` (`picture`)

Excluded pairs stayed excluded: P03, P06, P08, and P09.

## Artifacts

- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_visual_qa_pass_warn_predictions.jsonl`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_visual_qa_pass_warn_predictions.jsonl.metadata.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_visual_qa_pass_warn_selection.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_visual_qa_pass_warn_score_summary.json`

The output is still under `probes/` and is not canonical
`predictions.jsonl`.

## Result

The run produced 12 predictions across 6 original/converted pairs.

Score summary:

- `schema_version=5`
- Raw pixel `point_in_bbox_accuracy`: original 0/6, converted 0/6
- Raw pixel `point_in_image_accuracy`: original 1/6, converted 0/6
- Normalized-1000 `point_in_bbox_normalized_1000_accuracy`: original 4/6,
  converted 3/6
- `answer_accuracy`: original 6/6, converted 6/6
- Normalized-1000 pair hit agreement: 5/6
- Normalized-1000 both-hit pair count: 3/6
- Normalized-1000 mean pair point delta: 20.931062 px

Interpretation: Gemma4 is consistently producing category strings and appears
to use normalized visual coordinates more than raw pixels. The converted
condition is slightly worse than original on normalized-1000 point-in-box in
this small pilot, but five of six pairs are visual-QA `WARN`, so this must not
be cited as final model robustness or material-generalization evidence.

## Claim Boundary

This probe supports only:

- the local Gemma4 backend can run on a QA-filtered render subset,
- the scorer can separate raw-pixel and normalized-1000 coordinate conventions,
- normalized-1000 pair consistency is now available for original-vs-converted
  comparisons,
- the selection sidecar records the PASS/WARN/FAIL split in machine-readable
  form,
- the next experiment should either retake WARN pairs or clearly report the
  visual-QA tier of each scored sample.

Final paper claims still require a larger QA-accepted set, an explicit
coordinate protocol, and a frozen canonical `predictions.jsonl` /
`score_summary.json` pair.
