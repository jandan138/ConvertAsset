# 2026-06-04 ACL Supplement GRScenes PASS-Only Companion V3

## Scope

Round 26 still ranked page 23 among the lowest-density non-reference,
non-formula supplement pages. This pass revisits the GRScenes PASS-only table
companion after the v2 layout, with the goal of adding more visible render
evidence and a fresh PASS-only provenance-gate AI slot while keeping the ACL
supplement at 45 pages.

## Changes

- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_grscenes_pass_only_gate_v3_ai_slot.png`.
- Rebuilt `fig_supplement_grscenes_pass_only_table_companion.png` as a
  `1800 x 1200` v3 companion.
- Enlarged the PASS-only pilot render audit strip and kept the evidence-bearing
  bottle, two cup-view, and faucet render anchors visible.
- Muted the enlarged audit-strip tiles to avoid the faucet red material reading
  as an artificial warning color.
- Updated the PASS-only include allocation from `0.42\textheight` to
  `0.50\textheight`.
- Updated caption, source registration, AI-slot manifest provenance, and layout
  tests to require the v3 slot and denser figure.

## Claim Boundary

The v3 AI-generated PASS-only provenance-gate schematic is exposition only. It
is not a new VLM run, benchmark row, scoring result, or experimental evidence.
The evidence-bearing content remains the registered original/noMDL render pairs
and audit-strip crops composed by deterministic code.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_pass_only_companion_v3_20260604.json`

Generated v3 slot:
`paper/shared/figures/ai_slots/fig_supplement_grscenes_pass_only_gate_v3_ai_slot.png`

- Size: `1672 x 941`
- Layout-guard active238: `0.264221230`
- Layout-guard active245: `0.279986932`
- Red-pixel fraction: `0.000580925`
- SHA-256:
  `4ef70cb0157be9121c1f0a8c1a6038a8d945afad802e41f3d6554987f8a6cbdc`

Standalone figure:
`paper/shared/figures/fig_supplement_grscenes_pass_only_table_companion.png`

- Size: `1800 x 1040` -> `1800 x 1200`
- Standalone layout-guard active238: `0.434549679` -> `0.518971296`
- Standalone layout-guard active245: `0.447080662` -> `0.536434722`
- Red-pixel fraction: `0.013353704`
- SHA-256:
  `f4c28ffb79b1e2b361c91ecac845df9c2505ba29ffcc42ce0341a0ab039124e7`

PDF review window:
`tmp/acl_supplement_page23_grscenes_pass_only_v3_final_20260604/page-22.png`
through `tmp/acl_supplement_page23_grscenes_pass_only_v3_final_20260604/page-24.png`

- Page 23 active245 at 90 dpi before round 26: `0.156093488`
- Page 23 active245 at 90 dpi after: `0.199153585`
- Improvement from round 26 page 23: `+0.043060097`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `594996ef11c1afeac7fbbbfbff245754d73e4939ec8360334ec8011e5746c389`

Result: PASS by local `render-visual-reviewer` checklist. The p23 companion
now reads as the page's visual body, the bottom render audit strip is
inspectable at page scale, and pages 22 and 24 remain intact.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grscenes_pass_only_table_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_grscenes_pass_only_gate_v3_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_pass_only_table_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_pass_only_companion_v3_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'grscenes_tables_have_render_companions or grscenes_table_companions_are_registered_and_dense'`
  - RED first for the missing v3 slot, include allocation, and taller v3
    companion; GREEN after implementation with `2 passed, 73 deselected`.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 22 -l 24 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page23_grscenes_pass_only_v3_final_20260604/page`
- `pdftoppm -r 90 -png -f 23 -l 23 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page23_grscenes_pass_only_v3_final_90dpi_20260604/page`
