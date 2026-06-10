# 2026-06-05 ACL Supplement Navigation-Derivation Footer Visual Scan

## Scope

Continued the ACL supplement visual audit for obvious occlusion, unsafe scaling,
and incomplete figure display after the AI-slot containment pass.

## Finding

The rendered supplement PDF did not show a page-level float crop, but the
standalone source image for Figure S13
(`fig_supplement_navigation_derivation_companion.png`) had its internal
boundary sentence drawn too close to the bottom of the canvas. In the PDF this
made the sentence look clipped at the figure edge.

Root cause: `build_navigation_derivation_companion()` used a fixed 700 px
canvas and drew the footer at `height - 26`, while the third content band already
ended near the bottom of the canvas.

## Change

- Increased the Figure S13 canvas height from 700 px to 740 px.
- Positioned the boundary footer after the third opener band rather than at the
  absolute bottom edge.
- Added a regression test that checks the final 20 px of the figure remain a
  low-activity safety band.

## Visual Evidence

- Full final overview:
  `tmp/acl_supplement_systematic_scan_20260605_round4_final/contact_sheets/supplement_pages_01_46_overview_final.png`
- Final page-group review:
  `tmp/acl_supplement_systematic_scan_20260605_round4_final/contact_sheets/supplement_pages_13_24_final.png`
- Figure S13 PDF crop after fix:
  `tmp/acl_supplement_systematic_scan_20260605_round4_final/crops/page14_figure_s13_after_fix.png`
- Standalone Figure S13 bottom crop after fix:
  `tmp/acl_supplement_systematic_scan_20260605_round4_final/crops/standalone_fig_s13_bottom_after_fix.png`

## Verification

- `make -C paper acl27-supplement` passed and produced a 46-page supplement.
- `python -m pytest -q tests/test_paper_layout.py -k 'navigation_derivation_companion_keeps_footer_inside_canvas'`
  passed.
- `python -m pytest -q tests/test_paper_layout.py -k 'supplement'` passed:
  66 passed, 17 deselected.
- LaTeX log scan for `Overfull`, `Float too large`, `too large`,
  `LaTeX Warning: Float`, undefined references, and label warnings returned no
  matches.

## Residual Risk

Several supplement figures intentionally use dense full-canvas card layouts or
source images with black bands. They were reviewed as rendered pages and did not
show a blocking incomplete-display defect in this pass. Continued audits should
prefer page-render evidence plus standalone figure bottom/edge crops for any
future dense figure updates.
