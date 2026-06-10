# 2026-06-03 ACL Supplement InternNav Upload-Gate Closure Card

## Scope

The official-scene submission closure status table was the sparsest non-reference
page in the ACL supplement after the previous render-heavy passes. This
iteration replaces the PDF-only use of that small table with a visual closure
card that keeps the same gate semantics while adding registered InternNav stills
and route panels.

## What Changed

- Added
  `paper/shared/figures/ai_slots/fig_supplement_internnav_upload_gate_ai_slot.png`.
- Added
  `paper/shared/figures/ai_slot_manifests/fig_supplement_internnav_upload_gate_closure_card.yaml`.
- Added
  `paper/shared/figures/fig_supplement_internnav_upload_gate_closure_card.png`.
- Added `build_internnav_upload_gate_closure_card()` to
  `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Registered the figure in `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex`
  to use the closure card instead of directly inputting the sparse table.
- Added regression tests in `tests/test_paper_layout.py`.
- Recorded structured evidence in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_internnav_upload_gate_closure_card_20260603.json`.

The generated table file
`paper/shared/tables/tab_official_scene_submission_closure_status.tex` remains
available as a source artifact, but the PDF supplement no longer gives it a
standalone sparse page.

## AI Slot Policy

The AI-generated slot is a small upload-approval schematic. It is used only for
exposition and is not navigation evidence. The evidence-bearing panels are the
registered navigation stills, route overlays, and official-scene closure
artifacts. Critical labels, gate names, claim-boundary text, and the final
caption are drawn by deterministic code or LaTeX.

The AI slot can be replaced later by a real upload-packet screenshot or a fully
deterministic manifest schematic.

## Visual Review

The standalone closure card has active fraction `0.252225` and red fallback
fraction `0.000411`. The rendered PDF page is page 38 of the 44-page supplement,
with active fraction `0.090967` at 170 dpi and `0.1185` at 120 dpi. The previous
sparse table page had active fraction `0.0065` at 120 dpi.

The rendered page has no clipping or caption collision. Residual risk: some
in-figure gate text is small at paper scale, but the main navigation stills and
caption remain readable.

## Verification

- Targeted tests failed before implementation because the section reference and
  sources registry entry were absent.
- Targeted tests passed after implementation with `2 passed, 54 deselected`.
- `python -m pytest -q tests/test_paper_layout.py` passed with `56 passed`.
- `make -C paper acl27-supplement` passed and produced a 44-page A4 supplement.
- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `4fb1c3c81bbfd31037f6bf2211a0a91fda4142583778ab570c604e07e35b7ed0`.
- `fig_supplement_internnav_upload_gate_closure_card.png` SHA-256:
  `14ac5e1eab69687196d583b13ba304179eeff9f845c465731af76332d8779cda`.
- `pdftotext` found the new Figure S25 caption and AI-generated upload-gate
  schematic disclosure.
- A risk-token scan found no old red-material caption tokens,
  `fig_vlm_grounding_cases`, author-identifying tokens, or local path tokens.
