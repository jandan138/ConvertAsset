# ACL Goal-Completion Report

Date: 2026-05-26

## Context

The ACL/ARR candidate had a human-readable `GOAL_COMPLETION_AUDIT.md` and a
machine-readable `report_final_blockers.py`, but there was no single JSON report
that mapped the active paper objective to current static repo readiness plus
remaining final-upload blockers.

## Change

- Added `paper/venues/acl27/scripts/report_goal_completion.py`.
- Added `tests/test_acl_goal_completion_report.py`.
- Added the reporter to `run_preupload_gate.py` after the final blocker report.
- Added the new focused test file to the consolidated pre-upload pytest suite.
- Updated status, goal-completion, final checklist, next-goal, and staging
  documents.

## Behavior

The reporter calls the existing lightweight checks for:

- claim boundaries;
- evidence-number consistency;
- citation inventory;
- OpenReview metadata/checklist copy sources;
- target-policy safety;
- final-integrity fingerprint;
- final blocker clearance.

The current report is intentionally not `complete`:

```text
status=candidate_ready_human_blocked
repo_static_ready=true
candidate_ready_for_human_gate=true
final_goal_complete=false
repo_requirement_failures=[]
```

It also carries the final blocker command handoff:

```bash
python paper/venues/acl27/scripts/init_author_gate.py
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

The `--preupload-gate-passed` flag exists only for the exact moment after
`run_preupload_gate.py` has passed on the same working tree. It prevents the
static reporter from silently replacing the full clean build/staging/PDF scan
gate.

## Verification

TDD red check:

```bash
python -m pytest -q tests/test_acl_goal_completion_report.py
```

It failed until `report_goal_completion.py` existed. After the minimal
implementation, the focused reporter tests passed 2 tests.

The pre-upload plan was then updated by first extending
`tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging`;
that test failed until the `goal_completion_report` step and focused test file
were added to `run_preupload_gate.py`.

Final verification:

```bash
python -m pytest -q tests/test_acl_goal_completion_report.py tests/test_acl_preupload_gate.py
python paper/venues/acl27/scripts/report_goal_completion.py
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Results: the targeted suite passed 9 tests; the goal-completion reporter
returned `status=candidate_ready_human_blocked`, `repo_static_ready=true`,
`candidate_ready_for_human_gate=true`, `repo_requirement_failures=[]`, and
`final_goal_complete=false`; the 41-source final-integrity fingerprint passed;
and the consolidated pre-upload gate passed with 55 focused ACL tests, a
12-page A4 PDF 1.5 staged packet, and 306187 bytes for `main.pdf`.
