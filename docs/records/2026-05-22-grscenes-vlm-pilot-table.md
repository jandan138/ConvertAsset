# 2026-05-22 GRScenes VLM Pilot Table

## Scope

This record documents the first paper-table artifact for the ACL-oriented
GRScenes VLM grounding pilot. It does not introduce new model results. It
turns existing PASS-only Gemma4 and Qwen2.5-VL score summaries into a
machine-readable CSV and a LaTeX table.

## Current Goal Audit

The current repository evidence supports the following status:

- Full dependency closure is no longer truncated:
  `full_dependency_closure_report.json` records 85,705 reachable source USDs,
  89,484 resolved USD dependency records, and zero missing dependencies,
  outside-source references, or recursive output collisions.
- Full scratch materialization has run with `dry_run=false`:
  `full_nomdl_scratch_materialization_report.json` records 99 existing
  top-level scratch inputs and zero missing top-level scratch inputs.
- Full no-MDL conversion has run with a single `Processor` instance:
  `full_nomdl_multi_root_run_report.json` records
  `completed_full_grscenes_nomdl_multi_root_run`, `dry_run=false`, and 99 jobs.
  `full_nomdl_apply_verification_report.json` records `passed=true`, 99
  existing top-level outputs, and zero source `_noMDL` sidecar pollution.
- Paired render evidence exists for 21 centerline-clear original/converted
  pairs: 10 first-pass recommended pairs and 11 alternative centerline pairs.
  Blind visual QA leaves four PASS pairs for the current real-model pilot.
- VLM evidence exists as pilot artifacts only: Gemma4 PASS-only provides the
  strongest positive result, while Qwen2.5-VL shows response-format and
  coordinate-protocol sensitivity.

Therefore the next useful paper step is not to rerun the completed full route,
but to turn the current pilot results into table/figure artifacts while keeping
their claim boundary explicit.

## Added Artifacts

- `paper/shared/tables/gen_vlm_pilot_tables.py`
- `paper/shared/tables/grscenes_vlm_pass_only_pilot.csv`
- `paper/shared/tables/tab_grscenes_vlm_pass_only_pilot.tex`
- `paper/shared/sections/experiments.tex`
- `tests/test_paper_vlm_pilot_table.py`

The generated CSV preserves both raw image-space and normalized-1000 point
metrics so the table does not hide the Gemma4/Qwen coordinate ambiguity.
It records scorable categorical-answer rows separately from per-version point
row coverage, because Qwen structured text has 8/8 scorable answers but only
3/4 original point rows and 4/4 converted point rows.
The shared Experiments section now inputs the LaTeX table in a short
`Pilot GRScenes VLM Grounding` subsection with an explicit pilot-only caveat.

## Source Data

- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/gemma4_pass_only_score_summary.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/qwen25_pass_only_score_summary.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/probes/qwen25_pass_only_structured_score_summary.json`

## Claim Boundary

The table caption states that the values are pilot-only and not final benchmark
performance. The Qwen direct-JSON row is retained as a response-format
diagnostic with no scored answers or points. The Qwen structured-text row is
retained as protocol-sensitivity evidence: it recovers answer scoring, but one
original point is unscorable and the normalized-1000 pair agreement is not a
positive result because all comparable normalized points miss the boxes. It
should not be promoted to a final robustness claim until the coordinate prompt
and parser policy are frozen.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_paper_vlm_pilot_table.py` failed first with the expected missing `gen_vlm_pilot_tables.py`.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_paper_vlm_pilot_table.py` passed after implementation: 2 tests.
- `python paper/shared/tables/gen_vlm_pilot_tables.py` generated the CSV and
  LaTeX outputs.
- A read-only review flagged that `Parsed` could overstate Qwen structured
  point recovery. The table was revised to use `Answer rows`, add explicit
  point-row coverage to the CSV, and derive numeric pair-note metrics from the
  score summaries.
- `make -C paper cvpr26` passed and confirmed that the shared table input
  resolves in an available venue wrapper.
- `make -C paper check-template-acl27` still fails because the official ACL
  template files are not present locally:
  `venues/acl27/acl.sty` and `venues/acl27/acl_natbib.bst`.
- A second read-only review found no blocking issues and recommended a
  non-blocking staleness guard. `tests/test_paper_vlm_pilot_table.py` now
  checks that the checked-in CSV/TEX exactly match freshly generated outputs.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider` passed:
  226 tests.
