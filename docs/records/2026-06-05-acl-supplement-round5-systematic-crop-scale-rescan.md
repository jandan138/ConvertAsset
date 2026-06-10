# 2026-06-05 ACL Supplement Round 5 Systematic Crop/Scale Rescan

## Scope

This pass continued the ACL supplement visual audit for obvious reader-facing
figure failures: occlusion, incorrect scaling, caption collision, page-edge
truncation, source-slot clipping, and incomplete display of dense atlas or
AI-slot panels.

The rendered artifact reviewed was:

- `paper/venues/acl27/build/supplement.pdf`
- SHA256: `4c5295b7306453238cfa9a2a14e8cbaea56c16ffec0b22d63b88c6d7a836cb0d`
- 46 pages, A4
- PDF creation timestamp: Fri Jun 5 10:42:11 2026 CST

## Evidence

Build and render commands:

```bash
make -C paper acl27-supplement
pdftoppm -r 180 -png paper/venues/acl27/build/supplement.pdf \
  tmp/acl_supplement_visual_scan_20260605_round5/pages_180/page
pdftotext -layout paper/venues/acl27/build/supplement.pdf \
  tmp/acl_supplement_visual_scan_20260605_round5/text/supplement_layout.txt
pdfimages -list paper/venues/acl27/build/supplement.pdf
```

Review artifacts:

- Full-page 180dpi renders:
  `tmp/acl_supplement_visual_scan_20260605_round5/pages_180/`
- Full-page contact sheets:
  `tmp/acl_supplement_visual_scan_20260605_round5/contact_sheets/supplement_pages_01_08.png`
  through
  `tmp/acl_supplement_visual_scan_20260605_round5/contact_sheets/supplement_pages_41_46.png`
- Content-crop contact sheets:
  `tmp/acl_supplement_visual_scan_20260605_round5/contact_sheets/supplement_candidate_crops_01_06.png`
  through
  `tmp/acl_supplement_visual_scan_20260605_round5/contact_sheets/supplement_candidate_crops_43_46.png`
- Layout text:
  `tmp/acl_supplement_visual_scan_20260605_round5/text/supplement_layout.txt`
- Page-edge scan:
  `tmp/acl_supplement_visual_scan_20260605_round5/supplement_page_edge_risk_report.json`
- Embedded-image list:
  `tmp/acl_supplement_visual_scan_20260605_round5/pdfimages_list.txt`

## Findings

No new blocking crop, occlusion, unsafe scale, caption collision, or incomplete
figure display defect was found in this pass.

Specific rechecks:

- Fig. S25 on page 27 was rechecked against the user-reported prior failure.
  The bottom claim-boundary gate schematic is fully visible in the rendered
  page, with the caption below it and no page-edge collision.
- Fig. S26 on page 28 was rechecked because it also contains a bottom
  schematic/decision-gate region. The visual decision gate remains complete.
- Dense GRScenes pages 20-24 were reviewed at full-page and content-crop scale.
  The audit strips and table companions remain complete.
- Navigation pages 29-38 were reviewed for narrow route strips and tall
  companion figures. The route panels, media-boundary rows, and upload-gate
  panels remain inside their figure frames.
- Theory and manifest pages 39-45 were reviewed for bottom evidence walls,
  boundary companions, and source trays. The rendered figures are compact but
  complete.
- `pdfimages -list` reported embedded figure resolution in the reviewed PDF
  between approximately 125ppi and 339ppi. The lowest-PPI navigation case
  strips on pages 34-35 are visually complete and not an obvious upscaling or
  clipping failure.

The page-edge detector was noisy because ACL line numbers and page numbers are
legitimate non-white content near page margins. Its output was therefore used
only as a reminder to inspect all rendered content crops manually.

## Changes

No LaTeX source, figure asset, table, or generator change was required. This
pass adds only the durable audit record and the raw visual-review evidence JSON.

## Verification

- PASS: `make -C paper acl27-supplement`
- PASS: rendered all 46 pages at 180dpi with `pdftoppm`
- PASS: extracted layout text with `pdftotext -layout`
- PASS: reviewed all six full-page contact sheets and all eight content-crop
  contact sheets
- PASS: `pdfimages -list` found no extreme low-resolution embedded image
- PASS: LaTeX log scan for overfull boxes, float-size warnings, rerun warnings,
  label warnings, and lineno warnings returned no matches

## Residual Risk

This pass was a visual containment and scaling audit, not an OCR readability or
semantic-claim review. Some atlas/index pages remain intentionally dense, and
small labels may be hard to read at print scale, but no obvious clipping,
occlusion, incorrect PDF scaling, or incomplete display was visible in the
current supplement.
