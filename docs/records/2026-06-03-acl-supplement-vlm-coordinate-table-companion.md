# 2026-06-03 ACL Supplement VLM Coordinate Table Companion

## Scope

The VLM coordinate ablation table page was one of the sparsest remaining
content pages after the previous render-heavy supplement passes. This iteration
adds a same-page companion strip after the coordinate ablation table so the
raw-image, target-box, and normalized-1000 coordinate distinction is visible
rather than only described in table text.

## What Changed

- Added
  `paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_contract_gate_ai_slot.png`.
- Added
  `paper/shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_table_companion.yaml`.
- Added
  `paper/shared/figures/fig_supplement_vlm_coordinate_table_companion.png`.
- Added `build_vlm_coordinate_table_companion()` to
  `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Registered the figure in `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/02_vlm_protocol.tex`
  to place the companion immediately after
  `tab_grscenes_vlm_coordinate_ablation`.
- Added regression tests in `tests/test_paper_layout.py`.
- Recorded structured visual-review evidence in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_vlm_coordinate_table_companion_20260603.json`.

## AI Slot Policy

The AI-generated coordinate-contract gate is a replaceable exposition slot. It
shows an abstract coordinate-frame transformation and does not carry
experimental evidence. The evidence-bearing content remains the registered
GRScenes original/noMDL render pairs and the existing coordinate tables.
Critical labels, target overlays, boundary text, and captions are drawn by
deterministic code or LaTeX.

## Visual Review

The standalone companion figure has active fraction `0.329163` and red fallback
fraction `0.0`. Rendered supplement page 17 now contains the coordinate table,
companion figure, caption, and boundary paragraph on the same page. Its active
fraction at 140 dpi is `0.088187`; the preceding density audit had page 17 at
`0.0243`.

No clipping, caption collision, local path leakage, author-name leakage, or old
red-material diagnostic caption tokens were observed. Residual risk: some
in-figure labels are small at paper scale, but the surrounding caption keeps the
claim boundary explicit.

## Verification

- RED tests failed before implementation because the section reference and
  sources registry entry were absent.
- Targeted tests passed after implementation with `2 passed, 58 deselected`.
- `python paper/shared/figures/gen_supplement_task_media_atlases.py` passed.
- `make -C paper acl27-supplement` passed and produced a 44-page supplement.
- `python -m pytest -q tests/test_paper_layout.py` passed with `60 passed`.
- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `35e9299bdc9abd1293950dbf63691d081957191cba1612750b85513fb2adeeeb`.
- `pdftotext` found the new Figure S11 caption and did not find old
  red-material caption tokens, `fig_vlm_grounding_cases`, local path tokens, or
  author-identifying tokens.
