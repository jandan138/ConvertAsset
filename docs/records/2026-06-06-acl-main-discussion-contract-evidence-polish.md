# 2026-06-06 ACL Main Discussion Contract Evidence Polish

## Scope

Round 40 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The accepted target was the page 9
Discussion paragraph `Contracts before deltas`, where the old wording split
`renders` and `finding` across lines and read more like a result restatement than
an ACL discussion takeaway.

## Change

- Reframed the GRScenes stress result as the clearest warning that proxy
  similarity is not enough.
- Added the close-image/scoring-contract contrast so the paragraph reads as a
  discussion claim rather than a table recap.
- Replaced `contract finding` with `contract evidence`, while preserving the
  boundary against model ranking.
- Kept the coordinate-frame and parser-coverage frozen-condition sentence so the
  page 9 flow remains stable and the limitations heading stays in the right
  column.

Rejected intermediate route: an attempted Related Work opening rewrite reduced
some old splits but introduced worse page 3 breaks and was restored before the
accepted Discussion edit.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round40_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round40_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round40_after/focus_before_after_p9.png`
- Pages 9-10 focus sheet: `tmp/acl_main_visual_iter_20260606_round40_after/focus_p9_p10_after.png`

Observed result: the accepted page 9 paragraph removes the old `ren-` / `ders`
and `find-` / `ing` splits in the Contracts paragraph. It keeps the page's
two-column structure stable: `Limitations` remains at the top of the right
column, `Conclusion` remains in the lower left, and Figure 4 / Ethical
Considerations / References remain on page 10. A shorter intermediate Discussion
version was rejected because it pushed the `Limitations` heading to the bottom of
the left column and made the section flow worse.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 15.06s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.

Final PDF identity:

- SHA256: `8cf186677adc81c1f48bc8ecbdd2302154a8b7c4e03634775b7471e25e36d364`
- Pages: 11
- Size: 5,188,357 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round40_discussion_contract_evidence_polish_20260606.json`
