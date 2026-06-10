# 2026-06-04 ACL Supplement Theory Evidence Bridge v2

## Scope

This pass revisits page 39 after the round 14 density audit ranked it as the
lowest non-reference page. The goal was to make the hypothesis-level theory
bridge less sparse by adding more registered render content and an
exposition-only theory-evidence lens strip while keeping the supplement at 45
pages.

## Changes

- Rebuilt `fig_supplement_theory_evidence_bridge.png` at `1800x1650`.
- Added the theory-evidence lens AI slot:
  `paper/shared/figures/ai_slots/fig_supplement_theory_evidence_lens_ai_slot.png`.
- Added a top lens strip and a selected-failure anchor wall with three
  registered original/noMDL render pairs from cup, faucet, and picture target
  views.
- Enlarged the supplement include to
  `\includegraphics[width=\textwidth,height=0.74\textheight,keepaspectratio]{...}`.
- Updated `tests/test_paper_layout.py` to require the selected-failure render
  wall, the AI slot, the manifest, registered render sources, and the denser
  standalone bridge.
- Updated `paper/shared/figures/sources.yaml` and added
  `paper/shared/figures/ai_slot_manifests/fig_supplement_theory_evidence_bridge.yaml`
  for traceability.

## Claim Boundary

The AI-generated theory-evidence lens is exposition only. It is not a metric,
model prediction, benchmark row, VLM output, or new experiment. The
evidence-bearing content is the registered render crops and deterministic
protocol overlays composed by
`paper/shared/figures/gen_supplement_task_media_atlases.py`.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_theory_evidence_bridge_v2_20260604.json`

Standalone figure:
`paper/shared/figures/fig_supplement_theory_evidence_bridge.png`

- Size: `1800x1650`
- Layout-guard active fraction: `0.395395286`
- Active245 fraction: `0.410946128`
- Red-pixel fraction: `0.005156902`
- SHA-256:
  `d86a4f795c9d69fd18cc9f2fad098850e6c5ecee986f43bdb9a1875aceed6c67`

PDF review window:
`tmp/acl_supplement_page39_theory_bridge_v2_final_20260604/page-38.png`
through
`tmp/acl_supplement_page39_theory_bridge_v2_final_20260604/page-40.png`

- Page 39 active245 at 90 dpi:
  `0.139262064` -> `0.192053385`
- Page 39 active245 at 144 dpi after full placement:
  `0.176189294`
- Page 38 active245 at 144 dpi after: `0.212400107`
- Page 40 active245 at 144 dpi after: `0.175787428`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 39 is visibly
denser, the enlarged bridge remains on one page, the caption stays complete,
and pages 38 and 40 show no clipping, spill, or float-order regression. Visual
review was local rather than an independent subagent review; the evidence JSON
records `independent_subagent_review: false`.

Round 15 full-density audit:
`tmp/acl_supplement_full_density_review_20260604_round15/density_rank.json`

- Page 39 no longer appears in the lowest 12 pages.
- Excluding reference pages 43 and 45, the next low-density targets are page 14
  (`0.140447555`), page 41 (`0.140809576`), and page 36 (`0.143086229`).

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_theory_evidence_bridge.png`
- `paper/shared/figures/ai_slots/fig_supplement_theory_evidence_lens_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_theory_evidence_bridge.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/06_theory.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_theory_evidence_bridge_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'theory_has_visual_evidence_bridge or theory_bridge_is_registered_and_dense'`
  - RED first for the missing selected-failure render wall and source
    registration; GREEN after implementation with `2 passed, 72 deselected`.
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -f 38 -l 40 -png -r 144 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page39_theory_bridge_v2_final_20260604/page`
- `pdftoppm -f 39 -l 39 -png -r 90 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page39_theory_bridge_v2_final_90dpi_20260604/page`
- `pdftoppm -png -r 90 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_full_density_review_20260604_round15/page`
