# 2026-06-04 ACL Supplement Page-4 Claim-Boundary Companion v3

## Scope

Round 24 still ranked page 4 as a low-density non-formula page after the v2
claim-boundary companion. This pass keeps the same overview position but makes
the right-column figure taller and more render-heavy, with a fresh v3
AI-generated boundary-marker slot used only as an exposition aid.

## Changes

- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_page4_boundary_marker_v3_ai_slot.png`.
- Rebuilt `fig_supplement_page4_claim_boundary_companion.png` from `920 x 1040`
  to `920 x 1480`.
- Enlarged the registered exclusion-to-render ladder so the proxy pair,
  GRScenes target pairs, material limits, rollout stills, and case media read as
  a stronger visual evidence bridge.
- Moved the AI boundary marker into a larger full-width bottom block with
  deterministic labels for exposition-only use.
- Increased the overview include cap from `0.40\textheight` to
  `0.52\textheight`.
- Updated source registration, AI-slot manifest provenance, and layout tests to
  require the v3 slot, taller figure, and v3 caption wording.

## Claim Boundary

The v3 boundary-marker AI slot remains exposition only. It is not a render
result, metric, VLM output, navigation run, benchmark row, or new evidence
source. Evidence-bearing content remains the registered proxy, GRScenes,
material-effect, and InternNav render/media panels drawn into the deterministic
composition.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_page4_claim_boundary_companion_v3_20260604.json`

Standalone figure:
`paper/shared/figures/fig_supplement_page4_claim_boundary_companion.png`

- Size: `920 x 1040` -> `920 x 1480`
- Standalone layout-guard active238: `0.423647575` -> `0.468169066`
- Standalone layout-guard active245: `0.493166863`
- Standalone red-pixel fraction: `0.005073443`
- SHA-256:
  `ebfeeab3183c00d07945e32ab35964fde076f45fcb688a033322ad012ef71a07`

PDF review window:
`tmp/acl_supplement_page4_claim_boundary_v3_final_20260604/page-03.png`
through `tmp/acl_supplement_page4_claim_boundary_v3_final_20260604/page-05.png`

- Page 4 active245 at 90 dpi before round 24: `0.153922637`
- Page 4 active245 at 90 dpi after: `0.183705233`
- Improvement from round 24 page 4: `+0.029782596`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `5f29ff8c1e620ec059d2d9e79aa6e80c838c7ada482ac959027bbabcc2ba0bdb`

Result: PASS by local `render-visual-reviewer` checklist. Page 4 now uses more
of the right column without clipping, caption collision, or neighbor-page float
displacement. The visual review inspected the standalone figure, rendered page
4, pages 3 and 5 as neighbors, and page-4 crops for the figure, caption, and
bottom marker block.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_page4_claim_boundary_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_page4_boundary_marker_v3_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_page4_claim_boundary_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_page4_claim_boundary_companion_v3_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'page4_claim_boundary_companion'`
  - RED first for the old v2 slot, shorter figure, and old caption/include
    expectations; GREEN after the v3 rebuild.
- `python -m pytest -q tests/test_paper_layout.py`
  - `75 passed`
- `make -C paper acl27-supplement`
- `pdftoppm -r 144 -png -f 3 -l 5 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page4_claim_boundary_v3_final_20260604/page`
- `pdftoppm -r 90 -png -f 4 -l 4 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page4_claim_boundary_v3_final_90dpi_20260604/page`
