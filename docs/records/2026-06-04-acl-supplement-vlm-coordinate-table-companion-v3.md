# 2026-06-04 ACL Supplement VLM Coordinate Table Companion V3

## Scope

Round 28 ranked page 17 among the lowest-density non-reference, non-formula
pages after the page 3 and page 23 passes. This pass updates the VLM coordinate
table companion below Table S2 so the coordinate-frame ablation page carries
more visible render evidence and a denser coordinate-contract schematic.

## Changes

- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_contract_gate_v3_ai_slot.png`.
- Rebuilt `fig_supplement_vlm_coordinate_table_companion.png` from
  `1800 x 1020` to `1800 x 1240`.
- Replaced the v2 coordinate-contract slot with a denser v3 schematic.
- Enlarged the registered coordinate-frame render audit strip, preserving the
  backpack, clock, bottle, cup, and faucet target-view anchors.
- Increased the p17 include allocation from `0.42\textheight` to
  `0.50\textheight`.
- Updated source registration, AI-slot manifest provenance, caption wording,
  and layout tests to require the v3 slot and denser companion.

## Claim Boundary

The v3 AI-generated coordinate-contract schematic is exposition only. It is not
a new VLM prediction, metric, benchmark row, or scoring result. The
evidence-bearing content remains the registered original/noMDL render pairs and
coordinate-frame audit-strip crops composed by deterministic code.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_table_companion_v3_20260604.json`

Generated v3 slot:
`paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_contract_gate_v3_ai_slot.png`

- Size: `1536 x 1024`
- Layout-guard active238: `0.217112859`
- Layout-guard active245: `0.241831462`
- Red-pixel fraction: `0.000219981`
- SHA-256:
  `ddf21bb5b919e372f19885474b28847304d4b6dc0c77fa12019c041aec3c6ffc`

Standalone figure:
`paper/shared/figures/fig_supplement_vlm_coordinate_table_companion.png`

- Size: `1800 x 1020` -> `1800 x 1240`
- Standalone layout-guard active238: `0.450469499` -> `0.514337814`
- Standalone layout-guard active245: `0.460129085` -> `0.529288530`
- Red-pixel fraction: `0.000005376`
- SHA-256:
  `051acb397137307179ac645facba9c5cb0f04444b897cb512ad82d055d50ea2a`

PDF review window:
`tmp/acl_supplement_page17_vlm_coordinate_table_v3_final_20260604/page-16.png`
through `tmp/acl_supplement_page17_vlm_coordinate_table_v3_final_20260604/page-18.png`

- Page 17 active245 at 90 dpi before round 28: `0.160243982`
- Page 17 active245 at 90 dpi after: `0.204405438`
- Improvement from round 28 page 17: `+0.044161456`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `218949fd9de3261b51f85830b8c1f529666e2bd32e163e80ce86888381beaeda`

Result: PASS by local `render-visual-reviewer` checklist. The coordinate table
remains readable, the enlarged companion becomes the page's visual body, and
pages 16 and 18 remain intact.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_vlm_coordinate_table_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_contract_gate_v3_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_table_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/02_vlm_protocol.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_table_companion_v3_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'vlm_protocol or coordinate_table_companion'`
  - RED first for the missing v3 slot, larger include allocation, and taller
    companion; GREEN after implementation with `4 passed, 71 deselected`.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 16 -l 18 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page17_vlm_coordinate_table_v3_final_20260604/page`
- `pdftoppm -r 90 -png -f 17 -l 17 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page17_vlm_coordinate_table_v3_final_90dpi_20260604/page`
