# 2026-06-06 ACL Supplement Round 6 Crop/Scale Rescan

## Scope

This pass continued the ACL supplement visual audit for obvious reader-facing
figure failures: occlusion, incorrect scaling, incomplete figure display,
caption collision, page-edge clipping, and source-slot edge crops. The reviewed
artifact was:

- `paper/venues/acl27/build/supplement.pdf`
- SHA256: `4c5295b7306453238cfa9a2a14e8cbaea56c16ffec0b22d63b88c6d7a836cb0d`
- 46 pages, A4
- PDF creation timestamp: Fri Jun 5 10:42:11 2026 CST

## Evidence

Build and render commands:

```bash
make -C paper acl27-supplement
pdftoppm -r 180 -png paper/venues/acl27/build/supplement.pdf \
  tmp/acl_supplement_visual_scan_20260606_round6/pages_180/page
pdftotext -layout paper/venues/acl27/build/supplement.pdf \
  tmp/acl_supplement_visual_scan_20260606_round6/text/supplement_layout.txt
pdfimages -list paper/venues/acl27/build/supplement.pdf
```

Review artifacts:

- Full-page renders:
  `tmp/acl_supplement_visual_scan_20260606_round6/pages_180/`
- Full-page contact sheets:
  `tmp/acl_supplement_visual_scan_20260606_round6/contact_sheets/supplement_pages_01_08.png`
  through
  `tmp/acl_supplement_visual_scan_20260606_round6/contact_sheets/supplement_pages_41_46.png`
- All-page overview:
  `tmp/acl_supplement_visual_scan_20260606_round6/contact_sheets/supplement_pages_01_all_overview.png`
- Content-crop contact sheets:
  `tmp/acl_supplement_visual_scan_20260606_round6/contact_sheets/supplement_content_crops_01_08.png`
  through
  `tmp/acl_supplement_visual_scan_20260606_round6/contact_sheets/supplement_content_crops_41_46.png`
- Source edge risk sheet:
  `tmp/acl_supplement_visual_scan_20260606_round6/contact_sheets/source_edge_risk_candidates.png`
- Page and source scan JSON:
  `tmp/acl_supplement_visual_scan_20260606_round6/page_content_bbox_report.json`,
  `tmp/acl_supplement_visual_scan_20260606_round6/page_edge_candidate_report.json`,
  `tmp/acl_supplement_visual_scan_20260606_round6/source_image_edge_scan.json`,
  `tmp/acl_supplement_visual_scan_20260606_round6/source_image_edge_risk_candidates.json`,
  and `tmp/acl_supplement_visual_scan_20260606_round6/pdfimages_summary.json`
- Durable evidence:
  `paper/shared/evidence/raw/acl27_visual_review/supplement_round6_crop_scale_rescan_20260606.json`

## Findings

No new blocking crop, occlusion, unsafe scaling, caption collision, or incomplete
figure display defect was found in this pass.

Specific rechecks:

- Fig. S25 on page 27 was rechecked against the previously reported incomplete
  bottom concept display. The bottom claim-boundary gate is fully visible in
  the current rendered PDF, with the caption below it and no page-edge collision.
- Fig. S26 on page 28 was rechecked because it also has a bottom visual decision
  gate. The decision gate and right-side reading lanes remain complete.
- GRScenes dense pages 19-24 were reviewed in full-page and content-crop views.
  The VLM guide, stress strip, failure-taxonomy companion, PASS-only companion,
  and zoom-stress companion remain inside their panels and pages.
- Navigation pages 30-38 were reviewed for route-still and media-boundary
  scaling. The selected stills, route overlays, and upload-gate panels are
  visible within their figure frames. Source-edge flags on route case PNGs come
  from intentional still crops, not from PDF-level clipping.
- Theory and manifest pages 39-45 were reviewed for dense figure containment.
  The hypothesis-boundary, review-packet manifest, and source-boundary figures
  are compact but complete.

The page-edge detector reported 27 candidates, mainly due to ACL line numbers,
page numbers, and dense but in-bounds content areas. The source-edge detector
reported 10 candidates. Manual review of the candidate sheet showed intended
full-canvas backgrounds, panel borders, or still-image crops rather than missing
figure content.

`pdfimages -list` reported 47 embedded images with no image below 120 ppi; the
observed ppi range was 125 to 339.

## Changes

No LaTeX source, figure asset, table, or generator change was required. This
pass adds only the durable audit record and the raw visual-review evidence JSON.

## Verification

- PASS: `make -C paper acl27-supplement`
- PASS: rendered all 46 pages at 180 dpi with `pdftoppm`
- PASS: extracted layout text with `pdftotext -layout`
- PASS: generated full-page, content-crop, and source-edge contact sheets
- PASS: `pdfimages -list` found no embedded image below 120 ppi
- PASS: LaTeX log scan found no overfull boxes, float-size warnings, rerun
  warnings, label warnings, or `lineno` warnings

## Residual Risk

This was a visual containment, crop, and scale audit, not an OCR readability or
semantic-claim review. Some atlas/index pages remain intentionally dense. The
current PDF does not show an obvious clipping, occlusion, incorrect scaling, or
incomplete display blocker.
