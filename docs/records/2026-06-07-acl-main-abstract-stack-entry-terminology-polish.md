# 2026-06-07 ACL Main Abstract Stack-Entry Terminology Polish

## Summary

Round89 reviewed the current ACL main PDF after the Round88 stack-entry gate
prose polish. The first-page abstract still described the 99-episode InternNav
evidence as a `sanity run`. That wording was accurate as a narrow gate, but it
was less precise than the stack-entry terminology now used in Results.

## Changes

- Rewrote the abstract phrase in
  `paper/venues/acl27/sections/abstract.tex` from `sanity run` to
  `stack-entry check`.
- Synchronized the matching abstract text in
  `paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md`.
- Kept the edit local to terminology. No metrics, evidence pools, figures,
  tables, citations, metadata fields other than the abstract text, or claim
  scopes were changed.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round89_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round89_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round89_after/page-01.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round89_abstract_stack_entry_terminology_polish_20260607.json`
- Final PDF hash:
  `7eb468adee807132e3db5d6371fc3125538bea48bc89774bb0c13c2e2de3f47f`

The accepted after screenshot shows the abstract line as
`stack-entry check over 99 episodes` without placing the explicit hyphen at a
line end. The PDF remains 10 pages. The enhanced after scan reports only the
existing explicit `human-subject` wording and normal reference-column
hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 15.45s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed and
  reported matching source/metadata abstracts with `abstract_word_count: 168`.

## Claim Boundary

This round changed only first-page abstract terminology and the corresponding
OpenReview metadata abstract. It did not change metrics, evidence pools,
figures, tables, citations, or supported/forbidden claim scopes.
