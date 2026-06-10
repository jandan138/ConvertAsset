# 2026-06-07 ACL Main Intro Isaac Linebreak Polish

## Scope

Round 59 of the ACL main-paper visual/prose review polished the page-1
Introduction opening and gate-chain paragraph. The source change is in:

- `paper/venues/acl27/sections/intro.tex`

## Issue

The rendered first page still contained reader-visible linebreak damage in the
Introduction, especially around the Isaac Sim setup and the gate-chain summary:

- `con- / crete`
- `Intern- / Nav`
- `no-MDL con- / version`
- `preserva- / tion`, `preser- / vation`, and `usabil- / ity` in follow-on
  attempts

Intermediate rewrites also introduced replacement defects such as
`vis- / ible`, `com- / pares`, `ref- / erence`, `Sec- / ond`, `un- / der`,
`ma- / terial`, `au- / dit`, and `Defi- / nition`. The final pass therefore
kept the claim boundary but used shorter sentences and one protected word in
the MDL expansion.

## Change

The first-page Introduction now:

- states the Isaac Sim material setup with `NVIDIA's MDL shaders (Material
  \mbox{Definition} Language)`;
- frames the first question as visual match and the second as whether the same
  object query and target still hold after material changes;
- turns the roadmap paragraph into four shorter gates: asset visual/feature
  match, GRScenes grounding probes, a bounded source/noMDL/NVIDIA check, and an
  official InternNav stack-use check;
- avoids broadening the paper claim beyond bounded reliability evidence.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round59_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round59_after`
- Before PDF SHA-256:
  `e2a6d65204fa5970202aca1ff2afae8a0113fa902ab520aca707f59f16a21721`
- After PDF SHA-256:
  `df89b3fe95422ca1a1b3a0e93721087ddd97cbb19cb6e78ac108fba9c28bdae4`
- After page-1 intro crop:
  `tmp/acl_main_visual_iter_20260607_round59_after/page1_intro_focus_latest.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round59_intro_isaac_linebreak_polish_20260607.json`

The final page-1 text layer removes the targeted Introduction splits and keeps
the MDL expansion visible without splitting `Definition`. The full contact sheet
remains 11 pages with no obvious float, table, or blank-page regression.

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
