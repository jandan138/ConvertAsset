# 2026-05-22 GRScenes stress expansion candidates

## Current count

The material-shift stress manifest currently has 14 target-visible zoom pairs. The final stress gate requires at least 30 pairs, so the next expansion needs 16 additional visually accepted pairs.

`retake_zoom_visibility_preflight_report.json` contains 41 centerline-clear zoom pairs. Fourteen have already been rendered and visually reviewed in `retake_zoom_visual_review_batch.json`, leaving 27 centerline-clear candidates.

## Recommended first expansion batch

Prioritize non-cup categories first, then add enough cup candidates to reach 16 pairs:

| Pair id | Category | Scene |
|---|---|---|
| `c27086f557d316584264.zoom_018` | bottle | `MV7J6NIKTKJZ2AABAAAAADA8_usd` |
| `c27086f557d316584264.zoom_019` | bottle | `MV7J6NIKTKJZ2AABAAAAADA8_usd` |
| `21dde4a14ca93f539a47.zoom_017` | pillow | `MV7J6NIKTKJZ2AABAAAAADA8_usd` |
| `21dde4a14ca93f539a47.zoom_021` | pillow | `MV7J6NIKTKJZ2AABAAAAADA8_usd` |
| `32ba3ade1a8e63c981af.zoom_019` | plate | `MV7J6NIKTKJZ2AABAAAAADA8_usd` |
| `ef6a4fe9448f672c2ecc.zoom_021` | picture | `MV7J6NIKTKJZ2AABAAAAADI8_usd` |
| `f35ef3d86c42446b7ddf.zoom_020` | clock | `MV7J6NIKTKJZ2AABAAAAADQ8_usd` |
| `2c2bd8f1c808f5a4b227.zoom_019` | bottle | `MV7J6NIKTKJZ2AABAAAAAEA8_usd` |
| `1e397951c1926c7f0a0b.zoom_020` | clock | `MV7J6NIKTKJZ2AABAAAAAEA8_usd` |
| `1e397951c1926c7f0a0b.zoom_021` | clock | `MV7J6NIKTKJZ2AABAAAAAEA8_usd` |
| `90e105daa7e6ff59da38.zoom_020` | picture | `MV7J6NIKTKJZ2AABAAAAAEA8_usd` |
| `bb985fd4504a1afe8516.zoom_017` | cup | `MV7J6NIKTKJZ2AABAAAAADQ8_usd` |
| `bb985fd4504a1afe8516.zoom_018` | cup | `MV7J6NIKTKJZ2AABAAAAADQ8_usd` |
| `bb985fd4504a1afe8516.zoom_019` | cup | `MV7J6NIKTKJZ2AABAAAAADQ8_usd` |
| `bb985fd4504a1afe8516.zoom_020` | cup | `MV7J6NIKTKJZ2AABAAAAADQ8_usd` |
| `bb985fd4504a1afe8516.zoom_021` | cup | `MV7J6NIKTKJZ2AABAAAAADQ8_usd` |

This batch would bring the candidate pool from 14 to 30 pairs before visual QA. It also adds bottle, plate, and cup categories to the current stress category mix.

## Execution notes

- Camera stages for the zoom render manifest have already been authored; the checked `retake_zoom_camera_stage_authoring_report.json` reports 276 authored camera stages and zero failures.
- The current 14 zoom rendered pairs occupy only about 10 MiB of render images and 19 MiB of logs, so rendering this first 16-pair expansion is compatible with the current storage budget.
- Run paired render smoke for each pair into `retake_zoom_paired_render_reports/` and `retake_zoom_render_logs/`, then regenerate a selected render summary and projection QA before visual review.
- Do not add these pairs to `stress_vlm_run_manifest.json` until render smoke, projection QA, and independent visual review pass.

## Plain version

We do not need a new dataset to reach the 30-pair stress gate. The existing zoom preflight already found enough plausible camera/target pairs. The next real work is rendering and visually reviewing 16 more pairs, not changing the paper story.
