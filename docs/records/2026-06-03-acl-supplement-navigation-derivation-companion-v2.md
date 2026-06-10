# 2026-06-03 ACL Supplement Navigation Derivation Companion V2

## Scope

The navigation derivation page still read as sparse math. This pass replaces the
old navigation companion with a compact, full-width 1800 x 560 media atlas that
fits with its caption on page 14.

## Changes

- Added a new AI-generated `navigation_metric_gate` slot at
  `paper/shared/figures/ai_slots/fig_supplement_navigation_metric_gate_v2_ai_slot.png`.
- Rebuilt `fig_supplement_navigation_derivation_companion.png` as five compact
  top cards plus a registered navigation media audit strip.
- Expanded the companion provenance to include selected rollout panels,
  0036/0066 route panels, and selected case crops.
- Tightened the supplement include height and caption typography so the figure
  and caption stay together on page 14.
- Updated layout tests to require the navigation-specific AI slot, registered
  media sources, bounded figure height, and density threshold.

## Claim Boundary

The AI slot is exposition only. The evidence-bearing content remains the
registered InternNav metric panel, route strips, rollout stills, and selected
case panels. The caption says the AI-generated navigation-metric gate schematic
is not new metrics, model predictions, or benchmark rows.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_derivation_companion_v2_20260603.json`

Page 14 raster:
`tmp/acl_supplement_navigation_derivation_v2_review_20260603/page-14.png`

Result: PASS. Page 14 keeps the companion and caption together, with no visible
clipping or overlap. Page 15 starts the metric-boundary summary and remains
intact. The standalone figure has active238 fraction `0.309787698`; page 14
active245 fraction is `0.092388038`.

## Files

- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_navigation_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_navigation_metric_gate_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_derivation_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_derivation_companion_v2_20260603.json`

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_derivations_have_render_companions tests/test_paper_layout.py::test_supplement_derivation_companions_are_registered_and_dense`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 140 -f 14 -l 15 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_navigation_derivation_v2_review_20260603/page`

Final PDF: `paper/venues/acl27/build/supplement.pdf`

PDF SHA-256:
`7a775b089e68cf94ffd5fce1e4e5293a98b256106660e2c3a29752860612e323`
