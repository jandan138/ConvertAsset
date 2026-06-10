# 2026-06-07 ACL Main Intro Page1 Stack-Entry Route Polish

## Summary

Round92 reviewed the current ACL main PDF after the Round91 Discussion
entry-evidence terminology polish. The first-page Introduction roadmap still
said the official InternNav run `checks stack use on noMDL scenes`. That wording
was understandable, but it was looser than the stack-entry claim boundary now
used in the abstract, Results, Related Work, Limitations, and Discussion.

## Changes

- Rewrote the Introduction roadmap sentence in
  `paper/venues/acl27/sections/intro.tex` to say the official
  `99-episode run tests noMDL stack entry`.
- Kept the edit local to first-page Introduction prose. No metrics, evidence
  pools, figures, tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- The first rewrite, `checks noMDL stack entry`, rendered `entry` as a visible
  `en-` / `try` split on page 1. The accepted rewrite changes the sentence
  structure to remove that line-width pressure.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round92_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round92_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round92_after/page-01.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round92_intro_page1_stack_entry_route_polish_20260607.json`
- Final PDF hash:
  `063db0dfff2b01b26d658e70bd626a7b7523158848981282d29d0f0e3942858d`

The accepted after screenshot shows the revised first-page roadmap sentence
without new body-text linebreak hyphenation. The PDF remains 10 pages. The
enhanced after scan reports only the existing explicit `human-subject` wording
and normal reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.18s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only first-page Introduction prose. It did not change
metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
