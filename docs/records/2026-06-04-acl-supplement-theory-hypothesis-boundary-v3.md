# 2026-06-04 ACL Supplement Theory Hypothesis-Boundary v3

## Scope

This pass revisits supplement page 41 after the round 16 density audit ranked
it as the lowest non-reference page. The goal was to make the in-column
hypothesis-boundary companion more render-heavy without increasing the
supplement beyond 45 pages.

## Changes

- Added the v3 render-backed AI slot:
  `paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v3_ai_slot.png`.
- Rebuilt `fig_supplement_theory_hypothesis_boundary_companion.png` with larger
  evidence tiles inside the four registered render lanes.
- Kept the accepted LaTeX allocation at `0.36\textheight` after confirming that
  longer captions can still create a sparse spill page.
- Updated the caption to name the render-backed boundary lens while keeping the
  claim boundary compact.
- Updated `sources.yaml`, the AI-slot manifest, and layout tests to require the
  v3 slot and denser standalone figure.

## Claim Boundary

The v3 AI-generated hypothesis-boundary lens is exposition only. It is not a
new experiment, causal proof, population rate, metric, VLM run, or navigation
run. The evidence-bearing content remains the registered material, grounding,
navigation, and selected-failure render crops composed by deterministic code.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_companion_v3_20260604.json`

Generated v3 slot:
`paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v3_ai_slot.png`

- Size: `1024x1536`
- Active238 fraction: `0.451678594`
- Active245 fraction: `0.541306814`
- Red-pixel fraction: `0.000466029`
- SHA-256:
  `63ee48a9034fc20fa6361841cd159b9883a574e6f0d85824bb74b3ee6f8fe8a8`

Standalone figure:
`paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png`

- Size: `920x1500`
- Active238 fraction: `0.492108696`
- Active245 fraction: `0.505718841`
- Red-pixel fraction: `0.000304348`
- SHA-256:
  `320082335d40a3301c10c031ea10c95d6bf28ea8ba2aa7bf4e330c620df48440`

PDF review window:
`tmp/acl_supplement_page41_theory_hypothesis_v3_final_20260604/page-40.png`
through `tmp/acl_supplement_page41_theory_hypothesis_v3_final_20260604/page-42.png`

- Page 41 active245 at 90 dpi: `0.140809576` -> `0.144267895`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `a0d942f26f01f2d8d4637a1e7ee9ba231b3ff0fc31d41d72dd0155c0d1895f1c`

Result: PASS by local `render-visual-reviewer` checklist. Page 41 keeps H.1-H.5
complete on one page, the companion is visibly denser, and page 42 returns to
the reproducibility manifest. Visual review was local rather than an independent
subagent review; the evidence JSON records `independent_subagent_review: false`.

## Regression Note

The first v3 PDF rebuild produced 46 pages. Root cause: the longer S39 caption
pushed the final H.5 sentence onto a mostly blank page, which shifted the
reproducibility manifest to the following page. The accepted fix kept the v3
figure and shortened the caption while preserving the render-backed lens and
claim-boundary statements.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v3_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_theory_hypothesis_boundary_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/06_theory.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_companion_v3_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'theory_has_hypothesis_boundary_companion or theory_hypothesis_boundary_companion_is_registered_and_dense'`
  - RED first for the missing v3 source registration and render-backed caption;
    GREEN after implementation with `2 passed, 72 deselected`.
- `latexmk -g -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex`
- `pdftoppm -f 40 -l 42 -r 144 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_v3_final_20260604/page`
- `pdftoppm -f 41 -l 41 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_v3_final_90dpi_20260604/page`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
