# 2026-06-06 ACL Main Discussion Static Conversion Pass Polish

## Scope

Round 42 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The accepted target was page 9,
`Discussion`, where the `Boundaries as method` paragraph rendered
`static conversion suc-` / `cess` in the first sentence.

## Change

- Replaced `prevents static conversion success` with `prevents a static
  conversion pass`.
- Kept the evidence-boundary meaning unchanged: static conversion, zero-MDL
  output, and effect-token coverage still cannot be counted as visual or task
  success.
- Left the adjacent Limitations, Conclusion, Figure 4, Ethics, and References
  layout unchanged.

Rejected intermediate route: earlier page 5 VLM-stress wording candidates were
built and visually reviewed, but they either worsened local line breaks or
changed page flow. No page 5 source change was retained for this record.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round42_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round42_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round42_after/focus_before_after_p9.png`
- Pages 9-10 focus sheet: `tmp/acl_main_visual_iter_20260606_round42_after/focus_p9_p10.png`

Observed result: page 9 no longer renders `static conversion suc-` / `cess`.
The accepted line now reads `effect audit prevents a static conversion pass,`.
The page 9 Discussion / Limitations / Conclusion structure is stable, and page
10 keeps Figure 4 above Ethical Considerations with References starting at the
top of the right column. The PDF remains 11 pages.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, label warnings, undefined references,
  multiply defined labels, rerun-to-cross-reference warnings, and lineno
  warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 14.24s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.

Final PDF identity:

- SHA256: `fbce0b5fb8145a55ee640a95c3df7b17dad67b1dde312c410f146d0f1cb553c5`
- Pages: 11
- Size: 5,188,359 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round42_discussion_static_conversion_pass_polish_20260606.json`
