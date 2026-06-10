# 2026-06-03 ACL Supplement GRScenes Failure-Taxonomy V2

## Scope

Page 22 remained a sparse table page in the GRScenes supplement. This iteration
keeps the selected failure taxonomy unchanged but rebuilds
`fig_supplement_grscenes_failure_taxonomy_table_companion.png` as a taller
render-forward companion with more registered original/noMDL evidence.

## Changes

- Added `fig_supplement_grscenes_failure_taxonomy_gate_v2_ai_slot.png` as the
  selected exposition-only table-reading schematic.
- Updated
  `paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_failure_taxonomy_table_companion.yaml`
  to point at the v2 AI slot and source generated image.
- Rebuilt the failure-taxonomy companion at 1800 x 1260 with six registered
  original/noMDL pair cards plus a taxonomy edge-case render audit strip.
- Expanded `sources.yaml` and the density guard to include the cup-view-B,
  faucet, and picture render pairs used by the v2 companion.
- Raised the ACL supplement include cap for this figure to `0.50\textheight`
  while keeping the table, caption, explanatory paragraph, and next page intact.

## Claim Boundary

The AI slot is exposition only. It is not a VLM prediction, benchmark row,
taxonomy frequency estimate, or model-performance result. The evidence-bearing
content remains the registered GRScenes original/converted render pairs, the
failure-taxonomy table, and the tracked target-projection QA evidence.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_failure_taxonomy_v2_20260603.json`

Page 22 raster:
`tmp/acl_supplement_grscenes_failure_taxonomy_v2_review_20260603/page-22.png`

Result: PASS. Page 22 keeps Table S4, the taller companion, caption, and
explanatory paragraph on one page. Page 23 still starts with the PASS-only
table and companion. Page 22 active245 fraction increased from `0.103080850`
to `0.151929245`.

## Files

- `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`
- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grscenes_failure_taxonomy_table_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_grscenes_failure_taxonomy_gate_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_failure_taxonomy_table_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_failure_taxonomy_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 140 -f 22 -l 23 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_grscenes_failure_taxonomy_v2_review_20260603/page`

Final PDF: `paper/venues/acl27/build/supplement.pdf`

PDF SHA-256:
`139b00ea3d10f9a279b0a572060ff50c8a20aeafb7f001231ae771c897138dfa`
