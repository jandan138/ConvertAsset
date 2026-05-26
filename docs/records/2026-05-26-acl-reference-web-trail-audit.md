# ACL Reference Web-Trail Audit

Date: 2026-05-26

## Purpose

Move the ACL/ARR citation gate from build-clean and DOI/URL-present to a
reference-by-reference web-trail audit for the current ACL wrapper. This was a
paper-integrity pass, not a new experiment.

## Changes

- Added a 2026-05-26 ACL-wrapper addendum to
  `paper/shared/evidence/references/verification_report.md`.
- Updated `paper/venues/acl27/CITATION_PROVENANCE_AUDIT.md`.
- Normalized `paper/shared/references.bib` for four references:
  `Singh2025Synthetica`, `Tobin2017Domain`, `Tremblay2018Training`, and
  `Zakharov2022Photo`.
- Updated `paper/venues/acl27/GOAL_COMPLETION_AUDIT.md` and `STATUS.md` to
  distinguish the now-closed reference-existence web trail from the remaining
  final citation-context/data/originality gate.

## Findings

- The current ACL wrapper cites 20 unique bibliography keys.
- All 20 were verified against concrete source URLs: arXiv, CVF, OpenReview,
  PMLR, NeurIPS Datasets and Benchmarks, ETH Research Collection,
  CiNii/Crossref-backed records, J-GLOBAL, Springer, ECVA, DBLP, or DOI
  redirects.
- No fabricated-reference finding was found for the current ACL-wrapper
  bibliography.
- This does not close the final submission integrity gate by itself: any future
  manuscript or bibliography change still needs citation-context, data-claim,
  originality, clean-build, and upload-packet checks.

## Verification To Run After This Pass

```bash
git diff --check
make -C paper acl27
```
