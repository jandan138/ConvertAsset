# ACL Citation And Provenance Closure Pass

Date: 2026-05-26.

## Purpose

Continue the ACL/ARR-ready goal by closing the most concrete citation and
Responsible NLP checklist gaps left after the submission-readiness audit.

## Changes

- Added DOI and/or URL metadata to all 20 citation keys currently used by the
  ACL wrapper.
- Added `paper/venues/acl27/RESPONSIBLE_NLP_CHECKLIST_DRAFT.md`.
- Added `paper/venues/acl27/ARTIFACT_PROVENANCE_DRAFT.md`.
- Updated ACL status and claim-audit files to point at these new artifacts.
- Updated `CITATION_PROVENANCE_AUDIT.md` and `SUBMISSION_READINESS_AUDIT.md`
  so they no longer describe citation URLs as wholly missing.

## Source Checks

Public/primary-ish sources checked in this pass included arXiv pages, CVF open
access pages, PMLR, OpenReview, NeurIPS Datasets and Benchmarks proceedings,
Hugging Face model cards, GRUtopia package/project pages, the InteriorAgent
dataset page, and the InternNav repository. The audit remains conservative:
InteriorAgent/KuJiaLe full terms text and the exact public Gemma4 quantized
checkpoint/commit still require final human confirmation.

## Remaining Gates

- Official Annual ACL 2027 call/author kit is still not public in the checked
  sources.
- Gemma4 local checkpoint must be matched to an exact public model page,
  commit/hash, and license.
- InteriorAgent/KuJiaLe dataset license and preferred citation must be checked
  before packaging supplemental media.
- Final ARR checklist still needs exact section/page/line references and a
  concise compute/runtime version summary.
