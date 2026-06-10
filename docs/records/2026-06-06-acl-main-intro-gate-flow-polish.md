# 2026-06-06 ACL Main Intro Gate Flow Polish

## Scope

Round 46 of the ACL main-paper visual/prose review polished the page-2
introductory gate-flow paragraph after Figure 1 in
`paper/venues/acl27/sections/intro.tex`.

## Issue

The previous paragraph carried the right evidence boundary, but it created a
dense visual cluster in the left column with multiple reader-visible line
breaks across important terms:

- `selected material- / effect`
- `Conver- / tAsset`
- `PreviewSur- / face`
- `99-episode official Ku- / JiaLe`

The paragraph also read like a list of experiment artifacts rather than an ACL
paper setup that connects the GRScenes gate, material-effect audit, and
InternNav sanity run as one bounded evidence chain.

## Change

The paragraph now frames the clean pool, stress pool, material audit, and
KuJiaLe InternNav run under the same gate logic. The revised prose keeps the
claim boundary unchanged: these gates support bounded claims, not broad
robustness claims.

Rejected intermediate candidates either introduced worse line breaks
(`A se- / lected`, standalone `A`, or `es- / tablish`) or pushed contribution
flow into a less stable column position. The accepted candidate removes the old
special-term break cluster while preserving the contribution and Related Work
placement.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260606_round46_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260606_round46_after`
- Before PDF SHA-256:
  `27ac5e0c3714de620638348893d4ad30e174564c918f3182fdbd6939ae82c9b3`
- After PDF SHA-256:
  `b5f8ef0e47f76db3bef99945a76a853f1516372b7d69152acbbb724a4330d05a`
- After page-2 comparison:
  `tmp/acl_main_visual_iter_20260606_round46_after/focus_before_after_p2.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round46_intro_gate_flow_polish_20260606.json`

The final page-2 text still contains the mild break `broad ro- / bustness`,
but the previous dense cluster across project names and material terms is
removed. This was accepted for this round to avoid destabilizing the
contribution block and Related Work start.

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
