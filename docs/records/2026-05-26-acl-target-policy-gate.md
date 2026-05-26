# ACL Target Policy Gate

Date: 2026-05-26.

## Summary

Added an automated local target-policy consistency gate for the ACL/ARR
candidate packet. The gate does not choose the venue for the authors. It checks
that the target-policy notes remain candidate-safe: EACL 2027 via ARR is
recorded as the current public 2027 ACL-family route, Annual ACL 2027 is not
marked final-ready, and the official policy source URLs and key route markers
remain present in the tracked policy notes.

This reduces the risk that a later edit accidentally turns the generic ACL/ARR
candidate packet into an unsupported Annual ACL 2027 final packet.

## Official Source Refresh

The implementation was checked against official public sources on 2026-05-26:

- ARR Dates lists the August 2026 cycle with August 3, 2026 as the submission
  date and lists EACL 2027 with final ARR submission date August 3, 2026 and
  commitment date October 11, 2026.
- ARR Authors Guidelines say submissions are made in OpenReview, require
  formatting templates, require all submitting authors to sign up as reviewers
  after submission, and make dual-submission / resubmission status author
  duties.
- EACL 2027's main-paper page lists August 3, 2026 AoE as the ARR submission
  deadline and says the comprehensive CFP and detailed timetable are still
  being finalized.
- ACLPUB formatting guidance gives the generic review-version long-paper
  budget, A4 requirement, plain metadata guidance, Limitations placement, and
  no acknowledgments in review versions.

## Changed Files

- Added `paper/venues/acl27/scripts/check_target_policy.py`.
- Added `tests/test_acl_target_policy.py`.
- Updated `paper/venues/acl27/scripts/run_preupload_gate.py` so the target
  policy gate runs before metadata, checklist, citation, evidence, build, and
  staging checks.
- Updated `paper/venues/acl27/scripts/report_final_blockers.py` so unsafe or
  missing target-policy notes become repo blockers.
- Updated ACL readiness, staging, and next-goal docs.

## Current Report

```json
{
  "ok": true,
  "route_status": "acl_arr_candidate",
  "annual_acl_final_ready": false,
  "eacl_arr_public_route": true,
  "missing_urls": [],
  "missing_required_markers": [],
  "forbidden_final_claim_hits": []
}
```

## Verification

RED:

```bash
python -m pytest -q tests/test_acl_target_policy.py
```

Failed because `check_target_policy.py` did not exist.

GREEN:

```bash
python -m pytest -q tests/test_acl_target_policy.py
python paper/venues/acl27/scripts/check_target_policy.py
python -m pytest -q tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging tests/test_acl_target_policy.py tests/test_acl_final_blockers.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

The consolidated gate passed after the target-policy check was inserted; its
focused pytest step now covers 45 tests, and the staged candidate PDF remains
12 A4 pages, PDF 1.5, and 306187 bytes.

## Remaining Gates

- Authors still need to choose EACL 2027 via ARR now, or wait for Annual ACL
  2027's official call.
- Re-open official venue pages again immediately before upload.
- Copy final metadata and checklist fields into the real OpenReview form after
  the route decision is locked.
