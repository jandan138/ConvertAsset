# 2026-06-03 ACL Supplement VLM Coordinate Baseline Sanity Companion v2

## Scope

Iterated the ACL supplement coordinate-baseline page after a density review
flagged page 18 as still visually thin. The v2 pass keeps
`fig_supplement_vlm_coordinate_baseline_sanity_companion.png` as the stable
paper figure path, but rebuilds it as a taller `1800x1040` slot-composed
figure.

The final companion now includes:

- three deterministic baseline cards for image-center pixel, bbox-center pixel,
  and bbox-center normalized-1000 checks;
- a new imagegen-created v2 `baseline_gate` AI slot;
- a registered baseline audit strip with four original/noMDL target-view render
  pairs for backpack, clock, bottle, and cup.

## Claim Boundary

The v2 AI-generated baseline-gate slot is exposition only. It is not a VLM
prediction, metric, benchmark row, or new experiment.

The evidence-bearing content remains Table S3, registered GRScenes target-view
render pairs, and deterministic scorer overlays drawn by
`paper/shared/figures/gen_supplement_task_media_atlases.py`.

## Layout Outcome

The first v2 PDF pass improved page 18 density but introduced a one-line spill
page on page 19. The final pass compressed the figure internally and shortened
the D.2 interpretation paragraph so page 18 closes cleanly and page 19 starts
the next GRScenes visual guide.

Measured outcomes:

- standalone figure: `1800x1040`, active245 `0.439638`, red fraction
  `0.000022`;
- page 18 active245 at 90dpi: `0.185937`, up from round-5 page-18 baseline
  `0.134572`;
- page 19 active245 at 90dpi: `0.162338`, no longer a spill-only page;
- supplement PDF: 45 pages, A4.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_vlm_coordinate_baseline_sanity_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_baseline_gate_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_baseline_sanity_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/02_vlm_protocol.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_baseline_sanity_companion_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'coordinate_baseline_sanity_companion'`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- Rendered PDF pages 18-20 with `pdftoppm` at 140dpi and 90dpi.
- PDF text scan for `registered baseline audit strip`,
  `AI-generated baseline-gate schematic used only for exposition`, and the
  no-new-prediction boundary.
- Local visual review of the standalone PNG and rendered page 18. Independent
  subagent review was not used because the available subagent tool requires an
  explicit user request for delegation.
