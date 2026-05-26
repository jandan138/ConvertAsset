# ACL Current-Commit Pre-Upload Gate

Date: 2026-05-26

## Purpose

Rerun the complete ACL/ARR pre-upload rehearsal after synchronizing the active
status, next-goal, final-checklist, and completion-audit documents to the
current `pdf_profile` gate vocabulary.

This was a verification and documentation pass, not a new experiment and not a
change to the manuscript claim surface.

## Command

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

## Result

The full gate passed.

Completed steps:

- claim-boundary check;
- OpenReview metadata consistency check;
- evidence-number consistency check;
- focused ACL pytest suite, 23 tests passed;
- clean ACL PDF build;
- final LaTeX log scan;
- candidate packet staging;
- exact five-file packet inventory check;
- local path/private-token scan;
- acknowledgment scan;
- `pdfinfo`;
- `pdf_profile`;
- `pdftotext_sections`.

The staged PDF remained within the current candidate profile:

- 12 pages;
- A4 page size;
- PDF version 1.5;
- 306187 bytes.

The staged packet still contained only:

```text
main.pdf
openreview/METADATA.md
openreview/RESPONSIBLE_NLP_CHECKLIST.md
supplemental/README.md
supplemental/manifest.json
```

## Remaining Gates

This pass strengthens current repository-side readiness but does not close the
human/external gates:

- final route decision: EACL 2027 via ARR versus waiting for Annual ACL 2027;
- official OpenReview form copy;
- private filled author worksheet;
- author/runtime/AI-assistance confirmation;
- optional media/legal decision;
- final target-policy refresh immediately before any real upload.
