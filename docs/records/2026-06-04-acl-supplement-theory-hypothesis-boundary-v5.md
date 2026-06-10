# 2026-06-04 ACL Supplement Theory Hypothesis-Boundary v5

## Scope

Round 25 still ranked page 41 as the lowest non-reference, non-formula page.
This pass revisits the theory hypothesis-boundary companion after the accepted
v4 allocation. The goal was to add more visible render evidence and a fresh
AI-generated hypothesis-boundary slot without reintroducing the 46-page spill
observed by earlier p41 attempts.

## Changes

- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v5_ai_slot.png`.
- Rebuilt `fig_supplement_theory_hypothesis_boundary_companion.png` as a
  `920 x 1540` v5 companion.
- Added a compact cross-hypothesis render audit strip that reuses registered
  proxy, material, VLM target, navigation, and selected-failure render panels.
- Updated the companion to use the v5 AI slot in the bottom
  hypothesis-boundary lens block.
- Increased the accepted page-41 include from `0.38\textheight` to
  `0.40\textheight`.
- Shortened the H.5 final sentence enough to keep the supplement at 45 pages.
- Updated source registration, AI-slot manifest provenance, and layout tests to
  require the v5 slot and the compact v5 companion.

## Claim Boundary

The v5 AI-generated hypothesis-boundary lens is exposition only. It is not a
new experiment, causal proof, population rate, metric, VLM run, or navigation
run. The evidence-bearing content remains the registered material, grounding,
navigation, selected-failure, and cross-hypothesis render crops composed by
deterministic code.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_companion_v5_20260604.json`

Generated v5 slot:
`paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v5_ai_slot.png`

- Size: `1672 x 941`
- Layout-guard active238: `0.295665560`
- Layout-guard active245: `0.324537039`
- Red-pixel fraction: `0.000197032`
- SHA-256:
  `d66340daea1dcbda42ffd8530803fcdb1d948715d7e154ab2a9938bf7c8240a3`

Standalone figure:
`paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png`

- Size: `920 x 1500` -> `920 x 1540`
- Standalone layout-guard active238: `0.489833333` -> `0.446494212`
- Standalone layout-guard active245: `0.457092038`
- Red-pixel fraction: `0.000264681`
- SHA-256:
  `0426c594a5f6debaa6cc56c45da800e78a77f32e427162656448bb95c97868c2`

PDF review window:
`tmp/acl_supplement_page41_theory_hypothesis_v5_final_20260604/page-40.png`
through `tmp/acl_supplement_page41_theory_hypothesis_v5_final_20260604/page-42.png`

- Page 41 active245 at 90 dpi before round 25: `0.147281337`
- Page 41 active245 at 90 dpi after: `0.148213159`
- Improvement from round 25 page 41: `+0.000931822`
- Supplement PDF: 45 pages, A4
- PDF SHA-256:
  `e67b03f36772a59acda98a9f38f877dd640162a8754ee6c4253cfefbd034cd2d`

Result: PASS with limits by local `render-visual-reviewer` checklist. The page
is still text-heavy, but the accepted v5 layout adds a real render audit strip,
uses the fresh v5 boundary-lens slot, keeps H.4 and H.5 on page 41, and leaves
page 42 as the reproducibility media manifest.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Rejected Iterations

- `1740px` standalone with `0.46\textheight`: rejected because the supplement
  rebuilt to 46 pages.
- `1740px` standalone with `0.44\textheight` and `0.42\textheight`: rejected
  because the final H.5 sentence still spilled to an otherwise blank page.
- Accepted compromise: `1540px` standalone with `0.40\textheight`, plus compact
  H.5 wording.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v5_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_theory_hypothesis_boundary_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/06_theory.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_companion_v5_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'theory_has_hypothesis_boundary_companion or theory_hypothesis_boundary_companion_is_registered_and_dense'`
  - RED first for the missing v5 slot, include allocation, and taller v5
    companion; GREEN after implementation with `2 passed, 73 deselected`.
- `make -C paper acl27-supplement`
- `pdftoppm -r 144 -png -f 40 -l 42 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_v5_final_20260604/page`
- `pdftoppm -r 90 -png -f 41 -l 41 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_v5_final_90dpi_20260604/page`
- `pdfinfo paper/venues/acl27/build/supplement.pdf`
