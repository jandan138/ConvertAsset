# 2026-06-04 ACL Supplement Theory Failure-Mode Map v2

## Scope

Round 38 still ranked page 40 among the lowest non-reference, non-formula
pages. The original failure-mode interpretation map was useful but landscape
shaped, so it left a large blank lower half on the PDF page. This pass makes
page 40 materially denser by adding a render-backed evidence wall while keeping
the map a claim-boundary reading aid rather than a new experiment.

## Changes

- Generated and registered
  `paper/shared/figures/ai_slots/fig_supplement_theory_failure_mode_gate_v2_ai_slot.png`.
- Added
  `paper/shared/figures/ai_slot_manifests/fig_supplement_theory_failure_mode_map.yaml`.
- Rebuilt `fig_supplement_theory_failure_mode_map.png` from `1800 x 1300` to
  `1800 x 1800`.
- Added a bottom failure-mode evidence wall containing:
  - the v2 AI gate slot placed with `cover=False` contain scaling;
  - material cue crops;
  - target-contract crop;
  - navigation route crops;
  - selected failure pair crops.
- Increased the page-40 include from `0.62\textheight` to
  `0.74\textheight`.
- Updated source registration and layout tests to require the new slot,
  manifest, raw failure render sources, portrait-ish aspect ratio, and higher
  standalone density.

## Claim Boundary

The new failure-mode gate slot is exposition only and replaceable. The
evidence-bearing content remains registered material, grounding, navigation,
and selected-failure render crops. The figure remains a reading aid over
existing evidence; it does not add a new metric, VLM run, navigation run,
converter ranking, population rate, or mechanism proof.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_theory_failure_mode_map_v2_20260604.json`

Generated v2 slot:
`paper/shared/figures/ai_slots/fig_supplement_theory_failure_mode_gate_v2_ai_slot.png`

- Size: `1672 x 941`
- Layout-guard active238: `0.364448642`
- Layout-guard active245: `0.382907321`
- Red-pixel fraction: `0.004133214`
- SHA-256:
  `b49d773da897b4263f1135c33e25d036ea18976fe40a7a3b6ddf8ca502fafd4a`

Standalone figure:
`paper/shared/figures/fig_supplement_theory_failure_mode_map.png`

- Size: `1800 x 1300` -> `1800 x 1800`
- Current layout-guard active238: `0.552476543`
- Current layout-guard active245: `0.562639815`
- Red-pixel fraction: `0.001266358`
- SHA-256:
  `0c47e0d9e21b477110a0bec8af61bfe9259bbfed02ef7cb26d4dea30a5053c07`

Evidence-wall crop:
`tmp/acl_supplement_page40_theory_failure_mode_v2_20260604/failure_mode_evidence_wall_crop.png`

- Size: `1724 x 538`
- Layout-guard active245: `0.513925426`
- SHA-256:
  `48c2283521dee0a83d10cbc3537fe82fca65b106b3e08be50a706f213980d282`
- Result: PASS. The AI slot is contained inside its frame and the adjacent
  render crops do not overlap labels or each other.

PDF review window:
`tmp/acl_supplement_page40_theory_failure_mode_v2_20260604/page-39.png`
through
`tmp/acl_supplement_page40_theory_failure_mode_v2_20260604/page-41.png`

- Page 40 active245 at 90 dpi before round 38: `0.183465586`
- Page 40 active245 at 90 dpi after: `0.266826007`
- Improvement from round 38 page 40: `+0.083360421`
- Supplement PDF: 45 pages, A4, `51,297,310` bytes
- PDF SHA-256:
  `5b95ce3e8b4ca48f5531a507ad0f1d5097f82e17c1a56fb550e19a54979a4e83`

Result: PASS by local `render-visual-reviewer` and
`research-figure-ai-slot-composer` checklists. Figure S38 and the caption fit
on page 40 without clipping, caption collision, or page-count spill. Page 39
remains the theory bridge and page 41 still starts the hypothesis text.

Visual review was local rather than an independent subagent review; the
evidence JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_theory_failure_mode_map.png`
- `paper/shared/figures/ai_slots/fig_supplement_theory_failure_mode_gate_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_theory_failure_mode_map.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/06_theory.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_theory_failure_mode_map_v2_20260604.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'theory_failure_mode_map'`
  - RED first for missing v2 slot/manifest/source rows and stale landscape
    dimensions; GREEN after the v2 evidence wall implementation.
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf | rg '^Pages:'`
- `pdftoppm -r 144 -png -f 39 -l 41 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page40_theory_failure_mode_v2_20260604/page`
- `pdftoppm -r 90 -png -f 40 -l 40 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_page40_theory_failure_mode_v2_90dpi_20260604/page`
