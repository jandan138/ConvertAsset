# 2026-06-03 ACL Supplement Page-4 Claim-Boundary Companion v2

## Scope

This pass revisits the ACL supplement page-4 claim-boundary companion after the
round-9 density audit made page 4 the lowest non-reference page. The goal was to
replace the small right-column card with a denser registered-render companion
while keeping the AI-generated boundary marker outside the evidence chain.

## Changes

- Rebuilt `fig_supplement_page4_claim_boundary_companion.png` at `920x1040`.
- Expanded the proxy, GRScenes VLM, material-effect, and navigation cards to
  three registered render/media tiles each.
- Added a registered exclusion-to-render ladder using proxy scene crops,
  GRScenes zoom-019 pairs, material-limit crops, and InternNav route/case media.
- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_page4_boundary_marker_v2_ai_slot.png`.
- Increased the inline overview include cap from `0.24\textheight` to
  `0.40\textheight`.
- Updated `tests/test_paper_layout.py` to require the v2 slot, denser/taller
  figure, source registration, and caption ladder phrase.

## Claim Boundary

The v2 boundary-marker AI slot remains exposition only. It is not a render
result, metric, model prediction, VLM run, navigation run, benchmark row, or new
evidence source. Evidence-bearing content remains the registered proxy,
GRScenes, material-effect, and InternNav render/media panels drawn into the
deterministic composition.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_page4_claim_boundary_companion_v2_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_page4_claim_boundary_companion.png`

- Size: `920x1040`
- Layout-guard active fraction: `0.423647575`
- Red-pixel fraction: `0.005221572`
- SHA-256:
  `4f43752f53f385fba0ec3de577c896e2b889f59674341de0cd0eab33308ea517`

PDF review window:
`tmp/acl_supplement_page4_claim_boundary_v2_20260603/page-03.png` through
`tmp/acl_supplement_page4_claim_boundary_v2_20260603/page-06.png`

- Page 4 active245 at 90 dpi before: `0.126364430`
- Page 4 active245 at 90 dpi after: `0.153922637`
- Page 5 active245 at 90 dpi after: `0.166830468`
- Page 6 active245 at 90 dpi after: `0.216154547`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 4 now uses much
more of the right column for the overview companion while retaining a readable
caption and without creating a spill page. Page 5 remains a coherent full
claim-boundary examples page, and page 6 starts the render atlas normally.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_page4_claim_boundary_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_page4_boundary_marker_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_page4_claim_boundary_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_page4_claim_boundary_companion_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'page4_claim_boundary_companion or overview_has_page4'` (RED before implementation, GREEN after)
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py`
- `make -C paper acl27-supplement`
- `pdftoppm -f 3 -l 6 -r 140 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page4_claim_boundary_v2_20260603/page`
- `pdftoppm -f 3 -l 6 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page4_claim_boundary_v2_20260603/page90`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_page4_claim_boundary_companion_v2_20260603.json`
- `pdftotext -f 4 -l 4 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page4_claim_boundary_v2_final_20260603/page4.txt`
- `pdfinfo paper/venues/acl27/build/supplement.pdf` (`45` A4 pages)
- `git diff --check` on touched tracked files, plus a direct trailing-whitespace
  scan over the new doc and evidence JSON
