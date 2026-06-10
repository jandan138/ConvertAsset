# 2026-06-06 ACL Main Material Scope Sentence Polish

## Scope

Round 31 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 5 sentence that
introduces Table 5 in Results Section 4.3.

## Change

- Replaced `sets the material claim boundary` with `defines the material-effect
  scope`.
- Removed the rendered line break where `material claim bound-` was followed by
  `ary` on the next line.
- Preserved the claim-boundary meaning while making the transition into the
  covered-bin discussion shorter.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round31_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round31_after/contact_sheet.png`
- After focus sheet: `tmp/acl_main_visual_iter_20260606_round31_after/focus_p5_after.png`
- Pages 5-6 focus sheet: `tmp/acl_main_visual_iter_20260606_round31_after/focus_p5_p6_after.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round31_after/focus_before_after_p5.png`

Observed result: page 5 now renders `Table 5 defines the material-effect scope.`
as a complete sentence, without the old `bound-` / `ary` split. Page 6 Figure 3
and its caption remain stable.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 13.67s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- Page-5 text extraction confirmed the old split in the current render and the
  new complete sentence in the after render.

Final PDF identity:

- SHA256: `513cf208bbc0684a15813b2d41979a12b4267a847b739f9c0e79d7ccff25ba34`
- Pages: 11
- Size: 5,188,806 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round31_material_scope_sentence_polish_20260606.json`
