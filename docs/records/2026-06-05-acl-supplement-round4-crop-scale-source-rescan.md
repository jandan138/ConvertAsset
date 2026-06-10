# 2026-06-05 ACL Supplement Round 4 Crop/Scale Source Rescan

## Scope

This pass continued the ACL supplement visual audit for obvious reader-facing
failures: clipped figures, source-PNG slot crops, incorrect scaling,
caption/image collision, page-edge truncation, and incomplete display of dense
atlas panels.

The target artifact was:

- `paper/venues/acl27/build/supplement.pdf`
- SHA256: `4c5295b7306453238cfa9a2a14e8cbaea56c16ffec0b22d63b88c6d7a836cb0d`
- 46 pages, A4
- PDF creation timestamp: Fri Jun 5 10:42:11 2026 CST

## Evidence

Build and render commands:

```bash
make -C paper acl27-supplement
pdftoppm -png -r 180 paper/venues/acl27/build/supplement.pdf \
  tmp/acl_supplement_visual_scan_20260605_round4/pages_180/page
pdftotext -layout paper/venues/acl27/build/supplement.pdf \
  tmp/acl_supplement_visual_scan_20260605_round4/text/supplement_layout.txt
```

Review artifacts:

- Full-page contact sheets:
  `tmp/acl_supplement_visual_scan_20260605_round4/contact_sheets/supp_pages_01_12_round4.png`
  through
  `tmp/acl_supplement_visual_scan_20260605_round4/contact_sheets/supp_pages_37_46_round4.png`
- High-risk rendered-page sheet:
  `tmp/acl_supplement_visual_scan_20260605_round4/contact_sheets/supp_high_risk_pages_round4.png`
- Source-PNG contact sheets:
  `tmp/acl_supplement_visual_scan_20260605_round4/contact_sheets/source_figures_S01_S12_round4.png`
  through
  `tmp/acl_supplement_visual_scan_20260605_round4/contact_sheets/source_figures_S37_S38_round4.png`
- Source figure manifest:
  `tmp/acl_supplement_visual_scan_20260605_round4/source_figures.json`
- Page-boundary metrics:
  `tmp/acl_supplement_visual_scan_20260605_round4/page_bbox_margins.json`

## Findings

No new blocking crop, occlusion, scaling, or incomplete-display defect was found
in the current supplement render or in the 38 standalone supplement source PNGs.

Specific regression targets:

- Current PDF text maps Figure S25 to page 27. The figure is
  `fig_supplement_material_claim_boundary_atlas.png`, included from
  `04_material_effects.tex`. The bottom claim-boundary gate schematic is fully
  visible in both the source PNG and the rendered PDF page.
- Figure S26 on page 28 was also rechecked because it contains a bottom
  material-decision AI schematic. The full decision gate and caption are visible.
- Dense or historically risky pages 22, 27, 28, 41, 43, and 45 were inspected
  at full rendered-page scale after the contact-sheet pass. Their figures are
  complete and do not collide with captions or page edges.
- The automated page-boundary detector reported zero pages with non-white
  content unusually close to the rendered page edge under the 180dpi threshold.

The remaining tight visual areas are density tradeoffs, not display failures:
Figure S39 on page 41 is compact, and Figures S40/S41 are manifest/index-style
figures with small source thumbnails. They remain complete on the rendered page.

## Changes

No LaTeX source, figure assets, tables, or generator scripts were changed in
this pass. This record and the companion JSON evidence document the audit only.

## Verification

- PASS: `make -C paper acl27-supplement`
- PASS: rendered all 46 pages at 180dpi with `pdftoppm`
- PASS: extracted layout/plain text with `pdftotext`
- PASS: generated full-page and source-PNG contact sheets
- PASS: page-boundary detector reported `edge_flags: 0`
- PASS: manual full-page inspection of pages 22, 27, 28, 41, 43, and 45

## Residual Risk

This was a visual containment audit, not a semantic review or OCR readability
audit. Very small labels inside dense atlas/index figures can still be hard to
read at print scale, but no obvious clipping, occlusion, incorrect PDF scaling,
or incomplete source-slot display remained visible in this pass.
