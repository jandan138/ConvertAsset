# 2026-06-04 ACL Supplement Navigation Media Atlas p30

## Context

The supplement-wide visual audit found that page 30 did not have a LaTeX page
crop, but the bottom navigation index panels were still visually fragile. The
old atlas used wide index-sheet crops for compact context. At paper scale those
panels read as compressed rows, and the right-hand official still sheet carried
a partial-row/clutter risk.

The updated AI-slot composer guidance requires wide strips to be split into
semantic segments before they are placed into fixed figure cards. This pass
applied that rule to the deterministic navigation atlas rather than increasing
crop pressure.

## Changes

- Added a regression assertion to
  `test_supplement_navigation_media_atlas_uses_non_cover_index_row_summaries`
  requiring row-card composers and rejecting the old wide crop path.
- Added `_navigation_pair_row_cards` for the selected6 rows 05-06 panel.
- Added `_navigation_0036_row_detail_cards` for four complete 0036/0066
  official still rows with key original/noMDL start/end cells.
- Kept all row and cell imagery on contain/letterbox placement; the
  `build_navigation_atlas` block does not use `cover=True`.

## Visual Review

Local paper-scale review used the render visual reviewer protocol. No
independent subagent was spawned because this environment only permits
`spawn_agent` when explicitly requested.

- Standalone atlas: the bottom left and right row-card panels are complete; row
  labels stay inside their lanes; no cell crosses a card boundary.
- PDF page 30: the figure is fully contained, the caption does not collide with
  the image, and the bottom row cards remain readable as compact context.
- Residual caveat: the upper 0036/0066 route panel remains intentionally small
  because the larger paired case pages below carry the main qualitative still
  evidence.

## Evidence

- Review JSON:
  `paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_media_atlas_p30_20260604.json`
- Rendered page evidence:
  `tmp/acl_render_visibility_fix_20260604/p30_row_cards/page-30.png`
- Final standalone figure:
  `paper/shared/figures/fig_supplement_navigation_media_atlas.png`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'navigation_media_atlas_uses_non_cover_index_row_summaries'`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py -k 'navigation_media_atlas_uses_non_cover_index_row_summaries or task_media_atlases_are_registered_and_dense'`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 160 -f 30 -l 30 paper/venues/acl27/build/supplement.pdf tmp/acl_render_visibility_fix_20260604/p30_row_cards/page`

## Follow-Up

The broader supplement polish goal remains active. Pages 22-23 and 33-38 remain
dense visual-review targets, but this pass closes the page-30 index-row
composition issue.
