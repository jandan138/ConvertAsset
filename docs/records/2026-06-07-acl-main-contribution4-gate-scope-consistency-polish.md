# 2026-06-07 ACL Main Contribution4 Gate-Scope Consistency Polish

## Summary

Round95 reviewed the current ACL main PDF after the Round94 Contribution 3
terminology polish. Contribution 4 said material and stack checks were kept
`in one gate`, while the method section defines material effects and
embodied-stack entry as separate evidence gates. That wording made the
contribution list less consistent with the gate registry.

## Changes

- Rewrote Contribution 4 in
  `paper/venues/acl27/sections/intro.tex` from `in one gate` to
  `scoped to an NVIDIA material audit, 99 KuJiaLe VLN episodes, and repeated
  load/render checks`.
- Replaced `This gate supports` with `They support` so the sentence refers to
  the scoped checks rather than collapsing Gate 3 and Gate 4 into one gate.
- Kept the edit local to Contribution 4 prose. No metrics, evidence pools,
  figures, tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- The first direct fix used `claim-bounded` and introduced visible page-2
  contribution-column hyphenation: `claim-` / `bounded` and `sup-` / `port`.
- A shorter `scoped:` version removed the hyphenation but produced a visibly
  stretched line in the narrow contribution column.
- The accepted rewrite uses `scoped to` so the contribution reads as one
  continuous evidence sentence without new linebreak defects.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round95_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round95_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round95_current/after/page-02.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round95_contribution4_gate_scope_consistency_polish_20260607.json`
- Final PDF hash:
  `cf0e5e64c83aa10fbb2454e13b1219b6d39a19ce40a98fccdfc374820ab2355d`

The accepted after screenshot shows Contribution 4 without the rejected
hyphenation or stretched-line regressions. The PDF remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.43s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Contribution 4 prose on page 2. It did not change
metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
