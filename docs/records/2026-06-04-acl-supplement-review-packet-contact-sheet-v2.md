# 2026-06-04 ACL supplement review-packet contact sheet v2

## Summary

Reworked the page-42 review-packet media manifest into a denser render-backed contact sheet. The figure now uses more registered render/source figures while preserving the review-packet claim boundary.

## Changes

- Rebuilt `paper/shared/figures/fig_supplement_review_packet_contact_sheet.png` as a `1800x2200` portrait board.
- Added a dedicated `Render evidence` row using `fig_supplement_render_scene_evidence_extended.png`.
- Registered additional source figures:
  - `paper/shared/figures/fig_supplement_render_atlas.png`
  - `paper/shared/figures/fig_supplement_render_scene_evidence_extended.png`
  - `paper/shared/figures/fig_supplement_navigation_media_boundary_strip.png`
- Updated `paper/venues/acl27/sections/supplement/07_reproducibility.tex` to place the figure at `0.98\textwidth` and `0.78\textheight`.
- Tightened the contact sheet label lane without treating any thumbnail as new evidence.

## Visual Review

- Standalone PNG: PASS, five rows are contained and row labels do not overlap thumbnails.
- PDF page 42: PASS, no clipping or caption collision after the larger include height.
- Dense crops reviewed:
  - `tmp/acl_supplement_page42_review_packet_v2_20260604/crops/page42_render_rows.png`
  - `tmp/acl_supplement_page42_review_packet_v2_20260604/crops/page42_vlm_navigation_rows.png`
  - `tmp/acl_supplement_page42_review_packet_v2_20260604/crops/page42_caption_area.png`

## Metrics

- Page 42 active245 at 90 dpi: `0.177541954` -> `0.235889788` (`+0.058347833`).
- Standalone figure active238: `0.374109343`.
- Figure size: `1800x2200`.
- Supplement page count after rebuild: `45`.

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'review_packet_contact_sheet or reproducibility_has_visual_media_manifest'`
- `make -C paper acl27-supplement`

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/supplement_review_packet_contact_sheet_v2_20260604.json`
