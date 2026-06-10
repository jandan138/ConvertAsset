# 2026-06-04 ACL Supplement Theory Hypothesis-Boundary v6

## Scope

This pass revisits page 41 after the AI-slot composition rule was updated to
avoid generated-slot cropping and occlusion. The goal was to keep the theory
companion render-backed while replacing the v5 AI lens with a denser v6 slot
that is composed with contain scaling rather than center-crop/cover scaling.

## Changes

- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v6_ai_slot.png`.
- Rebuilt `fig_supplement_theory_hypothesis_boundary_companion.png` with the
  v6 hypothesis-boundary slot, deterministic checkpoint cards, and a denser
  bottom lens block.
- Changed the composer to place
  `THEORY_HYPOTHESIS_BOUNDARY_V6_AI_SLOT` with `cover=False` contain scaling.
- Added material, target-box, and selected-failure checkpoint cards beside the
  AI slot so the contain placement does not create a sparse wide blank lane.
- Updated the AI-slot manifest, source registry, supplement caption, and layout
  tests to require the v6 slot and contain placement.
- Kept the accepted PDF include at `0.40\textheight`: larger trials at
  `0.48\textheight` and `0.42\textheight` created a sparse H.5 orphan page and
  a 46-page supplement.

## Claim Boundary

The v6 AI-generated hypothesis-boundary lens is exposition only. It is not a
new experiment, causal proof, population rate, metric, VLM run, or navigation
run. Evidence-bearing content remains the registered material, grounding,
navigation, selected-failure, and cross-hypothesis render crops composed by
deterministic code.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_v6_20260604.json`

Generated v6 slot:
`paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v6_ai_slot.png`

- Size: `1536 x 1024`
- Layout-guard active238: `0.380282084`
- Layout-guard active245: `0.396162669`
- Red-pixel fraction: `0.002194722`
- SHA-256:
  `5850a7b3c9713a4e1bfb1b2e5d86d1fe1e8d9c38a84f10ed0837f3c3664b3a68`

Standalone figure:
`paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png`

- Size: `920 x 1540`
- Standalone layout-guard active238: `0.446494212` -> `0.466949464`
- Standalone layout-guard active245: `0.457092038` -> `0.476667137`
- Red-pixel fraction: `0.000206098`
- SHA-256:
  `9644aa37b23d44f64ba2745c11cd14bea59c98083977aabd45a5e4f77259565d`

Slot containment crop:
`tmp/acl_supplement_page41_theory_hypothesis_boundary_v6_20260604/hypothesis_boundary_lens_contain_crop.png`

- Layout-guard active245: `0.521918278`
- SHA-256:
  `e38eed926c7e89db0c4d7509938f4d009c0db07c1d9f6bc0a2cfe6441ebee640`
- Result: PASS. The AI slot is contained in a proportioned frame and is not
  center-cropped or overlapped by deterministic text.

PDF review window:
`tmp/acl_supplement_page41_theory_hypothesis_boundary_v6_20260604/page-40.png`
through
`tmp/acl_supplement_page41_theory_hypothesis_boundary_v6_20260604/page-42.png`

- Page 41 active245 at 90 dpi before round 37: `0.148192763`
- Page 41 active245 at 90 dpi after: `0.149026431`
- Improvement from round 37 page 41: `+0.000833668`
- Supplement PDF: 45 pages, A4, `50,608,328` bytes
- PDF SHA-256:
  `3f7c408ac47600a98655c0d878c45a5acf5f68ed24ec9ceb682887bc99f4d18b`

Result: PASS with limits by local `render-visual-reviewer` and
`research-figure-ai-slot-composer` checklists. The standalone companion and
bottom crop are denser and no longer crop the AI slot. Whole-page density
changes only slightly because page 41 remains a theory text page. Visual review
was local rather than an independent subagent review; the evidence JSON records
`independent_subagent_review: false`.

## Rejected Iterations

- `0.48\textheight`: rejected because H.5 spilled to a sparse page 42 and the
  supplement rebuilt to 46 pages.
- `0.42\textheight`: rejected because page 42 still held only the H.5 tail.
- Accepted compromise: v6 contain slot and denser standalone companion at the
  existing `0.40\textheight` PDF placement.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v6_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_theory_hypothesis_boundary_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/06_theory.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_theory_hypothesis_boundary_v6_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'theory_hypothesis_boundary'`
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf | rg '^Pages:'`
- `pdftoppm -r 144 -png -f 40 -l 42 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_boundary_v6_20260604/page`
- `pdftoppm -r 90 -png -f 41 -l 41 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page41_theory_hypothesis_boundary_v6_90dpi_20260604/page`
