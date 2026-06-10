# 2026-06-07 ACL Main Results Stack-Entry Heading Polish

## Summary

Round99 reviewed the current ACL main PDF after the Round98 evidence-registry
terminology polish. Page 5 still titled Section 4.4 as
`Embodied-Data Sanity and Official Scene Stability` even though the surrounding
main-paper prose, Table 1, and companion image now scope the same evidence as a
stack-entry check. The heading was therefore the next visible terminology drift.

## Changes

- Rewrote the visible Section 4.4 heading in
  `paper/venues/acl27/sections/results.tex` to
  `Stack-Entry Evidence and Official Scene Stability`.
- Kept `\label{sec:embodied_sanity}` unchanged because it is an internal anchor
  and not reader-facing.
- Updated
  `tests/test_paper_layout.py::test_acl_material_figure_enters_float_queue_before_claim_boundary_table`
  to use the stable section label as its float-order anchor instead of the old
  visible heading string.
- Kept all metrics, evidence pools, tables, figures, citations, metadata, and
  claim scopes unchanged.

The pre-existing page-5 text extraction gap in `result.    The official` was
left out of scope. Earlier experiments against that sentence produced worse
body-text line breaks, so this round only resolves the heading mismatch.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round99_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round99_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round99_current/after/page-05.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round99_results_stack_entry_heading_polish_20260607.json`
- Baseline PDF hash:
  `0a167be408b2b8a2c37284372ea07d66ed954623c000b60bcb0eb016e75bfdae`
- Final PDF hash:
  `7b2e044625a75cebfaa10ace6f3bdb8959d16f56f6ba61989065e69a6ddca645`

The accepted after screenshot shows Section 4.4 as `Stack-Entry Evidence and
Official Scene Stability`, split cleanly across two heading lines. The figure,
caption, tables, and right-column body text remain in the same local layout. The
PDF remains 10 pages.

## Verification

- `python -m pytest -q tests/test_paper_layout.py::test_acl_material_figure_enters_float_queue_before_claim_boundary_table`
  passed with `1 passed in 0.39s` after the test anchor update.
- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.69s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only one reader-facing Results heading and one layout-test
anchor. It did not change metrics, evidence pools, figures, tables, citations,
metadata, or supported/forbidden claim scopes.
