# 2026-06-07 ACL Main Limitations Page8 Stack-Check Terminology Polish

## Summary

Round102 reviewed the current ACL main PDF after the Round101 Introduction gate
question polish. Page 8 Limitations still opened the material/navigation
boundary paragraph with `Material and embodied checks follow...`. The rest of
the main paper now describes the navigation evidence as stack-entry or stack
checks, so this phrase was a visible terminology mismatch.

## Changes

- Rewrote the page-8 Limitations sentence in
  `paper/venues/acl27/sections/limitations.tex` from
  `Material and embodied checks follow the same evidence boundary` to
  `Material and stack checks follow the same evidence boundary here`.
- Added `here` to keep the right-column line flow compact after replacing the
  longer `embodied` wording.
- Kept the 30 GRScenes samples, four material bins, cited KuJiaLe route,
  99 paired episodes, evidence limits, citations, figures, tables, metadata,
  and claim scopes unchanged.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round102_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round102_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round102_current/after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round102_limitations_page8_stack_check_terminology_polish_20260607.json`
- Baseline PDF hash:
  `dabb2125c36b50da3752bad2ff174de2f6b742faad1203034d313e50122b81eb`
- Final PDF hash:
  `a92998369245596827442843e82dc88355206b72f686754fe15fbb95dc04cd0d`

The accepted after screenshot shows the right-column Limitations paragraph as
`Material and stack checks follow the same evidence boundary here.` The page
stays at 10 pages overall and has no new visible overlap or hyphenation issue.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.89s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only one Limitations terminology sentence on page 8. It did
not change metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
