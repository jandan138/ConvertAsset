# 2026-06-07 ACL Main Conclusion Page 8 Boundary Tail Polish

## Summary

Round77 reviewed the current ACL main PDF after Round76. Page 8 had a small
but visible conclusion-tail issue: the final sentence rendered as `Portable
assets are useful only inside the gates` followed by the one-line tail `they
pass.` The wording was also slightly casual for the final ACL claim-boundary
close.

## Changes

- Rewrote the second Conclusion paragraph in
  `paper/venues/acl27/sections/conclusion.tex`.
- Replaced `embodied smoke tests` with the more formal `stack checks`.
- Recast the closing sentence as a claim-boundary statement: the gates define
  the evidence boundary, and outside them the asset is not a benchmark
  substitute.
- Rejected intermediate rewrites that removed `they pass.` but introduced
  `ground-`, `ar-`, or a one-word `satisfies.` line.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round77_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round77_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round77_after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round77_conclusion_page8_boundary_tail_polish_20260607.json`
- Final PDF hash:
  `72a978305a2752c273b38b3dd47b88be9ef959a5ac74ca6684670f39e2d0239c`

The accepted after scan removes the page-8 conclusion tail and introduces no
new body-text hyphenation. The full after scan reports only normal
bibliography-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Conclusion prose and linebreak behavior. It did not
change metric values, evidence pools, figures, citations, metadata, or
supported/forbidden claim scopes.
