# ACL Claim-Boundary Check

Date: 2026-05-26.

## Summary

Added an automated claim-boundary gate for the ACL/ARR candidate. The checker
turns the existing manual `CLAIM_AUDIT.md` guardrails into a pre-upload command
that scans the ACL manuscript, appendix, and OpenReview metadata source for
unsupported broad claims.

## Files Added

- `paper/venues/acl27/scripts/check_claim_boundaries.py`
- `tests/test_acl_claim_boundaries.py`

## Behavior

The checker scans:

- `paper/venues/acl27/sections/*.tex`
- `paper/shared/sections/appendix.tex`
- `paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md`

It flags positive, unguarded claims about:

- broad embodied or GRScenes robustness;
- broad benchmark completion;
- all-GRScenes, all-InteriorNav, R2R/MP3D, or manipulation robustness;
- official-scene noMDL speedup;
- NVIDIA official-scene performance/baseline/comparison;
- population NVIDIA failure rate;
- procedural-texture preservation success;
- learned automatic classifier/recommender claims.

Guardrailed uses are allowed when the sentence clearly scopes or negates the
claim, for example with `does not`, `do not report`, `rather than`, `scoped`,
`selected`, `bounded`, `limitation`, `sanity`, or `overclaiming`.

## TDD Evidence

RED:

```bash
python -m pytest -q tests/test_acl_claim_boundaries.py
```

Failed with:

```text
AssertionError: ACL claim-boundary checker is missing
```

GREEN:

```bash
python -m pytest -q tests/test_acl_claim_boundaries.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
```

Passed:

```text
3 passed
"ok": true
"violations": []
```

## Submission Impact

`NEXT_LARGE_GOAL.md` and `FINAL_SUBMISSION_PACKET_CHECKLIST.md` now include this
checker in the final pre-upload command set. This strengthens the active
ACL/ARR goal by making the most dangerous unsupported-claim regressions
machine-checkable.

