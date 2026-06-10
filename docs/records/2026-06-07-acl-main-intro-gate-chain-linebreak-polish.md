# 2026-06-07 ACL Main Intro Gate Chain Linebreak Polish

## Scope

Round 54 of the ACL main-paper visual/prose review polished the page-1
Introduction answer paragraph in the right column. The source change is in
`paper/venues/acl27/sections/intro.tex`.

## Issue

The page-1 answer paragraph contained a reader-visible split:

- `proxy simi- / larity`

The split landed in the first statement of the paper's evidence logic, where
the Introduction turns the motivating question into the gate-chain story.
During review, intermediate rewrites were rejected because they traded the
targeted split for `mate- / rial`, `an- / swer`, `mat- / ters`, `embod- / ied`,
`bench- / marks`, or `set- / tings`.

## Change

The paragraph now uses:

`The answer is a chain of gates, not a single score: proxy scores may pass even when grounding, material, and stack checks ask different reliability questions. The issue is concrete in GRScenes, where evaluation runs may combine large USD scenes, object-level goals, VLM prompting, and navigation frameworks such as InternNav/DualVLN.`

This keeps the claim boundary unchanged. It still says that proxy evidence,
grounding evidence, material evidence, and downstream stack evidence answer
different questions; it does not claim broader benchmark reliability or
performance improvement.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round54_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round54_after`
- Before PDF SHA-256:
  `bbd7729977b21eac43291cf7ce9a3fc13f2fda8e79e9d4fa51559b1c89e4e68d`
- After PDF SHA-256:
  `f970fa69d7e4e13c73bef9c129b767d33b38496685a4e06c69a4ba19af64ce1b`
- After page-1 comparison:
  `tmp/acl_main_visual_iter_20260607_round54_after/focus_before_after_p1.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round54_intro_gate_chain_linebreak_polish_20260607.json`

The final page-1 comparison removes the targeted `proxy simi- / larity` split.
The accepted render also avoids the rejected intermediate `mate- / rial`,
`an- / swer`, `mat- / ters`, `embod- / ied`, `bench- / marks`, and
`set- / tings` splits. The full contact sheet remains 11 pages with no obvious
float, table, or blank-page regression.

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
