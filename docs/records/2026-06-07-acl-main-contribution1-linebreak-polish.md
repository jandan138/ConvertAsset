# 2026-06-07 ACL Main Contribution 1 Linebreak Polish

## Scope

Round 55 of the ACL main-paper visual/prose review polished the first
contribution statement on page 2. The source change is in
`paper/venues/acl27/sections/intro.tex`.

## Issue

The first contribution contained three reader-visible splits in a short list
item:

- `con- / trolled`
- `ground- / ing`
- `optimiza- / tion`

The list sits at the end of the Introduction, where the paper moves from the
gate-chain story into its contribution claims. The wording was accurate, but
the triple split made the first contribution read like layout damage rather
than a crisp ACL contribution.

## Change

The first contribution now uses:

`We make material conversion a controlled test of VLM grounding, not neutral asset cleanup.`

This keeps the same claim boundary: material conversion is treated as a
controlled VLM-grounding test rather than neutral asset work. It does not add a
new benchmark claim or imply general VLM robustness.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round55_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round55_after`
- Before PDF SHA-256:
  `f970fa69d7e4e13c73bef9c129b767d33b38496685a4e06c69a4ba19af64ce1b`
- After PDF SHA-256:
  `29d4d48fda3868b411a75ea9105de9c483d68d8ba6d1d4da519fd8f9be400dc8`
- After page-2 comparison:
  `tmp/acl_main_visual_iter_20260607_round55_after/focus_before_after_p2.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round55_contribution1_linebreak_polish_20260607.json`

The final page-2 comparison removes the targeted `con- / trolled`,
`ground- / ing`, and `optimiza- / tion` splits from the first contribution. The
full contact sheet remains 11 pages with no obvious float, table, or blank-page
regression. Existing Related Work splits such as `set-` and `referen-` are
unchanged and outside this round's target.

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
