# 2026-06-10 ACL27 AI Text Audit Cleanup

## Context

The ACL27 paper text audit at
`paper/shared/evidence/reviews/ai-text-audit-20260610.md` found heavy
defensive, AI-like wording in the supplement and lighter traces in the main
paper. The main issues were repeated figure-caption disclaimers, the
`What This Supplement Does Not Prove` section, repeated `registered` source
watermarks, overuse of `deliberately` / `intentionally`, and broad `X, not Y`
sentence patterns.

## Changes

- Removed the `What This Supplement Does Not Prove` subsection from
  `paper/venues/acl27/sections/supplement/00_overview.tex`, including the two
  companion figure blocks that only illustrated exclusions.
- Rewrote supplement captions across derivations, VLM protocol, GRScenes,
  material, InternNav, theory, and reproducibility sections so they describe
  figure meaning instead of repeating disclaimer lists.
- Rewrote main-paper prose in abstract, introduction, method, results,
  discussion, limitations, ethics, and conclusion to use positive scope
  statements instead of repeated defensive negation.
- Updated Table 1 and related table captions to use natural scope language.
- Updated supplement figure generation scripts and regenerated the affected
  PNG figures so raster labels no longer contain the old disclaimer wording.
- Updated ACL tests that previously asserted the old disclaimer phrases, while
  preserving checks for figure presence, order, dimensions, density, and claim
  boundaries.
- Synchronized `OPENREVIEW_METADATA_PACKET.md` and
  `FINAL_INTEGRITY_SOURCE_FINGERPRINT.json`.

## Verification

- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_evidence_numbers.py` passed.
- `python paper/venues/acl27/scripts/check_integrity_fingerprint.py` passed.
- `python -m pytest tests/test_paper_layout.py tests/test_acl_claim_boundaries.py tests/test_acl_metadata_consistency.py tests/test_acl_integrity_fingerprint.py -q` passed with 99 tests.
- `make -C paper acl27 acl27-supplement` rebuilt `main.pdf` and
  `supplement.pdf`.
- `pdftotext` scans over the rebuilt PDFs found no audit-listed disclaimer
  phrases. The remaining `prompted for` match is the VLM experiment prompt
  description in Table S2, not figure-generation or manuscript-production
  wording.

## Notes

The visible paper text is clean against the audit phrase set. Internal file
names such as `fig_acl_method_chain_imagegen_v18.png` were left unchanged to
avoid structural churn; the production term does not appear in the rendered PDF
text.
