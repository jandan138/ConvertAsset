# 2026-06-04 ACL Supplement VLM Coordinate Protocol Atlas V2

## Scope

Round 30 ranked page 16 among the next low-density non-reference,
non-formula pages after the page 19 pass. This pass updates the VLM coordinate
protocol atlas so the protocol page carries more registered render crops and a
denser route schematic.

## Changes

- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_vlm_protocol_route_v2_ai_slot.png`.
- Rebuilt `fig_supplement_vlm_coordinate_protocol_atlas.png` from
  `1800 x 1560` to `1800 x 1840`.
- Added a registered protocol audit strip with the route slot plus backpack,
  clock, bottle, and cup target-view crops.
- Increased the p16 include allocation from `0.70\textheight` to
  `0.76\textheight`.
- Updated source registration, AI-slot manifest provenance, caption wording,
  and layout tests to require the v2 slot, taller atlas, and denser protocol
  page.

## Claim Boundary

The v2 AI-generated protocol-route schematic is exposition only. It is not a
new VLM prediction, metric, benchmark row, or scoring result. The
evidence-bearing content remains the registered GRScenes target-view renders
and protocol overlays composed by deterministic code.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_protocol_atlas_v2_20260604.json`

Generated v2 slot:
`paper/shared/figures/ai_slots/fig_supplement_vlm_protocol_route_v2_ai_slot.png`

- Size: `1536 x 1024`
- Layout-guard active238: `0.247330983`
- Layout-guard active245: `0.259911855`
- Red-pixel fraction: `0.000995636`
- SHA-256:
  `d094279a4efb87ea9d6b5271a3e8a554212731af735d270afa60dd42ca84762c`

Standalone figure:
`paper/shared/figures/fig_supplement_vlm_coordinate_protocol_atlas.png`

- Size: `1800 x 1560` -> `1800 x 1840`
- Standalone layout-guard active238: `0.356385328` -> `0.389181159`
- Standalone layout-guard active245: `0.358988604` -> `0.393325483`
- Red-pixel fraction: `0.000003925`
- SHA-256:
  `ffee4d8619002b10252da63b60591ad9747849c9205f0730349432b35f94769e`

PDF review window:
`tmp/acl_supplement_page16_vlm_coordinate_protocol_atlas_v2_final_20260604/page-15.png`
through
`tmp/acl_supplement_page16_vlm_coordinate_protocol_atlas_v2_final_20260604/page-17.png`

- Page 16 active245 at 90 dpi before round 30: `0.166217327`
- Page 16 active245 at 90 dpi after: `0.211681549`
- Improvement from round 30 page 16: `+0.045464222`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `f51a5d6518d855234c38b513ba0427d0466b6b45aee80cfd7986c04b9e3e35eb`

Result: PASS by local `render-visual-reviewer` checklist. The section heading,
explanatory paragraph, enlarged atlas, and caption remain on page 16 without
clipping or overlap, while pages 15 and 17 remain intact.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_vlm_coordinate_protocol_atlas.png`
- `paper/shared/figures/ai_slots/fig_supplement_vlm_protocol_route_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_protocol_atlas.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/02_vlm_protocol.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_protocol_atlas_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'vlm_protocol_has_coordinate_visual_atlas or vlm_coordinate_protocol_atlas_is_registered_and_dense'`
  - RED first for the missing v2 slot, larger include allocation, and taller
    atlas; GREEN after implementation with `2 passed, 73 deselected`.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 15 -l 17 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page16_vlm_coordinate_protocol_atlas_v2_final_20260604/page`
- `pdftoppm -r 90 -png -f 16 -l 16 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page16_vlm_coordinate_protocol_atlas_v2_final_90dpi_20260604/page`
