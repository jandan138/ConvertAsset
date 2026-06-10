# 2026-06-03 ACL Supplement Metric-Boundary Bridge v2

## Scope

This pass revisits page 15 after the round 13 density audit ranked it as the
lowest non-reference page. The goal was to make the Metric Boundary Summary
less sparse by adding more registered render content and an exposition-only
metric-boundary lens strip while keeping the supplement at 45 pages.

## Changes

- Rebuilt `fig_supplement_metric_boundary_bridge.png` at `1800x1250`.
- Added the metric-boundary lens AI slot:
  `paper/shared/figures/ai_slots/fig_supplement_metric_boundary_lens_ai_slot.png`.
- Added a top lens strip with three registered original/noMDL selected-failure
  render pairs from cup, faucet, and picture target views.
- Enlarged the supplement include from `0.92\textwidth` to `\textwidth`.
- Updated `tests/test_paper_layout.py` to require the lens strip, the AI slot,
  the new registered render sources, the manifest, and the denser standalone
  bridge.
- Updated `paper/shared/figures/sources.yaml` and added
  `paper/shared/figures/ai_slot_manifests/fig_supplement_metric_boundary_bridge.yaml`
  for traceability.

## Claim Boundary

The AI-generated metric-boundary lens is exposition only. It is not a metric,
model prediction, benchmark row, VLM output, or new experiment. The
evidence-bearing content is the registered render crops and deterministic
protocol overlays composed by
`paper/shared/figures/gen_supplement_task_media_atlases.py`.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_metric_boundary_bridge_v2_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_metric_boundary_bridge.png`

- Size: `1800x1250`
- Layout-guard active fraction: `0.362602222`
- Active245 fraction: `0.381038667`
- Red-pixel fraction: `0.002457333`
- SHA-256:
  `ff339303e68fcb2bde0bab3c91a7ed32046c871c76a2641a48b008571347c926`

PDF review window:
`tmp/acl_supplement_page15_metric_boundary_lens_v3_final_20260603/page-14.png`
through
`tmp/acl_supplement_page15_metric_boundary_lens_v3_final_20260603/page-16.png`

- Page 15 active245 at 90 dpi:
  `0.138870724` -> `0.179121334`
- Page 15 active245 at 144 dpi after full-textwidth placement:
  `0.157927828`
- Page 14 active245 at 144 dpi after: `0.127156664`
- Page 16 active245 at 144 dpi after: `0.153328308`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 15 is visibly
denser, the full-textwidth bridge remains inside the one-column layout, the
caption stays complete, and pages 14 and 16 show no clipping or spill
regression. Visual review was local rather than an independent subagent review;
the evidence JSON records `independent_subagent_review: false`.

Round 14 full-density audit:
`tmp/acl_supplement_full_density_review_20260603_round14/density_rank.json`

- Page 15 no longer appears in the lowest 12 pages.
- Excluding reference pages 43 and 45, the next low-density targets are page 39
  (`0.139262064`), page 14 (`0.140447555`), and page 41 (`0.140809576`).

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_metric_boundary_bridge.png`
- `paper/shared/figures/ai_slots/fig_supplement_metric_boundary_lens_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_metric_boundary_bridge.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_metric_boundary_bridge_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'metric_boundary_bridge'`
  - RED first for the missing lens strip and source registration, then RED
    again for the full-textwidth include; GREEN after implementation with
    `2 passed, 72 deselected`.
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- `pdftoppm -f 14 -l 16 -png -r 144 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page15_metric_boundary_lens_v3_final_20260603/page`
- `pdftoppm -f 15 -l 15 -png -r 90 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page15_metric_boundary_lens_v3_final_90dpi_20260603/page`
- `pdftoppm -png -r 90 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_full_density_review_20260603_round14/page`
