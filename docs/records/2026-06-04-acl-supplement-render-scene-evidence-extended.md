# 2026-06-04 ACL Supplement Render-Scene Evidence Extended

## Scope

Round 31 ranked page 8 among the next sparse render-evidence pages. The page
previously reused the shared main-paper `fig_render_scene_evidence_wide.png`,
which is intentionally wide and compact for the main results section. This
pass adds a supplement-only extended version so the supplement page carries
more real render evidence without changing the shared main-paper figure.

## Changes

- Added `paper/shared/figures/fig_supplement_render_scene_evidence_extended.png`.
- Composed four tracked render-pair rows: proxy object `#0011`, proxy object
  `#0023`, GRScenes scene view 1, and GRScenes scene view 2.
- Updated the supplement render-atlas page to use the extended figure at
  `0.88\textheight`.
- Registered exact render sources and added layout tests requiring the
  supplement-only figure.

## Claim Boundary

No generated image is used in this pass. The figure is qualitative
preservation evidence under selected cameras. It does not claim full semantic
equivalence, and it does not replace metric tables, VLM evidence, or task
evidence.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_render_scene_evidence_extended_20260604.json`

Standalone figure:
`paper/shared/figures/fig_supplement_render_scene_evidence_extended.png`

- Size: `1800 x 1592`
- Layout-guard active238: `0.627097292`
- Layout-guard active245: `0.670726898`
- Red-pixel fraction: `0.000000349`
- SHA-256:
  `05ecaf28fb181a71c31967e950bb4b3c1b4fd0e07da080fb942dc1f78012208b`

Previous shared wide figure:
`paper/shared/figures/fig_render_scene_evidence_wide.png`

- Size: `1800 x 884`
- Layout-guard active238: `0.661898567`
- Layout-guard active245: `0.769854827`
- SHA-256:
  `c3916d57c87efd00edda9052f8a643881cd0e400959de7af669d4f45e6db5758`

PDF review window:
`tmp/acl_supplement_page08_render_scene_evidence_extended_final_20260604/page-07.png`
through
`tmp/acl_supplement_page08_render_scene_evidence_extended_final_20260604/page-09.png`

- Page 8 active245 at 90 dpi before round 31: `0.168724705`
- Page 8 active245 at 90 dpi after: `0.262400173`
- Improvement from round 31 page 8: `+0.093675468`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `b6f5d9d622b3f0d28e70cecffe9e3cb4cd857cbb3bb18bde5e1424fb4bdd2b23`

Result: PASS by local `render-visual-reviewer` checklist. The extended figure
and caption remain readable on page 8, and pages 7 and 9 remain intact.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_render_scene_evidence_extended.png`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/01a_render_atlas.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_render_scene_evidence_extended_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'has_render_evidence_atlas or render_scene_evidence_extended'`
  - RED first for the missing supplement-only figure and source registration;
    GREEN after implementation with `2 passed, 74 deselected`.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 7 -l 9 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page08_render_scene_evidence_extended_final_20260604/page`
- `pdftoppm -r 90 -png -f 8 -l 8 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page08_render_scene_evidence_extended_final_90dpi_20260604/page`
