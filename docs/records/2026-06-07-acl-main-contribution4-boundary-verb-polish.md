# 2026-06-07 ACL Main Contribution4 Boundary Verb Polish

## Summary

Round93 reviewed the current ACL main PDF after the Round92 first-page
stack-entry route polish. Contribution 4 still said `We group material and
stack checks in one gate`. The evidence boundary was correct, but `group` read
like a bookkeeping action rather than the paper's claim-bounding contribution.

## Changes

- Rewrote Contribution 4 in
  `paper/venues/acl27/sections/intro.tex` from `We group` to `We bound`.
- Kept the edit local to the contribution verb. No metrics, evidence pools,
  figures, tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- The first rewrite changed the phrase to `with one gate`, which rendered
  `material audit` as `au-` / `dit` and `repeated` as `re-` / `peated` in the
  left contribution column on page 2. The accepted rewrite keeps the original
  line structure and changes only the verb.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round93_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round93_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round93_after/page-02.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round93_contribution4_boundary_verb_polish_20260607.json`
- Final PDF hash:
  `c84e9cf106443c2d9b8431f0c9a0ec2a5498e79b3b913b552069462401c0e24f`

The accepted after screenshot shows Contribution 4 without new body-text
linebreak hyphenation. The PDF remains 10 pages. The enhanced after scan
reports only the existing explicit `human-subject` wording and normal
reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.33s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only the Contribution 4 verb on page 2. It did not change
metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
