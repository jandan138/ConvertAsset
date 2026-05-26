# ACL Final-Integrity Fingerprint Gate

Date: 2026-05-26.

## Summary

Added a repository-side freshness gate for the ACL final-integrity audit. The
new checker records a deterministic SHA-256 fingerprint over the current ACL
manuscript, bibliography, OpenReview copy sources, target-policy notes,
reference web-trail, shared tables, and key CSV/JSON evidence files. The
pre-upload runner now fails before PDF build/staging if any of those sources
drift without a refreshed integrity pass.

This is not a new experiment and not a substitute for human citation-context,
data-claim, originality, or OpenReview form review. It prevents the already
completed integrity audit from silently becoming stale after a source edit.

## Changed Files

- Added `paper/venues/acl27/scripts/check_integrity_fingerprint.py`.
- Added `paper/venues/acl27/FINAL_INTEGRITY_SOURCE_FINGERPRINT.json`.
- Added `tests/test_acl_integrity_fingerprint.py`.
- Updated `paper/venues/acl27/scripts/run_preupload_gate.py` to run the
  fingerprint check after evidence-number consistency and before focused tests,
  clean build, and packet staging.
- Updated ACL status/checklist/audit docs to describe the new gate and the
  refreshed 34-test focused suite.

## Source Coverage

The current fingerprint covers 41 source files, including:

- ACL wrapper LaTeX source under `paper/venues/acl27/`;
- shared appendix and rendered table sources;
- `paper/shared/references.bib`;
- OpenReview metadata and Responsible NLP checklist copy sources;
- target-policy and route-lock notes;
- the reference verification web-trail;
- proxy, VLM, InternNav, official-scene, and material-effect CSV/JSON evidence.

## Verification

RED checks failed before implementation because the checker did not exist and
the pre-upload plan did not include `integrity_fingerprint`.

```bash
python -m pytest -q tests/test_acl_integrity_fingerprint.py tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging
```

GREEN checks after implementation:

```bash
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python -m pytest -q tests/test_acl_integrity_fingerprint.py tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging
python -m pytest -q tests/test_acl_submission_staging.py tests/test_paper_layout.py tests/test_acl_metadata_consistency.py tests/test_acl_claim_boundaries.py tests/test_acl_citation_inventory.py tests/test_acl_integrity_fingerprint.py tests/test_acl_evidence_numbers.py tests/test_acl_author_gate.py tests/test_acl_preupload_gate.py
```

The focused ACL pytest suite now passes 34 tests.

Full repository-side rehearsal:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The full runner completed claim-boundary, metadata,
citation-inventory, evidence-number, final-integrity fingerprint, 34-test
focused pytest, clean ACL build, LaTeX log scan, staging, packet inventory,
checksum-sidecar validation, private-token scan, acknowledgment scan,
`pdfinfo`, `pdf_profile`, and `pdftotext_sections`. The staged PDF is 12 A4
pages, PDF 1.5, 306187 bytes, and the staged packet remains the five-file safe
boundary.

## Remaining Gates

- The authors still need to choose EACL 2027 via ARR or wait for Annual ACL
  2027 official policy.
- The ignored private author worksheet still needs human completion.
- The official OpenReview form still needs final manual copy.
- Optional scene-derived videos remain excluded unless authors approve a
  separate media/legal path.
