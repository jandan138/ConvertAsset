# 2026-06-03 ACL Supplement Derivation Page 14 Navigation Flow

## Scope

After the grounding-derivation companion v3 pass, the refreshed full supplement
density audit made page 14 the lowest non-reference page. The page was
continuous derivation text, but it had no render companion after the grounding
figure moved to page 13.

## Changes

- Moved the existing
  `fig_supplement_navigation_derivation_companion.png` block before the
  Navigation Metrics subsection, between Bootstrap Paired Intervals and the
  SR/NE/SPL/TL equations.
- Kept the navigation companion path, caption boundary, and `0.26\textheight`
  include cap unchanged.
- Updated `tests/test_paper_layout.py` so the derivation section must keep the
  navigation companion in this pre-navigation-metrics position.

## Claim Boundary

This is a layout and reading-flow change only. The navigation companion remains
a registered media summary with an AI-generated navigation-metric gate used only
for exposition. It is not a new metric, model prediction, benchmark row, or new
experiment.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_derivation_page14_navigation_flow_20260603.json`

PDF review window:
`tmp/acl_supplement_page14_navigation_flow_20260603/page-13.png` through
`tmp/acl_supplement_page14_navigation_flow_20260603/page-16.png`

- Page 14 active245 at 90 dpi before: `0.052717388`
- Page 14 active245 at 90 dpi after: `0.135478690`
- Page 15 active245 at 90 dpi after: `0.136022996`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 14 now contains
the navigation media companion and the start of the navigation equations. Page
15 carries the remaining navigation equations, metric-boundary summary, and
metric-boundary bridge without a caption-only spill page. Page 16 still starts
the next supplement section.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_derivation_page14_navigation_flow_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'derivations_have_render_companions'` (RED before the LaTeX move)
- `python -m pytest -q tests/test_paper_layout.py -k 'derivation_companions or derivations_have_render_companions'`
- `python -m pytest -q tests/test_paper_layout.py` (`74 passed`)
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -f 13 -l 16 -r 140 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page14_navigation_flow_20260603/page`
- `pdftoppm -f 13 -l 16 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page14_navigation_flow_20260603/page90`
- `pdftotext -f 14 -l 14 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page14_navigation_flow_final_20260603/page14.txt`
- `pdfinfo paper/venues/acl27/build/supplement.pdf` (`45` A4 pages)
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_derivation_page14_navigation_flow_20260603.json`
- `git diff --check` on touched tracked files, plus a direct trailing-whitespace
  scan over the new docs and evidence JSONs
