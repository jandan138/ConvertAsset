# 2026-06-04 ACL Supplement Review-Packet Black Tile p42

## Context

The post-p30 supplement contact-sheet review exposed a real page-42 defect: the
review-packet media manifest contained a large black tile in the `Render
evidence` row. This was not a PDF renderer artifact. The standalone PNG already
contained the black region.

## Root Cause

`build_review_packet_contact_sheet` still used the old bottom crop
`(0, 1730, 1800, 2794)` from `fig_supplement_render_atlas.png`. After the p7/p8
visibility pass shortened the render atlas to `1800x2014`, that crop exceeded
the source image bounds. Pillow filled the out-of-bounds crop area with black.

## Changes

- Added a near-black regression check to
  `test_supplement_review_packet_contact_sheet_is_registered_and_dense`.
- Replaced the bad tile with a valid registered scene-evidence crop inside the
  current render atlas: `(900, 1160, 1800, 2014)`.
- Regenerated `fig_supplement_review_packet_contact_sheet.png`.
- Rebuilt the ACL supplement and rendered page 42 for paper-scale review.

## Visual Review

Local paper-scale visual review used the render visual reviewer protocol. No
independent subagent was spawned because this environment only permits
`spawn_agent` when explicitly requested.

- Standalone contact sheet: the `Render evidence` row now shows a valid scene
  render tile instead of a black padded crop.
- PDF page 42: the figure is fully contained, the caption does not collide, and
  the prior black block is gone.
- Residual caveat: legitimate source images still include some black bars and
  dark regions, so the regression checks for an aggregate near-black increase
  rather than banning black pixels entirely.

## Evidence

- Review JSON:
  `paper/shared/evidence/raw/acl27_visual_review/supplement_review_packet_black_tile_p42_20260604.json`
- Rendered page evidence:
  `tmp/acl_render_visibility_fix_20260604/p42_contact_sheet_black_tile/page-42.png`
- Final standalone figure:
  `paper/shared/figures/fig_supplement_review_packet_contact_sheet.png`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'review_packet_contact_sheet_is_registered_and_dense'`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py -k 'review_packet_contact_sheet_is_registered_and_dense or navigation_media_atlas_uses_non_cover_index_row_summaries or task_media_atlases_are_registered_and_dense'`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 160 -f 42 -l 42 paper/venues/acl27/build/supplement.pdf tmp/acl_render_visibility_fix_20260604/p42_contact_sheet_black_tile/page`
