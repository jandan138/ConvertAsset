# 2026-06-04 ACL Supplement InternNav Selected6 Neutral Companion v2

## Scope

Round 34 ranked page 33 as the next practical sparse non-reference and
non-formula page after the page-5 claim-boundary pass. Page 33 showed the
selected6 neutral cases with the generic `\suppcasepair` macro: two horizontal
case panels and a large amount of empty page area.

## Changes

- Added
  `paper/shared/figures/fig_supplement_internnav_selected6_neutral_companion.png`
  as a page-shaped companion board for case `493_493` and case `484_484`.
- Reused registered selected6 still and route panels from
  `internnav_selected6_case05.png`, `internnav_selected6_case06.png`,
  `fig_internnav_rollout_selected6_supp.png`, and
  `fig_internnav_rollout_stills.png`.
- Added
  `paper/shared/figures/ai_slots/fig_supplement_internnav_selected6_neutral_gate_ai_slot.png`
  as a bounded review-gate schematic.
- Replaced the selected6 neutral `\suppcasepair` with a full-page figure and
  caption that preserves the navigation-metric claim boundary.
- Registered the new figure sources and AI-slot manifest.

## Claim Boundary

The selected6-neutral gate is exposition only. It is not a new evidence source,
a navigation metric, a benchmark run, a video-package approval, or a raw video
artifact. The evidence-bearing content is the registered selected still and
route media reused by the deterministic composition.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_internnav_selected6_neutral_companion_v2_20260604.json`

Standalone figure:
`paper/shared/figures/fig_supplement_internnav_selected6_neutral_companion.png`

- Size: `1500 x 1900`
- Layout-guard active238: `0.641001404`
- Layout-guard active245: `0.648092632`
- Red-pixel fraction: `0.001488070`
- SHA-256:
  `91f7f1c750752a1c31286ca6a87a54d05b283a6b73f9c603589a45047b7a39a9`

Selected6-neutral gate slot:
`paper/shared/figures/ai_slots/fig_supplement_internnav_selected6_neutral_gate_ai_slot.png`

- Size: `1536 x 1024`
- Layout-guard active238: `0.374973297`
- Layout-guard active245: `0.438938777`
- Red-pixel fraction: `0.000078837`
- SHA-256:
  `e1df556a853dba1d7ecd06434accf7b5a9ef2b4a7918f4f1e6a6c7f8cfb90c0a`

PDF review window:
`tmp/acl_supplement_page33_selected6_neutral_v2_final_20260604/page-32.png`,
`tmp/acl_supplement_page33_selected6_neutral_v2_final_20260604/page-33.png`,
and
`tmp/acl_supplement_page33_selected6_neutral_v2_final_20260604/page-34.png`

- Page 33 active245 at 90 dpi before round 34: `0.169179780`
- Page 33 active245 at 90 dpi after: `0.339810194`
- Improvement from round 34 page 33: `+0.170630414`
- Supplement PDF: 45 pages, A4, `49,969,445` bytes
- PDF SHA-256:
  `fa053ee8ac75d3c1dced99e3ee5377c6d1c4c962978fa648d4572ae6599545fc`

Result: PASS by local `render-visual-reviewer` checklist. Page 33 now contains
a dense registered navigation-evidence board, the caption fits, and the
neighboring selected-case pages remain intact.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_internnav_selected6_neutral_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_internnav_selected6_neutral_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_internnav_selected6_neutral_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_internnav_selected6_neutral_companion_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'internnav_selected6_neutral_companion or has_task_media_atlases'`
  - RED first for missing figure/source/slot expectations; GREEN after
    implementation with `2 passed, 75 deselected`.
- `python -m pytest -q tests/test_paper_layout.py`
  - `77 passed`.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
- `pdftoppm -r 144 -png -f 32 -l 34 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page33_selected6_neutral_v2_final_20260604/page`
- `pdftoppm -r 90 -png -f 33 -l 33 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page33_selected6_neutral_v2_final_90dpi_20260604/page`
