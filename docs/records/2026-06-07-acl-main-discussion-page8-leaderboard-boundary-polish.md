# 2026-06-07 ACL Main Discussion Page8 Leaderboard Boundary Polish

## Summary

Round80 reviewed the current ACL main PDF after the Round79 Results/Table-6
terminology polish. The page-8 Discussion opener still described the protocol as
`not proof that a tool is safe, faster, or better than NVIDIA's route`. The
meaning was correct, but the phrasing was conversational and still sounded like
a leaderboard comparison. The ACL claim-boundary story is stronger when this is
stated as an explicit non-claim.

## Changes

- Rewrote the page-8 Discussion opener in
  `paper/venues/acl27/sections/discussion.tex` to say noMDL is `not a safety,
  speed, or quality claim about ConvertAsset versus NVIDIA's route`.
- Changed `After rendering, scenes are data` to `Rendered scenes are data` so
  the transition stays compact in the rendered column.
- Kept the edit local to Discussion prose. No metric values, evidence pools,
  tables, figures, citations, metadata, or claim scopes were changed.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round80_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round80_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round80_after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round80_discussion_page8_leaderboard_boundary_polish_20260607.json`
- Final PDF hash:
  `53e91d3d41556c401a46b0eeb01f4d481302453b19fa1d23ea3e18c52c3dd9d3`

The accepted after scan shows the revised page-8 paragraph as:
`not a safety, speed, or quality claim about ConvertAsset versus NVIDIA's
route. Rendered scenes are data; the route gives context but does not rank
tools.` The PDF remains 10 pages, and the full after scan found no alphabetic
line-end hyphenation in the rendered text extraction.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Discussion prose on page 8. It did not change metric
values, evidence pools, tables, figures, citations, metadata, or
supported/forbidden claim scopes.
