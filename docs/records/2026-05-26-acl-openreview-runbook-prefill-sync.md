# ACL OpenReview Runbook Prefill Sync

Date: 2026-05-26

## Context

The ACL/ARR candidate already had a private author-gate initializer, a
repo-verifiable prefill helper, and a final blocker report. The human-facing
OpenReview upload runbook still described the older initializer-first workflow
and did not list the incomplete-private-worksheet state or the prefill refresh
command as part of the final handoff surface.

## Change

- Updated `OPENREVIEW_UPLOAD_RUNBOOK.md` so the current repository state covers
  both `private_author_gate_missing` and `private_author_gate_incomplete`.
- Added `prefill_author_gate.py --apply` to the creation path and
  `prefill_author_gate.py --apply --overwrite` to the final exact-packet
  refresh sequence.
- Added the prefill command to `report_final_blockers.py` required commands.
- Extended the runbook and final-blocker focused tests so future edits cannot
  silently drop the prefill handoff.

## Decision

The final safe sequence is:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
python paper/venues/acl27/scripts/prefill_author_gate.py --apply --overwrite
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/report_final_blockers.py
```

Authors still must fill the route, author, OpenReview profile, form-copy,
runtime/AI/license, optional-media, and final upload rows in the ignored local
worksheet. The prefill helper only synchronizes rows that are proven by the
repo-side staged packet and scans.

## Verification

TDD red check:

```bash
python -m pytest -q tests/test_acl_final_blockers.py::test_current_repo_reports_without_private_values tests/test_acl_openreview_upload_runbook.py::test_openreview_upload_runbook_covers_final_handoff_surface
```

Result: failed because the final blocker report did not list the prefill
command and the runbook did not contain `private_author_gate_incomplete` or the
prefill commands.

Focused green check after the change:

```bash
python -m pytest -q tests/test_acl_final_blockers.py::test_current_repo_reports_without_private_values tests/test_acl_openreview_upload_runbook.py::test_openreview_upload_runbook_covers_final_handoff_surface
```

Result: passed 2 tests.
