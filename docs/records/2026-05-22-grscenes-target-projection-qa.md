# 2026-05-22 GRScenes Target Projection QA

## Scope

This record documents the first image-space target-label gate for the GRScenes
VLM grounding pilot. It follows the corrected centerline-AABB preflight and the
recommended-pair render-smoke batch.

The output is geometric label evidence, not VLM result evidence.

## Changes

- Added
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/project_target_bboxes.py`.
- Added `tests/test_grscenes_vlm_target_projection.py`.
- Generated
  `paper/shared/evidence/raw/grscene_vlm_grounding/target_projection_qa_report.json`.

The projection script is pure Python and import-clean outside Isaac Sim. It
uses the manifest camera fields (`position_world`, `look_at`, `up_world`,
`fov_h_deg`) and each target `world_bbox` to compute a pinhole projected
`bbox_xyxy`.

## Current Report

The current generated report summary is:

| Field | Value |
|---|---:|
| `recommended_pair_count` | 10 |
| `projection_ok_pair_count` | 10 |
| `projection_blocked_pair_count` | 0 |
| `scoring_record_count` | 20 |
| `image_width` | 600 |
| `image_height` | 450 |
| `min_area_px` | 1000.0 |

All 10 recommended render-smoke pairs now have projected target boxes. The 20
scoring records correspond to original/converted material conditions for those
pairs.

## Claim Boundary

This report can support point-in-box scoring setup because it provides
image-space target boxes. It does not prove that a VLM answered correctly, and
it does not prove true visible surface coverage. The boxes are projected from
world-space AABBs, so they can include empty image area around non-box-shaped
objects or fail to capture real occlusion.

Before final paper claims, this gate still needs one of:

- visual QA over the candidate images and projected boxes, or
- depth/mask-level validation from the renderer.

## Verification

Targeted projection tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_grscenes_vlm_target_projection.py
```

Latest local result: `5 passed in 0.55s`.

Generation command:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/project_target_bboxes.py \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/target_projection_qa_report.json
```

Latest local output: `projection_ok=10 records=20`.

## Next

- Run visual QA over the 10 recommended pairs with the projected boxes in mind.
- Produce VLM `predictions.jsonl` using the scoring records.
- Run `score_grounding.py` to produce `score_summary.json`.
