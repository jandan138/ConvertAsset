# 2026-06-07 ACL Main Intro Opening Linebreak Polish

## Scope

Round 53 of the ACL main-paper visual/prose review polished the page-1
Introduction opening paragraph. The source change is in
`paper/venues/acl27/sections/intro.tex`.

## Issue

The page-1 Introduction opener contained a reader-visible split:

- `Vision-language and embodied-language mod- / els`

The sentence sat immediately under the section heading, so the split was more
visible than a body-column hyphenation. During review, intermediate rewrites
were rejected because they traded the original split for `en- / vironments`,
`rou- / tine`, `ren- / der`, `im- / age`, `as- / sets`, `render- / ing`,
`interven- / tion`, and then `bench- / mark`.

## Change

The opening paragraph now uses:

`Vision-language systems and embodied agents are increasingly tested in simulated 3D scenes, where they must bind language to objects, views, and actions. These evaluations treat the rendered scene as fixed input, yet the view is also the measurement interface. When scenes cross shader systems for large runs, sharing, viewer export, or robotics reuse, that step can become a hidden task factor.`

This keeps the same claim boundary while replacing the long
`embodied-language models` phrase with a shorter ACL-style setup. The paragraph
still frames synthetic 3D scenes as a measurement interface and shader-system
crossing as a possible hidden task factor; it does not add a broader benchmark
or performance claim.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round53_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round53_after`
- Before PDF SHA-256:
  `ad9d09a920a21997ef84467e7edc82990cb6963926d5e5635c7a200c705aed8a`
- After PDF SHA-256:
  `bbd7729977b21eac43291cf7ce9a3fc13f2fda8e79e9d4fa51559b1c89e4e68d`
- After page-1 comparison:
  `tmp/acl_main_visual_iter_20260607_round53_after/focus_before_after_p1.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round53_intro_opening_linebreak_polish_20260607.json`

The final page-1 comparison removes the targeted `mod- / els` split and avoids
the rejected intermediate splits. The full contact sheet remains 11 pages with
no obvious float, table, or blank-page regression.

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
