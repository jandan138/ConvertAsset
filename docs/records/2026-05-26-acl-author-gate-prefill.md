# ACL Author-Gate Prefill

Date: 2026-05-26

## Context

The ACL/ARR candidate already had an ignored private author-gate worksheet and
machine-readable blocker reports. After initializing the local worksheet, the
remaining checker output mixed human-only decisions with final pre-upload
evidence rows that the repository can prove from the staged packet and
pre-upload gate.

## Change

- Added `paper/venues/acl27/scripts/prefill_author_gate.py`.
- Added `tests/test_acl_author_gate_prefill.py`.
- Added the prefill tests to the consolidated `run_preupload_gate.py` focused
  pytest suite.
- Updated final-blocker next actions so an incomplete private worksheet points
  authors to `prefill_author_gate.py --apply` before manual completion.
- Documented the command in the author-gate filling guide, final packet
  checklist, status page, and staging audit.

## Behavior

The helper only fills repo-verifiable final evidence rows in the ignored local
worksheet:

- clean build / pre-upload command evidence;
- final PDF page count, page size, PDF version, and file size;
- citation/reference scan;
- staging command and packet path;
- staged file list;
- private-token scan;
- acknowledgment scan;
- required PDF text-section scan.

It intentionally does not fill author names, route choice, OpenReview profile
readiness, reviewer registration, dual-submission state, OpenReview form-copy
approval, runtime/AI/license approvals, optional media decision, or final upload
decision.

In this workspace the command was applied to
`paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md`, which remains
git-ignored. `check_author_gate.py` still fails, but the TODO list is reduced to
human-only rows.

## Verification

TDD red check:

```bash
python -m pytest -q tests/test_acl_author_gate_prefill.py
```

It failed until `prefill_author_gate.py` existed.

Focused green checks:

```bash
python -m pytest -q tests/test_acl_author_gate_prefill.py
python -m pytest -q tests/test_acl_final_blockers.py::test_incomplete_private_author_gate_reports_completion_handoff tests/test_acl_author_gate_prefill.py tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging
```

Results: the prefill suite passed 2 tests; the blocker-handoff plus preupload
plan checks passed 4 tests.

Local application and blocker audit:

```bash
python paper/venues/acl27/scripts/prefill_author_gate.py --apply
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/report_goal_completion.py
git status -sb --ignored=matching paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
```

Results: the prefill command changed only the 8 repo-verifiable rows and did
not print private worksheet values; `check_author_gate.py` still reports
`ok=false` because human rows remain; the goal report remains
`candidate_ready_human_blocked`; git reports the filled local worksheet as
ignored.
