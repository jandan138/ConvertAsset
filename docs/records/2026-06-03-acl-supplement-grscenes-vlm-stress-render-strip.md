# 2026-06-03 ACL Supplement GRScenes VLM Stress Render Strip

## Scope

The GRScenes VLM diagnostic table pages were still visually sparse after the
earlier supplement passes. This iteration adds a render-heavy strip before the
failure-taxonomy, PASS-only, and zoom-stress tables so reviewers can inspect
the target-view evidence before reading the low-density tabular pages.

## What Changed

- Added
  `paper/shared/figures/ai_slots/fig_supplement_grscenes_vlm_scoring_gate_ai_slot.png`.
- Added
  `paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_vlm_stress_render_strip.yaml`.
- Added
  `paper/shared/figures/fig_supplement_grscenes_vlm_stress_render_strip.png`.
- Added `build_grscenes_vlm_stress_render_strip()` to
  `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Registered the figure in `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`
  to include the strip between the GRScenes diagnostic atlas and the tables.
- Added regression tests in `tests/test_paper_layout.py`.
- Recorded structured evidence in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_vlm_stress_render_strip_20260603.json`.

## AI Slot Policy

The AI-generated slot is a small schematic of the prompt/point/score flow. It
is used only for exposition and is not experimental evidence. The large panels
are registered original-MDL and noMDL target-view renders. Critical labels,
target-box overlays, claim-boundary text, and the final caption are drawn by
deterministic code or LaTeX.

The AI slot can be replaced later by a deterministic protocol schematic
without changing the figure layout.

## Visual Review

The standalone figure has active fraction `0.383020` and red fallback fraction
`0.000011`. The rendered PDF page is page 21 of the 44-page supplement, with
active fraction `0.136203` at 170 dpi. The page has no clipping or caption
collision. Residual risk: small in-figure text remains less readable than the
main render pairs, so the caption keeps the claim boundary explicit.

## Verification

- Targeted tests failed before implementation because the section reference and
  sources registry entry were absent.
- Targeted tests passed after implementation with `2 passed, 52 deselected`.
- `python -m pytest -q tests/test_paper_layout.py` passed with `54 passed`.
- `make -C paper acl27-supplement` passed and produced a 44-page A4 supplement.
- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `6ec3dfbedb5959d0b35ac4c1e4d31d947ef89a4f265f483d83789d6932f10cd9`.
- `fig_supplement_grscenes_vlm_stress_render_strip.png` SHA-256:
  `87904c72bf90fa233e5dc2f642e3aa59ee2f6cba0011a7110d2e3d96b988a4f1`.
- `pdftotext` found the new Figure S13 caption and AI-generated scoring
  schematic disclosure.
- A risk-token scan found no old red-material caption tokens,
  `fig_vlm_grounding_cases`, author-identifying tokens, or local path tokens.
