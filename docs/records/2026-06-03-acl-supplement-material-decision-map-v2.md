# 2026-06-03 ACL Supplement Material Decision Map V2

## Scope

Page 28 was still visually sparse after the earlier material supplement pass.
This iteration keeps the same claim boundary but rebuilds
`fig_supplement_material_decision_map.png` to put more visible material-render
evidence on the page and replace the text-only footer with a bounded visual
decision gate.

## Changes

- Added `fig_supplement_material_decision_gate_ai_slot.png` as an
  exposition-only material-decision schematic.
- Added
  `paper/shared/figures/ai_slot_manifests/fig_supplement_material_decision_map.yaml`
  and registered it in `sources.yaml`.
- Rebuilt the material decision map with larger fitted render crops for covered
  bins, clearcoat, and procedural texture.
- Replaced the prior NVIDIA-baseline text footer with a deterministic visual
  gate section that embeds the AI slot and repeats the claim-boundary choices.
- Tightened `test_supplement_material_decision_map_is_registered_and_dense` to
  require the AI slot, manifest, caption boundary text, and active density at or
  above `0.22`.

## Claim Boundary

The AI slot is exposition only. It does not serve as material-effect evidence,
converter-ranking evidence, or a material-mechanism result. The evidence-bearing
panels remain the registered material qualitative render figures and the
registered risk/recommender artifacts.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_material_decision_map_v2_20260603.json`

Page 28 raster:
`tmp/acl_supplement_material_decision_map_v2_review_20260603/page-28.png`

Result: PASS. Page 28 keeps the figure and caption on one page, and page 29
starts the navigation supplement cleanly. Page 28 active245 fraction increased
from `0.106611` to `0.156651399`.

## Files

- `paper/venues/acl27/sections/supplement/04_material_effects.tex`
- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_material_decision_map.png`
- `paper/shared/figures/ai_slots/fig_supplement_material_decision_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_material_decision_map.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_material_decision_map_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py::test_supplement_material_decision_map_is_registered_and_dense`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 140 -f 28 -l 29 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_material_decision_map_v2_review_20260603/page`

Final PDF: `paper/venues/acl27/build/supplement.pdf`

PDF SHA-256:
`7cf8515bf8b2e88fef333a5691123ca9d97b031453432526d715ffbe0f641692`
