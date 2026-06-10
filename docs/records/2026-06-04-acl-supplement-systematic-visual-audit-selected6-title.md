# 2026-06-04 ACL Supplement Systematic Visual Audit Selected6 Title

## Context

After the Figure S25 fix, user review requested a broader scan of the ACL
supplement for other obvious occlusion, bad scaling, incomplete figures, black
tiles, or caption/image collisions.

This pass rebuilt the supplement, rendered all 45 pages, generated fresh contact
sheets, and manually inspected the dense candidate pages. The confirmed blocker
was on page 32: the top title of the first selected6 navigation case panel was
only partially visible.

## Root Cause

The defect was not a LaTeX float issue. The standalone
`internnav_selected6_case03.png` already contained the clipped title because
`gen_acl_supplement_navigation_crops.py` cropped the source selected6 sheet from
a fixed y position inside the title row. `internnav_selected6_case04.png` also
started too close to the title edge and carried the next row title near its
bottom.

## Changes

- Adjusted selected6 crop boxes in
  `paper/shared/figures/gen_acl_supplement_navigation_crops.py` so case03-case06
  begin at the full title row and avoid including the next title row.
- Regenerated selected6 case crops under
  `paper/shared/figures/supplement/`.
- Added `test_acl_supplement_navigation_selected6_crops_keep_titles_visible`,
  which rejects crop images whose title dark pixels begin at the top edge.

## Visual Review

Local visual review used the browser visual review and render visual reviewer
protocols. No independent subagent was spawned because this environment only
permits `spawn_agent` when explicitly requested.

- Page 32: Figure S30 now shows complete `464_464` and `473_473` titles.
- Candidate pages inspected at page scale: 22, 23, 24, 28, 31, 32, 33, 34, 35,
  36, 37, 38, 42, and 44.
- Final 45-page contact sheet: no remaining obvious hard clipping, black padded
  tile, incomplete figure footer, or caption/image collision was found.

## Evidence

- Review JSON:
  `paper/shared/evidence/raw/acl27_visual_review/supplement_systematic_visual_audit_selected6_title_20260604.json`
- Before page 32:
  `tmp/acl_supplement_systematic_visual_audit_20260604/pages_150/page-32.png`
- Final page 32:
  `tmp/acl_supplement_systematic_visual_audit_20260604/final_pages_150/page-32.png`
- Final contact sheets:
  `tmp/acl_supplement_systematic_visual_audit_20260604/final_contact_sheets/pages_01_45_compact.png`,
  `tmp/acl_supplement_systematic_visual_audit_20260604/final_contact_sheets/pages_31_45.png`

## Verification

- `make -C paper acl27-supplement`
- `pdftoppm -png -r 150 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_systematic_visual_audit_20260604/pages_150/page`
- `pdfimages -list paper/venues/acl27/build/supplement.pdf`
- `python -m pytest -q tests/test_paper_layout.py -k 'navigation_selected6_crops_keep_titles_visible'`
- `python paper/shared/figures/gen_acl_supplement_navigation_crops.py`
- `python -m pytest -q tests/test_paper_layout.py -k 'navigation_selected6_crops_keep_titles_visible or groups_internnav_case_figures'`
- `pdftoppm -png -r 150 -f 31 -l 36 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_systematic_visual_audit_20260604/selected6_title_fix_pages_150/page`
- `pdftoppm -png -r 150 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_systematic_visual_audit_20260604/final_pages_150/page`
- `python -m pytest -q tests/test_paper_layout.py`
- `make -C paper acl27-supplement`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_systematic_visual_audit_selected6_title_20260604.json >/dev/null`
- `git diff --check -- paper/shared/figures/gen_acl_supplement_navigation_crops.py tests/test_paper_layout.py docs/records/README.md docs/records/2026-06-04-acl-supplement-systematic-visual-audit-selected6-title.md paper/shared/evidence/raw/acl27_visual_review/supplement_systematic_visual_audit_selected6_title_20260604.json`

## Residual Risk

Several pages remain dense review indexes by design. This pass treats hard
clipping, incomplete generated crops, black padded tiles, and caption/image
collision as blockers; it does not rewrite all dense index pages into lower
density layouts.
