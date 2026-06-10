# 2026-06-07 ACL Main Abstract Linebreak Metadata Polish

## Scope

Round 58 of the ACL main-paper visual/prose review polished the first-page
abstract. The source changes are in:

- `paper/venues/acl27/sections/abstract.tex`
- `paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md`

## Issue

The rendered abstract on page 1 still contained reader-visible linebreak splits
in the narrow ACL column:

- `vision- / language`
- `Pre- / viewSurface`
- `NVIDIA- / baseline`
- `99- / episode`
- `de- / fine`

Early rewrites removed those target splits but introduced replacement splits
such as `con- / version`, `DI- / NOv2`, `pre- / serves`, and `In- / ternNav`.
The accepted version therefore combines shorter abstract prose with a local
ragged-right abstract setting and nonbreaking model/system names where needed.

## Change

The abstract now presents the same evidence boundary in shorter prose:

- material conversion is framed as a bounded measurement test;
- the MDL rewrite path is described without repeating long tool names;
- the `normalized-1000 point hits` evidence phrase is preserved for the
  metadata/test contract;
- the OpenReview metadata packet is synchronized with the source abstract and
  still reports 168 words.

This does not broaden the claim. The abstract still says proxy fidelity does
not certify grounding behavior and keeps visual match, grounding, material
effects, and stack checks as separate gates.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round58_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round58_after`
- Before PDF SHA-256:
  `82e1d7f60d5b4222ee878d15ae6ed44f2420a9715b3493be4783bc8ce68ea382`
- After PDF SHA-256:
  `e2a6d65204fa5970202aca1ff2afae8a0113fa902ab520aca707f59f16a21721`
- After page-1 abstract crop:
  `tmp/acl_main_visual_iter_20260607_round58_after/page1_abstract.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round58_abstract_linebreak_metadata_polish_20260607.json`

The final page-1 text layer removes the targeted abstract splits and preserves
the required `converted normalized-1000 point hits` wording. The accepted
abstract uses a ragged-right local setting, which leaves a slightly uneven right
edge but avoids the previous first-page hyphenation damage and wide justified
spacing. The full contact sheet remains 11 pages with no obvious float, table,
or blank-page regression.

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
