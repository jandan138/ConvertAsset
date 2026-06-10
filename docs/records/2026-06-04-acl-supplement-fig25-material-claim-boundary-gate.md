# 2026-06-04 ACL Supplement Fig. S25 Material Claim-Boundary Gate

## Context

User visual review found that the bottom concept diagram in supplement Figure
S25 was not fully displayed. The affected asset is
`fig_supplement_material_claim_boundary_atlas.png`, included by
`04_material_effects.tex` as the material claim-boundary visual atlas.

The source AI slot was complete. The defect came from the deterministic atlas
composition path: `_draw_material_claim_boundary_gate_footer` fit the slot with
cover-style scaling, so the schematic was cropped inside the atlas footer before
LaTeX placed the PNG.

## Changes

- Changed the Figure S25 footer slot placement from cover scaling to
  contain/letterbox scaling.
- Regenerated
  `paper/shared/figures/fig_supplement_material_claim_boundary_atlas.png`.
- Added a regression assertion in
  `test_supplement_material_claim_boundary_atlas_is_registered_and_dense` so
  the material claim-boundary gate footer cannot silently return to
  `cover=True`.

## Visual Review

Local visual review used the render visual reviewer protocol. No independent
subagent was spawned because this environment only permits `spawn_agent` when
explicitly requested.

- Standalone atlas: the bottom claim-boundary gate schematic shows all three
  input rows, the center gate, and all three output boxes inside the frame.
- Supplement page 27: Figure S25 is fully contained on the page; the bottom
  concept diagram is complete and the caption remains below the image without
  collision.
- Residual caveat: the AI schematic is slightly smaller because the full source
  aspect ratio is preserved. This is preferable to cropping an exposition-only
  slot.

## Evidence

- Review JSON:
  `paper/shared/evidence/raw/acl27_visual_review/supplement_fig25_material_claim_boundary_gate_20260604.json`
- Rendered page evidence:
  `tmp/acl_fig25_claim_boundary_fix_20260604/page-27.png`
- Final standalone figure:
  `paper/shared/figures/fig_supplement_material_claim_boundary_atlas.png`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'material_claim_boundary_atlas_is_registered_and_dense'`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 160 -f 27 -l 27 paper/venues/acl27/build/supplement.pdf tmp/acl_fig25_claim_boundary_fix_20260604/page`
- `python -m pytest -q tests/test_paper_layout.py`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_fig25_material_claim_boundary_gate_20260604.json >/dev/null`
- `git diff --check -- paper/shared/figures/gen_supplement_task_media_atlases.py tests/test_paper_layout.py docs/records/README.md docs/records/2026-06-04-acl-supplement-fig25-material-claim-boundary-gate.md paper/shared/evidence/raw/acl27_visual_review/supplement_fig25_material_claim_boundary_gate_20260604.json`

## Follow-Up

Keep the updated AI-slot guidance in force for the remaining ACL/supplement
visual review: exposition slots and media strips should default to contained
placement unless a crop is explicitly intentional and visually audited.
