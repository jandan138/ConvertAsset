# 2026-06-02 ACL Supplement Metric Boundary Bridge

## Scope

Page 15 was one of the lowest-density supplement pages. It contained the
Metric Boundary Summary but no visual evidence, so it still looked like a
sparse text-only page in an otherwise render-heavy supplement. This pass adds a
metric-boundary bridge that ties the derivations to real render evidence.

## What Changed

- Added `paper/shared/figures/fig_supplement_metric_boundary_bridge.png`.
- Added `build_metric_boundary_bridge()` to
  `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Registered the figure in `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/01_derivations.tex` so the
  Metric Boundary Summary remains one-column and includes the full-width visual
  bridge.
- Added layout and source-density tests in `tests/test_paper_layout.py`.
- Recorded provenance in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_metric_boundary_bridge_20260602.json`.

## Imagegen Role

The generated layout reference was:

`/root/.codex/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_0ef86247e532efe7016a1eeb5aa6dc8195b213dcae73893d5a.png`

It was used only for layout direction. The final paper figure is deterministic
and uses registered real render crops.

## Visual Review

The final page-15 render is no longer a sparse text-only page. It now shows
four metric families: proxy render metrics, VLM point-in-box grounding,
material mechanism diagnostics, and navigation metrics. The page active
fraction increased from 0.0202 to 0.13577 at 120 dpi.

Residual risk: small text inside the figure is readable as a visual guide but
not ideal for detailed study. Future passes can simplify the in-figure labels
or replace the navigation thumbnails with cleaner single-frame stills.

## Verification

- Targeted bridge tests first failed before implementation.
- Targeted bridge tests passed after implementation with `2 passed, 44
  deselected`.
- `python -m pytest -q tests/test_paper_layout.py` passed with `46 passed`.
- `make -C paper acl27-supplement` passed and produced a 41-page A4
  supplement.
- A `pdftotext` scan for private paths, author tokens, old red-material caption
  tokens, and `fig_vlm_grounding_cases` returned no matches.
- The source bridge has active fraction 0.303356 and red fraction 0.000148.
- Page 15 is no longer in the low-density page list. The next visual iteration
  targets should be p36, p23, p22, p17, p5, p4, p21, p13, and p14, plus the
  references tail on p41.
