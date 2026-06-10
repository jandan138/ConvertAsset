# 2026-06-05 ACL Supplement S37 Grounding-Contract Visual Fix

## Scope

Continued the ACL27 supplement visual QA pass for obvious figure occlusion,
wrong scaling, and incomplete figure display after the AI-slot containment
updates. The target artifact was:

- `paper/venues/acl27/build/supplement.pdf`
- 46 pages, A4
- PDF creation timestamp: Fri Jun 5 08:49:54 2026 CST

This pass rechecked the full supplement through rendered page contact sheets,
with focused inspection on the material pages, navigation pages, and the theory
appendix.

## Finding

One current blocking visual defect was found on page 39 / Figure S37:

- The `Grounding contract` band in
  `paper/shared/figures/fig_supplement_theory_evidence_bridge.png` was embedding
  the full `fig_supplement_vlm_clean_rerender_panel.png` atlas into a short
  bridge band.
- The source code used cover-style fitting for that full atlas, so the nested
  registered target-view strip appeared as a partially visible sliver rather
  than complete target-box evidence.
- This was a standalone figure-composition issue before LaTeX included the PNG,
  not a PDF page-edge crop.

Figure S25 on page 27 was rechecked in the same pass. Its bottom
claim-boundary concept diagram remains fully visible in the current PDF.

## Changes

Updated `paper/shared/figures/gen_supplement_task_media_atlases.py`:

- Added `_compose_grounding_contract_bridge(size)`.
- Built four complete contained target-box pair cards: backpack, clock, bottle,
  and cup.
- Replaced the `Grounding contract` band in `build_theory_bridge()` with the
  dedicated compositor instead of `_fit(VLM_CLEAN_RERENDER, ..., cover=True)`.

Updated `tests/test_paper_layout.py`:

- Added a regression assertion that the theory bridge uses
  `_compose_grounding_contract_bridge((image_w, band_image_h))`.
- Added a regression assertion rejecting the previous
  `_fit(VLM_CLEAN_RERENDER, (image_w, band_image_h), cover=True)` placement in
  the theory bridge block.
- Adjusted the active-pixel density floor for the theory bridge from `0.38` to
  `0.37`, matching the new contain-safe composition.

Regenerated:

- `paper/shared/figures/fig_supplement_theory_evidence_bridge.png`
- `paper/venues/acl27/build/supplement.pdf`

## Evidence

Raw evidence:

- `paper/shared/evidence/raw/acl27_visual_review/supplement_systematic_visual_scan_s37_grounding_contract_20260605.json`

Rendered review artifacts:

- Before/finding render:
  `tmp/acl_supplement_visual_scan_20260605_round3/pages_160/page-39.png`
- Final rendered pages:
  `tmp/acl_supplement_visual_scan_20260605_round4_after_s37_fix/pages_160/`
- Final full contact sheets:
  `tmp/acl_supplement_visual_scan_20260605_round4_after_s37_fix/contact_sheets/supp_pages_01_12_160.png`
  through
  `tmp/acl_supplement_visual_scan_20260605_round4_after_s37_fix/contact_sheets/supp_pages_37_46_160.png`
- Focused context sheets:
  `tmp/acl_supplement_visual_scan_20260605_round4_after_s37_fix/contact_sheets/s37_fix_context_p37_41.png`
  `tmp/acl_supplement_visual_scan_20260605_round4_after_s37_fix/contact_sheets/material_p25_28.png`
  `tmp/acl_supplement_visual_scan_20260605_round4_after_s37_fix/contact_sheets/nav_p31_38.png`

Final artifact fingerprints:

- `paper/shared/figures/fig_supplement_theory_evidence_bridge.png`
  - SHA-256:
    `0b2994ab99a6f8c47c705f7d562aff35013f89636abbb0b888916dddf12f2ac1`
  - Size: 1800 x 1650
- `paper/venues/acl27/build/supplement.pdf`
  - SHA-256:
    `83fba3dea075a884b0727be510169e1bf9dfcc56f9acb4f98880b144e498e54f`
  - Pages: 46

## Verification

- PASS: `make -C paper acl27-supplement`
- PASS: `python -m pytest -q tests/test_paper_layout.py -k 'supplement_theory_bridge_is_registered_and_dense or acl_supplement_theory_has_visual_evidence_bridge or supplement_material_claim_boundary_atlas_is_registered_and_dense or supplement_material_decision_map_is_registered_and_dense'`
  - Result: `4 passed, 81 deselected`
- PASS: supplement log scan for overfull floats, float-too-large warnings,
  undefined labels, rerun warnings, and lineno warnings returned no matches.
- PASS: rendered all 46 pages at 160 dpi and manually reviewed the page contact
  sheets after the S37 fix.
- PASS: `python -m json.tool` on the raw evidence JSON.
- PASS: `git diff --check` on the touched tracked files, plus
  `git diff --no-index --check` on the two new untracked record/evidence files.

## Residual Risk

This pass targets reader-blocking visual defects: clipped panels, incorrect
scale/crop, incomplete figure display, caption collision, page-edge cuts, and
obvious occlusion. It is not a full OCR readability pass or semantic correctness
review. Several navigation and VLM pages are intentionally dense; in the final
render they are complete but may still be hard to read at print scale.
