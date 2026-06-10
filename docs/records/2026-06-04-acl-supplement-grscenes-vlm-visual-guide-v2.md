# 2026-06-04 ACL Supplement GRScenes VLM Visual Guide V2

## Scope

Round 29 still ranked page 19 as a low-density GRScenes VLM page after the
page 17 pass. This pass updates the GRScenes VLM visual guide so the page
carries more registered render evidence and a denser reading-route overview.

## Changes

- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_grscenes_vlm_reading_route_v2_ai_slot.png`.
- Rebuilt `fig_supplement_grscenes_vlm_visual_guide.png` from
  `1800 x 1510` to `1800 x 1710`.
- Added a registered guide audit strip with the reading-route slot plus
  backpack, clock, bottle, cup, and scene-context render crops.
- Increased the p19 include allocation from `0.78\textheight` to
  `0.84\textheight`.
- Updated source registration, AI-slot manifest provenance, caption wording,
  and layout tests to require the v2 slot, taller figure, and denser visual
  guide.

## Claim Boundary

The v2 AI-generated reading-route schematic is exposition only. It is not a new
VLM prediction, metric, benchmark row, or scoring result. The evidence-bearing
content remains the registered target-view renders, context crops, and
normalized-coordinate panels composed by deterministic code.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_vlm_visual_guide_v2_20260604.json`

Generated v2 slot:
`paper/shared/figures/ai_slots/fig_supplement_grscenes_vlm_reading_route_v2_ai_slot.png`

- Size: `1536 x 1024`
- Layout-guard active238: `0.292286555`
- Layout-guard active245: `0.300230662`
- Red-pixel fraction: `0.005732218`
- SHA-256:
  `bee71e9b60cfd76518f3eeac1e274677df1b8797bbfd3da4911fdcbed593238e`

Standalone figure:
`paper/shared/figures/fig_supplement_grscenes_vlm_visual_guide.png`

- Size: `1800 x 1510` -> `1800 x 1710`
- Standalone layout-guard active238: `0.370761589` -> `0.395805068`
- Standalone layout-guard active245: `0.372955850` -> `0.398844704`
- Red-pixel fraction: `0.000065627`
- SHA-256:
  `8162210f4c0d52bd8485b9f550ddad82488ba896c8ba3bedfd9fc3d3516ba2a5`

PDF review window:
`tmp/acl_supplement_page19_grscenes_vlm_visual_guide_v2_final_20260604/page-18.png`
through
`tmp/acl_supplement_page19_grscenes_vlm_visual_guide_v2_final_20260604/page-20.png`

- Page 19 active245 at 90 dpi before round 29: `0.162338349`
- Page 19 active245 at 90 dpi after: `0.195692716`
- Improvement from round 29 page 19: `+0.033354367`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `019226a7d4aca52a1cab80bc6416f2021a692200c6eedc40f23ce0304653aa7a`

Result: PASS by local `render-visual-reviewer` checklist. The section heading,
enlarged visual guide, and caption remain on page 19 without clipping or
overlap, while pages 18 and 20 remain intact.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grscenes_vlm_visual_guide.png`
- `paper/shared/figures/ai_slots/fig_supplement_grscenes_vlm_reading_route_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_vlm_visual_guide.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_vlm_visual_guide_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'grscenes_vlm_has_visual_guide or grscenes_vlm_visual_guide_is_registered_and_dense'`
  - RED first for the missing v2 slot, larger include allocation, and taller
    guide; GREEN after implementation with `2 passed, 73 deselected`.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 18 -l 20 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page19_grscenes_vlm_visual_guide_v2_final_20260604/page`
- `pdftoppm -r 90 -png -f 19 -l 19 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page19_grscenes_vlm_visual_guide_v2_final_90dpi_20260604/page`
