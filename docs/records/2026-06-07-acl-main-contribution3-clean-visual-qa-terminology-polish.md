# 2026-06-07 ACL Main Contribution3 Clean Visual-QA Terminology Polish

## Summary

Round94 reviewed the current ACL main PDF after the Round93 Contribution 4
boundary-verb polish. Contribution 3 still described the clean branch as a
`clean preservation pilot`. That phrase was stronger than the evidence
boundary: the paper elsewhere describes the branch as a clean visual-QA pilot
below the final clean-pool gate.

## Changes

- Rewrote Contribution 3 in
  `paper/venues/acl27/sections/intro.tex` to use `clean visual-QA pilot`.
- Shortened the second half of the contribution to
  `backend differences in answer, point, and coordinate checks` after the
  direct terminology replacement introduced linebreak hyphenation.
- Kept the edit local to Contribution 3 prose. No metrics, evidence pools,
  figures, tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- The direct `clean visual-QA pilot` replacement introduced visible page-2
  contribution-column hyphenation: `show-` / `ing`, `ground-` / `ing`, and
  `sepa-` / `rate`.
- A shorter follow-up using `coordinate behavior can diverge` still rendered
  `behavior` as `behav-` / `ior`.
- The accepted rewrite keeps the clean visual-QA terminology and avoids the
  contribution-column split regressions.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round94_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round94_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round94_after/page-02.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round94_contribution3_clean_visual_qa_terminology_polish_20260607.json`
- Final PDF hash:
  `9649ba974d704abeacb3a7d50430f4910813b439824fe0e4190fbb426c2c1448`

The accepted after screenshot shows Contribution 3 without new body-text
linebreak hyphenation. The PDF remains 10 pages. The enhanced after scan
reports only the existing explicit `human-subject` wording and normal
reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.51s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Contribution 3 prose on page 2. It did not change
metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
