# 2026-06-07 ACL Main Related/Limitations Stack-Entry Terminology Polish

## Summary

Round90 reviewed the current ACL main PDF after the Round89 abstract
stack-entry terminology polish. The abstract and Results now used
`stack-entry` language, but Related Work and Limitations still described the
KuJiaLe evidence as a `sanity check`. This round removed the remaining
main-text `sanity check` labels while keeping the embodied-navigation boundary
narrow.

## Changes

- Rewrote the Related Work KuJiaLe sentence in
  `paper/venues/acl27/sections/related.tex` to use `entry evidence` rather than
  `sanity check`.
- Rewrote the Limitations sentence in
  `paper/venues/acl27/sections/limitations.tex` to use `stack-entry check` over
  the three KuJiaLe `val_unseen` scenes and 99 paired episodes.
- Kept the edit local to prose terminology. No metrics, evidence pools,
  figures, tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- `The official KuJiaLe stack-entry check uses...` rendered `official` as a
  visible `offi-` / `cial` split on page 2.
- `matched source/noMDL scenes give stack-entry evidence` rendered
  `stack-` / `entry` on page 2.
- `matched source/noMDL scenes give stack entry evidence` rendered
  `en-` / `try` on page 2.
- `matched source/noMDL scenes give entry evidence` rendered
  `ev-` / `idence` on page 2.
- The accepted Related Work wording shortens the sentence to fit the narrow
  right column while preserving the claim boundary.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round90_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round90_after/`
- Rendered after screenshots:
  `tmp/acl_main_visual_iter_20260607_round90_after/page-02.png`,
  `tmp/acl_main_visual_iter_20260607_round90_after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round90_related_limitations_stack_entry_terminology_polish_20260607.json`
- Final PDF hash:
  `c4a7e550b14a0f7a9ee3b9fc63bb824bcf00da694fa31cf26de4bb895557e602`

The accepted after screenshots show page-2 Related Work and page-8 Limitations
without new body-text linebreak hyphenation. The PDF remains 10 pages. The
enhanced after scan reports only the existing explicit `human-subject` wording
and normal reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.11s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Related Work and Limitations prose. It did not change
metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
