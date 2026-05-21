# 2026-05-21 GRScenes Visibility Preflight

## Scope

This record starts the next render gate after camera-stage authoring and paired
smoke. The goal is to avoid batch-rendering camera views that are visibly bad
for VLM grounding: camera inside geometry, line of sight blocked before the
target, or no clear candidate for a target.

## Changes

- Added `plan_visibility_aware_views.py` under the GRScenes VLM experiment
  directory.
- Added pure-Python AABB segment tests for the first visibility contract:
  - segment-to-AABB intersection interval
  - camera inside non-target obstacle
  - obstacle before target
  - obstacle behind target
  - first clear view selection per target

## Design Boundary

This first implementation does not open USD stages. It accepts an explicit
`geometry_index` mapping scene ids to obstacle bboxes. The next step is a
PXR/Isaac stage scanner that populates this geometry index from composed
GRScenes stages while preserving lazy `pxr` imports.

The classifier is intentionally approximate. It uses axis-aligned boxes as a
cheap preflight, not final visibility proof. Rendered-image visual review and
image-space target boxes are still required before VLM scoring.

## Verification

Command run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_grscenes_vlm_visibility_preflight.py
```

Result:

```text
5 passed
```

## Next

- Add a USD/PXR geometry-index extractor that computes visible non-target
  boundable bboxes per scene.
- Run the preflight over `render_manifest.json` and emit
  `visibility_preflight_report.json`.
- Use the recommended clear pairs to drive the next paired render batch.
