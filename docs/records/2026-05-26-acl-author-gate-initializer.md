# ACL Author-Gate Initializer

Date: 2026-05-26

## Context

The ACL/ARR candidate already had a blank tracked author-gate worksheet, a
filling guide, a private checker, and a final upload runbook. The remaining
weak point was the first private-file operation: authors still had to create
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md` by hand before filling private author,
route, OpenReview, runtime, AI-assistance, license, media, scan, and upload
decision fields.

## Change

- Added `paper/venues/acl27/scripts/init_author_gate.py`.
- Added `tests/test_acl_author_gate_init.py`.
- Added the initializer test to the focused pytest step inside
  `paper/venues/acl27/scripts/run_preupload_gate.py`.
- Updated `report_final_blockers.py` so the `private_author_gate_missing`
  handoff points authors to the initializer.
- Updated `OPENREVIEW_UPLOAD_RUNBOOK.md` and
  `OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md` to prefer the initializer before
  any private worksheet filling.
- Updated ACL status, final packet checklist, staging audit, and docs indexes.

## Behavior

The initializer creates the ignored local file:

```text
paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
```

from the blank tracked template:

```text
paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_WORKSHEET.md
```

It refuses to overwrite an existing private worksheet. By default it also runs
a git-ignore check and deletes the newly created file if the path is not
ignored. Its JSON report contains only path/status metadata and does not print
private worksheet values.

This change does not fill the private worksheet and does not close the active
human gates. It makes the first author-side operation safer and repeatable.

## Verification

TDD red checks were run before wiring the initializer into the existing
handoff:

```bash
python -m pytest -q tests/test_acl_author_gate_init.py
python -m pytest -q tests/test_acl_final_blockers.py::test_current_repo_reports_structured_human_handoff_details tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging tests/test_acl_openreview_upload_runbook.py
```

The first command failed until the initializer script existed. The second
command failed until the final blocker handoff, focused pre-upload pytest list,
and upload runbook mentioned the initializer.

Expected green checks after implementation:

```bash
python -m pytest -q tests/test_acl_author_gate_init.py tests/test_acl_final_blockers.py tests/test_acl_preupload_gate.py tests/test_acl_openreview_upload_runbook.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Actual result: the targeted suite passed 17 tests, and the consolidated
pre-upload gate passed with 52 focused ACL tests. The staged candidate PDF
remained 12 A4 pages, PDF 1.5, and 306187 bytes.

The consolidated gate remains a repository-side rehearsal. The real
author-gate checker is still expected to fail until authors create and fill the
ignored private worksheet locally.
