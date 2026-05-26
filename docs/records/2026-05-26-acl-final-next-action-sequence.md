# ACL Final Next-Action Sequence

Date: 2026-05-26

## Context

The OpenReview upload runbook already documented the final exact-packet
sequence:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
python paper/venues/acl27/scripts/prefill_author_gate.py --apply --overwrite
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/report_final_blockers.py
```

However, the machine-readable `next_actions` emitted by
`report_final_blockers.py` still used the older shorthand that mentioned only
`check_author_gate.py` and `run_preupload_gate.py`.

## Change

`report_final_blockers.py` now emits the same final sequence in its last
`next_actions` item: run the full pre-upload gate, refresh repo-verifiable
private worksheet evidence with `prefill_author_gate.py --apply --overwrite`,
then run the private author checker and final blocker reporter.

Because `report_goal_completion.py` forwards final-blocker next actions, the
goal-completion report now carries the same exact-packet sequence.

## Boundary

This is a handoff/reporting change only. It does not make the repository fill
author-only fields and it does not make the active ACL/ARR goal complete. The
package remains `candidate_ready_human_blocked` until authors complete the
ignored private worksheet, copy the official OpenReview form fields, confirm
route/runtime/AI/license/media decisions, and rerun the final gates.

## Verification

TDD red check:

```bash
python -m pytest -q tests/test_acl_final_blockers.py::test_incomplete_private_author_gate_reports_completion_handoff tests/test_acl_goal_completion_report.py::test_current_repo_reports_static_candidate_ready_but_not_complete
```

Result: failed because neither report contained
`prefill_author_gate.py --apply --overwrite` in `next_actions`.

Focused green check after the change:

```bash
python -m pytest -q tests/test_acl_final_blockers.py::test_incomplete_private_author_gate_reports_completion_handoff tests/test_acl_goal_completion_report.py::test_current_repo_reports_static_candidate_ready_but_not_complete
```

Result: passed 2 tests.
