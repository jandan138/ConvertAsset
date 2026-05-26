# ACL Author-Gate Semantic Check

Date: 2026-05-26.

## Summary

Hardened the private author-gate checker so the final upload gate cannot be
cleared by arbitrary non-TODO text. The checker now requires positive
confirmation for high-risk private fields such as OpenReview profile readiness,
reviewer-registration commitment, authorship approval, dual-submission status,
form-copy approvals, final scans, optional-media decision, and final upload
decision.

This keeps the anonymous repository packet separate from private author data,
but makes the private upload gate stronger: values such as `do not upload`,
`failed`, `not approved`, or `not confirmed` keep the worksheet incomplete.

## Behavior

- `check_author_gate.py` still does not print private worksheet values.
- The report now includes `invalid_fields`, a field-name-only list for required
  rows whose values are filled but semantically unsafe.
- A complete worksheet must use positive evidence such as `approved`,
  `confirmed`, `copied`, `excluded`, `pass`, `clean`, or final decision
  `upload` where those meanings are required.
- The current repository state is unchanged: without the ignored private
  worksheet, `report_final_blockers.py` remains `status=human_blocked` with
  `repo_blockers=[]`.

## Verification

RED:

```bash
python -m pytest -q tests/test_acl_author_gate.py
```

The new semantic tests failed because negative decisions and failed scans were
still accepted as complete.

GREEN:

```bash
python -m pytest -q tests/test_acl_author_gate.py
python -m pytest -q tests/test_acl_author_gate.py tests/test_acl_final_blockers.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

The consolidated gate passed after the semantic checker update; its focused
pytest step now covers 48 tests, and the staged candidate PDF remains 12 A4
pages, PDF 1.5, and 306187 bytes.
