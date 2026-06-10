# 2026-06-07 ACL Main Results Page5 Mechanism Question Prose Polish

## Summary

Round87 reviewed the current ACL main PDF after the Round86 Results task-question
prose polish. The page-5 Material Effects paragraph introduced the mechanism
bridge with `when evidence moves, which cue moved it?`. The sentence had useful
story movement, but the repeated `moves/moved` phrasing was more conversational
than the surrounding ACL claim-boundary prose.

## Changes

- Rewrote the Results transition in
  `paper/venues/acl27/sections/results.tex` to say
  `which cue changed the evidence?`
- Shortened the following comparison boundary to `only in checked bins` after
  the first rewrite introduced a visible `prove-` / `nance` split.
- Kept the edit local to Results prose. No metrics, evidence pools, figures,
  tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- The first rewrite changed the mechanism question but left the following
  sentence as `only for bins with bounded provenance`, which rendered as
  `prove-` / `nance` on page 5.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round87_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round87_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round87_after/page-05.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round87_results_page5_mechanism_question_prose_polish_20260607.json`
- Final PDF hash:
  `6ffb25f266907b729be2c5ab6f9898da1ef2eedddfed6388b4f7ed5e28b16ab5`

The accepted after screenshot shows the revised page-5 Material Effects opener
without body-text linebreak hyphenation. The PDF remains 10 pages. The enhanced
after scan reports only the existing explicit `human-subject` wording and
normal reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.25s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Results prose on page 5. It did not change metrics,
evidence pools, figures, tables, citations, metadata, or supported/forbidden
claim scopes.
