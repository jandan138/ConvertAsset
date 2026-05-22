# 2026-05-22 GRScenes Alternative Centerline Render Views

## Scope

This record documents the first alternative-view expansion after the initial
blind visual-QA batch found that the 10 default recommended render pairs were
not clean enough for final VLM metrics. The goal was to look for better camera
views inside the already planned GRScenes render manifest, without touching the
immutable source dataset.

## Selection

Input artifact:

- `paper/shared/evidence/raw/grscene_vlm_grounding/visibility_preflight_report.json`

The visibility preflight had 21 `centerline_clear` pairs. Ten were already in
the first recommended render batch, so this pass rendered the remaining 11
clear pairs:

- `f35ef3d86c42446b7ddf.view_002`
- `bb985fd4504a1afe8516.view_001`
- `bb985fd4504a1afe8516.view_002`
- `bb985fd4504a1afe8516.view_003`
- `e2ec085d524d5df4455d.view_001`
- `e2ec085d524d5df4455d.view_003`
- `f405f964229ca3d3fbad.view_001`
- `f405f964229ca3d3fbad.view_002`
- `f405f964229ca3d3fbad.view_003`
- `c8ee4b66274b05d242c2.view_003`
- `1e397951c1926c7f0a0b.view_003`

## Artifacts

- `paper/shared/evidence/raw/grscene_vlm_grounding/alternative_centerline_paired_render_summary.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/alternative_centerline_target_projection_qa_report.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/alternative_centerline_visual_review_batch.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/paired_render_reports/*.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/renders/`
- `paper/shared/evidence/raw/grscene_vlm_grounding/render_logs/`

## Result

Render and projection gates:

- 11/11 alternative pairs passed paired render smoke.
- 11/11 alternative pairs have `projection_ok` target boxes.
- The new `project_target_bboxes.py --pair-id` option generated the
  alternative projection report without relying on the default
  `recommended_pairs_by_target` selection.

Independent clean-room visual QA:

- PASS: 3 pairs.
- WARN: 6 pairs.
- FAIL: 2 pairs.

New PASS candidates:

- `e2ec085d524d5df4455d.view_001` (`cup`)
- `e2ec085d524d5df4455d.view_003` (`cup`)
- `c8ee4b66274b05d242c2.view_003` (`faucet`)

Together with the original PASS pair
`c27086f557d316584264.view_001`, the current clean VLM probe pool is four
original/converted pairs.

## Storage

This pass added roughly 13M of rendered PNGs, 29M of render logs, and 377K of
paired render reports. No large monolithic artifact was introduced.

## Claim Boundary

These artifacts support only candidate filtering and experiment routing:

- the renderer can produce non-dark original/converted PNGs for the 11 extra
  centerline-clear views,
- geometric projected boxes exist for these views,
- independent visual QA identifies three additional clean PASS candidates.

They are not final VLM performance evidence. WARN/FAIL pairs must either be
retaken or explicitly reported as lower-quality visual-QA tiers. The next
publishable experiment step is a PASS-only Gemma4 run over the four clean
pairs, with one combined projection artifact preserving label provenance.
