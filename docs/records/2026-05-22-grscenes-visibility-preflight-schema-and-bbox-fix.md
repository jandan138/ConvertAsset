# 2026-05-22 GRScenes Visibility Preflight Schema And BBox Fix

## Scope

This record updates the GRScenes visibility preflight status after the
geometry-index extraction and preflight planner were corrected. It supersedes
the earlier interpretation that `visibility_preflight_report.json` showed
`92/92` clear render pairs.

The preflight remains an approximate centerline-vs-AABB gate. It is useful for
rejecting obviously bad camera/target pairs before rendering, but it is not
image-space visibility proof and it is not VLM evidence.

## Root Cause

The previous `visibility_preflight_report.json` result with `92/92` clear pairs
was invalid evidence. `plan_visibility_aware_views.py` expected a direct
`scene_id -> obstacles` mapping, but the CLI was given the complete
`visibility_geometry_index.json` report wrapper. The planner treated the wrapper
top-level keys as scene ids, so manifest scene ids did not match and every
scene effectively ran with `obstacles=[]`.

That failure mode made all pairs appear clear even when the geometry extractor
had produced obstacle bboxes.

## Changes

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_visibility_aware_views.py`
  now accepts both geometry input shapes:
  - direct `scene_id -> obstacles` mapping
  - full `visibility_geometry_index.json` report wrapper containing
    `geometry_index`
- The planner validates geometry coverage for every scene referenced by the
  render manifest. Missing geometry now raises an error instead of silently
  producing clear views.
- Visibility status names now state the actual preflight method:
  - `centerline_clear`
  - `blocked_centerline_aabb`
  - `blocked_camera_inside_obstacle_aabb`
- The report summary records the method as
  `single_centerline_vs_non_target_aabb_preflight` and the claim boundary as
  `preflight_only_not_rendered_visibility_or_vlm_evidence`.
- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/extract_visibility_geometry_index.py`
  filters extreme or overlarge bboxes before they enter the obstacle index:
  - `--max-diagonal`, default `1000.0`
  - `--max-abs-coordinate`, default `1e6`

The bbox filters prevent USD max-float bounds or very large instanced
components from swallowing the entire scene and blocking every centerline.

## Current Report

The current generated `visibility_geometry_index.json` summary is:

| Field | Value |
|---|---:|
| `scene_count` | 5 |
| `obstacle_count` | 19435 |
| `failed_scene_count` | 0 |

The current generated `visibility_preflight_report.json` summary is:

| Field | Value |
|---|---:|
| `render_pair_count` | 92 |
| `centerline_clear_pair_count` | 21 |
| `blocked_pair_count` | 71 |
| `recommended_target_count` | 10 |

The status distribution is:

| Status | Count |
|---|---:|
| `blocked_camera_inside_obstacle_aabb` | 7 |
| `blocked_centerline_aabb` | 64 |
| `centerline_clear` | 21 |

The recommended-pair render smoke follow-up produced:

| Field | Value |
|---|---:|
| `recommended_pair_count` | 10 |
| `reports_found_count` | 10 |
| `report_dir_count` | 9 |
| `fallback_report_count` | 1 |
| `paired_non_dark_render_smoke_count` | 10 |
| `black_or_missing_image_count` | 0 |
| `render_smoke_pass_count` | 10 |

The aggregate is stored in
`paper/shared/evidence/raw/grscene_vlm_grounding/recommended_paired_render_summary.json`.
It aggregates 9 new per-pair reports under `paired_render_reports/` plus the
earlier `paired_render_smoke_report.json` fallback.

## Claim Boundary

Use this report only as a pre-render filtering aid:

- `centerline_clear` means the camera-to-target centerline did not hit a
  non-target obstacle AABB before the target AABB.
- `blocked_centerline_aabb` means a non-target obstacle AABB intersects the
  centerline before the target interval.
- `blocked_camera_inside_obstacle_aabb` means the camera position lies inside a
  non-target obstacle AABB.

These labels do not prove that the target is visible in the rendered image.
They do not account for full target extent, image-space occlusion, material
state, transparency, thin geometry, camera projection, or final VLM grounding
behavior.

Use `recommended_paired_render_summary.json` only as render-smoke evidence:
the candidate images exist, have hashes, and are not all black. It still does
not prove image-space target coverage, visual quality, fair material
comparison, or VLM task performance.

## Verification

The relevant unit coverage is:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_grscenes_vlm_visibility_preflight.py \
  tests/test_grscenes_vlm_visibility_geometry_index.py \
  tests/test_grscenes_vlm_recommended_render_summary.py
```

Latest local targeted result: `17 passed in 0.63s`.

The full local suite also passed:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

Latest local result: `184 passed in 6.72s`.

The generated report summaries above were read from:

- `paper/shared/evidence/raw/grscene_vlm_grounding/visibility_geometry_index.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/visibility_preflight_report.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/recommended_paired_render_summary.json`

## Next

- Run image-space projection/bbox or mask QA over the rendered recommended
  pairs before using them as paper evidence.
- Run independent visual QA over the recommended candidate images.
- Treat the preflight report as a candidate selector only, not as final
  visibility or VLM completion evidence.
