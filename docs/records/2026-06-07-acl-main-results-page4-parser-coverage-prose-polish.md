# 2026-06-07 ACL Main Results Page4 Parser Coverage Prose Polish

## Summary

Round84 reviewed the current ACL main PDF after the Round83 Discussion
contract-evidence prose polish. The page-4 Results paragraph described
Qwen2.5-VL as `weaker on parser coverage` when the evidence being reported was
the narrower fact that it had fewer scorable answer rows under the parser. The
sentence was numerically correct, but the adjective sounded more model-ranking
like than the local parser-coverage claim.

## Changes

- Rewrote the Results sentence in
  `paper/venues/acl27/sections/results.tex` from `Qwen2.5-VL is weaker on
  parser coverage` to `Qwen2.5-VL has lower parser coverage`.
- Kept all reported counts unchanged: 23/30 scorable answer rows, raw point
  hits of 5/14 and 5/15, and zero normalized-1000 point hits in both
  conditions.
- Kept the edit local to Results prose. No metrics, evidence pools, figures,
  tables, citations, metadata, or claim scopes were changed.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round84_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round84_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round84_after/page-04.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round84_results_page4_parser_coverage_prose_polish_20260607.json`
- Final PDF hash:
  `1c0b271cd3c2747c3750bb1eade028a642aa6d0858d06c2f6b8173fb89e19dd8`

The accepted after screenshot shows the revised page-4 right-column sentence
without body-text linebreak hyphenation. The PDF remains 10 pages. The strict
hyphenation scan reports only the existing explicit `human-subject` wording and
normal reference-column hyphenation on pages 9-10.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.35s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Results prose on page 4. It did not change metrics,
evidence pools, figures, tables, citations, metadata, or supported/forbidden
claim scopes.
