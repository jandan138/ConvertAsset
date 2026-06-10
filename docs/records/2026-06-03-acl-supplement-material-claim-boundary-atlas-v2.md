# 2026-06-03 ACL Supplement Material Claim-Boundary Atlas V2

## Scope

Page 27 remained visually sparse in the material supplement. This iteration
keeps the existing claim boundary but rebuilds
`fig_supplement_material_claim_boundary_atlas.png` with larger real material
render crops and a bounded visual gate so the page carries more visual evidence
instead of unused white space.

## Changes

- Added `fig_supplement_material_claim_boundary_gate_ai_slot.png` as an
  exposition-only claim-boundary schematic.
- Added
  `paper/shared/figures/ai_slot_manifests/fig_supplement_material_claim_boundary_atlas.yaml`
  and registered it in `sources.yaml`.
- Rebuilt the claim-boundary atlas at 1800 x 1940 with larger fitted render
  crops for covered bins, clearcoat, and procedural texture.
- Added a deterministic claim-boundary gate footer that embeds the AI slot and
  repeats the bounded claim choices.
- Raised the ACL supplement include cap for the atlas to `0.82\textheight`.
- Tightened `test_supplement_material_claim_boundary_atlas_is_registered_and_dense`
  to require the AI slot, manifest, caption boundary text, a taller source, and
  active density at or above `0.26`.

## Claim Boundary

The AI slot is exposition only. It does not serve as material-effect evidence,
converter-ranking evidence, a population-rate estimate, or a material-mechanism
result. The evidence-bearing panels remain the registered material qualitative
render figures and the registered risk/recommender artifacts.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_material_claim_boundary_atlas_v2_20260603.json`

Page 27 raster:
`tmp/acl_supplement_material_claim_boundary_v2_review_20260603/page-27.png`

Result: PASS. Page 27 keeps the figure and caption on one page, and page 28
remains the material decision-map page. Page 27 active245 fraction increased
from `0.110883` to `0.178586717`.

## Files

- `paper/venues/acl27/sections/supplement/04_material_effects.tex`
- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_material_claim_boundary_atlas.png`
- `paper/shared/figures/ai_slots/fig_supplement_material_claim_boundary_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_material_claim_boundary_atlas.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_material_claim_boundary_atlas_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py::test_supplement_material_claim_boundary_atlas_is_registered_and_dense`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 140 -f 27 -l 28 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_material_claim_boundary_v2_review_20260603/page`

Final PDF: `paper/venues/acl27/build/supplement.pdf`

PDF SHA-256:
`f0e3fa4e3906f5b5661378079c761f88e2b6d240843e3a4e54c21b669dd7dd4e`
