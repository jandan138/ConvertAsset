# 2026-06-05 ACL Supplement AI-Slot Containment Visual Scan

## Scope

Continued the ACL supplement visual scan for obvious crop, occlusion,
mis-scaling, and incomplete-display defects after the AI-slot composition rules
were tightened toward contain/letterbox placement.

## Findings And Changes

- Rebuilt and rerendered `paper/venues/acl27/build/supplement.pdf` as a fresh
  46-page A4 artifact before judging page images.
- Rechecked Figure S25 on Page 27. The bottom claim-boundary concept schematic
  is fully visible in the current PDF render, including the right-side cards and
  caption spacing.
- Found a recurrence risk on Page 4 / Figure S3: the bottom boundary-marker
  AI-slot was technically inside the figure but had been placed with
  center-crop/cover semantics, making the lower schematic edge look easy to
  clip. Switched final supplement AI-slot placements in
  `paper/shared/figures/gen_supplement_task_media_atlases.py` from `cover=True`
  to contain/letterbox placement.
- Added a regression test that rejects future `AI_SLOT` placements with
  `cover=True` in the supplement atlas composer.
- Regenerated the supplement atlas PNGs and rebuilt the PDF. Page 4 now shows
  the boundary-marker schematic fully inside the card with margin; Pages 1, 5,
  12, 15, 21, 27, 28, 29, 30, 37, 38, 39, 40, 41, 43, and 45 were rechecked as
  high-risk dense or AI-slot pages.

## Evidence

- Initial rendered pages:
  `tmp/acl_supplement_systematic_scan_20260605_round3/pages_180/`
- Initial contact sheets:
  `tmp/acl_supplement_systematic_scan_20260605_round3/contact_sheets/`
- Final rendered pages:
  `tmp/acl_supplement_systematic_scan_20260605_round3_final/pages_180/`
- Final targeted high-risk sheet:
  `tmp/acl_supplement_systematic_scan_20260605_round3_final/contact_sheets/supp_targeted_high_risk_pages_final.png`
- Final full contact sheets:
  `tmp/acl_supplement_systematic_scan_20260605_round3_final/contact_sheets/supp_pages_01_12_final.png`
  through
  `tmp/acl_supplement_systematic_scan_20260605_round3_final/contact_sheets/supp_pages_37_46_final.png`
- Final page boundary metrics:
  `tmp/acl_supplement_systematic_scan_20260605_round3_final/page_bbox_margins.json`

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 180 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_systematic_scan_20260605_round3_final/pages_180/page`
- `python -m pytest -q tests/test_paper_layout.py -k 'supplement'`
  - Result: `65 passed, 17 deselected`
- `rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label" paper/venues/acl27/build/supplement.log`
  - Result: no matches
- `git diff --check -- paper/shared/figures/gen_supplement_task_media_atlases.py tests/test_paper_layout.py`
  - Result: no output

## Residual Risk

The scan targeted reader-blocking visual failures: clipped AI slots, missing
lower panels, caption collisions, page-edge overflow, and obvious figure
mis-scaling. Several supplement atlases remain intentionally dense because they
serve as review indices, but the final rendered pages checked in this pass do
not show an obvious incomplete-display blocker.
