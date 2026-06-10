# 2026-06-03 ACL Supplement First-Page Evidence Quickstart v2

## Scope

This pass revisits the ACL supplement opening page after the full supplement
density audit still listed page 1 among the lowest non-reference pages. The goal
was to use more registered render material in the first viewport without turning
the AI-generated reading compass into evidence.

## Changes

- Rebuilt `fig_supplement_first_page_evidence_quickstart.png` at `920x1580`
  with four-tile proxy, GRScenes VLM, material-effect, and navigation lanes.
- Added a deterministic registered opening render ladder that uses paired proxy,
  GRScenes target, material-limit, and InternNav media anchors.
- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v2_ai_slot.png`.
- Updated the first-page include cap from `0.58\textheight` to
  `0.72\textheight` and extended the caption with the render-ladder boundary.
- Updated `tests/test_paper_layout.py` to require the v2 slot, the taller dense
  figure, the opening render ladder phrase, and the new include cap.

## Claim Boundary

The v2 reading-compass AI slot remains exposition only. It is not a render
result, metric, model prediction, VLM run, navigation run, benchmark row, or new
evidence source. Evidence-bearing panels remain deterministic crops or pair
tiles from registered proxy, GRScenes, material-effect, and InternNav media.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_first_page_evidence_quickstart_v2_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_first_page_evidence_quickstart.png`

- Size: `920x1580`
- Layout-guard active fraction: `0.400189185`
- Red-pixel fraction: `0.000358420`
- SHA-256:
  `854e9c84c0722f5bc9dae4167c6ee9db4686961d20cf7dc5a4951639038555e8`

PDF review window:
`tmp/acl_supplement_page1_quickstart_v2_final_20260603/page-01.png` through
`tmp/acl_supplement_page1_quickstart_v2_final_20260603/page-03.png`

- Page 1 active245 at 90 dpi before: `0.121222203`
- Page 1 active245 at 90 dpi after: `0.146943536`
- Page 2 active245 at 90 dpi after: `0.204015373`
- Page 3 active245 at 90 dpi after: `0.156829002`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 1 now fills the
right-column opening with the taller quickstart card, render ladder, and
caption without visible overlap or spill. Pages 2 and 3 remain readable after
the taller first-page figure.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_first_page_evidence_quickstart.png`
- `paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_first_page_evidence_quickstart.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_first_page_evidence_quickstart_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'first_page_evidence_quickstart or overview_has_first_page'` (RED before implementation, GREEN after)
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py`
- `make -C paper acl27-supplement`
- `pdftoppm -f 1 -l 3 -r 140 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page1_quickstart_v2_final_20260603/page`
- `pdftoppm -f 1 -l 3 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page1_quickstart_v2_final_20260603/page90`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_first_page_evidence_quickstart_v2_20260603.json`
- `pdftotext -f 1 -l 1 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page1_quickstart_v2_final_20260603/page1.txt`
- `pdfinfo paper/venues/acl27/build/supplement.pdf` (`45` A4 pages)
- `git diff --check` on touched tracked files, plus a direct trailing-whitespace
  scan over the new doc and evidence JSON
