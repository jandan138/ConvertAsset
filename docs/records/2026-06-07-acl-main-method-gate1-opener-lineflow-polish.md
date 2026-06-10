# 2026-06-07 ACL Main Method Gate1 Opener Lineflow Polish

## Summary

Round107 reviewed the current ACL main PDF after the Round106 contribution
claim-boundary polish. Page 3 Method still had a visible sentence-break gap in
the Evidence Gates opener: `evidence gates.    Gate 1 screens...`. A direct
colon rewrite removed that gap but pushed `evidence` to the column edge and
split it as `evi-` / `dence`, so that candidate was rejected.

The accepted rewrite shortens the opener and makes the Gate 1 transition read
as normal ACL prose while preserving the same evidence boundary.

## Changes

- Rewrote the page-3 Evidence Gates opener in
  `paper/venues/acl27/sections/method.tex`.
- Final accepted wording:
  `The four evidence gates start with Gate 1, which screens four assets from Isaac Sim...`
- Rejected the intermediate `evidence gates: Gate 1...` candidate because it
  introduced `evi-` / `dence` hyphenation.
- Kept metrics, evidence pools, figures, tables, citations, metadata, and claim
  scopes unchanged.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round107_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round107_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round107_current/after/page-03.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round107_method_gate1_opener_lineflow_polish_20260607.json`
- Baseline PDF hash:
  `5e598fb9feb14a5bb8cf5231cb2a96a748a6fe24e8629461110ebbe972340707`
- Final PDF hash:
  `162bd09a9a1ce850aa53e428a2f95c502fdca331267664b252093607734ba34d`

The accepted after screenshot shows the Evidence Gates opener reading over
lines 177-180 without the old wide gap and without the rejected `evi-` /
`dence` split. The PDF remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.38s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed one Method opener on page 3. It did not change measured
values, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
