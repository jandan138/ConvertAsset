# 2026-06-03 ACL Supplement Navigation Derivation Companion V3

## Scope

Page 14 still read as a sparse derivation page. A first tall rebuild made the
companion visually denser but pushed it to page 15, so this iteration keeps the
page-fit footprint and makes the figure itself denser.

## Changes

- Added `fig_supplement_navigation_metric_gate_v3_ai_slot.png` as the selected
  exposition-only navigation-metric gate schematic.
- Rebuilt `fig_supplement_navigation_derivation_companion.png` at 1800 x 560
  with a light page-fit canvas, render-heavy top cards, and a registered
  navigation media audit strip.
- Expanded `sources.yaml` and the layout guard to include selected cases 04-06,
  0036/0066 route cases 04-06, and the v3 AI slot.
- Updated
  `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_derivation_companion.yaml`
  to point at the v3 generated image and workspace slot.
- Kept the ACL supplement include cap at `0.26\textheight` because larger caps
  moved the figure to page 15.

## Claim Boundary

The AI slot is exposition only. It is not a navigation metric, route-success
statistic, model prediction, benchmark row, or replacement for the frozen
official-scene run. The evidence-bearing content remains the registered
InternNav stills, route panels, metric panel, selected-case crops, and
0036/0066 route-case crops.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_derivation_companion_v3_20260603.json`

Page 14 raster:
`tmp/acl_supplement_navigation_derivation_v3_review_20260603/page-14.png`

Result: PASS. Page 14 keeps the navigation formulas, v3 companion, and caption
together. Page 15 starts the metric-boundary summary normally. Page 14
active245 fraction increased from `0.092388038` in the v2 record to
`0.126527569533`.

## Files

- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_navigation_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_navigation_metric_gate_v3_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_derivation_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_derivation_companion_v3_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_derivations_have_render_companions tests/test_paper_layout.py::test_supplement_derivation_companions_are_registered_and_dense`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -png -r 140 -f 13 -l 15 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_navigation_derivation_v3_review_20260603/page`

Final PDF: `paper/venues/acl27/build/supplement.pdf`

PDF SHA-256:
`53a1d4ff935cff87ffbe70510210ae10b3e598e304cfb10cba316bae09181909`
