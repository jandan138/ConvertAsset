# 2026-06-05 ACL Supplement Systematic Visual Scan: No New Blocking Crops

## Scope

This pass re-audited the ACL27 supplement PDF for visible figure defects after the
recent AI-slot and selected-case layout fixes. The target artifact was:

- `paper/venues/acl27/build/supplement.pdf`
- 45 pages, A4
- PDF creation timestamp: Fri Jun 5 01:27:17 2026 CST

The audit focused on obvious reader-facing visual failures: figure occlusion,
incorrect scaling, incomplete figure display, caption collision, page-edge
clipping, and dense atlas panels whose bottom or side content might have been
cut off.

## Commands And Evidence

Build:

```bash
make -C paper acl27-supplement
```

Rendered evidence:

```bash
pdftoppm -png -r 180 paper/venues/acl27/build/supplement.pdf \
  tmp/acl_supplement_visual_scan_20260605/pages_180/page
pdftotext -layout paper/venues/acl27/build/supplement.pdf \
  tmp/acl_supplement_visual_scan_20260605/text/supplement_layout.txt
pdftotext paper/venues/acl27/build/supplement.pdf \
  tmp/acl_supplement_visual_scan_20260605/text/supplement_plain.txt
```

Generated review artifacts:

- `tmp/acl_supplement_visual_scan_20260605/contact_sheets/supp_pages_01_15.png`
- `tmp/acl_supplement_visual_scan_20260605/contact_sheets/supp_pages_16_30.png`
- `tmp/acl_supplement_visual_scan_20260605/contact_sheets/supp_pages_31_45.png`
- `tmp/acl_supplement_visual_scan_20260605/pages_180/`
- `tmp/acl_supplement_visual_scan_20260605/page_bbox_margins.json`
- `tmp/acl_supplement_visual_scan_20260605/pdfinfo.txt`

The page-boundary scan flagged zero pages with non-white content unusually close
to the page edges under the configured 180dpi thresholds.

## Findings

No new high-confidence blocking visual defects were found in this pass.

Manual page-scale review covered the full 45-page supplement through contact
sheets, followed by full-page inspection of dense or historically risky pages:
S4-S7, S9-S10, S14-S26, and S28-S41. The pass specifically rechecked:

- Fig. S25 material claim-boundary visual atlas: bottom AI claim-boundary gate is
  fully visible and no longer cut off.
- Selected6 / 0036 navigation case pages: titles, still panels, route overlays,
  black status strips, and captions remain within the rendered page.
- Material diagnostic and decision-map pages: dense but complete; no caption
  collision or bottom truncation.
- VLM coordinate, GRScenes diagnostic, PASS-only, zoom-stress, media-manifest,
  theory, and source-boundary atlas pages: scaled into the page with visible
  panel borders and captions.

Some panels intentionally contain close crops or compact index strips. Those were
treated as acceptable when the panel border, label, and caption made the crop
scope clear and the surrounding figure was fully rendered.

## Continuation Pass

After the AI-slot containment rules were rechecked, a second rendered-PDF pass
was run under:

- `tmp/acl_supplement_visual_scan_20260605_continued/`
- `tmp/acl_supplement_visual_scan_20260605_continued/contact_sheets/supp_pages_01_45.png`
- `tmp/acl_supplement_visual_scan_20260605_continued/contact_sheets/source_figures_contact_sheet.png`
- `tmp/acl_supplement_visual_scan_20260605_continued/source_image_edge_scan.json`

This continuation specifically mapped Fig. S25 to page 27 and reviewed both the
rendered page and the standalone source image:

- `tmp/acl_supplement_visual_scan_20260605_continued/pages_180/page-27.png`
- `paper/shared/figures/fig_supplement_material_claim_boundary_atlas.png`

Result: Fig. S25's bottom claim-boundary gate is fully visible in the current
PDF and in the source PNG. The earlier incomplete bottom-concept display no
longer reproduces.

The continuation also inspected high-risk source-edge candidates from the
automatic scan, including GRScenes visual guide/diagnostic pages, material
diagnostic and decision-map pages, Selected6 and 0036 neutral navigation
companions, the theory hypothesis-boundary companion, and the source-boundary
review companion. Edge-contact flags on several source PNGs were caused by the
intended gray canvas or full-bleed panel background, not by visible content being
cut off in the PDF.

Known tight area: Fig. S39 remains a compact in-column companion on page 41.
Prior v6 iteration records show that larger `0.42\textheight` and
`0.48\textheight` placements caused a 46-page supplement and a sparse H.5 orphan
page. In the current pass it is complete but dense, so it remains a readability
tradeoff rather than a blocking crop or occlusion defect.

## Changes

No LaTeX source, figure assets, tables, or supplement layout parameters were
changed in this pass. This record documents the audit evidence only.

## Verification

- PASS: `make -C paper acl27-supplement`
- PASS: rendered all 45 pages with `pdftoppm -png -r 180`
- PASS: generated three contact sheets covering pages 1-45
- PASS: page-boundary detector reported `flags: 0`
- PASS: continuation pass generated full-page and source-figure contact sheets
  covering all 45 rendered pages and 38 resolved source figures

## Residual Risk

This was a rendered-PDF visual QA pass, not an OCR readability audit or a
semantic correctness review. Very small text inside dense overview/index panels
may still be hard to read at print scale, but no obvious clipping, occlusion, or
incomplete figure display remained visible in the current supplement render.
