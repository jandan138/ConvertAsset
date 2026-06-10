# 2026-06-04 ACL Supplement Material Decision Map v3

## Scope

Round 36 ranked page 28 as the next practical visual-density target after the
GRScenes failure-taxonomy v4 pass. Page 28 already had the v2 material decision
map, but the PDF page still showed unused vertical space and only a limited
covered-bin render view.

## Changes

- Added
  `paper/shared/figures/ai_slots/fig_supplement_material_decision_gate_v2_ai_slot.png`
  as the selected material-decision gate slot.
- Expanded
  `paper/shared/figures/fig_supplement_material_decision_map.png`
  from `1800 x 1940` to `1800 x 2480`.
- Added a covered-bin render matrix with original, ConvertAsset, and NVIDIA
  crops for bottle, clock, cup, and backpack, all cropped from the registered
  material qualitative evidence figure.
- Updated the material-decision manifest and source registry to point at the v2
  gate slot.
- Updated the composer to place `MATERIAL_DECISION_GATE_AI_SLOT` with
  `cover=False` contain scaling, following the updated AI-slot composition rule
  against slot cropping or occlusion.
- Tightened the layout test to require the v2 slot, taller page-shaped board,
  and contain placement for the material-decision gate.

## Claim Boundary

The new render matrix is reviewer guidance over already registered material
qualitative renders. It does not add a converter ranking, material-mechanism
result, population rate, or new experimental outcome. The AI-generated
material-decision gate is exposition only and remains replaceable by a real
render or deterministic schematic later.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_material_decision_map_v3_20260604.json`

Standalone figure:
`paper/shared/figures/fig_supplement_material_decision_map.png`

- Size: `1800 x 2480`
- Layout-guard active238: `0.256641129`
- Layout-guard active245: `0.288958333`
- Red-pixel fraction: `0.000624776`
- SHA-256:
  `ef24da1ace3332447604b09d3fb3de3f9e31944e70589a8f1b359a8165f9f6af`

Material-decision gate v2 slot:
`paper/shared/figures/ai_slots/fig_supplement_material_decision_gate_v2_ai_slot.png`

- Size: `1536 x 1024`
- Layout-guard active238: `0.261547089`
- Layout-guard active245: `0.306255976`
- Red-pixel fraction: `0.007268270`
- SHA-256:
  `ed7bf7e9104866f059a96d58f3715d40d19b7b529c95b36c3b0078826f254e9e`

Slot containment crop:
`tmp/acl_supplement_page28_material_decision_map_v3_20260604/material_decision_gate_contain_crop.png`

- SHA-256:
  `47bc6f59c5906f870d0d885befce375353f58652c8561f80b47bb6c7e86486b1`
- Result: PASS. The AI slot is contained inside its footer frame, not
  center-cropped or overlapped by deterministic claim cards.

PDF review window:
`tmp/acl_supplement_page28_material_decision_map_v3_20260604/page-27.png`
through
`tmp/acl_supplement_page28_material_decision_map_v3_20260604/page-29.png`

- Page 28 active245 at 90 dpi before round 36: `0.172372958`
- Page 28 active245 at 90 dpi after: `0.186445885`
- Improvement from round 36 page 28: `+0.014072927`
- Supplement PDF: 45 pages, A4, `50,642,089` bytes
- PDF SHA-256:
  `4af2e93fcedb0f2240176c75139edf52cecd4488987624cb4b8e594ca27904fc`

Result: PASS by local `render-visual-reviewer` and
`research-figure-ai-slot-composer` checklists. Page 28 contains the expanded
decision map and full caption without clipping or page spill; page 29 still
starts the navigation evidence opener. Visual review was local rather than an
independent subagent review; the evidence JSON records
`independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_material_decision_map.png`
- `paper/shared/figures/ai_slots/fig_supplement_material_decision_gate_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_material_decision_map.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_material_decision_map_v3_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'material_decision_map_is_registered_and_dense'`
  - RED first for the old slot/source and stale shorter board; GREEN after the
    v2 gate, covered-bin matrix, and contain placement.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 27 -l 29 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page28_material_decision_map_v3_20260604/page`
- `pdftoppm -r 90 -png -f 28 -l 28 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page28_material_decision_map_v3_90dpi_20260604/page`
