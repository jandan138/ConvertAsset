# 2026-06-07 ACL Main Method Page3 Claim Registry Linebreak Polish

## Scope

Round 68 of the ACL main-paper visual/prose review polished the page-3 Method
right column at the Claim Registry opener. The final source change is in:

- `paper/venues/acl27/sections/method.tex`

## Issue

The rendered Claim Registry opener began at the page-3 right-column bottom and
split a short reader-facing word:

- `ta- / ble`

The defect came from the sentence `Every major result is tied to a manifest,
table, or claim entry...`, where the list was longer than needed for the Method
role. An initial rewrite removed the `table` split but introduced replacement
splits: `evi- / dence`, `reg- / istry`, `con- / trolled`, `met- / rics`, and
`evi- / dence` again on the following page. That intermediate version was
rejected.

## Change

The accepted version shortens the Claim Registry paragraph without changing the
claim boundary. It now says that each result points to the evidence registry,
that the entry states the supported claim, scope, and forbidden promotion, and
that conversion is the test. The final sentence keeps the same safeguard:
proxy metrics, selected videos, and single-scene results cannot stand in for
task-wide claims.

This removes a low-value list from the Method prose and makes the registry role
easier for a reviewer to parse at the page break.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round68_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round68_after`
- Before PDF SHA-256:
  `ce7e409bef671cdec2d0e79574be20443e0f27e0a03b3d44fb6c44bf3c818dda`
- After PDF SHA-256:
  `60abce690523873e3a3ef86e9ff1898ff9788c715e8288cb2cc192a76d959766`
- After page-3 right-bottom crop:
  `tmp/acl_main_visual_iter_20260607_round68_after/page3_right_bottom.png`
- After page-4 top crop:
  `tmp/acl_main_visual_iter_20260607_round68_after/page4_top.png`
- After contact sheet:
  `tmp/acl_main_visual_iter_20260607_round68_after/contact_sheet.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round68_method_page3_claim_registry_linebreak_polish_20260607.json`

The accepted page-3 text scan has no remaining target split in the Claim
Registry opener. Page 4 was checked after reflow; the rejected replacement
splits are absent. The remaining page-4 Results splits are inherited and are
recorded as next-round candidates.

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
