# 2026-06-07 ACL Main Discussion Page9 Left Linebreak Polish

## Scope

Round 66 of the ACL main-paper visual/prose review polished the page-9
Discussion left column. The final source change is in:

- `paper/venues/acl27/sections/discussion.tex`

## Issue

The rendered page-9 Discussion left column contained a visible split cluster:

- `contri- / bution`
- `coordinate compli- / ance`
- `be- / fore`
- `material- / effect`

An initial page-4 Results/Claim Registry rewrite was rejected because it moved
Figure 2 onto page 4 ahead of the Results text. That source edit was reverted;
the final page-4 render is byte-identical to the Round66 baseline page-4 render.

During the accepted Discussion iteration, intermediate wording briefly
introduced replacement splits such as `lo- / cal`, `in- / side`,
`ma- / terial`, `suc- / cess`, `vi- / sual`, `embod- / ied`, and `af- / ter`.
The accepted version removes the page-9 target cluster without changing the
claim boundary.

## Change

The Discussion opener now frames the contribution as a measurement protocol in
shorter sentences: noMDL is a visible intervention, the route gives context but
does not rank tools, and the gate is the unit. The list of separated evidence
channels now uses `coordinate checks` and says the smoke tests stay separate.

The contract paragraph now states that coordinate frames and parser coverage
come first, and only then can a conversion delta become evidence.

The boundary paragraph now says the audit keeps static conversion, zero-MDL
output, and effect-token coverage out of success claims; the GRScenes bins
support visual checks; the KuJiaLe run is a stack check, not broad navigation
evidence; and portable scenes carry auditable claims only when gates pass.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round66_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round66_after`
- Before PDF SHA-256:
  `9f764b2b764055a0675ab2eaa24c12ed8f07e9f94d0e924eae28b3bc003c0034`
- After PDF SHA-256:
  `2dda5c1f787115f15d5b75424d416b2568c865541bc7c8219f9df425bb3c09c6`
- After page-9 left-column crop:
  `tmp/acl_main_visual_iter_20260607_round66_after/page9_left.png`
- After contact sheet:
  `tmp/acl_main_visual_iter_20260607_round66_after/contact_sheet.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round66_discussion_page9_left_linebreak_polish_20260607.json`

The final page-9 extracted text scan has no hyphen-line matches on that page.
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
