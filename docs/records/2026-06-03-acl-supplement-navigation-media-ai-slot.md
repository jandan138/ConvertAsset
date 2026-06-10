# 2026-06-03 ACL Supplement Navigation Media AI Slot

## Scope

The InternNav media-inventory boundary page was still one of the sparsest
supplement pages. This pass uses the `research-figure-ai-slot-composer`
workflow to add a navigation media boundary strip that combines registered
navigation stills with an explicitly disclosed AI-generated media-package gate
slot.

## What Changed

- Added `paper/shared/figures/ai_slots/fig_supplement_navigation_media_package_ai_slot.png`.
- Added
  `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_media_boundary_strip.yaml`.
- Added `paper/shared/figures/fig_supplement_navigation_media_boundary_strip.png`.
- Added `build_navigation_media_boundary_strip()` to
  `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Registered the figure in `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex`
  to include the new strip in the Media Inventory Boundary subsection.
- Added regression tests in `tests/test_paper_layout.py`.
- Recorded structured evidence in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_media_boundary_ai_slot_20260603.json`.

## AI Slot Policy

The AI-generated slot is used only as exposition for the media-package approval
gate. It is not navigation evidence and is not used for any metric. Critical
labels, row titles, claim-boundary text, and the caption are drawn by
deterministic code or LaTeX.

The AI slot can be replaced later by a real media-upload screenshot or a
deterministic manifest visualization without changing the surrounding figure
layout.

## Visual Review

The rendered page has no clipping or caption collision. It now shows selected
stills, route overlays, manifest/media-package context, and the author approval
boundary on the same page. The page active fraction at 170 dpi is `0.099078`,
up from the previous low-density page active fraction of `0.0205`.

Residual risk: small in-figure text remains visible but not ideal for detailed
reading. The figure is acceptable as a media-boundary guide, not as a primary
metric table.

## Verification

- Targeted navigation-media-boundary tests failed before implementation.
- Targeted tests passed after implementation with `3 passed, 49 deselected`.
- `python -m pytest -q tests/test_paper_layout.py` passed with `52 passed`.
- `make -C paper acl27-supplement` passed and produced a 43-page A4 supplement.
- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `73472e88977d2fecd5504722909509920275046401d589589c65f26a853ee5a2`.
- `fig_supplement_navigation_media_boundary_strip.png` SHA-256:
  `59199f41290ff01d58b60b73200d1bc24e64a841d7ffe4021fec6ca2494b0cbd`.
- `pdftotext` found the new Figure S23 caption and its AI-generated schematic
  disclosure.
- A risk-token scan found no old red-material caption tokens,
  `fig_vlm_grounding_cases`, author-identifying tokens, or local path tokens.
