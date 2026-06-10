# 2026-06-07 ACL Main Related Opening Linebreak Polish

## Scope

Round 57 of the ACL main-paper visual/prose review polished the Related Work
opening on page 2. The source change is in
`paper/venues/acl27/sections/related.tex`.

## Issue

The page-2 Related Work opening contained several reader-visible splits in the
first paragraph and first related-work lane:

- `syn- / thetic`
- `set- / ting`
- `referen- / tial`
- follow-on experimental rewrites briefly introduced worse splits such as
  `embod- / ied`, `identifi- / cation`, `coordi- / nate`, and `archi- / tecture`
  before the final wording was accepted.

Because this section is the paper's transition from contribution claims into
prior work, the opening needed to read as a compact literature frame rather
than a sequence of visibly hyphenated terms.

## Change

The opening now uses shorter wording:

`This paper links VLM grounding, embodied simulation, and rendered 3D evaluation.`

The first related-work lane is also tightened:

`Grounding and VLN. Vision-language navigation maps instructions to views and paths.`

The final wording removes the targeted splits, keeps the same related-work
boundary, and preserves the claim that the paper studies a measurement question
rather than proposing a new VLM model or VLN benchmark.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round56_after`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round57_after`
- Before PDF SHA-256:
  `fc5a3559c298e9f2575234db35764ae2e59b5ac69428019febda79bacd78cfcd`
- After PDF SHA-256:
  `82e1d7f60d5b4222ee878d15ae6ed44f2420a9715b3493be4783bc8ce68ea382`
- After page-2 Related Work crop:
  `tmp/acl_main_visual_iter_20260607_round57_after/page2_related_top.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round57_related_opening_linebreak_polish_20260607.json`

The final page-2 text layer removes the targeted `syn- / thetic`,
`set- / ting`, and `referen- / tial` splits from the Related Work opening and
does not introduce a replacement split in the accepted local wording. The full
contact sheet remains 11 pages with no obvious float, table, or blank-page
regression.

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
