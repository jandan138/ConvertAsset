# ACL Final Blocker Report

Date: 2026-05-26.

## Summary

Added a read-only final blocker reporter for the ACL/ARR candidate packet. The
new report separates repository-side blockers from human-only upload blockers
without printing private author worksheet values.

The report is intentionally not an upload approval. It shows whether the repo
evidence path is structurally ready and which human gates still block a real
OpenReview upload.

## Changed Files

- Added `paper/venues/acl27/scripts/report_final_blockers.py`.
- Added `tests/test_acl_final_blockers.py`.
- Updated `paper/venues/acl27/scripts/run_preupload_gate.py` so the
  consolidated pre-upload rehearsal prints the blocker report before focused
  tests/build/staging.
- Updated ACL status, readiness, checklist, and next-goal docs.

## Current Report

The current repository report is:

```json
{
  "upload_ready": false,
  "status": "human_blocked",
  "repo_blockers": [],
  "human_blockers": [
    "author_runtime_ai_media_approval_pending",
    "official_openreview_form_copy_pending",
    "private_author_gate_missing",
    "target_route_author_confirmation_pending"
  ]
}
```

This matches the current goal state: the repo-side packet rehearsal is strong,
but the final upload still requires author-only route, worksheet, OpenReview
form-copy, runtime/AI wording, and optional-media decisions.

## Verification

RED:

```bash
python -m pytest -q tests/test_acl_final_blockers.py
```

Failed because `report_final_blockers.py` did not exist.

GREEN:

```bash
python -m pytest -q tests/test_acl_final_blockers.py
python -m pytest -q tests/test_acl_final_blockers.py tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging
python paper/venues/acl27/scripts/report_final_blockers.py
```

The focused ACL pytest suite now includes the new blocker-report tests.

## Remaining Gates

- Fill the ignored private worksheet and pass `check_author_gate.py`.
- Choose EACL 2027 via ARR now, or wait for Annual ACL 2027 official policy.
- Copy metadata/checklist answers into the real OpenReview form.
- Rerun the full pre-upload gate on the exact final upload state.
