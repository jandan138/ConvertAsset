# 2026-06-07 ACL Main Intro Page1 Gate Question Polish

## Summary

Round101 reviewed the current ACL main PDF after the Round100 Figure 4 caption
polish. Page 1 still asked what evidence is needed for `grounding or
embodied-data claims`. That phrase was now out of step with the main-paper
stack-entry framing and the cleaned Figure 4 caption.

## Changes

- Rewrote the page-1 Introduction evidence question in
  `paper/venues/acl27/sections/intro.tex` as a gate question:
  converted assets must clear grounding and stack checks rather than rely on a
  single proxy score.
- Shortened the GRScenes setup sentence from `evaluation runs may combine...`
  to `runs combine...`, avoiding broad embodied-data wording and reducing
  narrow-column line pressure.
- Protected `InternNav` and `DualVLN` with `\mbox{}` in the revised sentence so
  the model/route names do not break across lines.
- Kept metrics, evidence pools, figures, tables, citations, metadata, and claim
  scopes unchanged.

## Rejected Iterations

- `grounding or stack-entry checks` was rejected because it rendered as
  `stack-` / `entry` and pushed later text into `re-` / `liability`.
- `support grounding or stack checks` was rejected because it rendered
  `an-` / `swer` and `re-` / `liability`.
- `grounding claims or stack checks` was rejected because it rendered
  `con-` / `verted`.
- Several `which gates must hold` variants were rejected before the final
  wording because they rendered `be-` / `fore`, `eval-` / `uation`,
  `navi-` / `gation`, `Du-` / `alVLN`, or `In-` / `ternNav`.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round101_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round101_current/after/`
- Rendered after screenshots:
  `tmp/acl_main_visual_iter_20260607_round101_current/after/page-01.png`
  and
  `tmp/acl_main_visual_iter_20260607_round101_current/after/page-02.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round101_intro_page1_gate_question_polish_20260607.json`
- Baseline PDF hash:
  `b3e8e3a48b94a67fb23c0939be6f8326d08c16cde05c362a05221ec319182b89`
- Final PDF hash:
  `dabb2125c36b50da3752bad2ff174de2f6b742faad1203034d313e50122b81eb`

The accepted after screenshot shows the page-1 right-column question as:
`We therefore ask which gates must hold as converted assets move into grounding
and stack checks, because a single proxy score is not enough.` Page 2 was also
checked because the shorter paragraph pulls the contribution list upward. The
Figure 1 area, caption, contribution list, and Related Work start remain
visually stable. The PDF remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 13.19s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.
- PDF text scan found no reader-visible `embodied-data`, `sanity`, or
  production-wording terms in the accepted after artifact.

## Claim Boundary

This round changed only Introduction prose on page 1. It did not change
metrics, evidence pools, figures, tables, citations, metadata, or
supported/forbidden claim scopes.
