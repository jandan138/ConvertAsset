# ACL/ARR Submission Readiness Audit

Date: 2026-05-26.

## Purpose

Continue the ACL/ARR conversion goal after the ACL manuscript story pass by
checking the remaining external-policy and citation/provenance gates. This is a
documentation and audit pass, not a new experiment run.

## Files Added

- `paper/venues/acl27/SUBMISSION_READINESS_AUDIT.md`
- `paper/venues/acl27/CITATION_PROVENANCE_AUDIT.md`

## Official Sources Checked

- ARR Authors Guidelines: `https://aclrollingreview.org/authors`
- ARR CFP: `https://aclrollingreview.org/cfp`
- ARR Common Submission Problems: `https://aclrollingreview.org/authorchecklist`
- ACLPUB Formatting Guidelines: `https://acl-org.github.io/ACLPUB/formatting.html`
- ACLPUB Detailed Style Guide: `https://acl-org.github.io/ACLPUB/style.html`
- ARR Responsible NLP Checklist PDF: `https://aclrollingreview.org/static/responsibleNLPresearch.pdf`
- ARR checklist-as-appendix update: `https://aclrollingreview.org/responsible-nlp-checklist-appendices`
- EACL 2027 site: `https://2027.eacl.org/`

## Findings

- Public official Annual ACL 2027 CFP, author kit, commitment deadline,
  city/date page, and venue-specific supplemental policy were not found in this
  check. EACL 2027 is public, but it is not Annual ACL 2027.
- The current ACL wrapper is compatible with generic ARR/ACLPUB long-paper
  checks: anonymous review author line, no acknowledgments, Limitations and
  Ethical Considerations before references, A4 PDF, and main content ending
  within the generic 8-page long-paper review budget.
- The latest citation set has 20 unique ACL-wrapper citation keys. All are
  present in `paper/shared/references.bib` and the latest clean ACL build
  resolved citations.
- The bibliography is not yet final-submission normalized: many entries lack a
  DOI, URL, OpenReview/PMLR link, arXiv DOI/URL, or ACL Anthology fallback.
- Responsible NLP checklist mapping is partially prepared, but final checklist
  answers still need artifact licenses, compute/infrastructure, software/model
  version details, and AI-assistance disclosure.

## Verification Commands

Already run before this documentation pass:

```bash
git diff --check
python -m pytest -q tests/test_paper_layout.py tests/test_reviewer_closure_package.py tests/test_official_scene_submission_closure.py
make -C paper clean-acl27 && make -C paper acl27
pdfinfo paper/venues/acl27/build/main.pdf
pdftotext paper/venues/acl27/build/main.pdf - | rg -n "Limitations|Ethical Considerations|References"
```

Expected follow-up after this doc pass:

```bash
make -C paper acl27
git diff --check
```

## Remaining Gates

The active ACL/ARR goal should remain open until:

1. The final target venue policy is checked against the actual public call.
2. Citation/provenance identifiers are normalized.
3. Artifact-license and intended-use notes are complete.
4. Responsible NLP checklist answers are filled with section numbers and
   justifications.
5. A final anonymization audit covers the uploadable PDF and supplement.
