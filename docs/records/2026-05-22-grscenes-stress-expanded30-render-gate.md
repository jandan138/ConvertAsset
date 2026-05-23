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
Gemma4/Qwen over the 30-pair stress pool. It is still not final benchmark
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
