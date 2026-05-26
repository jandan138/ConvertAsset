# ACL Final Blocker Clearance Gate

Date: 2026-05-26.

## Summary

Updated the privacy-preserving final blocker report so the final upload state is
reachable in code. Previously, `report_final_blockers.py` always reported the
target-route, OpenReview-form, and runtime/AI/media gates as human blockers,
even in a simulated state where the private ignored author worksheet was fully
filled. That contradicted `NEXT_LARGE_GOAL.md`, whose definition of done
requires the final blocker report to be able to report no repo blockers and no
human blockers.

The report now keeps those human blockers while the private author worksheet is
missing or incomplete. Once `OPENREVIEW_AUTHOR_GATE_FILLED.local.md` is complete
and `check_author_gate.py` passes, the report can clear all human blockers
without printing any private author values.

## Behavior

- Current repository state is unchanged: without a filled private worksheet, the
  report remains `status=human_blocked` with `repo_blockers=[]`.
- A complete private worksheet can now make the report return
  `status=upload_ready` when repo evidence blockers are also clear.
- The filled worksheet remains ignored and untracked; the report exposes only
  blocker names and booleans, not author names, OpenReview IDs, emails, or
  submission-history details.

## Verification

RED:

```bash
python -m pytest -q tests/test_acl_final_blockers.py::test_completed_author_gate_can_clear_all_human_blockers
```

Failed because the report still returned `upload_ready=false` after a complete
private worksheet fixture.

GREEN:

```bash
python -m pytest -q tests/test_acl_final_blockers.py
python paper/venues/acl27/scripts/report_final_blockers.py
python -m pytest -q tests/test_acl_author_gate.py tests/test_acl_final_blockers.py tests/test_acl_preupload_gate.py
```

The focused tests pass, and the current real repository report remains
`status=human_blocked` until authors create and fill the ignored private
worksheet.
