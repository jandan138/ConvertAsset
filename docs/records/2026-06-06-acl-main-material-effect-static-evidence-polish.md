# 2026-06-06 ACL Main Material-Effect Static Evidence Polish

## Scope

Round 34 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 5 Results Section
4.3 transition immediately after Table 5, where the material-effect claim
boundary is explained before Figure 3.

## Change

- Replaced `Four covered bins carry selected three-condition static evidence`
  with `The audit provides static evidence only for the four covered bins`.
- Removed the rendered page-5 `three-` / `condition` split.
- Preserved the same claim boundary: the static evidence supports only the four
  covered bins, not clearcoat, procedural texture, or population-rate claims.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round34_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round34_after/contact_sheet.png`
- After focus sheet: `tmp/acl_main_visual_iter_20260606_round34_after/focus_p5_after.png`
- Pages 5-6 focus sheet: `tmp/acl_main_visual_iter_20260606_round34_after/focus_p5_p6_after.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round34_after/focus_before_after_p5.png`

Observed result: page 5 now renders the Table 5 transition without the old
`three-` / `condition` split. Page 5 column endings remain stable, and page 6
Figure 3 with its caption remains stable.

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
- Page-5 text extraction confirmed the old split in the current render and the
  new static-evidence sentence in the after render.

Final PDF identity:

- SHA256: `0bfba9b0b69f0d480f28b1202ec6535c1d23fdef18e8348c79763b4949074bff`
- Pages: 11
- Size: 5,188,704 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round34_material_effect_static_evidence_polish_20260606.json`
