# 2026-06-07 ACL Main Discussion Page 8 Stack Checks Terminology Polish

## Summary

Round78 reviewed the current ACL main PDF after the Round77 conclusion-tail
polish. Page 8 still used `embodied smoke tests` in the Discussion opener,
while the abstract, related work, introduction, and conclusion had converged on
`stack checks` / `embodied stack checks` as the claim-gate terminology.

## Changes

- Replaced `embodied smoke tests` with `embodied stack checks` in
  `paper/venues/acl27/sections/discussion.tex`.
- Kept the edit local to Discussion terminology. The surrounding claim remains
  unchanged: proxy similarity, VLM answers, point grounding, coordinate checks,
  material-risk bins, and stack checks remain separate evidence gates.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round78_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round78_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round78_after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round78_discussion_page8_stack_checks_terminology_polish_20260607.json`
- Final PDF hash:
  `358597f80ed843efc743dffc0df0d9b347881b0f6fd68308fc17a402b0ba53ce`

The accepted after scan shows the page-8 Discussion opener with `embodied stack
checks` and no new body-text hyphenation. The full after scan reports only
normal bibliography-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Discussion terminology and linebreak behavior. It did
not change metric values, evidence pools, figures, citations, metadata, or
supported/forbidden claim scopes.
