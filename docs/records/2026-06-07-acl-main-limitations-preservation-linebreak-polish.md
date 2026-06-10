# 2026-06-07 ACL Main Limitations Preservation Linebreak Polish

## Scope

Round 51 of the ACL main-paper visual/prose review polished the page-9
Limitations paragraph. The source change is in
`paper/venues/acl27/sections/limitations.tex`.

## Issue

The page-9 Limitations paragraph contained a reader-visible split:

- `general VLM-grounding preserva- / tion claim`

This was a prose and layout defect, not a claim-scope bug. It interrupted the
paragraph that deliberately states why the 15-pair clean visual-QA pool cannot
support a general VLM-grounding preservation claim.

## Change

The sentence now uses:

`claim that VLM grounding is preserved`

This keeps the evidence boundary unchanged while replacing the long compound
nominal phrase with a clearer clause. The final rendered page reads:

`cannot support a general claim that VLM grounding is preserved.`

The 30-pair expanded stress set remains described as a frozen target-centered
stress set, and the paragraph still denies a broad GRScenes benchmark claim.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round51_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round51_after`
- Before PDF SHA-256:
  `85e89fc7e4a1d1016cffbc66cf811c9fbef3b270309a98a13265d24b0abfa274`
- After PDF SHA-256:
  `c11bb6289cb1c6d40a0221d906ba2a4ad8247020dc26ef23af67e1ed74b6b47e`
- After page-9 comparison:
  `tmp/acl_main_visual_iter_20260607_round51_after/focus_before_after_p9.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round51_limitations_preservation_linebreak_polish_20260607.json`

The final page-9 comparison removes the targeted `general VLM-grounding
preserva- / tion claim` split. The full contact sheet remains 11 pages with no
obvious float, table, or blank-page regression.

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
