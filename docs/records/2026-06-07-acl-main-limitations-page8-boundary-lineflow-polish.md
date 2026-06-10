# 2026-06-07 ACL Main Limitations Page8 Boundary Lineflow Polish

## Summary

Round96 reviewed the current ACL main PDF after the Round95 contribution
gate-scope consistency polish. On page 8, the Limitations right column rendered
`bounded claims. The audit covers 30` with visibly stretched spacing in the
narrow column. The wording was correct, but the lineflow looked less like a
polished ACL page.

## Changes

- Rewrote the opening sentence of the second Limitations paragraph in
  `paper/venues/acl27/sections/limitations.tex`.
- Changed `Material and embodied checks also have bounded claims` to
  `Material and embodied checks follow the same evidence boundary`.
- Kept the following audit scope unchanged: 30 GRScenes samples, four effect
  bins, clearcoat and texture fixtures, selected-case support, the three
  KuJiaLe `val_unseen` scenes, and 99 paired episodes.

## Rejected Iteration

- `Material and embodied evidence follows the same boundary` removed the
  original `bounded claims. The audit covers 30` stretch but still left a
  slightly loose `the same boundary. The audit covers 30` line.
- The accepted version uses `same evidence boundary`, which gives the right
  column a more natural three-line flow.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round96_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round96_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round96_current/after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round96_limitations_page8_boundary_lineflow_polish_20260607.json`
- Final PDF hash:
  `cdb1538d253f11edb038b22e8308c902e51538cf951f8421f667ef3532986940`

The accepted after screenshot shows the Limitations right-column opening without
the baseline stretched spacing. The PDF remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.42s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Limitations prose on page 8. It did not change metrics,
evidence pools, figures, tables, citations, metadata, or supported/forbidden
claim scopes.
