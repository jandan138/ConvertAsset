# 2026-06-06 ACL Main Claim Registry Boundary Polish

## Scope

Round 49 of the ACL main-paper visual/prose review polished the page-4 claim
registry paragraph. The source change is in
`paper/venues/acl27/sections/method.tex`.

## Issue

The page-4 Claim Registry paragraph ended with a reader-visible split:

- `broader robust- / ness claims`

The wording was correct, but the hyphenated break weakened the method narrative
where the paper explains how the evidence registry prevents local observations
from becoming broader claims.

## Change

The paragraph now says that the registry:

`keeps proxy metrics, selected videos, or single-scene results from standing in for task-wide evidence.`

This preserves the claim boundary while avoiding the fragile `robustness` line
break.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260606_round49_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260606_round49_after`
- Before PDF SHA-256:
  `c63a33f973d20a3e5fb60b0a114e8c7dfb875e36e4ee4d4e82c489b2ab257766`
- After PDF SHA-256:
  `581eadfeb25816d81e77c2a75835e24d17a64aefbef4115f7e76a786f929075f`
- After page-4 comparison:
  `tmp/acl_main_visual_iter_20260606_round49_after/focus_before_after_p4.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round49_claim_registry_boundary_polish_20260606.json`

The final page-4 render removes the targeted `broader robust- / ness claims`
split, keeps the Claim Registry paragraph in the same column, and preserves the
11-page layout.

## Verification

- `make -C paper acl27` exited 0.
- Log blocker scan for overfull boxes, undefined references, rerun warnings,
  multiply-defined labels, and `lineno` warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `"ok": true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `"ok": true` with a 168-word abstract.
