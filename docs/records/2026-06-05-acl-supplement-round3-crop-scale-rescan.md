# 2026-06-05 ACL Supplement Round 3 Crop/Scale Rescan

## Scope

Continued the ACL supplement rendered-PDF review for obvious occlusion, unsafe
scaling, incomplete figure display, and AI-slot containment failures. The source
of truth was the current 46-page
`paper/venues/acl27/build/supplement.pdf`.

This pass added a mechanical page-edge/risk scan on top of contact-sheet and
page-scale visual review:

- Rendered all 46 pages at 180 dpi.
- Generated six contact sheets covering pages 1-8, 9-16, 17-24, 25-32, 33-40,
  and 41-46.
- Generated a high-risk page sheet for pages 22, 24, 27, 28, 30, 33, 36, 37,
  38, 41, 43, and 45.
- Generated dense crops for the same high-risk pages.
- Ran a simple image metric pass for page-edge dark pixels, near-page-edge
  content boxes, large dark blocks, and dense bottom bands.

## Finding

No new blocking crop, occlusion, unsafe scaling, caption collision, or
incomplete-display defect was found.

Specific high-risk rechecks:

- Page 22 / Fig. S21: table, companion figure, bottom render matrix, and
  caption remain complete.
- Page 27 / Fig. S25: the bottom claim-boundary gate is fully displayed,
  including the three input rows, center gate, and right-side cards.
- Page 28 / Fig. S26: the visual decision gate and caption remain on-page.
- Page 38 / Fig. S36: the upload-gate media wall, AI slot, gate cards, paper
  claim-boundary footer, and caption remain complete.
- Page 45 / Fig. S41: the source-boundary gate, registered source tray, paired
  target-view closeups, claim-boundary footer, and caption remain complete.

Some pages remain intentionally dense, especially GRScenes companion tables,
InternNav media atlases, and review-packet/source-boundary contact sheets. This
pass treats those as acceptable when the final PDF still contains the intended
panels and captions without clipping.

## Change

No source, TeX, figure, or test change was required. This record and the raw
visual-review evidence JSON are the only durable additions from this pass.

## Visual Evidence

- Full-page renders:
  `tmp/acl_supplement_visual_scan_20260605_round3/pages_180/`
- Contact sheets:
  - `tmp/acl_supplement_visual_scan_20260605_round3/contact_sheets/supplement_pages_01_08.png`
  - `tmp/acl_supplement_visual_scan_20260605_round3/contact_sheets/supplement_pages_09_16.png`
  - `tmp/acl_supplement_visual_scan_20260605_round3/contact_sheets/supplement_pages_17_24.png`
  - `tmp/acl_supplement_visual_scan_20260605_round3/contact_sheets/supplement_pages_25_32.png`
  - `tmp/acl_supplement_visual_scan_20260605_round3/contact_sheets/supplement_pages_33_40.png`
  - `tmp/acl_supplement_visual_scan_20260605_round3/contact_sheets/supplement_pages_41_46.png`
- High-risk overview:
  `tmp/acl_supplement_visual_scan_20260605_round3/contact_sheets/supplement_high_risk_pages_fullsize_sheet.png`
- Dense crop sheet:
  `tmp/acl_supplement_visual_scan_20260605_round3/contact_sheets/supplement_high_risk_dense_crops_sheet.png`
- Mechanical risk report:
  `tmp/acl_supplement_visual_scan_20260605_round3/supplement_page_edge_risk_report.json`
- Text extraction:
  `tmp/acl_supplement_visual_scan_20260605_round3/text/supplement_layout.txt`

## Verification

- `make -C paper acl27-supplement` reported the supplement target up to date.
- `pdfinfo paper/venues/acl27/build/supplement.pdf` reported 46 A4 pages.
- `sha256sum paper/venues/acl27/build/supplement.pdf`:
  `4c5295b7306453238cfa9a2a14e8cbaea56c16ffec0b22d63b88c6d7a836cb0d`
- The page-edge risk report produced no flagged pages.
- LaTeX log scan for overfull boxes, float sizing warnings, undefined
  references, rerun warnings, and label warnings returned no matches.
- `python -m json.tool tmp/acl_supplement_visual_scan_20260605_round3/supplement_page_edge_risk_report.json >/dev/null`
  passed.
- `python -m pytest -q tests/test_paper_layout.py -k supplement` passed:
  66 passed, 19 deselected.

## Residual Risk

This pass is a rendered-PDF visual review, not semantic proof that every tiny
thumbnail is readable at print size. The residual risk is limited to intentional
dense inspection panels, not observed clipping, occlusion, or incomplete figure
display.
