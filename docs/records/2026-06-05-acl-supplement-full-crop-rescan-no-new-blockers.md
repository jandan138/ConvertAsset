# 2026-06-05 ACL Supplement Full Crop Rescan: No New Blockers

## Scope

Continued the ACL supplement visual review after the Fig. S37 material-row
containment fix. This pass used the current 46-page
`paper/venues/acl27/build/supplement.pdf` as the rendered source of truth and
looked for obvious occlusion, unsafe scaling, and incomplete figure display in
the supplement.

The scan covered all pages through 160-dpi rendered contact sheets, then opened
high-risk pages at page scale:

- Pages 1-12, 13-24, 25-36, and 37-46 as four contact sheets.
- Fig. S25/S26 material pages: pages 27 and 28.
- InternNav case and companion pages: pages 31, 32, 33, 36, and 38.
- GRScenes table companion pages: pages 20, 21, 22, 23, and 24.
- Source-boundary companion: page 45.

## Finding

No new blocking crop, scale, page-edge overflow, caption collision, or
incomplete-display defect was found in this pass.

Specific rechecks:

- Fig. S25 on page 27 remains complete. The bottom claim-boundary gate, its
  right-side interpretation cards, and the caption spacing are visible.
- Fig. S26 on page 28 remains complete. The visual decision gate is visible;
  the caption is near the bottom but still safely on-page.
- Fig. S29/S30 on pages 31/32 remain readable. Some route-map content is tight
  because the source case strips are compact, but the PDF is not cutting off
  the rendered image.
- Fig. S31/S34/S36 on pages 33, 36, and 38 remain complete despite dense
  navigation media layouts.
- Fig. S19-S23 on pages 20-24 remain complete. Audit-strip crops are intentional
  row-inspection crops rather than PDF clipping.
- Fig. S41 on page 45 remains complete, including the source-boundary gate,
  registered render source tray, paired target-view closeups, and claim-boundary
  footer.

## Change

No source, TeX, figure, or test change was required by this pass. The only
durable additions are this review record and the raw visual-review evidence
JSON.

## Visual Evidence

- Full-page renders:
  `tmp/acl_supplement_visual_scan_20260605_round2_before/pages_160/`
- Contact sheets:
  - `tmp/acl_supplement_visual_scan_20260605_round2_before/contact_sheets/supplement_pages_01_12.png`
  - `tmp/acl_supplement_visual_scan_20260605_round2_before/contact_sheets/supplement_pages_13_24.png`
  - `tmp/acl_supplement_visual_scan_20260605_round2_before/contact_sheets/supplement_pages_25_36.png`
  - `tmp/acl_supplement_visual_scan_20260605_round2_before/contact_sheets/supplement_pages_37_46.png`
- Text extraction:
  `tmp/acl_supplement_visual_scan_20260605_round2_before/text/supplement_layout.txt`

## Verification

- `make -C paper acl27-supplement` reported the supplement target up to date.
- `pdfinfo paper/venues/acl27/build/supplement.pdf` reported 46 A4 pages.
- `sha256sum paper/venues/acl27/build/supplement.pdf`:
  `4c5295b7306453238cfa9a2a14e8cbaea56c16ffec0b22d63b88c6d7a836cb0d`
- LaTeX log scan for overfull boxes, float sizing warnings, undefined
  references, rerun warnings, and label warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py -k supplement` passed:
  66 passed, 19 deselected.

## Residual Risk

Several supplement pages are intentionally dense and some registered case
strips use source-level crops to show selected route/still evidence. This pass
did not treat those compact source strips as blockers unless the final PDF
visibly cut off a figure, caption, AI slot, gate card, or evidence panel.
