# ACL Final-Blocker Required Commands

Date: 2026-05-26

## Context

The ACL/ARR candidate already had a guarded private author-gate initializer,
checker, final blocker report, and OpenReview upload runbook. The runbook told
authors to initialize the ignored private worksheet before checking it, but the
machine-readable final blocker report only listed the checker and consolidated
pre-upload gate under `required_commands`.

## Change

- Updated `paper/venues/acl27/scripts/report_final_blockers.py` so
  `required_commands` now lists:

```bash
python paper/venues/acl27/scripts/init_author_gate.py
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

- Added a regression assertion in `tests/test_acl_final_blockers.py`.
- Updated ACL status, final packet checklist, and staging audit notes.

## Boundary

This is a handoff/reporting fix. The consolidated repository-side gate does not
execute `init_author_gate.py`, because that command creates an ignored private
local worksheet. The author worksheet remains outside git and outside the
review packet.

The active ACL/ARR package remains `human_blocked`, not repo-blocked: authors
still need to choose the final route, fill the official OpenReview form, fill
the private author gate, confirm runtime/AI/license/media decisions, and rerun
the final checks on the exact upload state.

## Verification

TDD red check:

```bash
python -m pytest -q tests/test_acl_final_blockers.py::test_current_repo_reports_human_blockers_without_private_values
```

It failed until `init_author_gate.py` was added to `required_commands`.

Final verification:

```bash
python -m pytest -q tests/test_acl_final_blockers.py tests/test_acl_author_gate_init.py
python paper/venues/acl27/scripts/run_preupload_gate.py
git diff --check
```

The targeted suite passed 10 tests. The consolidated pre-upload gate passed
with 53 focused ACL tests, the final blocker report showed the three required
commands in order, and the staged candidate PDF remained 12 A4 pages, PDF 1.5,
and 306187 bytes.
