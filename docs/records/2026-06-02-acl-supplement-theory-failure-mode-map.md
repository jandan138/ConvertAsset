# 2026-06-02 ACL Supplement Theory Failure-Mode Map

## Scope

The supplement still had a theory section that was visually sparse compared
with the render-heavy material and navigation evidence sections. This pass adds
a full-width failure-mode interpretation map so the theory page connects back to
real render and task evidence.

## What Changed

- Added `paper/shared/figures/fig_supplement_theory_failure_mode_map.png`.
- Added `build_theory_failure_mode_map()` to
  `paper/shared/figures/gen_supplement_task_media_atlases.py`.
- Registered the figure in `paper/shared/figures/sources.yaml`.
- Inserted the figure into
  `paper/venues/acl27/sections/supplement/06_theory.tex`.
- Added regression and source-density checks in `tests/test_paper_layout.py`.
- Recorded structured evidence in
  `paper/shared/evidence/raw/acl27_visual_review/supplement_theory_failure_mode_map_20260602.json`.

## Imagegen Role

The generated bitmap below was used only as a layout reference:

```text
/root/.codex/generated_images/019e5ded-e82b-7c03-91bd-2a636674e25e/ig_0293332e291c3dc3016a1ef6425f888197b3b9c7118a2b20b1.png
```

The final paper figure is deterministic and uses registered real-render crops.
It is a reading guide, not new experimental evidence.

## Visual Review

The resulting page is no longer a pure text page. It shows the chain from
appearance perturbation to static measurements, VLM grounding boxes, navigation
signals, and bounded claim wording. The source figure active fraction is
0.570662, and the rendered PDF page active fraction is 0.173318.

Residual risk: some in-figure labels are small. This is acceptable for a
high-level interpretive map, but a final polish pass could simplify labels if
the supplement is later tightened.

## Verification

- Targeted failure-mode-map tests failed before implementation.
- Targeted tests passed after implementation and density iteration with
  `2 passed, 46 deselected`.
- `make -C paper acl27-supplement` passed and produced a 42-page A4 supplement.
- The rebuilt supplement SHA-256 is
  `7ebbf7872643da487ead9d4be91a111acb80b0ee4879acfc5bbacc8d0664a6a3`.
- `pdftotext` found the new Figure S23 caption and did not find the old
  red-material caption tokens, `fig_vlm_grounding_cases`, or private local
  paths.
