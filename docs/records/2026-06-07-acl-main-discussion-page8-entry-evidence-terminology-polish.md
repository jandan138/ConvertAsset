# 2026-06-07 ACL Main Discussion Page8 Entry Evidence Terminology Polish

## Summary

Round91 reviewed the current ACL main PDF after the Round90 Related/Limitations
stack-entry terminology polish. Discussion page 8 still used the loose phrase
`stack check` for the 99-episode KuJiaLe run. The claim boundary was already
narrow, but the term was less precise than the paper's current
`stack-entry`/`entry evidence` language.

## Changes

- Rewrote the Discussion boundary sentence in
  `paper/venues/acl27/sections/discussion.tex` from `it is a stack check` to
  `it gives entry evidence`.
- Kept the edit local to Discussion prose. No metrics, evidence pools, figures,
  tables, citations, metadata, or claim scopes were changed.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round91_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round91_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round91_after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round91_discussion_page8_entry_evidence_terminology_polish_20260607.json`
- Final PDF hash:
  `2ad195a00c2acb3f7981655d43897264bb88d94f4f383bd5da6cdcfc319f6c02`

The accepted after screenshot shows the revised Discussion sentence without new
body-text linebreak hyphenation. The PDF remains 10 pages. The enhanced after
scan reports only the existing explicit `human-subject` wording and normal
reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.23s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Discussion prose on page 8. It did not change metrics,
evidence pools, figures, tables, citations, metadata, or supported/forbidden
claim scopes.
