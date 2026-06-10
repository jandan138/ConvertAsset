# 2026-06-07 ACL Main Method Page3 Stack-Entry Clause Polish

## Summary

Round105 reviewed the current ACL main PDF after the Round104 Related Work
stack-check polish. The first target was the page-5 `result.    The official`
spacing in Results 4.4, but three source-level candidates made the line worse
by introducing `bench-` / `mark`, `re-` / `sult`, or `cov-` / `ers` splits.
That target was restored and left for a separate, higher-risk pass.

The accepted change is on page 3 Method. Gate 4 still read
`Gate 4 is the embodied-stack entry check.` This retained the older
embodied-stack phrasing after the paper had converged on stack-entry/stack-check
terminology. The accepted rewrite removes the drift and keeps the narrow claim
boundary.

## Changes

- Rewrote the page-3 Gate 4 opener in
  `paper/venues/acl27/sections/method.tex`.
- Final accepted wording:
  `Gate 4 checks stack entry through the KuJiaLe route, which supplies matched original/noMDL scenes...`
- Added a local `\mbox{KuJiaLe}` guard in the source so the proper name does
  not split as `Ku-` / `JiaLe`.
- Rejected an intermediate `The official \mbox{KuJiaLe}` version because it
  split `official` as `of-` / `ficial`.
- Kept metrics, evidence pools, figures, tables, citations, metadata, and claim
  scopes unchanged.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round105_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round105_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round105_current/after/page-03.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round105_method_page3_stack_entry_clause_polish_20260607.json`
- Baseline PDF hash:
  `88fb7ee3e0addda66ba89ff140d1de57f9a0f7113736a5400a456c9c963de922`
- Final PDF hash:
  `db5955e8151e6009827c829ef0cd0968fb13ccc74546bc53cb9491fb070875b2`

The accepted after screenshot shows Gate 4 reading `checks stack entry through
the KuJiaLe route` without the old `embodied-stack` compound. The right column
wraps without the rejected proper-name and adjective hyphenations. The PDF
remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.32s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed one Method clause on page 3. It did not change measured
values, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes. The rejected page-5 trials were restored and
are not part of the accepted PDF.
