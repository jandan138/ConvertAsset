# 2026-06-06 ACL Main Limitations Boundary Story Polish

## Scope

Round 28 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 9 Limitations
opening paragraph.

## Change

- Reframed the opening as a deliberate evidence-boundary statement.
- Preserved the substantive caveats: 15 clean visual-QA pairs, the configured
  20-pair clean final gate, the frozen 30-pair target-centered stress set, and
  unresolved Qwen2.5-VL coordinate semantics.
- Replaced the looser broad-distribution wording with a clearer ACL limitation:
  the stress set supports a controlled material-shift stress-test claim, not a
  broad benchmark over GRScenes.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round28_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round28_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round28_after/focus_before_after_p9_p10.png`

Observed result: page 9 keeps the Discussion, Limitations, and Conclusion flow
on the same page. The Limitations opening compacts by one line, and page 10
remains stable.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 13.41s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- PDF text extraction confirmed the new evidence-boundary wording.

Final PDF identity:

- SHA256: `367c40a1bbdd5272e3ef15305511ec8d2141d63a66b8d4fdf7ff43a64b92b85d`
- Pages: 11
- Size: 5,188,964 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round28_limitations_boundary_story_polish_20260606.json`
