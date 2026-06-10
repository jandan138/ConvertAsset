# 2026-06-06 ACL Main Evidence Gate Column Break Polish

## Scope

Round 30 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 4 Evidence Gates
closing sentence in Method Section 3.2, immediately before Claim Registry and
Results.

## Change

- Replaced `summarizes the allowed claim boundary for each gate` with
  `names each gate's permitted claim`.
- Removed the visual split where `claim bound-` ended the left column and
  `ary for each gate.` opened the right column.
- Kept the claim-boundary meaning while making the section close shorter and
  more method-like.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round30_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round30_after/contact_sheet.png`
- After focus sheet: `tmp/acl_main_visual_iter_20260606_round30_after/focus_p4_after.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round30_after/focus_before_after_p4.png`

Observed result: page 4 no longer opens the right column with the orphaned
`ary for each gate.` fragment. The complete sentence now sits at the bottom of
the Evidence Gates column: `Table 1 names each gate's permitted claim.` The
Claim Registry heading and Results transition remain readable.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 13.56s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- Page-4 text extraction confirmed the old split in the current render and the
  new complete sentence in the after render.

Final PDF identity:

- SHA256: `f2023008b50efb706eb2c50281d25b4d284b51e410b1360ef9927ab1b40e7d40`
- Pages: 11
- Size: 5,188,815 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round30_evidence_gate_column_break_polish_20260606.json`
