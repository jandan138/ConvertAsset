# ACL Final Blocker Handoff Details

Date: 2026-05-26.

## Summary

Expanded the privacy-preserving ACL final blocker report so the remaining
human blockers are not just names. The report now includes
`human_blocker_details`, keyed by blocker id, with:

- `required_action`: what the author/operator must do next;
- `worksheet_fields`: which private worksheet rows prove the decision;
- `copy_sources`: which tracked repository files provide the copy source or
  supporting evidence;
- `done_when`: the concrete condition that clears the blocker.

This makes the final OpenReview handoff more executable without adding private
author data to the repository.

## Behavior

- Current repository state remains `status=human_blocked` with
  `repo_blockers=[]`, because the ignored private worksheet is not present.
- The four active human blockers now point to exact worksheet rows and source
  files:
  - `private_author_gate_missing`;
  - `target_route_author_confirmation_pending`;
  - `official_openreview_form_copy_pending`;
  - `author_runtime_ai_media_approval_pending`.
- The report still does not print author names, OpenReview IDs, emails,
  private submission links, or private worksheet values.
- A completed private worksheet still clears the human blocker list and returns
  an empty `human_blocker_details` object.

## Verification

RED:

```bash
python -m pytest -q tests/test_acl_final_blockers.py
```

The new handoff-detail tests failed with `KeyError: 'human_blocker_details'`.

GREEN:

```bash
python -m pytest -q tests/test_acl_final_blockers.py
python paper/venues/acl27/scripts/report_final_blockers.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

The focused blocker tests pass, and the current report prints structured
handoff details while keeping private values out of the JSON. The consolidated
pre-upload gate also passes with 49 focused ACL tests; the staged PDF remains
12 A4 pages, PDF 1.5, and 306187 bytes.

## Remaining Gates

- Authors still need to create and fill
  `paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md`.
- Authors still need to choose the final route, copy the official OpenReview
  form fields, approve runtime/AI/license/media wording, and run the final
  pre-upload gate on the exact upload state.
