# 2026-06-07 ACL Main Ethics Risk Linebreak Polish

## Scope

Round 50 of the ACL main-paper visual/prose review polished the page-10
Ethical Considerations paragraph. The source change is in
`paper/venues/acl27/sections/ethical-considerations.tex`.

## Issue

The page-10 ethics paragraph contained a reader-visible split:

- `overstated robust- / ness claims`

This was not a claim-scope bug, but it interrupted the final risk statement
immediately before the paper hands into References.

## Change

The risk phrase now uses:

`overbroad claims`

The neighboring sentence now says `Authors using converted scenes`, and the
accepted source uses narrow `\mbox{...}` guards only for `report` and
`evidence` so the final render does not trade the original `robustness` split
for `re- / port` or `evi- / dence` splits. The claim boundary remains unchanged:
the paragraph still warns that converted-scene reuse must disclose provenance,
licenses, filtering, intended use, and failures that alter task, safety,
texture, or grounding cues.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round50_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round50_after`
- Before PDF SHA-256:
  `581eadfeb25816d81e77c2a75835e24d17a64aefbef4115f7e76a786f929075f`
- After PDF SHA-256:
  `85e89fc7e4a1d1016cffbc66cf811c9fbef3b270309a98a13265d24b0abfa274`
- After page-10 comparison:
  `tmp/acl_main_visual_iter_20260607_round50_after/focus_before_after_p10.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round50_ethics_risk_linebreak_polish_20260607.json`

The final page-10 comparison removes the targeted `overstated robust- / ness
claims` split, keeps `References` at the top of the right column, and preserves
the 11-page layout.

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
