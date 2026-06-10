# 2026-06-05 ACL Supplement Systematic Visual Scan: S39 And Registry Density

## Scope

Continued the ACL supplement visual audit for obvious figure occlusion,
mis-scaling, and incomplete display problems. The pass used freshly rendered
PDF pages rather than source-only inspection.

## Findings And Changes

- Rebuilt `paper/venues/acl27/build/supplement.pdf` and rendered all pages to
  `tmp/acl_supplement_systematic_scan_20260605_round2/`.
- Confirmed the previously reported Figure S25 material claim-boundary gate is
  now fully visible in the final PDF page render.
- Found Figure S39 was not clipped, but was mis-scaled: the dense portrait
  hypothesis-boundary companion was squeezed into a right-column figure. Moved
  it to a one-column figure page in
  `paper/venues/acl27/sections/supplement/06_theory.tex`.
- Found the evidence-gate registry companion on Page 3 was visually complete but
  too sparse for the supplement density regression. Increased the real render
  area in `build_evidence_gate_registry_companion()` and regenerated
  `paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png`.
  The active-pixel density is now `0.427860`.
- Rechecked representative dense pages: S6, S7, S15, S17, S18, S21-S23, S25,
  S26, S28, S34-S36, S39, and the final source-boundary page. No additional
  blocking crop, overlap, or incomplete-display issue was found.

## Evidence

- Initial rendered pages:
  `tmp/acl_supplement_systematic_scan_20260605_round2/pages_160/`
- Initial contact sheets:
  `tmp/acl_supplement_systematic_scan_20260605_round2/contact_sheets/`
- Final rendered pages:
  `tmp/acl_supplement_systematic_scan_20260605_round2_final/pages_160/`
- Final contact sheets:
  `tmp/acl_supplement_systematic_scan_20260605_round2_final/contact_sheets/`
- Final page boundary metrics:
  `tmp/acl_supplement_systematic_scan_20260605_round2_final/page_bbox_margins.json`
- Final PDF:
  `paper/venues/acl27/build/supplement.pdf` (`46` A4 pages)

## Verification

- `make -C paper acl27-supplement`
- `python -m pytest -q tests/test_paper_layout.py -k 'supplement'`
- `python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_overview_has_evidence_gate_registry_companion tests/test_paper_layout.py::test_supplement_evidence_gate_registry_companion_is_registered_and_dense tests/test_paper_layout.py::test_acl_supplement_theory_has_hypothesis_boundary_companion tests/test_paper_layout.py::test_supplement_theory_hypothesis_boundary_companion_is_registered_and_dense`
- `pdftoppm -png -r 160 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_systematic_scan_20260605_round2_final/pages_160/page`
- `rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label" paper/venues/acl27/build/supplement.log`
- `git diff --check -- paper/venues/acl27/sections/supplement/06_theory.tex paper/shared/figures/gen_supplement_task_media_atlases.py paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png tests/test_paper_layout.py docs/records/README.md docs/records/2026-06-05-acl-supplement-systematic-visual-scan-s39-registry-density.md`
- `rg -n "[ \t]$" docs/records/2026-06-05-acl-supplement-systematic-visual-scan-s39-registry-density.md paper/shared/figures/gen_supplement_task_media_atlases.py paper/venues/acl27/sections/supplement/06_theory.tex`
- `python -m py_compile paper/shared/figures/gen_supplement_task_media_atlases.py`

## Residual Risk

The supplement still contains intentionally dense audit atlases and table
companions. This pass focused on obvious reader-blocking visual failures:
clipping, occlusion, wrong scale, missing lower panels, and page-edge overflow.
Further polish could still improve table prose density or split some dense
diagnostic atlases, but no current rendered page shows a blocking crop or
incomplete figure.
