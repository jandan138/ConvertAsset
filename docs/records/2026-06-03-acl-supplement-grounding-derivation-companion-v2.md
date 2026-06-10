# 2026-06-03 ACL Supplement Grounding Derivation Companion V2

## Scope

Page 13 still read as a sparse formula page after the first derivation-companion
pass. This iteration rebuilds the grounding companion as a render-heavy bridge
between the point-in-box / normalized-coordinate equations and the registered
GRScenes target-view evidence.

## Changes

- Added a new selected AI slot,
  `paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_ai_slot.png`,
  for the abstract metric-contract gate.
- Rebuilt `fig_supplement_grounding_derivation_companion.png` at `1800 x 780`
  with four original/noMDL render-pair cards and a bottom formula-to-render
  audit strip.
- Updated
  `paper/shared/figures/ai_slot_manifests/fig_supplement_grounding_derivation_companion.yaml`
  to point at the new generated slot.
- Kept the ACL supplement include cap at `0.23\textheight`; larger `0.24` to
  `0.36` trials caused caption-only or figure-only spillover pages.
- Hardened `tests/test_paper_layout.py` so the grounding companion must include
  the audit-strip disclosure, the expanded registered render-pair source set,
  the AI slot manifest, and a dense `740-820` px output.

## Claim Boundary

The AI slot is exposition only. It is not a VLM output, point prediction,
metric, benchmark row, new experiment, or replacement for the registered target
views. The evidence-bearing material remains the original/noMDL GRScenes render
pairs and deterministic protocol overlays.

## Visual Review

Raw record:
`paper/shared/evidence/raw/acl27_visual_review/supplement_grounding_derivation_companion_v2_20260603.json`

Standalone figure:
`paper/shared/figures/fig_supplement_grounding_derivation_companion.png`

- Size: `1800 x 780`
- Layout-guard active fraction: `0.363649573`
- SHA-256:
  `4def91adc3b9556de33328e029a2ee8211fdb2e0978290478241636e42e2b2d0`

Page 13 raster:
`tmp/acl_supplement_grounding_derivation_v2_review_20260603/page-13.png`

Final PDF:
`paper/venues/acl27/build/supplement.pdf`

- SHA-256:
  `c1151dbfd3e84e4b778db983e1d0ff08cb15ba2393e91aee29ac6581476a5ce4`
- Page count: `45`

Result: PASS by local `render-visual-reviewer` checklist. The rendered page
keeps the C.3-C.6 derivations, grounding companion, and caption on page 13.
The companion is compact but visibly connects the formulas to registered render
pairs, and the caption does not collide with adjacent content.

At the same 90 dpi `active245` density used for the sparse-page audit, page 13
increased from `0.109492215` to `0.115241209`.

Visual review was local rather than an independent subagent review; the evidence
JSON records `independent_subagent_review: false`.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_grounding_derivation_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_grounding_derivation_companion.yaml`
- `paper/venues/acl27/sections/supplement/01_derivations.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_grounding_derivation_companion_v2_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_derivations_have_render_companions tests/test_paper_layout.py::test_supplement_derivation_companions_are_registered_and_dense`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py`
- `make -C paper acl27-supplement`
- `pdftoppm -f 13 -l 15 -r 140 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_grounding_derivation_v2_review_20260603/page`
- `pdftoppm -f 13 -l 15 -r 90 -png paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_grounding_derivation_v2_review_20260603/page90`
- `pdftotext -f 13 -l 13 paper/venues/acl27/build/supplement.pdf tmp/acl_supplement_grounding_derivation_v2_review_20260603/page-13.txt`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_grounding_derivation_companion_v2_20260603.json`
- `git diff --check -- docs/records/README.md paper/shared/figures/gen_supplement_task_media_atlases.py paper/shared/figures/ai_slot_manifests/fig_supplement_grounding_derivation_companion.yaml paper/venues/acl27/sections/supplement/01_derivations.tex tests/test_paper_layout.py`
