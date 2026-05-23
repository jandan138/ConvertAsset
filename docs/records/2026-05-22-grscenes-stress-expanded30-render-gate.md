# 2026-05-22 GRScenes stress expanded30 render gate

## What changed

The material-shift stress pool was expanded from the original 14 visually accepted
zoom pairs to an exactly-30 pair input manifest:

- rendered 16 first-pass expansion candidates;
- independently visual-reviewed those 16 pairs;
- rejected 5 machine-passing but human-failing views;
- rendered and reviewed 11 replacement cup candidates;
- selected 5 replacement cup/mug views for the final exactly-30 stress pool;
- generated `stress_vlm_run_manifest_expanded30.json`.

## Key artifacts

First expansion batch:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expansion16_paired_render_summary.json
paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expansion16_target_projection_qa_report.json
paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expansion16_visual_review_batch.json
```

Replacement batch:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_replacement11_paired_render_summary.json
paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_replacement11_target_projection_qa_report.json
paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_replacement11_visual_review_batch.json
```

Exactly-30 manifest gate:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_paired_render_summary.json
paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json
paper/shared/evidence/raw/grscene_vlm_grounding/stress_vlm_run_manifest_expanded30.json
```

## Current status

The expanded stress manifest is now ready for real VLM inference:

```text
stress_pair_count: 30
stress_scoring_record_count: 60
stress_verdict_counts: PASS 4, WARN 26
render_smoke_pass_count: 30
projection_ok_pair_count: 30
ready_for_model_run: true
ready_for_final_benchmark_run: false
```

Remaining blockers are expected:

```text
canonical_predictions_missing
canonical_score_summary_missing
```

Plain version: the rendering and target-label gates are now good enough to run
Gemma4/Qwen over the 30-pair stress pool. It is still not citable stress-set
evidence until real model predictions and score summaries are generated.

## Important lesson

The biggest pitfall was assuming machine gates are enough. They are not.

`retake_zoom_expansion16_paired_render_summary.json` and
`retake_zoom_expansion16_target_projection_qa_report.json` both passed 16/16,
but clean-room visual review rejected 5/16 because the target was not actually
human-identifiable enough:

- two pillow views were too occluded;
- two clock/picture views missed or hid the intended object;
- one clock view had no clearly visible clock face.

This is why `render-visual-reviewer` style clean-room review must stay between
projection QA and VLM scoring. The scoring manifest should never blindly consume
all projection-passing pairs.

## Selection rationale

The final exactly-30 pool is:

- the original 14 visually accepted zoom stress pairs;
- 11 usable pairs from the first expansion batch;
- 5 selected close cup/mug replacements from `e2ec085d524d5df4455d`.

The final category counts are:

```text
backpack: 3
bottle: 3
clock: 5
cup: 10
faucet: 4
picture: 3
pillow: 1
plate: 1
```

This exceeds the stress gate of at least 30 pairs and at least 5 categories.
It does skew toward cup examples because the remaining centerline-clear backup
candidates were all cups; the paper should report this as a limitation rather
than imply balanced category coverage.

## Storage and safety

This round wrote only render evidence under:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_*
```

Approximate local size after the run:

```text
retake_zoom_render_logs: 67 MiB
retake_zoom_renders: 24 MiB
retake_zoom_paired_render_reports: 2.8 MiB
```

No source asset tree was modified. Do not run the remaining 138-pair zoom
manifest just to increase sample count; the current gate is satisfied and the
next bottleneck is VLM inference.

## Next gate

Run the real VLM backends against:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/stress_vlm_run_manifest_expanded30.json
```

Use the existing structured-text normalized-1000 protocol. The output should be
new canonical expanded-stress prediction and score files, not replacements for
the older 14-pair pilot probes unless the manuscript is intentionally updated.

## 2026-05-23 VLM inference and paper integration update

The next gate above has now been executed.

Canonical Gemma4 stress outputs:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/stress_predictions.jsonl
paper/shared/evidence/raw/grscene_vlm_grounding/stress_predictions.jsonl.metadata.json
paper/shared/evidence/raw/grscene_vlm_grounding/stress_score_summary.json
```

Second-model Qwen2.5-VL diagnostic outputs:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/stress_expanded30_probes/qwen25_stress_expanded30_structured_predictions.jsonl
paper/shared/evidence/raw/grscene_vlm_grounding/stress_expanded30_probes/qwen25_stress_expanded30_structured_predictions.jsonl.metadata.json
paper/shared/evidence/raw/grscene_vlm_grounding/stress_expanded30_probes/qwen25_stress_expanded30_structured_score_summary.json
```

After regenerating `stress_vlm_run_manifest_expanded30.json`, the
manifest-internal stress gate is open:

```text
claim_status: final_stress_benchmark_ready
final_benchmark_claimable: true
ready_for_final_benchmark_run: true
blockers: []
```

Paper wording caveat: despite the legacy field names above, the ACL text should
describe this as a frozen 30-pair target-centered stress set, not a broad
GRScenes benchmark.

Gemma4 result summary:

```text
answer accuracy: 30/30 original, 30/30 converted
normalized-1000 point-in-bbox: 27/30 original, 29/30 converted
normalized-1000 pair hit agreement: 28/30
normalized-1000 both-hit pairs: 27/30
raw pixel point-in-bbox diagnostic: 1/30 original, 1/30 converted
```

Qwen2.5-VL diagnostic summary:

```text
scorable answer rows: 55/60
answer hits: 27/29 original, 24/26 converted
raw point-in-bbox: 22/29 original, 19/29 converted
normalized-1000 point-in-bbox: 3/29 original, 3/29 converted
```

Paper integration changes:

- added `paper/shared/tables/gen_vlm_stress_expanded30.py`;
- generated `grscenes_vlm_stress_expanded30.csv` and
  `tab_grscenes_vlm_stress_expanded30.tex`;
- updated `paper/shared/sections/experiments.tex` to use the expanded30 stress
  result instead of the old 14-pair zoom stress pilot as the main stress table;
- updated `fig_vlm_grounding_cases` so the stress examples point to the
  expanded30 outputs;
- registered the new raw outputs and table in
  `paper/shared/evidence/results_manifest.yaml`;
- updated the ACL wrapper abstract, introduction, conclusion, and status.

One visual QA pass over the updated grounding-case figure returned `WARN`
because the original status-line formatting made the bottom-right answer look
truncated. A later independent visual QA pass still warned that long IDs, small
point markers, and tight lower padding reduced print readability. The figure
generator now removes long pair IDs from panel titles, uses larger haloed point
markers, and increases cell/padding height before regenerating the PNG/PDF.

## 2026-05-23 provenance and final-gate hardening

Reviewer-style evidence audit caught two reproducibility pitfalls:

- `protocol.yaml` had been updated after the expanded30 manifest was first
  generated, so the manifest's stored protocol hash was stale.
- The stress manifest final gate only checked that canonical prediction and
  score files existed; it did not prove that those files covered the exact 60
  manifest sample IDs in order.

Fixes applied:

- `build_stress_vlm_run_manifest.py` now validates canonical prediction JSONL
  row count, score-summary `num_records`, and exact `sample_id` alignment before
  opening the final stress gate.
- The claim-gate wording was narrowed to
  `frozen 30-pair target-centered material-shift stress set`.
- `stress_vlm_run_manifest_expanded30.json` was regenerated from the current
  protocol and the three visual-review reports.
- Gemma4 canonical and Qwen2.5-VL diagnostic predictions were rerun against the
  regenerated manifest, then both score summaries were regenerated.

Fresh provenance check:

```text
manifest hash: ac5a5f9783367e6ea7b39aed2d84953c9b25b6dbbcd5338704c32143574352af
protocol hash matches current protocol.yaml: true
Gemma4 metadata manifest hash match: true
Qwen2.5-VL metadata manifest hash match: true
Gemma4 prediction/score sample_id alignment: 60/60 true
Qwen2.5-VL prediction/score sample_id alignment: 60/60 true
```
