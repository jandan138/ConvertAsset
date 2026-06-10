# 2026-06-06 ACL Main Ethics Risk Paragraph Polish

## Scope

Round 37 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the first Ethical
Considerations paragraph on page 10, especially the risk/provenance sentence
flow next to the References column.

## Change

- Reframed the paragraph as direct ethics guidance: synthetic 3D assets are not
  human-subject data, but the risks remain indirect and practical.
- Replaced the older submission-oriented wording with author-facing reuse
  guidance for provenance, license compatibility, filtering criteria, and render
  intent.
- Tightened the downstream-model warning around material-change failures,
  object affordances, safety cues, texture, grounding cues, and real-world
  transfer.

The edit preserves the same claim boundary: converted synthetic scenes require
documented provenance, license checks, and failure reporting before supporting
downstream robustness or transfer claims.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round37_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round37_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round37_after/focus_before_after_p10.png`
- Pages 10-11 focus sheet: `tmp/acl_main_visual_iter_20260606_round37_after/focus_p10_p11_after.png`
- Pages 9-10 focus sheet: `tmp/acl_main_visual_iter_20260606_round37_after/focus_p9_p10_after.png`

Observed result: the page 10 first ethics paragraph no longer renders the old
`docu-` / `ment`, `ob-` / `ject`, `se-` / `mantic`, or `general-` /
`ization` split markers. A shorter intermediate rewrite was rejected because it
moved the `References` heading to the bottom of the left column and split the
first reference across the spread. The accepted wording keeps Figure 4 stable
above the section and keeps `References` aligned at the top of the right column.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 15.52s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- Page-10 text extraction confirms the old split markers in the current render
  and the final ethics-risk wording in the after render.

Final PDF identity:

- SHA256: `509a70c729a8286e2904b0a5044249e354718dcda596a8b6159fca683a99a0d6`
- Pages: 11
- Size: 5,188,574 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round37_ethics_risk_paragraph_polish_20260606.json`
