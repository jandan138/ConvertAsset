# 2026-06-04 ACL Supplement Navigation Derivation Companion v4

## Scope

This pass revisits page 14 after the round 15 density audit ranked it as the
lowest non-reference page. The goal was to make the navigation derivation
companion less sparse by adding a formula-to-route visual bridge, a v4
exposition-only AI navigation gate, and more registered route/case panels while
keeping the supplement at 45 pages.

## Changes

- Rebuilt `fig_supplement_navigation_derivation_companion.png` at `1800x700`.
- Added the v4 navigation metric gate AI slot:
  `paper/shared/figures/ai_slots/fig_supplement_navigation_metric_gate_v4_ai_slot.png`.
- Replaced the previous short two-row strip with three compact bands:
  formula-to-route bridge, route-outcome anchors, and registered route-pair
  audit wall.
- Kept the supplement include bounded at
  `\includegraphics[width=\textwidth,height=0.30\textheight,keepaspectratio]{...}`.
- Updated `tests/test_paper_layout.py` to require the v4 slot, source
  registration, formula-to-route wording, and the denser standalone figure.
- Updated `paper/shared/figures/sources.yaml` and
  `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_derivation_companion.yaml`
  for traceability.

## Claim Boundary

The AI-generated v4 navigation metric gate is exposition only. It is not a
metric, model prediction, benchmark row, navigation run, or new experiment. The
evidence-bearing content is the registered navigation metric panel, route
stills, selected case panels, and 0036/0066 route-case figures composed by
`paper/shared/figures/gen_supplement_task_media_atlases.py`.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_derivation_companion_v4_20260604.json`

Standalone figure:
`paper/shared/figures/fig_supplement_navigation_derivation_companion.png`

- Size: `1800x700`
- Layout-guard active fraction: `0.511965873`
- Active245 fraction: `0.549590476`
- Red-pixel fraction: `0.000610317`
- SHA-256:
  `f8b094748667cca1a8f9e9e4845633f38c4835c0079ef776de60a3f20fd3312f`

Rejected intermediate:

- The first v4 attempt used an `1800x840` figure and `0.34\textheight`
  include. It looked dense but increased the supplement from 45 to 46 pages by
  spilling the Metric Boundary Summary caption onto a new page.
- The final `1800x700` / `0.30\textheight` version keeps the v4 visual content
  and restores the 45-page PDF.

PDF review window:
`tmp/acl_supplement_page14_navigation_derivation_v4_final_20260604/page-14.png`
through
`tmp/acl_supplement_page14_navigation_derivation_v4_final_20260604/page-16.png`

- Page 14 active245 at 90 dpi:
  `0.140447555` -> `0.146674570`
- Page 14 active245 at 144 dpi after final placement:
  `0.134004838`
- Page 15 active245 at 144 dpi after: `0.160508545`
- Page 16 active245 at 144 dpi after: `0.153328308`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 14 keeps the
denser navigation bridge and complete caption while preserving the Navigation
Metrics heading and first SR equation on the same page. Page 15 keeps the
metric-boundary figure and caption on one page, and page 16 still begins the
VLM protocol section. Visual review was local rather than an independent
subagent review; the evidence JSON records `independent_subagent_review:
false`.

Round 16 full-density audit:
`tmp/acl_supplement_full_density_review_20260604_round16/density_rank.json`

- Page 14 is no longer the lowest non-reference page.
- Excluding reference pages 43 and 45, the next low-density targets are page 41
  (`0.140809576`), page 36 (`0.143086229`), and page 22 (`0.144728070`).

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_navigation_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_navigation_metric_gate_v4_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_derivation_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_derivation_companion_v4_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'derivations_have_render_companions or derivation_companions_are_registered_and_dense'`
  - RED first for missing v4 wording, slot/source registration, include height,
    and figure height; GREEN after implementation with `2 passed, 72
    deselected`.
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -f 14 -l 16 -png -r 144 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page14_navigation_derivation_v4_final_20260604/page`
- `pdftoppm -f 14 -l 14 -png -r 90 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page14_navigation_derivation_v4_final_90dpi_20260604/page`
- `pdftoppm -png -r 90 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_full_density_review_20260604_round16/page`
