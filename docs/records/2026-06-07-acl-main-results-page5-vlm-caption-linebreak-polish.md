# 2026-06-07 ACL Main Results Page5 VLM/Caption Linebreak Polish

## Scope

Round 70 of the ACL main-paper visual/prose review polished two page-5 Results
linebreak defects in the paired-bootstrap paragraph and Figure 3 caption. The
final source change is in:

- `paper/venues/acl27/sections/results.tex`

## Issue

The rendered page contained two visible splits:

- `expanded 30- / pair`
- `original- / MDL`

The first split appeared in the VLM stress-set confidence-interval paragraph.
The second appeared in the Figure 3 caption, where the caption described the
source material cells that passed the clean rerender/provenance gate.

An initial rewrite removed those target splits but introduced replacement
splits: `normal- / ized` and `descrip- / tive`. That version was rejected.

## Change

The accepted paired-bootstrap paragraph now says `this 30-pair stress set` and
uses shorter `point-hit gain` and interval-description language. The evidence
boundary remains the same: the intervals describe frozen evidence pools, not
population-level guarantees.

The Figure 3 caption now says `source-MDL cells` instead of `original-MDL
cells`. This keeps the source material condition explicit while avoiding the
caption break.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round70_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round70_after`
- Before PDF SHA-256:
  `ab72227c64e4b8a0ecf51a4dda990640c8598cb531ff6ead788d6cf56e3fe0d5`
- After PDF SHA-256:
  `44a1e259678ac479ff5081214162bcfd31014611a0ab00b4b9d3351487f06dbd`
- After page-5 top crop:
  `tmp/acl_main_visual_iter_20260607_round70_after/page5_top.png`
- After page-5 bottom crop:
  `tmp/acl_main_visual_iter_20260607_round70_after/page5_bottom.png`
- After page-6 top crop:
  `tmp/acl_main_visual_iter_20260607_round70_after/page6_top.png`
- After contact sheet:
  `tmp/acl_main_visual_iter_20260607_round70_after/contact_sheet.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round70_results_page5_vlm_caption_linebreak_polish_20260607.json`

The accepted page-5 and page-6 text scans have no hyphen-line matches. Page 6
is byte-identical to the Round70 baseline render, so the accepted edit did not
propagate into the next page.

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
