# 2026-06-06 ACL Main Material Mechanism Bridge Polish

## Scope

Round 29 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the Results Section 4.3
bridge on pages 5-6, where the VLM stress result hands off to the material-effect
and NVIDIA-baseline boundary.

## Change

- Reframed the Section 4.3 opener as a mechanism question: when evidence moves,
  which material channel moved it?
- Kept the NVIDIA baseline comparison explicitly bounded to material bins with
  provenance.
- Shortened the static-gate boundary sentence to avoid a page-break hyphenation
  and keep the selected-bin/non-population-rate boundary in one visible block.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round29_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round29_after/contact_sheet.png`
- After focus sheet: `tmp/acl_main_visual_iter_20260606_round29_after/focus_p5_p6_after.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round29_after/focus_before_after_p5_p6.png`

Observed result: the first draft removed the page-5 spacing issue but introduced
a page-break split across `selected-bin interpretation`. The final wording ends
page 5 at a complete sentence: `selected bins, not population-level rates.`
Page 6 starts directly with Section 4.4, and Figure 3 remains stable.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 13.75s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- PDF text extraction confirmed the new mechanistic-question and selected-bin
  boundary wording.

Final PDF identity:

- SHA256: `03d3c18ca425a40c13c088c9d015b5ec553bea6e68f84a98a2280712613702aa`
- Pages: 11
- Size: 5,188,829 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round29_material_mechanism_bridge_polish_20260606.json`
