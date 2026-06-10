# 2026-06-03 ACL Supplement Grounding Derivation Companion v4

## Scope

This pass revisits the ACL supplement derivation cluster after the round 11
density audit still ranked page 13 as the lowest non-reference page. The goal
was to add more registered render material to the grounding derivation companion
without introducing new experimental evidence or breaking pages 14-15.

## Changes

- Rebuilt `fig_supplement_grounding_derivation_companion.png` at `1800x1320`.
- Added the v3 metric-contract AI slot:
  `paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_v3_ai_slot.png`.
- Added a target close-up scorer wall with six registered GRScenes render crops
  from cup, faucet, and picture target views.
- Increased the ACL supplement grounding companion include from
  `0.30\textheight` to `0.40\textheight`.
- Updated `tests/test_paper_layout.py` to require the target close-up scorer
  wall, the v3 slot, the new registered render sources, and the taller figure.
- Updated `paper/shared/figures/sources.yaml` and
  `paper/shared/figures/ai_slot_manifests/fig_supplement_grounding_derivation_companion.yaml`
  so the new AI slot and registered renders are traceable.

## Claim Boundary

The v3 AI-generated metric-contract slot remains exposition only. It is not a
metric, VLM output, model prediction, benchmark row, or new experiment. The
evidence-bearing content is still the registered original/noMDL GRScenes render
crops and deterministic protocol overlays drawn by
`paper/shared/figures/gen_supplement_task_media_atlases.py`.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grounding_derivation_companion_v4_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_grounding_derivation_companion.png`

- Size: `1800x1320`
- Layout-guard active fraction: `0.466649832`
- Active245 fraction: `0.473994529`
- Red-pixel fraction: `0.006297980`
- SHA-256:
  `73b43a29a50e37bf99390ddfbefe5ad9257e4ed9830b616006f60b053257554f`

PDF review window:
`tmp/acl_supplement_pages13_15_grounding_v4_20260603/page-13.png` through
`tmp/acl_supplement_pages13_15_grounding_v4_20260603/page-15.png`

- Page 13 active245 at 90 dpi: `0.134736802` -> `0.166936270`
- Page 14 active245 at 90 dpi: `0.135478690` -> `0.140447555`
- Page 15 active245 at 90 dpi: `0.136022996` -> `0.138870724`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 13 is denser
while retaining coherent text, figure, and caption flow. Pages 14 and 15 remain
readable and did not pick up a caption-only or figure-only spill. Visual review
was local rather than an independent subagent review; the evidence JSON records
`independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grounding_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_v3_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grounding_derivation_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grounding_derivation_companion_v4_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'derivations_have_render_companions or derivation_companions_are_registered_and_dense'`
  - RED first for the missing target close-up scorer wall and v3 source
    registration; GREEN after implementation with `2 passed, 72 deselected`.
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py` (`74 passed`)
- `make -C paper acl27-supplement`
- `pdftoppm -f 13 -l 15 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_pages13_15_grounding_v4_20260603/page`
- `pdftotext -f 13 -l 15 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_pages13_15_grounding_v4_20260603/pages13-15.txt`
