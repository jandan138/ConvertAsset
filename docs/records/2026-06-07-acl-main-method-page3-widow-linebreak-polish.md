# 2026-06-07 ACL Main Method Page 3 Widow Linebreak Polish

## Summary

Round75 reviewed the current 10-page ACL main PDF after the Round74
introduction contribution polish. Page 3 had a reader-visible Method layout
defect: the 3.1 heading wrapped as `Material Conversion as the` / `Intervention`,
and the preceding paragraph left a lone `promises.` at the top of the right
column.

## Changes

- Shortened the subsection title in `paper/venues/acl27/sections/method.tex`
  from `Material Conversion as the Intervention` to `Conversion as
  Intervention`.
- Rewrote the nearby MDL-semantics boundary paragraph with shorter method prose:
  it still states the PreviewSurface rewrite scope, declaring-layer path
  behavior, fixed-value fallback, and non-preserved MDL effects.
- Rejected intermediate rewrites that moved the orphan word or introduced new
  page-3 breaks such as `tex-`, `re-`, `procedu-`, and a trailing one-word
  `claims.` line.
- Kept the edit local to Method prose. No evidence values, tables, figures,
  citations, metadata, or claim scopes were changed.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round75_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round75_after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round75_after/page-03.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round75_method_page3_widow_linebreak_polish_20260607.json`
- Final PDF hash:
  `21cc21528dc6441d60562ad2d1e3f21f8108a33f6e0726a07b01fd46b3a5890c`

The accepted after scan removes the page-3 Method heading wrap and the
`promises.` widow. The full after scan reports only the pre-existing Related
Work compound break `sim-to-` and normal bibliography-column hyphenation.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed only Method prose and linebreak behavior. It did not change
metric values, evidence pools, figures, citations, metadata, or
supported/forbidden claim scopes.
