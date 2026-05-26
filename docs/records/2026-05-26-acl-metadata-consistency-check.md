# ACL Metadata Consistency Check

Date: 2026-05-26.

## Summary

Added an automated metadata consistency gate for the ACL/ARR candidate packet.
The new checker prevents the OpenReview title/abstract copy source from
drifting away from the LaTeX manuscript after future first-page edits.

## Files Added

- `paper/venues/acl27/scripts/check_metadata_consistency.py`
- `tests/test_acl_metadata_consistency.py`

## Behavior

The checker reads:

- `paper/venues/acl27/main.tex`
- `paper/venues/acl27/sections/abstract.tex`
- `paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md`

It verifies:

- the fenced plain-text metadata title matches the LaTeX title;
- the fenced metadata abstract matches the source abstract after conservative
  LaTeX-to-text normalization;
- the source abstract remains at or below the 200-word ACLPUB guidance.

Current expected count: 189 words.

## TDD Evidence

RED:

```bash
python -m pytest -q tests/test_acl_metadata_consistency.py
```

Failed with:

```text
AssertionError: ACL metadata consistency checker is missing
```

GREEN:

```bash
python -m pytest -q tests/test_acl_metadata_consistency.py
```

Passed:

```text
1 passed
```

## Submission Impact

`NEXT_LARGE_GOAL.md` and `FINAL_SUBMISSION_PACKET_CHECKLIST.md` now include the
checker in the final pre-upload command set. This does not close the active
ACL/ARR goal; it strengthens the upload gate by making metadata drift
machine-checkable.

