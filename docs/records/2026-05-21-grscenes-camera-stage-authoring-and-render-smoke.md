# 2026-05-21 GRScenes Camera Stage Authoring And Render Smoke

## Scope

This record closes the render-preflight gate after full no-MDL apply. It covers
camera wrapper stage authoring, render-manifest wiring to full scratch inputs,
the first paired Isaac viewport smoke run, and the root-cause findings from
independent visual/code review.

## Changes

- Added `author_render_camera_stages.py` for
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/`.
- Authored 184 thin camera wrapper USD stages under
  `paper/shared/evidence/raw/grscene_vlm_grounding/renders/`.
- Updated `prepare_render_manifest.py` so original render jobs use the full
  scratch input USD, while `source_usd` still records immutable benchmark
  provenance. This avoids source-tree `models` pointer-file resolver failures
  and keeps original/converted renders on the same repaired scratch layout.
- Hardened `scripts/render_with_viewport_capture.py` to lazy-import Isaac Sim,
  wait for `capture_viewport_to_file(...).wait_for_result()`, and verify that a
  non-empty image file exists before reporting a frame as saved.
- Added portable auto-light anchors to camera wrappers:
  `/World/GRScenesRenderDomeLight` and
  `/World/GRScenesRenderDistantLight`.

## Evidence

- `camera_stage_authoring_report.json`:
  - selected records: 184
  - authored camera stages: 184
  - blocked: 0
  - failed: 0
  - auto lights enabled: true
- `render_manifest.json`:
  - render jobs: 184
  - missing material inputs: 0
  - missing camera stages: 0
  - ready-to-run jobs: 184
- `paired_render_smoke_report.json` records the first usable view-001 smoke:
  - both original and converted commands exited 0
  - both images contain visible pixels
  - original stderr contains MDL/KooPbr failure signal; converted does not
  - archived stdout/stderr summaries and hashes live under `render_logs/`

## Findings

- The authored camera matrix is not the primary bug. A PXR check placed the
  target center at approximately `(0, 0, -34.9)` in camera-local coordinates.
- The first attempted view was visually unusable because scene geometry
  occluded the target. The independent visual reviewer marked that pair `FAIL`.
- `view_001` for the same bottle target is visually usable as a smoke sample:
  the bottle and scene context are visible in both material conditions.
- The original condition still logs many missing MDL module failures involving
  `KooPbr` / `KooPbr_maps`. The converted condition removes that signal.
- Independent clean-room visual review marked the retaken pair `WARN`: the
  bottle is visible, but the converted material/color shift is large enough
  that this image pair should not be used as final VLM grounding evidence.
- Therefore, the current smoke result is evidence that the local Isaac viewport
  stack can render a paired sample and expose the MDL/no-MDL material
  difference. It is not yet VLM task-performance evidence.

## Verification

Commands run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_render_with_viewport_capture.py \
  tests/test_grscenes_vlm_render_manifest.py \
  tests/test_grscenes_vlm_author_camera_stages.py

PYTHONDONTWRITEBYTECODE=1 ./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/author_render_camera_stages.py \
  --include-existing --overwrite --apply

PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py \
  --nomdl-run-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json \
  --require-converted

PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_paired_render_smoke.py \
  --pair-id c27086f557d316584264.view_001
```

The paired smoke script executes the `render_command` entries from
`render_manifest.json`, archives `.txt` stdout/stderr logs, and writes image
hashes, log hashes, and the executed viewport renderer script hash into
`paired_render_smoke_report.json`.

## Open Issues

- Implement visibility-aware camera selection before full batch rendering:
  reject camera eyes inside non-target geometry and reject rays that hit
  non-target geometry before the target.
- Migrate the richer HDRI/background/auto-exposure runtime behavior from
  `convert_asset.render.single` into the viewport renderer behind an explicit
  flag, rather than relying only on wrapper-authored lights.
- Add image-space bbox or mask projection before VLM grounding scoring.
- Do not claim final ACL/VLM results until rendered images, VLM predictions,
  scores, qualitative figures, and reviewer-style checks all exist.
