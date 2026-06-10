# 2026-06-07 ACL Main Method Gate3 Gate4 Linebreak Polish

## Scope

Round 60 of the ACL main-paper visual/prose review polished the page-4 Method
text for Evidence Gates 3 and 4. The source change is in:

- `paper/venues/acl27/sections/method.tex`

## Issue

The rendered page-4 left column had a dense linebreak cluster in the Gate 3 and
Gate 4 paragraphs:

- `Con- / vertAsset`
- `Con- / verter`
- `renderabil- / ity`
- `fi- / delity`
- `Du- / alVLN`
- `re- / peats`
- `ev- / idence`

Intermediate rewrites removed the system-name splits but introduced smaller
replacement splits such as `origi- / nal`, `out- / puts`, `ma- / terial`, and
`lim- / its`. The accepted version keeps the same claim boundary with shorter
gate prose and protects the `ConvertAsset` project name.

## Change

Gate 3 now describes the selected material-baseline check as a row-level
eligibility rule: source MDL, ConvertAsset noMDL, and NVIDIA PreviewSurface
outputs must be present; converted files must contain zero active MDL; and the
target must render. It states that the gate supports selected-bin checks and
does not certify full material semantics.

Gate 4 now states the scoped stack-entry claim directly: converted scenes load
and run in the selected InternNav/DualVLN stack, but the result is not a broad
navigation benchmark. This preserves the existing evidence boundary and result
counts.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round60_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round60_after`
- Before PDF SHA-256:
  `df89b3fe95422ca1a1b3a0e93721087ddd97cbb19cb6e78ac108fba9c28bdae4`
- After PDF SHA-256:
  `e33bd93d9dbed3c60a156eb2931cc24d048e0da7d1e05ed2a07198bbf38a7e82`
- After page-4 Method crop:
  `tmp/acl_main_visual_iter_20260607_round60_after/page4_left_method_focus.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round60_method_gate3_gate4_linebreak_polish_20260607.json`

The final page-4 Method crop removes the targeted Gate 3/Gate 4 split cluster
and keeps the Claim Registry and Results transition in the same page position.
The full contact sheet remains 11 pages with no obvious float, table, or
blank-page regression.

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
