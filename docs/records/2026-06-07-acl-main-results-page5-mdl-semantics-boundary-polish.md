# 2026-06-07 ACL Main Results Page5 MDL Semantics Boundary Polish

## Summary

Round81 reviewed the current ACL main PDF after the Round80 Discussion boundary
polish. The page-5 Material Effects paragraph still ended with `not broad rates
or proof that MDL semantics stay intact`. The claim boundary was correct, but
`proof` and `stay intact` sounded conversational and less precise than the
surrounding ACL-style evidence-gate prose.

## Changes

- Rewrote the page-5 Results sentence in
  `paper/venues/acl27/sections/results.tex` to: `These rows are diagnostic
  only. They mark cues, not rates or full MDL semantics.`
- Kept the edit local to Results prose. No metrics, table values, figures,
  evidence pools, citations, metadata, or claim scopes were changed.
- Rejected three intermediate rewrites because they introduced visible page-5
  linebreak hyphenation: `identi-`/`seman-`, `mech-`/`cer-`, and
  `esti-`/`se-`.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round81_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round81_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round81_after/page-05.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round81_results_page5_mdl_semantics_boundary_polish_20260607.json`
- Final PDF hash:
  `42447583c60ca0cc95a780a93fec28ccbdc2465f1369955639ac72516864e9db`

The accepted after scan shows the revised page-5 sentence as two short rendered
lines without body-text linebreak hyphenation. The PDF remains 10 pages. The
strict hyphenation scan reports only reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Results prose on page 5. It did not change metrics,
table values, figures, evidence pools, citations, metadata, or
supported/forbidden claim scopes.
