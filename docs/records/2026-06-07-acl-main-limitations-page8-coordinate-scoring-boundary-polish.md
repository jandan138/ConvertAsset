# 2026-06-07 ACL Main Limitations Page8 Coordinate Scoring Boundary Polish

## Summary

Round85 reviewed the current ACL main PDF after the Round84 Results
parser-coverage prose polish. The page-8 Limitations paragraph still said
`raw image-space scoring is stronger than the requested normalized-1000
interpretation`. The sentence named the right coordinate-semantics limitation,
but `stronger than` sounded like an evaluation preference instead of the
narrower fact that the two scoring interpretations disagree.

## Changes

- Rewrote the Limitations text in
  `paper/venues/acl27/sections/limitations.tex` to say
  `Qwen2.5-VL also leaves coordinate use open: raw image-space and
  normalized-1000 scores disagree`.
- Shortened the preceding clean-pool limitation from `cannot support a general
  claim that VLM grounding is preserved` to `does not support broad VLM
  grounding claims` to avoid a column-boundary orphan after the accepted
  coordinate-scoring rewrite.
- Protected the model name in source with `\mbox{Qwen2.5-VL}`.
- Kept the edit local to Limitations prose. No metrics, evidence pools,
  figures, tables, citations, metadata, or claim scopes were changed.

## Rejected Iterations

- The first rewrite removed `stronger than` but introduced visible page-8
  hyphenation: `Qwen2.5-` / `VL`, `unre-` / `solved`, `can-` / `not`, and
  `ground-` / `ing`.
- The second rewrite protected the model name and shortened the coordinate
  sentence, but still left `can-` / `not` at the page-8 column boundary.
- The third rewrite removed linebreak hyphenation but left a right-column
  opener that began with the isolated word `claim.`.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round85_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round85_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round85_after/page-08.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round85_limitations_page8_coordinate_scoring_boundary_polish_20260607.json`
- Final PDF hash:
  `224b7632bb00a5a25f43c6da91ca303b8cf7561c4003c8c23049e38760d6fa6a`

The accepted after screenshot shows the revised page-8 Limitations paragraph
without the previous ranking-like `stronger than` wording. The PDF remains 10
pages. The after text scan reports no line-end hyphenation candidates in the
extracted page text.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.30s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Limitations prose on page 8. It did not change metrics,
evidence pools, figures, tables, citations, metadata, or supported/forbidden
claim scopes.
