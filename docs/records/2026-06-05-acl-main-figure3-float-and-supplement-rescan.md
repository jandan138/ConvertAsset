# 2026-06-05 ACL Main Figure 3 Float And Supplement Rescan

## Scope

This pass handled two visible-layout concerns around the ACL27 artifacts:

- the ACL main PDF had a sparse material Figure 3 page after earlier float-order
  changes;
- the ACL supplement needed another rendered-PDF scan for obvious figure
  occlusion, unsafe scaling, and incomplete display after the Fig. S25
  bottom-gate fix.

## Main PDF Change

The material comparison figure was moved to a bottom double-column float with
`stfloats` enabled in the ACL venue preamble. The material-effect paragraph and
Figure 3 caption were also tightened so the official-scene paragraph no longer
spills into a nearly empty page.

Files touched:

- `paper/venues/acl27/preamble.tex`
- `paper/venues/acl27/sections/results.tex`
- `tests/test_paper_layout.py`

Rendered evidence:

- `tmp/acl_main_goal_iter_20260605_round7_compact/pages_180/`
- `tmp/acl_main_goal_iter_20260605_round7_compact/contact_sheets/main_pages_01_11_round7_compact.png`
- `tmp/acl_main_goal_iter_20260605_round7_compact/pdfinfo.txt`
- `tmp/acl_main_goal_iter_20260605_round7_compact/main_layout.txt`

Result: `paper/venues/acl27/build/main.pdf` is an 11-page A4 PDF in the
rendered evidence. Figure 3 now appears at the bottom of page 6 with its caption
fully visible. Page 7 carries the evidence-gate table instead of becoming a
float-only or nearly blank carry-over page.

## Supplement Rescan

The supplement was rebuilt and all 46 pages were rendered at 180dpi:

- `tmp/acl_supplement_visual_scan_20260605_round2/pages_180/`
- `tmp/acl_supplement_visual_scan_20260605_round2/contact_sheets/supp_pages_01_16_corrected.png`
- `tmp/acl_supplement_visual_scan_20260605_round2/contact_sheets/supp_pages_17_32_corrected.png`
- `tmp/acl_supplement_visual_scan_20260605_round2/contact_sheets/supp_pages_33_46_corrected.png`
- `tmp/acl_supplement_visual_scan_20260605_round2/pdfinfo.txt`
- `tmp/acl_supplement_visual_scan_20260605_round2/supplement_layout.txt`

Focused full-page checks covered pages 25-28, including Fig. S25 and Fig. S26:

- `tmp/acl_supplement_visual_scan_20260605_round2/pages_180/page-25.png`
- `tmp/acl_supplement_visual_scan_20260605_round2/pages_180/page-26.png`
- `tmp/acl_supplement_visual_scan_20260605_round2/pages_180/page-27.png`
- `tmp/acl_supplement_visual_scan_20260605_round2/pages_180/page-28.png`

Result: Fig. S25's bottom claim-boundary gate is fully visible. The material
diagnostic, claim-boundary, and decision-map pages do not show a new
reader-facing crop, overlap, or incomplete bottom display in this pass.

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'material_figure_can_use_bottom_double_column_placement or material_figure_enters_float_queue_before_claim_boundary_table or results_avoids_page_break_prone_original_nomdl_phrase'`
- `make -C paper acl27`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 180 paper/venues/acl27/build/main.pdf tmp/acl_main_goal_iter_20260605_round7_compact/pages_180/page`
- `pdftoppm -png -r 180 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_visual_scan_20260605_round2/pages_180/page`

## Residual Risk

This pass targeted visible clipping, occlusion, and sparse figure placement. It
did not re-author dense atlas internals or run an OCR readability pass over every
small label. Several supplement atlases remain intentionally dense but were
visibly contained in the rendered PDF.
