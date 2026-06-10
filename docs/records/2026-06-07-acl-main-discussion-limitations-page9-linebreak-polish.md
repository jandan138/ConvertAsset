# 2026-06-07 ACL Main Discussion/Limitations Page9 Linebreak Polish

## Scope

Round 64 of the ACL main-paper visual/prose review polished the page-9
Discussion and Limitations right column. The source changes are in:

- `paper/venues/acl27/sections/discussion.tex`
- `paper/venues/acl27/sections/limitations.tex`

## Issue

The rendered page-9 right column contained visible linebreak clusters across the
Discussion boundary paragraph and the material/embodied Limitations paragraph:

- `evi- / dence`
- `ma- / trix`
- `ef- / fect`
- `fix- / tures`
- `Intern- / Nav`
- `lo- / cal`
- `In- / teriorAgent`
- `manipula- / tion`

During iteration, shorter wording briefly introduced replacement splits such as
`pro- / cedural`, `san- / ity`, `han- / dled`, `distribu- / tion`,
`manip- / ulation`, `Fig- / ure`, and `official- / scene`. A later pass also
created wider justification pressure and a duplicated route phrase. The accepted
version removes the target cluster without changing the evidence boundary.

## Change

The Discussion boundary paragraph now separates the material-effect audit,
bounded GRScenes visual support, and 99-episode KuJiaLe sanity check with
shorter sentences. The closing sentence keeps the method-as-boundary framing:
portable scenes carry auditable claims only inside passed gates.

The Limitations material-and-embodied paragraph now states the 30 GRScenes
samples, four effect bins, three KuJiaLe scenes, 99 paired episodes, and
non-speedup boundary in shorter units. The claim scope remains unchanged: the
paragraph still does not generalize to all InternNav settings, InteriorAgent,
R2R/MP3D, manipulation, or broad GRScenes robustness.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round64_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round64_after`
- Before PDF SHA-256:
  `524882046d1793d398c31a197c03122f5f85e0ca772798ca2397b7135b41f759`
- After PDF SHA-256:
  `554fcf8d46aa9c39385c36d7945aa01a66ffa75b4f3fa8edda90812bd781745e`
- After page-9 right-column crop:
  `tmp/acl_main_visual_iter_20260607_round64_after/page9_right.png`
- After contact sheet:
  `tmp/acl_main_visual_iter_20260607_round64_after/contact_sheet.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round64_discussion_limitations_page9_linebreak_polish_20260607.json`

The final page-9 crop removes the targeted Discussion/Limitations split cluster.
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
