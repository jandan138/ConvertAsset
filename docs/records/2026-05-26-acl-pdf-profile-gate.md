# ACL PDF Profile Gate

Date: 2026-05-26.

## Summary

Added an explicit PDF profile guard to the ACL/ARR pre-upload runner. The gate
now checks the staged PDF's `pdfinfo` profile and rejects silent drift from the
current candidate packet shape.

The current repository-side candidate profile is:

- total pages: at most 12;
- page size: A4;
- PDF version: 1.5;
- required text markers: title, anonymous ACL header, `Limitations`,
  `Ethical Considerations`, and `References`;
- required section order: `Limitations` before `Ethical Considerations` before
  `References`.

The 12-page cap is a local candidate-profile guard, not a claim that every
future ACL-family venue has the same total-page policy. If later edits or venue
instructions require a different profile, update the cap and rerun the full
pre-upload gate intentionally.

## Files Updated

- `paper/venues/acl27/scripts/run_preupload_gate.py`
- `tests/test_acl_preupload_gate.py`
- `paper/venues/acl27/STATUS.md`
- `paper/venues/acl27/SUBMISSION_STAGING_AUDIT.md`
- `paper/venues/acl27/GOAL_COMPLETION_AUDIT.md`
- `docs/records/2026-05-26-acl-preupload-gate-runner.md`
- `docs/index.md`
- `docs/records/README.md`

## TDD Evidence

RED:

```bash
python -m pytest -q tests/test_acl_preupload_gate.py
```

Failed as expected because the pre-upload plan had no `pdf_profile` step and
the parser/validator functions did not exist.

GREEN:

```bash
python -m pytest -q tests/test_acl_preupload_gate.py
```

Passed:

```text
6 passed
```

## Verification

Executed after the edit:

```bash
git diff --check
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The consolidated ACL pre-upload gate now completes
`pdf_profile` between `pdfinfo` and `pdftotext_sections`. The focused suite
passes 23 tests, the staged PDF remains 12 A4 pages / PDF 1.5 / 306187 bytes,
and the staged packet still has exactly the five safe files.
