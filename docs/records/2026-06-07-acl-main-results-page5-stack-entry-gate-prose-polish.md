# 2026-06-07 ACL Main Results Page5 Stack-Entry Gate Prose Polish

## Summary

Round88 reviewed the current ACL main PDF after the Round87 Results
mechanism-question prose polish. The page-5 Embodied-Data Sanity paragraph used
both `sanity gate` and `sanity result`. The boundary was correct, but the
repetition was colloquial beside the surrounding claim-boundary prose.

## Changes

- Rewrote the opening boundary in
  `paper/venues/acl27/sections/results.tex` from `sanity gate` to
  `stack-entry gate`.
- Rewrote the later boundary from `sanity result` to `entry evidence`.
- Kept the edit local to Results prose. No metrics, evidence pools, figures,
  tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- The first accepted wording rendered `benchmark` as a visible `bench-` /
  `mark` split on page 5. The final wording keeps the stack-entry boundary but
  lowers the line-width pressure.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round88_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round88_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round88_after/page-05.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round88_results_page5_stack_entry_gate_prose_polish_20260607.json`
- Final PDF hash:
  `999b351fbae6a5ae5b74cc0037c70731f80ce016ec8ac8d7d70b945afa5d71e6`

The accepted after screenshot shows the revised page-5 Embodied-Data Sanity
paragraph without body-text linebreak hyphenation. The PDF remains 10 pages. The
enhanced after scan reports only the existing explicit `human-subject` wording
and normal reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.47s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Results prose on page 5. It did not change metrics,
evidence pools, figures, tables, citations, metadata, or supported/forbidden
claim scopes.
