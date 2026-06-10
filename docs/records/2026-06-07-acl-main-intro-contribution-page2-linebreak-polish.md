# 2026-06-07 ACL Main Intro Contribution Page 2 Linebreak Polish

## Summary

Round74 reviewed the ACL main PDF after the Round73 Related Work polish and
targeted page 2 of the introduction. The contribution list was semantically
correct, but two items ended narrow list lines with awkward automatic breaks:
`coordinate-` in contribution 2 and `embodied-` in contribution 4.

## Changes

- Shortened contribution 2 in `paper/venues/acl27/sections/intro.tex` from
  `coordinate-frame scoring` to `coordinate scoring`.
- Rewrote contribution 4 into a shorter claim-gate sentence that still names
  the material audit, 99 KuJiaLe VLN episodes, and repeated load/render checks.
- Rejected intermediate rewrites that traded the original issue for new splits
  such as `san-`, `se-`, `offi-`, `sup-`, `Ku-`, `au-`, and `re-`.
- Kept the edit local to introductory contribution wording. No evidence values,
  tables, figures, citations, metadata, or claim scopes were changed.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round74_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round74_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round74_after/page-02.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round74_intro_contribution_page2_linebreak_polish_20260607.json`
- Final PDF hash:
  `5cabab838bf41286b0010833c1a1fa303a2377b87fc738bd921f593dba55827d`

The accepted after scan found no alphabetic hyphenated line-end tokens on page
2. Page 3 still reports the unrelated literal compound `sim-to-`, which is
outside this round's target.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Introduction contribution prose and linebreak behavior.
It did not change metric values, evidence pools, figures, citations, metadata,
or supported/forbidden claim scopes.
