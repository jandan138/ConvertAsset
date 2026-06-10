# 2026-06-07 ACL Main Figure4 Stack-Entry Caption Polish

## Summary

Round100 reviewed the current ACL main PDF after the Round99 Results heading
polish. Page 9 Figure 4 still described the rollout evidence as
`Quantitative embodied-data claims`. The surrounding main paper now scopes the
same InternNav evidence as a selected stack-entry check, so the caption was the
next visible terminology mismatch.

## Changes

- Rewrote the Figure 4 caption in
  `paper/venues/acl27/sections/limitations.tex` from
  `Quantitative embodied-data claims` to `Quantitative stack-entry claims`.
- Kept the figure image, label, quantitative source, 99-episode paired run,
  official-scene load/render reference, citations, metadata, and claim boundary
  unchanged.

## Rejected Iterations

- A first Round100 target tried to rewrite the page-1 italic research question
  from `embodied-data claims` to stack-oriented wording. Four variants
  introduced worse visible line breaks, including `stack-` / `entry`,
  `con-` / `verted`, `an-` / `swer`, and `re-` / `liability`. Those attempts
  were reverted, leaving page 1 unchanged in the accepted after PDF.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round100_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round100_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round100_current/after/page-09.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round100_figure4_stack_entry_caption_polish_20260607.json`
- Baseline PDF hash:
  `7b2e044625a75cebfaa10ace6f3bdb8959d16f56f6ba61989065e69a6ddca645`
- Final PDF hash:
  `b3e8e3a48b94a67fb23c0939be6f8326d08c16cde05c362a05221ec319182b89`

The accepted after screenshot shows the Figure 4 caption as
`Quantitative stack-entry claims remain tied to the 99-episode paired run and
official-scene load/render checks.` The caption remains four lines, and the
Ethical Considerations and References starts are visually stable. The PDF
remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 17.91s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only one reader-facing figure caption phrase. It did not
change metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
