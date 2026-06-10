# 2026-06-06 ACL Main Intro Boundary Linebreak Polish

## Scope

Round 47 of the ACL main-paper visual/prose review polished the page-2
claim-boundary sentence at the end of the introductory gate-flow paragraph in
`paper/venues/acl27/sections/intro.tex`.

## Issue

Round 46 removed a dense cluster of special-term breaks, but the accepted page
still ended the setup paragraph with `broad ro- / bustness claims.` That split
landed at the transition into the contribution list, where it read like a
visible stumble in the paper's first evidence-chain story.

## Change

The sentence was shortened from:

`Together, these gates support bounded claims, not broad robustness claims.`

to:

`Together, these gates bound the paper's claim.`

This keeps the claim-boundary function while avoiding the long `robustness`
word in a narrow ACL column. An intermediate variant, `not a blanket claim`,
removed the hyphenated split but left a one-word `claim.` line; that variant
was rejected.

The accepted version also lets contribution item 3 begin at the bottom of the
left column while Related Work still starts cleanly in the right column.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260606_round47_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260606_round47_after`
- Before PDF SHA-256:
  `b5f8ef0e47f76db3bef99945a76a853f1516372b7d69152acbbb724a4330d05a`
- After PDF SHA-256:
  `2220f78d266b1c2c9a406c56c3ee33dc5dcccc03e6b0c7980286b1b6f6d020d3`
- After page-2 comparison:
  `tmp/acl_main_visual_iter_20260606_round47_after/focus_before_after_p2.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round47_intro_boundary_linebreak_polish_20260606.json`

## Verification

- `make -C paper acl27` exited 0.
- Log blocker scan for overfull boxes, undefined references, rerun warnings,
  multiply-defined labels, and `lineno` warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `"ok": true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `"ok": true` with a 169-word abstract.
