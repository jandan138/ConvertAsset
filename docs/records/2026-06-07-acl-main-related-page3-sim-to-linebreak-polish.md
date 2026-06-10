# 2026-06-07 ACL Main Related Page 3 Sim-To Linebreak Polish

## Summary

Round76 continued the page-3 polish after Round75. The remaining body-text
break was in the Related Work paragraph `Synthetic rendering shifts`, where
`Prior sim-to-real work` rendered as `Prior sim-to-` / `real work` at the top of
the left column.

## Changes

- Reworded the first sentence in `paper/venues/acl27/sections/related.tex` from
  `Prior sim-to-real work` to `Prior transfer work`.
- Added a local no-hyphen paragraph group for this short Related Work paragraph
  so TeX avoids trading one visible compound break for multiple ordinary-word
  breaks in the narrow column.
- Preserved the paragraph's role and citations: prior rendering/transfer work
  motivates the setup, and the paper's case remains narrower because MDL is
  rewritten while scene content and task labels stay fixed.
- Rejected intermediate rewrites that introduced `simula-`, `Trem-`, `pro-`,
  `ren-`, `Preview-`, `as-`, `Ran-`, `trans-`, and `mod-` breaks.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round76_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round76_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round76_after/page-03.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round76_related_page3_sim_to_linebreak_polish_20260607.json`
- Final PDF hash:
  `07dda1650cc081cd25bee0945c81f2cec02e944f94d4f30ae787866a486d1937`

The accepted after scan removes the page-3 Related Work body-text hyphenation.
The full after scan reports only normal bibliography-column hyphenation on
pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Related Work prose and local linebreak behavior. It did
not change metric values, evidence pools, figures, citations, metadata, or
supported/forbidden claim scopes.
