# 2026-06-03 ACL Supplement GRScenes Table Companions

## Scope

The GRScenes failure-taxonomy, PASS-only pilot, and zoom-stress table pages
were among the sparsest remaining supplement pages. This iteration adds a
render companion strip after each table so reviewers can connect the table row
logic to visible original/noMDL target-view render pairs.

## What Changed

- Added
  `paper/shared/figures/ai_slots/fig_supplement_grscenes_table_reading_gate_ai_slot.png`.
- Added three AI slot manifests under
  `paper/shared/figures/ai_slot_manifests/`:
  `fig_supplement_grscenes_failure_taxonomy_table_companion.yaml`,
  `fig_supplement_grscenes_pass_only_table_companion.yaml`, and
  `fig_supplement_grscenes_zoom_stress_table_companion.yaml`.
- Added three companion figures:
  `fig_supplement_grscenes_failure_taxonomy_table_companion.png`,
  `fig_supplement_grscenes_pass_only_table_companion.png`, and
  `fig_supplement_grscenes_zoom_stress_table_companion.png`.
- Added `build_grscenes_table_companions()` to
  `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Registered all three figures in `paper/shared/figures/sources.yaml`.
- Updated `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`
  to place each companion immediately after the corresponding table.
- Added regression tests in `tests/test_paper_layout.py`.
- Recorded structured visual-review evidence in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_grscenes_table_companions_20260603.json`.

## AI Slot Policy

The AI-generated table-reading gate is a replaceable exposition slot. It shows
a generic row-inspection flow and does not carry experimental evidence. The
evidence-bearing content remains the registered GRScenes render pairs and the
existing VLM metric tables. Critical labels, target overlays, boundary text,
and captions are drawn by deterministic code or LaTeX.

## Visual Review

Standalone companion figures have active fractions around `0.32` and red
fallback fraction `0.0`. Rendered supplement pages 22, 23, and 24 now contain
the table, companion figure, caption, and boundary paragraph on the same page.
Their active fractions at 140 dpi are `0.090659`, `0.082423`, and `0.080753`
respectively; the earlier sparse-page audit had these pages at roughly
`0.0345`, `0.0237`, and `0.0217`.

No clipping, caption collision, local path leakage, author-name leakage, or old
red-material diagnostic caption tokens were observed. Residual risk: some
in-figure text is small at paper scale, but the surrounding captions keep the
claim boundary explicit.

## Verification

- RED tests failed before implementation because the section references and
  sources registry entries were absent.
- Targeted tests passed after implementation with `2 passed, 56 deselected`.
- `python paper/shared/figures/gen_supplement_task_media_atlases.py` passed.
- `make -C paper acl27-supplement` passed and produced a 44-page supplement.
- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `eda4cea3395cadb7aa9fb0189069a45ebfcd7780581492c0e2dae6bc403a3453`.
- `pdftotext` found the new Figure S14-S16 captions and did not find old
  red-material caption tokens, `fig_vlm_grounding_cases`, local path tokens, or
  author-identifying tokens.
