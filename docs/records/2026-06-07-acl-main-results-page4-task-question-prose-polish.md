# 2026-06-07 ACL Main Results Page4 Task Question Prose Polish

## Summary

Round86 reviewed the current ACL main PDF after the Round85 Limitations
coordinate-scoring boundary polish. The page-4 Results paragraph introduced the
expanded stress set with `asks the stronger question`. The sentence was
bounded, but `stronger` was a vague comparative adjective where the paper's
story is more precise: the stress set moves from proxy similarity to the task
question.

## Changes

- Rewrote the Results transition in
  `paper/venues/acl27/sections/results.tex` from `asks the stronger question`
  to `moves to the task question`.
- Kept the stress-set prompt contract and all reported counts unchanged.
- Kept the edit local to Results prose. No metrics, evidence pools, figures,
  tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- The first rewrite changed `stronger question` to `grounding question`, but
  the rendered page split the word across lines as `ground-` / `ing`.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round86_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round86_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round86_after/page-04.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round86_results_page4_task_question_prose_polish_20260607.json`
- Final PDF hash:
  `d0d7117740b1e10a6124c85724783f7f2dfda98b8fc60401e24114e85b9b07c8`

The accepted after screenshot shows the revised page-4 right-column sentence as
`The expanded stress set moves to the task question`. The PDF remains 10 pages.
The enhanced after scan reports only the existing explicit `human-subject`
wording and normal reference-column hyphenation on pages 9-10; it reports no
new page-4 body-text linebreak hyphenation.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.40s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Results prose on page 4. It did not change metrics,
evidence pools, figures, tables, citations, metadata, or supported/forbidden
claim scopes.
