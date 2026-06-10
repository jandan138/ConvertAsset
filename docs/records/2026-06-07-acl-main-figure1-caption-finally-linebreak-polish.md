# 2026-06-07 ACL Main Figure 1 Caption Finally Linebreak Polish

## Scope

Round 56 of the ACL main-paper visual/prose review polished the Figure 1
caption on page 2. The source change is in
`paper/venues/acl27/sections/intro.tex`.

## Issue

The Figure 1 caption split `finally` as `fi- / nally` at the page top:

`compare matched renders for VLM grounding, and fi- / nally check selected ...`

The caption introduces the paper's evidence-chain roadmap, so the visible split
made the first page-2 transition look rough even though the claim boundary was
otherwise correct.

## Change

The caption now uses:

`compare matched renders for VLM grounding, then check selected official InternNav rollouts and paired metrics.`

This removes the targeted split, shortens redundant `InternNav navigation`
wording, and keeps the same schematic claim: the panel is an overview, while
empirical render, material-effect, and navigation figures remain the recorded
evidence sources.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round56_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round56_after`
- Before PDF SHA-256:
  `29d4d48fda3868b411a75ea9105de9c483d68d8ba6d1d4da519fd8f9be400dc8`
- After PDF SHA-256:
  `fc5a3559c298e9f2575234db35764ae2e59b5ac69428019febda79bacd78cfcd`
- After page-2 caption crop:
  `tmp/acl_main_visual_iter_20260607_round56_after/page2_caption_related_top.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round56_figure1_caption_finally_linebreak_polish_20260607.json`

The final page-2 text layer and caption crop remove the targeted `fi- / nally`
split. The full contact sheet remains 11 pages with no obvious float, table, or
blank-page regression. Existing Related Work splits such as `syn- / thetic`,
`set- / ting`, and `referen- / tial` remain visible and are outside this
round's target.

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
