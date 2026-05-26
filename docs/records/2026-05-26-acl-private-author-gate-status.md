# ACL Private Author-Gate Status

Date: 2026-05-26.

## Context

The ACL/ARR final blocker report already separated repository blockers from
human blockers and printed `human_blocker_details`, but it did not expose the
current author-gate checker details in the top-level report. That made the
last-mile handoff less direct: the authors could see that the private worksheet
was incomplete, but not which safe field names were still missing, TODO, or
semantically invalid from the same final report.

## Design Decision

The report now includes a privacy-preserving `private_author_gate_status`
object. It carries only:

- checker booleans and relative worksheet path;
- counts for checked, missing, TODO, and invalid fields;
- missing/TODO/invalid field names from the tracked worksheet schema;
- git ignored/tracked status;
- the checker message;
- `prints_private_author_values=false`.

It deliberately does not carry filled worksheet values, author names, emails,
OpenReview IDs, private links, or private submission decisions. The detailed
field names are safe because they are the tracked worksheet schema, not the
authors' filled values.

## Code Changes

- `paper/venues/acl27/scripts/report_final_blockers.py`
  - Added `author_gate_report()` so the final blocker report calls the private
    checker once.
  - Added `safe_author_gate_status()` to project the checker output into a
    value-free status summary.
  - Added `private_author_gate_status` to the final blocker JSON.
- `paper/venues/acl27/scripts/report_goal_completion.py`
  - Propagates `private_author_gate_status` inside its `final_blockers` object.
- `tests/test_acl_final_blockers.py`
  - Covers an incomplete private worksheet with a private filled value, a TODO
    field, and a semantically invalid field, then asserts only field names and
    counts are reported.
- `tests/test_acl_goal_completion_report.py`
  - Checks that the goal-completion report carries the same safe status.

## Verification

RED:

```bash
python -m pytest -q tests/test_acl_final_blockers.py -q
python -m pytest -q tests/test_acl_goal_completion_report.py -q
```

The first test failed with `KeyError: 'private_author_gate_status'`; the second
failed because the goal-completion report did not yet forward that field.

GREEN:

```bash
python -m pytest -q tests/test_acl_final_blockers.py tests/test_acl_goal_completion_report.py
python paper/venues/acl27/scripts/report_final_blockers.py
python paper/venues/acl27/scripts/report_goal_completion.py
python paper/venues/acl27/scripts/run_preupload_gate.py
python paper/venues/acl27/scripts/prefill_author_gate.py --apply --overwrite
python paper/venues/acl27/scripts/check_author_gate.py
```

Results: 12 targeted tests passed. The final blocker and goal-completion JSON
reports include `private_author_gate_status` and continue to report
`status=human_blocked`, `repo_blockers=[]`, and
`prints_private_author_values=false`. The consolidated pre-upload gate passed
with 60 focused ACL tests, a 12-page A4 PDF 1.5 staged packet, and 306187 bytes
for `main.pdf`. The private worksheet prefill refreshed the eight
repo-verifiable rows. `check_author_gate.py` still exits 1 as expected because
25 human-only rows remain TODO and 13 approval rows remain semantically
invalid until the authors fill them.

## Remaining Gates

The repository is still not final-upload complete. The private worksheet must
be completed locally, the authors must lock the route and OpenReview form
decisions, and the exact upload state must pass the full pre-upload gate before
`report_goal_completion.py --preupload-gate-passed` can be used.
