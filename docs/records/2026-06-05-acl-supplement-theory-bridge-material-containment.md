# 2026-06-05 ACL Supplement Theory Bridge Material Containment

## Scope

Continued the ACL supplement visual scan for obvious figure occlusion,
unsafe scaling, and incomplete figure display. This pass started from the
current 46-page `paper/venues/acl27/build/supplement.pdf` and specifically
rechecked Fig. S25 plus other dense or AI-slot supplement pages.

## Finding

Fig. S25 on page 27 remains complete in the current PDF: the bottom
claim-boundary gate is visible, including the right-side cards and caption
spacing.

The new blocking visual issue was on page 39 / Fig. S37. In the
`Material salience` row of `fig_supplement_theory_evidence_bridge.png`, the
clearcoat and procedural material strips were internally cropped into narrow
vertical slivers. The PDF page itself was not clipped; the source PNG had
already lost the left/right context because `_compose_material_bridge()` used
cover-style `_crop_fit()` for wide supplemental material crops.

## Change

- Switched the two wide supplemental material crops inside
  `_compose_material_bridge()` from `_crop_fit()` to `_crop_contain()`.
- Regenerated `paper/shared/figures/fig_supplement_theory_evidence_bridge.png`
  through `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Added a regression check in `tests/test_paper_layout.py` so the theory bridge
  material-row supplemental crops must use contain/letterbox placement.

## Visual Evidence

- Final high-risk contact sheet:
  `tmp/acl_supplement_systematic_scan_20260605_round5_final/contact_sheets/supp_high_risk_pages_final_180dpi.png`
- Final page 39 render:
  `tmp/acl_supplement_systematic_scan_20260605_round5_final/pages_180/page-39.png`
- Final Fig. S37 material-row crop:
  `tmp/acl_supplement_systematic_scan_20260605_round5_final/crops/page39_fig_s37_material_row_final.png`
- Final Fig. S25 crop:
  `tmp/acl_supplement_systematic_scan_20260605_round5_final/crops/page27_fig_s25_final.png`
- Final page boundary scan:
  `tmp/acl_supplement_systematic_scan_20260605_round5_final/page_bbox_margins.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py::test_supplement_theory_bridge_is_registered_and_dense`
  passed after first failing on the old `_crop_fit()` placement.
- `python paper/shared/figures/gen_supplement_task_media_atlases.py` regenerated
  the supplement figure set.
- `make -C paper acl27-supplement` passed and produced a 46-page A4 supplement.
- `python -m pytest -q tests/test_paper_layout.py -k 'supplement'` passed:
  66 passed, 19 deselected.
- LaTeX log scan for overfull boxes, float sizing warnings, undefined
  references, rerun warnings, and label warnings returned no matches.

Final PDF SHA-256:
`4c5295b7306453238cfa9a2a14e8cbaea56c16ffec0b22d63b88c6d7a836cb0d`

Final Fig. S37 source PNG SHA-256:
`579489ea2881712042f47fd156a3e1e4dfdd1cd7edfea6c3c54f3fac2e5411b8`

## Residual Risk

Several supplement pages remain intentionally dense. In this pass, the dense
pages reviewed at paper scale did not show a new blocking crop, caption
collision, page-edge overflow, or incomplete-display defect. Page 39 now uses
contain placement for the material strips, which preserves content at the cost
of some blank space inside the material row.
