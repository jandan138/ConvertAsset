# 2026-06-06 ACL Main Method Gate4 Entry Check Polish

## Scope

Round 38 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the Gate 4 paragraph in
`Method`, page 4, where the old wording created a conspicuous stretched `We run`
line and split `official` / `InternNav` across lines.

## Change

- Recast Gate 4 as an `embodied-stack entry check`, matching the paper's
  evidence-gate story.
- Replaced the old process sentence with a tighter account of the official
  KuJiaLe route supplying matched original/noMDL scenes for InternNav and
  DualVLN.
- Kept the claim boundary explicit: the evidence shows selected-stack entry and
  load/render trials, not a broad navigation benchmark.

The exact `val_unseen` split remains stated in the Results section; the Method
paragraph now carries the gate role and boundary without forcing that monospace
token into a narrow line.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round38_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round38_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round38_after/focus_before_after_p4.png`
- Pages 3-4 focus sheet: `tmp/acl_main_visual_iter_20260606_round38_after/focus_p3_p4_after.png`
- Pages 4-5 focus sheet: `tmp/acl_main_visual_iter_20260606_round38_after/focus_p4_p5_after.png`

Observed result: the page 4 Gate 4 paragraph no longer renders the old stretched
`We run` line, `from the of-` / `ficial KuJiaLe`, or `through In-` /
`ternNav`. Intermediate phrasings were rejected because `smoke test` split
awkwardly, the `val_unseen` monospace token produced a badness-10000 line, or
the `InternNav/DualVLN stack` wording introduced worse Gate 4 underfulls. The
accepted wording leaves a minor `Du-` / `alVLN` split, but it removes the more
visible stretched spacing and keeps Results, Figure 2, and the page 5 flow
stable.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 15.48s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- Page-4 text extraction confirms the old stretched/split markers in the current
  render and the final Gate 4 entry-check wording in the after render.
- The final build log has no `lines 57--63` Gate 4 underfull entry.

Final PDF identity:

- SHA256: `fa82288d41866e48febf661c1dce1d3d9fac5b4c0af9066260d23006b19ba08b`
- Pages: 11
- Size: 5,188,391 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round38_method_gate4_entry_check_polish_20260606.json`
