# 2026-06-06 ACL Main Conclusion Gate Close Polish

## Scope

Round 33 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 9 Conclusion
second paragraph, where the final takeaway sits below Discussion and beside the
Limitations column.

## Change

- Replaced the longer checklist-style closing paragraph with a shorter four-gate
  takeaway.
- Removed the rendered `intervention au-` / `ditable` and `visual compar-` /
  `ison` splits.
- Kept the same gate semantics: render similarity, grounding QA, material-risk
  bins, and embodied smoke tests.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round33_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round33_after/contact_sheet.png`
- After focus sheet: `tmp/acl_main_visual_iter_20260606_round33_after/focus_p9_after.png`
- Pages 9-10 focus sheet: `tmp/acl_main_visual_iter_20260606_round33_after/focus_p9_p10_after.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round33_after/focus_before_after_p9.png`

Observed result: page 9 now keeps the Conclusion closing paragraph inside the
left column, while Limitations still starts at the top of the right column. Page
10 Figure 4, Ethical Considerations, and References remain stable.

One longer intermediate rewrite was rejected because it removed the target
hyphenations but pushed the Conclusion's last two lines into the right column.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 14.10s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- Page-9 text extraction confirmed the old split in the current render and the
  new four-gate closing sentence in the after render.

Final PDF identity:

- SHA256: `ed41a93c5140bb9e06fce36bff58e65130e7d81dd448a9aaa3d9dc7dccb23628`
- Pages: 11
- Size: 5,188,699 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round33_conclusion_gate_close_polish_20260606.json`
