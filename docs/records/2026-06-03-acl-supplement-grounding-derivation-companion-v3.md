# 2026-06-03 ACL Supplement Grounding Derivation Companion v3

## Scope

This pass revisits the ACL supplement grounding-derivation spread after the
page-density audit still identified page 13 as visually thin. The goal was to
add more registered render content without converting the companion into a
figure-only spill page or weakening the AI-slot claim boundary.

## Changes

- Rebuilt `fig_supplement_grounding_derivation_companion.png` at `1800x1040`
  with a second registered coordinate-conversion render wall using zoom-019
  backpack and clock render pairs.
- Added the v2 metric-contract AI slot,
  `paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_v2_ai_slot.png`,
  and wired the grounding manifest and figure source manifest to it.
- Moved the grounding companion before the Point-in-Box Grounding subsection so
  the larger render companion lands on page 13 with the equations it introduces.
- Removed the hard page break after the grounding companion and shrank the
  downstream metric-boundary bridge include to `0.86\textwidth` so the section
  returns to 45 pages without a caption-only spill page.
- Updated `tests/test_paper_layout.py` to require the new render wall, v2 AI
  slot source, zoom-019 registered render sources, and the new companion
  placement.

## Claim Boundary

The v2 AI-generated metric-contract slot remains exposition only. It is not a
metric, VLM output, model prediction, benchmark row, or new experiment. The
evidence-bearing content is still the registered original/noMDL GRScenes render
pairs and deterministic protocol overlays drawn by
`paper/shared/figures/gen_supplement_task_media_atlases.py`.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grounding_derivation_companion_v3_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_grounding_derivation_companion.png`

- Size: `1800x1040`
- Layout-guard active fraction: `0.421898504`
- Red-pixel fraction: `0.000013889`
- SHA-256:
  `96d097cd26ca01bbd16ec9ba7ba6f3ad2179464cfcbb810c35a28708cd65cbab`

PDF review window:
`tmp/acl_supplement_page13_grounding_derivation_v2/page-12.png` through
`tmp/acl_supplement_page13_grounding_derivation_v2/page-16.png`

- Page 13 active245 at 90 dpi: `0.134736802`
- Page 15 active245 at 90 dpi: `0.218798320`
- Supplement PDF: 45 pages, A4

Result: PASS by local `render-visual-reviewer` checklist. Page 13 now carries
the larger grounding companion in context, page 15 closes the derivations
section without a caption-only tail, and page 16 starts the next supplement
section. Page 14 remains a low-density formula-only page, but it is continuous
derivation text rather than a stranded figure or spill page.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grounding_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grounding_derivation_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grounding_derivation_companion_v3_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'derivation_companions or derivations_have_render_companions'`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py` (`74 passed`)
- `make -C paper acl27-supplement`
- `pdftoppm -f 12 -l 16 -r 140 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page13_grounding_derivation_v2/page`
- `pdftoppm -f 12 -l 16 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page13_grounding_derivation_v2/page90`
- `pdftotext -f 13 -l 13 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_grounding_derivation_v3_final_20260603/page13.txt`
- `pdfinfo paper/venues/acl27/build/supplement.pdf` (`45` A4 pages)
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_grounding_derivation_companion_v3_20260603.json`
- `git diff --check` on touched tracked files, plus a direct trailing-whitespace
  scan over the new doc and evidence JSON
