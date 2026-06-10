# 2026-06-07 ACL Main Ethical Considerations Page9 Real Deployment Boundary Polish

## Summary

Round82 reviewed the current ACL main PDF after the Round81 Results page-5
boundary polish. The page-9 Ethical Considerations paragraph still warned
authors not to `treat success in synthetic scenes as proof for real settings`.
The boundary was correct, but `proof for real settings` was less precise than
the paper's evidence-gate framing and sounded more conversational than the
surrounding ACL prose.

## Changes

- Rewrote the page-9 Ethical Considerations sentence in
  `paper/venues/acl27/sections/ethical-considerations.tex` to say authors
  should not treat synthetic-scene success as evidence for real deployment.
- Changed the following boundary sentence to `That distinction marks the
  evidence boundary.`
- Kept the edit local to ethics prose. No metrics, evidence pools, figures,
  tables, citations, metadata, or claim scopes were changed.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round82_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round82_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round82_after/page-09.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round82_ethical_page9_real_deployment_boundary_polish_20260607.json`
- Final PDF hash:
  `7dd9d878ad2df7ee288003005037944460a0f9dcb2699fb063f5b93d4d249154`

The accepted after scan shows the revised page-9 sentence as: `treat success
in synthetic scenes as evidence for real deployment. That distinction marks the
evidence boundary.` The PDF remains 10 pages. The strict hyphenation scan
reports only the existing explicit `human-subject` wording and normal
reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.23s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Ethical Considerations prose on page 9. It did not
change metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
