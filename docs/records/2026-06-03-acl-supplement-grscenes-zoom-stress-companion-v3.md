# 2026-06-03 ACL Supplement GRScenes Zoom-Stress Companion V3

## Scope

Page 24 still had too much unused lower-page area after the v2 zoom-stress
companion. This iteration keeps the zoom-stress table unchanged and rebuilds
the companion as a larger render-heavy page bridge.

## Changes

- Added the v3 AI slot
  `paper/shared/figures/ai_slots/fig_supplement_grscenes_zoom_stress_gate_v3_ai_slot.png`.
- Rebuilt `fig_supplement_grscenes_zoom_stress_table_companion.png` from
  `1800 x 940` to `1800 x 1320`.
- Added a tall registered zoom-level audit strip using stacked original/noMDL
  target-view render pairs.
- Updated the AI-slot manifest and `sources.yaml` to include the v3 slot and
  added picture-pair render evidence.
- Raised the ACL supplement include cap for Figure S23 to `0.56\textheight`.
- Hardened `tests/test_paper_layout.py` so the zoom-stress companion must use
  the v3 slot, mention the registered zoom-level audit strip, include the
  expanded source set, and remain dense.

## Claim Boundary

The v3 zoom-stress gate is AI-generated and exposition only. It is not a VLM
prediction, benchmark row, material-preservation result, render result, or new
experiment. The evidence-bearing content remains the registered original/noMDL
render pairs and the frozen zoom-stress table.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_zoom_stress_companion_v3_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_grscenes_zoom_stress_table_companion.png`

- Size: `1800 x 1320`
- Layout-guard active fraction: `0.493427189`
- SHA-256:
  `2f07847695f1cbc1d6e9c708e8eb7292b5019fb4d8d0382b797a7ca7ecafc11f`

Page 24 raster:
`tmp/acl_supplement_zoom_stress_v3_review_20260603/page-24.png`

Final PDF:
`paper/venues/acl27/build/supplement.pdf`

- SHA-256:
  `04581780247671d6f057fcffd053992f5bc1c18ea7358b3227bd302f367bee39`
- Page count: `45`

Result: PASS by local `render-visual-reviewer` checklist. Page 24 keeps Table
S6, the larger v3 companion, the caption, and the boundary paragraph together.
Page 25 starts the material-effect section normally.

At the same 90 dpi `active245` density used for the sparse-page audit, page 24
increased from `0.131449295` to `0.201200788`.

An initial red-heavy v3 attempt using zoom-019, cup-view-B, and faucet stress
tiles was rejected because it reintroduced large red surfaces. The selected v3
keeps the red-test fraction at `0.000272727` in the standalone figure.

Visual review was local rather than an independent subagent review; the evidence
JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grscenes_zoom_stress_table_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_grscenes_zoom_stress_gate_v3_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_zoom_stress_table_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_zoom_stress_companion_v3_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_grscenes_tables_have_render_companions tests/test_paper_layout.py::test_supplement_grscenes_table_companions_are_registered_and_dense`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py`
- `make -C paper acl27-supplement`
- `pdftoppm -f 23 -l 25 -r 140 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_zoom_stress_v3_review_20260603/page`
- `pdftoppm -f 23 -l 25 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_zoom_stress_v3_review_20260603/page90`
- `pdftotext -f 24 -l 24 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_zoom_stress_v3_review_20260603/page-24.txt`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_zoom_stress_companion_v3_20260603.json`
- `git diff --check -- docs/records/README.md paper/shared/figures/gen_supplement_task_media_atlases.py paper/shared/figures/sources.yaml paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_zoom_stress_table_companion.yaml paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex tests/test_paper_layout.py`
