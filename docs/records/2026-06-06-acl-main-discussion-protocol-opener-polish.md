# 2026-06-06 ACL Main Discussion Protocol Opener Polish

## Scope

Round 36 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 9 Discussion
opener, especially the `Protocol, not leaderboard.` paragraph before the
Contracts and Boundaries discussion paragraphs.

## Change

- Replaced the old converter-leaderboard wording with a tighter protocol
  framing: noMDL is a visible intervention, not proof that a tool is safe,
  faster, or better than NVIDIA's route.
- Added `The gate is the unit, not the tool` to make the Discussion read more
  like the paper's central story rather than a generic caveat.
- Replaced the final language-grounding sentence with a shorter probe sentence:
  one gate can pass while the probe still sees a change.

The edit preserves the same claim boundary: the paper evaluates gated evidence,
not a general converter ranking or broad downstream robustness claim.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round36_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round36_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round36_after/focus_before_after_p9.png`
- Pages 9-10 focus sheet: `tmp/acl_main_visual_iter_20260606_round36_after/focus_p9_p10_after.png`
- Pages 8-9 focus sheet: `tmp/acl_main_visual_iter_20260606_round36_after/focus_p8_p9_after.png`

Observed result: the page 9 opener no longer renders the old `harm-` / `less`
split or the `As-` / `set Converter` split. Intermediate phrasings that
introduced `con-` / `verter`, `base-` / `line`, `instru-` / `ments`,
`test in-` / `puts`, `sepa-` / `rate`, or `Pass-` / `ing` were rejected before
the final wording. The accepted spread keeps `Limitations` at the top of the
right column and leaves Figure 4, Ethical Considerations, and References stable
on page 10.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 15.62s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- Page-9 text extraction confirms the old split markers in the current render
  and the final gate/unit wording in the after render.

Final PDF identity:

- SHA256: `63f8f5701ca35244fd143fa2dfc146ae1f24c58e84384ffdc7a5775819966a1e`
- Pages: 11
- Size: 5,188,621 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round36_discussion_protocol_opener_polish_20260606.json`
