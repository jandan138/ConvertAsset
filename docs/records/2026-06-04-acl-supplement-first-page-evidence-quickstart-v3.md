# 2026-06-04 ACL Supplement First-Page Evidence Quickstart v3

## Scope

Round 21 still ranked page 1 among the lowest non-reference supplement pages.
The previous first-page quickstart helped orientation, but the reader-compass
slot was visually light and the opening card did not carry enough render
evidence for the user's "more rendered figures" direction.

## Changes

- Promoted the first-page reader-compass slot from v2 to v3:
  `paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v3_ai_slot.png`.
- Rebuilt `fig_supplement_first_page_evidence_quickstart.png` as a `920 x 1720`
  compact right-column index with four evidence lanes, a registered opening
  render ladder, and a bottom reader-compass card.
- Increased tile label-bar contrast and height so the page remains readable
  when scaled into the first page's right column.
- Updated the overview caption to name the registered opening render ladder and
  keep the v3 AI compass explicitly outside the evidence set.
- Updated the source manifest, AI-slot manifest, and layout tests to require
  the v3 slot and denser quickstart image.

## Claim Boundary

The v3 reader compass is exposition only. The evidence-bearing content remains
the registered render, GRScenes target-view, material-effect, and InternNav
media assets reused in the quickstart. This change does not add a metric, VLM
run, navigation run, or new evidence source.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_first_page_evidence_quickstart_v3_20260604.json`

PDF review window:
`tmp/acl_supplement_page1_quickstart_v3_final_20260604/page-01.png`
through `tmp/acl_supplement_page1_quickstart_v3_final_20260604/page-03.png`

- Standalone quickstart active238: `0.400189185` -> `0.480123862`
- Reader-compass AI slot active238: `0.206495180` -> `0.395829414`
- Page 1 active245 at 90 dpi: `0.146943536` -> `0.165193726`
- Improvement from round 21 page 1: `+0.018250190`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `eff9b56077e88f2057b9faa13bb9d1b5b589306d6b0b10dcd4d5486bee2f6813`

Result: PASS with note by local `render-visual-reviewer` checklist. Page 1 now
has a denser right-column visual index without clipping or caption collision.
The remaining large blank region is the ACL title-page structure above the
supplement overview, not an empty quickstart figure. Visual review was local
rather than an independent subagent review; the evidence JSON records
`independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v3_ai_slot.png`
- `paper/shared/figures/fig_supplement_first_page_evidence_quickstart.png`
- `paper/shared/figures/sources.yaml`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_first_page_evidence_quickstart.yaml`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_first_page_evidence_quickstart_v3_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'first_page_evidence_quickstart or overview_has_first_page'`
  - RED first for the old v2 slot and lower-density quickstart; GREEN after
    switching to v3 and rebuilding the figure.
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -r 144 -png -f 1 -l 3 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page1_quickstart_v3_final_20260604/page`
- `pdftoppm -r 90 -png -f 1 -l 1 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page1_quickstart_v3_final_90dpi_20260604/page`
