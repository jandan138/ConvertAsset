# 2026-06-07 ACL Main Static Evidence Diagnostic Linebreak Polish

## Scope

Round 52 of the ACL main-paper visual/prose review polished the page-5
Material Effects and NVIDIA Baseline Boundaries paragraph. The source change is
in `paper/venues/acl27/sections/results.tex`.

## Issue

The page-5 material-effect boundary paragraph contained a reader-visible split:

- `MDL preserva- / tion`

The sentence was already claim-bounded, but the split landed in a short
paragraph that closes the static material-effect gate. During review, an
intermediate rewrite was rejected because it traded the original split for
`certify- / ing`, `esti- / mating`, and then `pre- / served`.

## Change

The paragraph now uses:

`The static evidence is diagnostic. It points to selected mechanisms, not broad rates or proof that MDL semantics stay intact.`

This keeps the same claim boundary while avoiding the long preservation noun
form. The statement remains narrower than a material-effect benchmark claim: it
says the static gate localizes selected mechanisms, and it does not claim broad
rates or semantic equivalence.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round52_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round52_after`
- Before PDF SHA-256:
  `c11bb6289cb1c6d40a0221d906ba2a4ad8247020dc26ef23af67e1ed74b6b47e`
- After PDF SHA-256:
  `ad9d09a920a21997ef84467e7edc82990cb6963926d5e5635c7a200c705aed8a`
- After page-5 comparison:
  `tmp/acl_main_visual_iter_20260607_round52_after/focus_before_after_p5.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round52_static_evidence_diagnostic_linebreak_polish_20260607.json`

The final page-5 comparison removes the targeted `MDL preserva- / tion` split.
The accepted render also avoids the rejected intermediate `certify- / ing`,
`esti- / mating`, and `pre- / served` splits. The full contact sheet remains 11
pages with no obvious float, table, or blank-page regression.

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
