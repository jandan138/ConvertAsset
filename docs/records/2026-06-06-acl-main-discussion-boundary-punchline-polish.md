# 2026-06-06 ACL Main Discussion Boundary Punchline Polish

## Scope

Round 32 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 9 Discussion
paragraph that closes with the paper's boundary-method claim before the
Conclusion begins.

## Change

- Replaced the longer closing sentence beginning `These boundaries are part of
  the method` with `The method is the boundary: portable scene workflows carry
  auditable claims only inside the gates they pass.`
- Removed the rendered page-9 `These bound-` / `aries` and `portable-` /
  `scene` splits.
- Preserved the claim-boundary semantics while giving the
  Discussion-to-Conclusion handoff a shorter ACL-style punchline.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round32_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round32_after/contact_sheet.png`
- After focus sheet: `tmp/acl_main_visual_iter_20260606_round32_after/focus_p9_after.png`
- Pages 9-10 focus sheet: `tmp/acl_main_visual_iter_20260606_round32_after/focus_p9_p10_after.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round32_after/focus_before_after_p9.png`

Observed result: page 9 now renders the boundary punchline without the old
`bound-` / `aries` or `portable-` / `scene` splits. The Conclusion still begins
on page 9, and page 10 remains stable.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 13.66s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- Page-9 text extraction confirmed the old split in the current render and the
  new boundary punchline in the after render.

Final PDF identity:

- SHA256: `a7eb18b17acf73ede0439e6a14c6034b15ec2a86c71b80cc530d296b12ba682c`
- Pages: 11
- Size: 5,188,795 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round32_discussion_boundary_punchline_polish_20260606.json`
