# 2026-06-07 ACL Main Intro Contribution4 Entry/Stability Polish

## Summary

Round106 reviewed the current ACL main PDF after the Round105 Method Gate 4
polish. The first target was the page-8 Limitations opener, which had a visible
sentence-break gap. Several variants removed that gap but created worse
column-flow regressions, including `con-` / `figured`, `visual-` / `QA`, and
`ex-` / `panded` splits. The Limitations source was restored.

The accepted change is on page 2 in the fourth contribution. The phrase
`bounded reliability claims` was broader than the actual evidence boundary,
which covers stack entry and load/run stability rather than reliability in the
general sense. The revision narrows the claim while keeping the contribution
readable in the ACL column.

## Changes

- Rewrote contribution 4 in `paper/venues/acl27/sections/intro.tex` from
  `bounded reliability claims` to `bounded entry and stability claims`.
- Kept the NVIDIA material audit, 99 KuJiaLe VLN episodes, repeated
  load/render checks, and the benchmark/speedup exclusion unchanged.
- Restored the page-8 Limitations opener after rejecting the column-flow
  candidates.
- Kept metrics, evidence pools, figures, tables, citations, metadata, and claim
  scopes unchanged.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round106_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round106_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round106_current/after/page-02.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round106_intro_contribution4_entry_stability_polish_20260607.json`
- Baseline PDF hash:
  `db5955e8151e6009827c829ef0cd0968fb13ccc74546bc53cb9491fb070875b2`
- Final PDF hash:
  `5e598fb9feb14a5bb8cf5231cb2a96a748a6fe24e8629461110ebbe972340707`

The accepted after screenshot shows contribution 4 reading
`They support bounded entry and stability claims, not broad benchmark or
speedup claims.` The page wraps cleanly across lines 92-94. The PDF remains 10
pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.56s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round narrowed one contribution phrase on page 2. It did not change
measured values, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes. The rejected page-8 Limitations trials were
restored and are not part of the accepted PDF.
