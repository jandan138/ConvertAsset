# 2026-06-07 ACL Main Discussion Page8 Stack-Entry Checks Polish

## Summary

Round103 reviewed the current ACL main PDF after the Round102 Limitations
stack-check terminology polish. Page 8 Discussion still grouped the gates as
`material-risk bins, and embodied stack checks`. The phrase was correct in
scope, but it lagged the now-consistent stack-entry wording used by the abstract,
Introduction, Results, Figure 4 caption, and Limitations.

## Changes

- Rewrote the page-8 Discussion phrase in
  `paper/venues/acl27/sections/discussion.tex` from `embodied stack checks` to
  `stack-entry checks`.
- Kept the sentence's purpose unchanged: proxy similarity, VLM answers, point
  grounding, coordinate checks, material-risk bins, and stack-entry checks stay
  separate.
- Kept metrics, evidence pools, figures, tables, citations, metadata, and claim
  scopes unchanged.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round103_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round103_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round103_current/after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round103_discussion_page8_stack_entry_checks_polish_20260607.json`
- Baseline PDF hash:
  `a92998369245596827442843e82dc88355206b72f686754fe15fbb95dc04cd0d`
- Final PDF hash:
  `24ffc5dc1cf846a1abd061d06544e9480297fc93fa6a596e044b0ea9c77b4b35`

The accepted after screenshot shows the Discussion opener reading
`material-risk bins, and stack-entry checks stay separate.` The sentence wraps
cleanly across lines 340-341 and the rest of page 8 remains visually stable.
The PDF remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.43s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only one Discussion phrase on page 8. It did not change
metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
