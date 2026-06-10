# 2026-06-03 ACL Supplement Theory Hypothesis-Boundary v2

## Scope

This pass addresses page 41 after the round 12 density audit ranked it as the
lowest non-reference page. The goal was to make the theory page less sparse by
adding more registered render content to the in-column hypothesis-boundary
companion without creating a new spill page.

## Changes

- Rebuilt `fig_supplement_theory_hypothesis_boundary_companion.png` at
  `920x1500`.
- Added the v2 hypothesis-boundary AI slot:
  `paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v2_ai_slot.png`.
- Added a selected failure render wall with paired cup, faucet, and picture
  target crops.
- Increased the rendered theory companion include from `0.34\textheight` to
  `0.36\textheight`.
- Updated `tests/test_paper_layout.py` to require the selected-failure render
  wall, the v2 slot, the new registered render sources, and the taller
  standalone companion.
- Updated the figure source manifest and AI-slot manifest for traceability.

## Claim Boundary

The v2 AI-generated hypothesis-boundary lens remains exposition only. It is not
a causal proof, population rate, metric, benchmark row, or new experiment. The
evidence-bearing content is the registered material, grounding, navigation, and
selected-failure render crops composed by deterministic code.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_companion_v2_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png`

- Size: `920x1500`
- Layout-guard active fraction: `0.414645652`
- Active245 fraction: `0.428055072`
- Red-pixel fraction: `0.000234058`
- SHA-256:
  `e3e70281fe1deabe968edbd7ef850ec77dabf34e145e85c3060dbed1a9db2c18`

PDF review window:
`tmp/acl_supplement_page41_theory_hypothesis_v2_final_20260603/page-40.png`
through `tmp/acl_supplement_page41_theory_hypothesis_v2_final_20260603/page-42.png`

- Page 41 active245 at 90 dpi: `0.136328929` -> `0.140809576`
- Page 40 active245 at 90 dpi: unchanged at `0.183431168`
- Page 42 active245 at 90 dpi: unchanged at `0.177535581`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 41 now has a
denser in-column companion and keeps the theory text complete on the same page.
A larger `0.38\textheight` include and an earlier `0.42\textheight` include both
created a 46-page PDF with a sparse theory spill page, so the accepted rendered
allocation is `0.36\textheight`. Visual review was local rather than an
independent subagent review; the evidence JSON records
`independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_theory_hypothesis_boundary_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/06_theory.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_companion_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'theory_has_hypothesis_boundary_companion or theory_hypothesis_boundary_companion_is_registered_and_dense'`
  - RED first for the missing selected-failure wall and v2 source registration;
    GREEN after implementation with `2 passed, 72 deselected`.
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py` (`74 passed`)
- `make -C paper acl27-supplement`
- `pdftoppm -f 40 -l 42 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_v2_final_20260603/page`
- `pdftotext -f 40 -l 42 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_v2_final_20260603/pages40-42.txt`
