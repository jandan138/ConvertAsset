# 2026-06-07 ACL Main Figure1 Caption Claim-Boundary Polish

## Summary

Round108 reviewed the current ACL main PDF after the Round107 Method Gate 1
opener polish. Page 2 Figure 1 had acceptable line flow, but its final caption
sentence still used reader-facing production wording: `empirical render,
material-effect, and navigation figures later in the paper use recorded project
artifacts.`

The accepted rewrite keeps Figure 1 as a schematic roadmap and assigns
empirical support to the later evidence figures without exposing internal
artifact-production wording.

## Changes

- Rewrote the final sentence of the Figure 1 caption in
  `paper/venues/acl27/sections/intro.tex`.
- Final accepted wording:
  `This panel is a schematic roadmap; later render, material-effect, and navigation figures carry the empirical claims.`
- Removed the reader-facing phrase `recorded project artifacts`.
- Kept the Figure 1 image, figure label, metrics, evidence pools, citations,
  metadata, and claim scopes unchanged.

## Evidence

- Baseline artifacts:
  `tmp/acl_main_visual_iter_20260607_round108_current/`
- After artifacts:
  `tmp/acl_main_visual_iter_20260607_round108_current/after/`
- Rendered after screenshot:
  `tmp/acl_main_visual_iter_20260607_round108_current/after/page-02.png`
- Raw evidence JSON:
  `paper/shared/evidence/raw/acl27_visual_review/main_round108_figure1_caption_claim_boundary_polish_20260607.json`
- Baseline PDF hash:
  `162bd09a9a1ce850aa53e428a2f95c502fdca331267664b252093607734ba34d`
- Final PDF hash:
  `ea46134a76a8dfa7c94bf73f79da848c7b5f858d1d419b8b5234c4d2f0f1b406`

The accepted after screenshot shows the Figure 1 caption still occupying four
lines on page 2. The final line now reads `material-effect, and navigation
figures carry the empirical claims.` The PDF remains 10 pages.

## Verification

- `make -C paper acl27` passed.
- LaTeX blocker scan over `paper/venues/acl27/build/main.log` passed with
  `no blocker matches`.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed in 14.01s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.

## Claim Boundary

This round changed one Figure 1 caption sentence on page 2. It did not change
the schematic itself, measured values, evidence pools, figures, tables,
citations, metadata, or supported/forbidden claim scopes.

## Residual Risk

The page-5 `result.    The official KuJiaLe val unseen` spacing remains
unchanged because earlier source-level attempts introduced worse line breaks.
