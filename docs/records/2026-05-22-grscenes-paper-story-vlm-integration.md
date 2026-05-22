# 2026-05-22 GRScenes paper story VLM integration

## Summary

This record documents the manuscript pass that integrates the current GRScenes
VLM pilot evidence into the paper story without upgrading it to a final
benchmark claim.

## Reviewer inputs

Two read-only reviewers were used before editing:

- Paper-structure review found that the shared manuscript still referenced only
  the older four-pair PASS-only table and had not connected the 15-pair
  clean-pool or 14-pair zoom-stress results.
- Figure/evidence review found that the existing GRScenes qualitative figure is
  useful for material appearance but not for VLM grounding, and recommended a
  separate overlay figure with target boxes and predicted points.

An independent visual QA reviewer then inspected the new grounding figure. The
overall verdict was PASS, with one warning that the row containing model answer
`fauc` could look like truncated layout text. The figure generator now prints
model answers in quotes to make that failure mode explicit.

## Manuscript changes

- `paper/shared/sections/abstract.tex` now mentions the clean-pool and
  zoom-stress VLM pilots as diagnostics, not final benchmark performance.
- `paper/shared/sections/intro.tex` adds GRScenes VLM grounding as a fourth
  contribution and changes the guideline claim from "safe" to lower-risk,
  task-gated language.
- `paper/shared/sections/method.tex` adds the GRScenes VLM pilot protocol:
  read-only source tree, scratch no-MDL conversion, projected boxes, blind
  visual QA, separate clean and stress pools, Gemma4/Qwen2.5-VL prompts, and
  raw versus normalized-1000 coordinate scoring.
- `paper/shared/sections/experiments.tex` now inputs:
  - `paper/shared/tables/tab_grscenes_vlm_clean_pool_pass15.tex`
  - `paper/shared/tables/tab_grscenes_vlm_zoom_stress.tex`
  - `paper/shared/figures/fig_vlm_grounding_cases.pdf`
- `paper/shared/sections/discussion.tex` adds a stricter VLM grounding gate:
  feature similarity is not enough for language-conditioned grounding claims.
- `paper/shared/sections/conclusion.tex` adds the VLM pilot result and keeps
  final downstream robustness as future work.
- `paper/shared/sections/appendix.tex` now includes an illustrative failure
  taxonomy table generated from checked prediction and score artifacts.
- `paper/venues/acl27/sections/limitations.tex` now states that the VLM results
  are pilot diagnostics below the final clean-pair gate.

## Figure provenance

Added `paper/shared/figures/gen_vlm_grounding_cases.py`, which builds four
paired panels directly from checked-in prediction JSONL and score-summary
artifacts:

- clean preservation success: Gemma4, `21dde4a14ca93f539a47.retake_008`
- clean coordinate disagreement: Qwen2.5-VL,
  `c27086f557d316584264.view_001`
- zoom stress success: Gemma4, `47aa36277a54f6ca90cc.zoom_018`
- zoom stress disagreement: Qwen2.5-VL,
  `c8ee4b66274b05d242c2.zoom_017`

The generated outputs are:

- `paper/shared/figures/fig_vlm_grounding_cases.png`
- `paper/shared/figures/fig_vlm_grounding_cases.pdf`

The generator and sources are registered in
`paper/shared/figures/sources.yaml`; the PDF is also listed in
`paper/shared/evidence/results_manifest.yaml`.

## Claim boundary

The supported story is:

- clean-pool answer recognition is often preserved, especially for Gemma4;
- point grounding is more fragile than answer recognition;
- Qwen2.5-VL remains sensitive to response format and coordinate semantics;
- zoom views are material-shift stress evidence, not clean preservation
  evidence;
- the current VLM outputs should be cited as pilot/protocol diagnostics only.

The unsupported story is:

- final ACL VLM benchmark performance;
- broad VLM robustness under material conversion;
- navigation or manipulation downstream gains;
- general safety of no-MDL conversion across all USD assets.

## Failure taxonomy

Added `paper/shared/tables/gen_vlm_failure_taxonomy.py`, which generates:

- `paper/shared/tables/grscenes_vlm_failure_taxonomy.csv`
- `paper/shared/tables/tab_grscenes_vlm_failure_taxonomy.tex`

The selected rows cover normalized-point flips, raw-point flips, answer flips,
parse/truncated-answer failures, null converted answers, and one converted
raw-point counterexample. The table is illustrative appendix material; it is
not a final error distribution.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_vlm_grounding_case_figure.py`
  passed: 4 tests.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_paper_vlm_failure_taxonomy.py`
  passed: 3 tests.
- `python paper/shared/figures/gen_vlm_grounding_cases.py` regenerated the PNG
  and PDF outputs.
- `python paper/shared/tables/gen_vlm_failure_taxonomy.py` regenerated the CSV
  and LaTeX appendix table.
- Independent visual QA over `fig_vlm_grounding_cases.png` returned overall
  PASS with the minor quoted-answer text edit applied afterward.
- A reviewer-style diff pass found no blocking issues. The shared clean-pool
  table caption was made venue-neutral, and the figure generator now fails fast
  when a selected sample lacks a score record.
