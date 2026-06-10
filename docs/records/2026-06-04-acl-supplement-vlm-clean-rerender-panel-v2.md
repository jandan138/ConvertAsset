# 2026-06-04 ACL Supplement VLM Clean-Rerender Panel v2

## Scope

Round 22 identified page 10 as one of the lowest non-reference supplement
pages. The page used the correct clean rerender evidence, but the source figure
was a wide `1802 x 1134` board; when placed in a page float, it left a large
blank lower half.

## Changes

- Rebuilt `fig_supplement_vlm_clean_rerender_panel.png` as a page-shaped
  `1602 x 1672` panel.
- Kept the four evidence-bearing original/noMDL pairs: backpack, clock,
  bottle, and cup.
- Added a registered target close-up strip that crops around the same target
  boxes from the same clean rerenders.
- Added clean-rerender report-gate rows for exit status, MDL/KooPbr error
  status, bbox-only interpretation, and PASS status.
- Updated the supplement caption to describe the target close-up strip and
  preserve the claim boundary that this is not a VLM rerun.
- Updated the layout test to require the page-shaped aspect ratio and active
  pixel density guard.

## Claim Boundary

This remains render-quality support for the tabulated grounding evidence. The
figure does not add VLM point markers, new VLM predictions, new metrics, or a
new benchmark row. The close-up strip reuses the same registered clean rerender
images and target projections.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_clean_rerender_panel_v2_20260604.json`

PDF review window:
`tmp/acl_supplement_page10_vlm_clean_rerender_v2_final_20260604/page-09.png`
through `tmp/acl_supplement_page10_vlm_clean_rerender_v2_final_20260604/page-11.png`

- Standalone figure size: `1802 x 1134` -> `1602 x 1672`
- Standalone figure active238: `0.501307092` -> `0.501968607`
- Page 10 active245 at 90 dpi: `0.150405680` -> `0.256958387`
- Improvement from round 22 page 10: `+0.106552707`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `8b45e6c51befdb904ceb02e25e396dd512e07d5d8f7f46bfd535630c9b9c1ca8`

Result: PASS by local `render-visual-reviewer` checklist. Page 10 now uses the
available page height without clipping or caption collision. Pages 9 and 11
remain in their expected float positions. Visual review was local rather than
an independent subagent review; the evidence JSON records
`independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_vlm_clean_rerender_panel.py`
- `paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png`
- `paper/venues/acl27/sections/supplement/01a_render_atlas.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_clean_rerender_panel_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'vlm_clean_rerender_panel_is_registered_and_not_red'`
  - RED first for the old wide `1802 x 1134` panel against the page-shaped
    aspect requirement; GREEN after rebuilding the `1602 x 1672` panel.
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -r 144 -png -f 9 -l 11 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page10_vlm_clean_rerender_v2_final_20260604/page`
- `pdftoppm -r 90 -png -f 10 -l 10 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page10_vlm_clean_rerender_v2_final_90dpi_20260604/page`
