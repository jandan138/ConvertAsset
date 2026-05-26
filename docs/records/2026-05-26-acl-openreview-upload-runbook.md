# ACL OpenReview Upload Runbook

Date: 2026-05-26.

## Summary

Added a final human-facing upload runbook for the ACL/ARR candidate packet at
`paper/venues/acl27/OPENREVIEW_UPLOAD_RUNBOOK.md`.

The runbook consolidates the last private/manual submission actions without
recording private values:

- create and validate the ignored private author worksheet;
- lock the route;
- copy OpenReview metadata and Responsible NLP checklist fields;
- record author, runtime, AI-assistance, license, media, scan, and final upload
  decisions;
- run the final author gate, blocker report, and consolidated pre-upload gate;
- stop if any blocker or privacy leak appears.

## Behavior

This does not close the active ACL/ARR goal. It makes the remaining human gates
more executable while preserving the existing safety boundary:

- `OPENREVIEW_AUTHOR_GATE_FILLED.local.md` remains ignored and untracked.
- The runbook does not contain author names, OpenReview IDs, emails, or private
  submission-history links.
- The expected upload-ready state remains `repo_blockers=[]`,
  `human_blockers=[]`, and `human_blocker_details={}` after the private
  worksheet is filled and the final gates pass.

## Verification

RED:

```bash
python -m pytest -q tests/test_acl_openreview_upload_runbook.py
```

The test failed because `OPENREVIEW_UPLOAD_RUNBOOK.md` did not exist.

GREEN:

```bash
python -m pytest -q tests/test_acl_openreview_upload_runbook.py
python -m pytest -q tests/test_acl_preupload_gate.py tests/test_acl_openreview_upload_runbook.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

The new test now guards that the runbook covers the four active human blocker
ids, the private worksheet, OpenReview metadata/checklist copy sources, final
gate commands, and the `Do not upload` stop condition. The consolidated
pre-upload gate now includes this runbook test in its focused pytest step and
passes with 50 focused ACL tests; the staged PDF remains 12 A4 pages, PDF 1.5,
and 306187 bytes.
