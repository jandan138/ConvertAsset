# 2026-06-04 ACL Supplement Claim-Boundary Examples v2

## Scope

Round 33 ranked page 5 as the next practical sparse non-reference and
non-formula page after the first-page quickstart pass. The first attempted
adjustment only increased the LaTeX include height, but the figure remained
width-constrained in the PDF and the page hash did not change. This record
tracks the content-level v2 rebuild that replaced that ineffective adjustment.

## Changes

- Replaced the claim-boundary gate slot with
  `paper/shared/figures/ai_slots/fig_supplement_claim_boundary_examples_gate_v2_ai_slot.png`.
- Expanded the cross-gate render audit strip from a smaller set of tiles to a
  15-tile strip that includes render-scene, VLM coordinate, GRScenes VLM,
  material, navigation, route-still, and blocked-claim examples.
- Added the extended render-scene evidence, VLM coordinate protocol atlas, and
  GRScenes VLM visual guide as declared figure sources.
- Increased the standalone figure from `1800 x 2070` to `1800 x 2320` and
  replaced the sparse footer with a compact boundary render registry strip.
- Updated the supplement caption to name the AI-generated claim-boundary gate
  v2 schematic and keep the claim boundary explicit.

## Claim Boundary

The v2 gate is exposition only. It is not a new evidence source, a new
experiment, a metric, a VLM run, or a navigation run. The evidence-bearing
content is the registered render media reused by the deterministic
composition.

The selected generated image was copied into the repository and locally
postprocessed with contrast `1.12` and brightness `0.93` so the schematic
survives PDF-page scaling. That postprocessed slot is still treated only as a
replaceable visual guide.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_claim_boundary_examples_v2_20260604.json`

Standalone figure:
`paper/shared/figures/fig_supplement_claim_boundary_examples.png`

- Size before: `1800 x 2070`
- Size after: `1800 x 2320`
- Layout-guard active238 before: `0.264567096`
- Layout-guard active238 after: `0.325059626`
- Layout-guard active245 before: `0.289111111`
- Layout-guard active245 after: `0.358414990`
- Red-pixel fraction: `0.000203065`
- SHA-256:
  `81391a3baa6fef0466c995e8254f66f7d3f0b7a9e4e566bfa8ba807731a00626`

Claim-boundary gate v2 slot:
`paper/shared/figures/ai_slots/fig_supplement_claim_boundary_examples_gate_v2_ai_slot.png`

- Size: `1536 x 1024`
- Source generated image active238: `0.345472972`
- Postprocessed slot active238: `1.000000000`
- Postprocessed slot red-pixel fraction: `0.006651560`
- SHA-256:
  `a6ca7442b05d4b14c321b28b0d16035683b7e6ff069dfdfdaab777995ade6eea`

PDF review window:
`tmp/acl_supplement_page05_claim_boundary_examples_v2_final_20260604/page-04.png`,
`tmp/acl_supplement_page05_claim_boundary_examples_v2_final_20260604/page-05.png`,
and
`tmp/acl_supplement_page05_claim_boundary_examples_v2_final_20260604/page-06.png`

- Page 5 active245 at 90 dpi before round 33: `0.166830468`
- Page 5 active245 at 90 dpi after: `0.196386164`
- Improvement from round 33 page 5: `+0.029555696`
- Supplement PDF: 45 pages, A4, `48,828,146` bytes
- PDF SHA-256:
  `5d274a37ca1c6c9067fac20e3570ef03cbe99f0d96883b903bfbafe2c0cf3b99`

Result: PASS by local `render-visual-reviewer` checklist. The standalone image
has substantially more registered visual evidence, page 5 does not clip or
spill, and the caption keeps the AI slot inside the stated claim boundary.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_claim_boundary_examples.png`
- `paper/shared/figures/ai_slots/fig_supplement_claim_boundary_examples_gate_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_claim_boundary_examples.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_claim_boundary_examples_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'claim_boundary_examples'`
  - RED first for v2 caption/source/slot/size expectations; GREEN after
    implementation with `2 passed, 74 deselected`.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 4 -l 6 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page05_claim_boundary_examples_v2_final_20260604/page`
- `pdftoppm -r 90 -png -f 5 -l 5 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page05_claim_boundary_examples_v2_final_90dpi_20260604/page`
