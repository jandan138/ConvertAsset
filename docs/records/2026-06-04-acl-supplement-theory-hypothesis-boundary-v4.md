# 2026-06-04 ACL Supplement Theory Hypothesis-Boundary v4

## Scope

This pass continues the page 41 iteration after round 17 still ranked it as the
lowest non-reference page. The goal was to make the v3 render-backed companion
larger in the actual PDF without creating the 46-page spill that earlier larger
allocations caused.

## Changes

- Increased the page-41 companion include from `0.36\textheight` to
  `0.38\textheight`.
- Changed only this companion caption from `footnotesize` to `scriptsize`.
- Kept the v3 AI slot and deterministic companion image unchanged.
- Updated `tests/test_paper_layout.py` to lock the larger include and compact
  caption allocation.

## Claim Boundary

The figure remains a reading aid over registered material, grounding,
navigation, and selected-failure render crops. The render-backed boundary lens
is still AI-generated exposition only, not a new experiment, causal proof, or
population rate.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_companion_v4_20260604.json`

PDF review window:
`tmp/acl_supplement_page41_theory_hypothesis_v4_final_20260604/page-40.png`
through `tmp/acl_supplement_page41_theory_hypothesis_v4_final_20260604/page-42.png`

- Page 41 active245 at 90 dpi: `0.144267895` -> `0.147503139`
- Improvement from round 16 page 41: `+0.006693563`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `23fde00c1c5abd5b5bac34e1f5bde795de0a3b2f8f3ceb90e46d6196ade9c764`

Result: PASS by local `render-visual-reviewer` checklist. Page 41 shows the
larger companion and compact caption without overlap, H.5 remains complete on
the same page, and page 42 still starts the reproducibility appendix and
review-packet manifest. Visual review was local rather than an independent
subagent review; the evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/venues/acl27/sections/supplement/06_theory.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_companion_v4_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'theory_has_hypothesis_boundary_companion or theory_hypothesis_boundary_companion_is_registered_and_dense'`
  - RED first for the missing `0.38\textheight` allocation and `scriptsize`
    caption; GREEN after implementation with `2 passed, 72 deselected`.
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -f 40 -l 42 -r 144 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_v4_final_20260604/page`
- `pdftoppm -f 41 -l 41 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_v4_final_90dpi_20260604/page`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
