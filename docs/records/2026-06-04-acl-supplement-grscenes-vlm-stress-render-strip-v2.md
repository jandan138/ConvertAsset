# 2026-06-04 ACL Supplement GRScenes VLM Stress Render Strip v2

## Scope

Round 20 showed page 21 as one of the lowest non-reference supplement pages.
The page contained only the GRScenes VLM stress render strip and its caption,
but the source figure was still a relatively short horizontal board. This pass
rebuilds the same evidence as a page-shaped render board.

## Changes

- Rebuilt `fig_supplement_grscenes_vlm_stress_render_strip.png` at
  `1500 x 1680`.
- Kept the same four registered original/noMDL render-pair cards: bottle, cup,
  backpack, and clock.
- Kept the AI scoring-gate slot as exposition only and enlarged the process
  card within the page-shaped board.
- Updated the layout test to require the page-shaped aspect ratio and a higher
  active-pixel density guard.

## Claim Boundary

The figure remains a reading guide for Tables S4-S6. It does not add a VLM run,
new metric, benchmark row, or population-level failure estimate. The
evidence-bearing content is still the registered render pairs and frozen source
artifacts; the scoring-gate schematic is replaceable exposition.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_vlm_stress_render_strip_v2_20260604.json`

PDF review window:
`tmp/acl_supplement_page21_grscenes_stress_v2_final_20260604/page-20.png`
through `tmp/acl_supplement_page21_grscenes_stress_v2_final_20260604/page-22.png`

- Standalone figure active238: `0.383019726` -> `0.664783730`
- Page 21 active245 at 90 dpi: `0.147615315` -> `0.328461347`
- Improvement from round 20 page 21: `+0.180846032`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `7892c1bb75e6e43b512cf57f994e0f018468e5ace1f648ef1f46c1feb4cfe03b`

Result: PASS by local `render-visual-reviewer` checklist. Page 21 now shows the
large page-shaped board without clipping or caption collision, and page 22
still starts with the failure-taxonomy table. Visual review was local rather
than an independent subagent review; the evidence JSON records
`independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grscenes_vlm_stress_render_strip.png`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_vlm_stress_render_strip_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'grscenes_vlm_stress_render_strip_is_registered_and_dense'`
  - RED first for the old `1800x1380` horizontal board against the page-shaped
    aspect requirement; GREEN after rebuilding the `1500x1680` board.
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -f 20 -l 22 -png -r 144 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page21_grscenes_stress_v2_final_20260604/page`
- `pdftoppm -f 21 -l 21 -png -r 90 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page21_grscenes_stress_v2_final_90dpi_20260604/page`
- `pdftotext -f 20 -l 22 paper/venues/acl27/build/supplement.pdf -`
