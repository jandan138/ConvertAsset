# 2026-06-03 ACL Supplement VLM Coordinate Table Companion V2

## Scope

Page 17 remained sparse after the first coordinate-table companion. This pass
keeps the same claim boundary but makes the visual evidence denser and larger:
the companion is now a 1800 x 1020 atlas with four original/noMDL target-view
cards, a cleaner AI gate slot, and a registered coordinate-frame render audit
strip.

## Changes

- Added `fig_supplement_vlm_coordinate_contract_gate_v2_ai_slot.png` as the
  exposition-only coordinate-contract gate.
- Rebuilt `fig_supplement_vlm_coordinate_table_companion.png` with a taller
  deterministic layout and six bottom-strip registered target-view render tiles.
- Added the faucet noMDL target view to the coordinate-table companion source
  registry.
- Raised the ACL supplement include cap for the companion to `0.42\textheight`.
- Tightened layout tests to require the v2 AI slot, the extra registered render
  source, a 900-1120 px figure height, and active density at or above `0.34`.

## Claim Boundary

The AI slot is exposition only. It explains coordinate-frame flow and does not
serve as VLM evidence. The evidence-bearing panels remain registered GRScenes
original/noMDL target-view renders and the coordinate tables.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_table_companion_v2_20260603.json`

Page 17 raster:
`tmp/acl_supplement_coordinate_table_v2_review_20260603/page-17.png`

Result: PASS. Page 17 keeps Table S2, the enlarged companion, caption, and
explanatory paragraph on one page. The bottom strip adds registered target-view
renders without red-dominant material cues. Page 17 active245 fraction increased
from `0.102799` to `0.145236935`.

## Files

- `paper/venues/acl27/sections/supplement/02_vlm_protocol.tex`
- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_vlm_coordinate_table_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_contract_gate_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_table_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_table_companion_v2_20260603.json`

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py::test_supplement_vlm_coordinate_table_companion_is_registered_and_dense`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 140 -f 17 -l 18 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_coordinate_table_v2_review_20260603/page`

Final PDF: `paper/venues/acl27/build/supplement.pdf`

PDF SHA-256:
`410b4be15b736f044e5f8f234bb2786c0b62e9c4ef99282836746572d5aaf9a5`
