# ACL Pre-Upload Gate Runner

Date: 2026-05-26.

## Summary

Added a consolidated ACL/ARR pre-upload gate runner for the current candidate
packet. The runner turns the manual final-gate checklist into one reproducible
command that runs claim checks, metadata drift checks, focused tests, clean PDF
build, staging, packet inventory checks, anonymization scans, acknowledgment
scans, and PDF text sanity checks.

## Files Added

- `paper/venues/acl27/scripts/run_preupload_gate.py`
- `tests/test_acl_preupload_gate.py`

## Behavior

The runner executes these steps in order:

1. `check_claim_boundaries.py`
2. `check_metadata_consistency.py`
3. `check_evidence_numbers.py`
4. focused ACL pytest suite
5. clean ACL PDF rebuild
6. final LaTeX log unresolved citation/reference scan
7. candidate packet staging
8. exact packet file inventory check
9. private local path / username / repository token scan
10. acknowledgment token scan
11. `pdfinfo` over the staged PDF
12. `pdftotext` title, anonymous-header, limitation, ethics, and reference scan

The expected staged packet remains exactly:

```text
main.pdf
openreview/METADATA.md
openreview/RESPONSIBLE_NLP_CHECKLIST.md
supplemental/README.md
supplemental/manifest.json
```

Selected qualitative videos, raw scenes, scratch no-MDL USD trees, InternNav
runtime outputs, LMDBs/logs, and local model checkpoints remain outside the
safe default upload boundary.

## TDD Evidence

RED:

```bash
python -m pytest -q tests/test_acl_preupload_gate.py
```

Failed because the runner did not exist:

```text
AssertionError: ACL pre-upload gate runner is missing
```

GREEN:

```bash
python -m pytest -q tests/test_acl_preupload_gate.py
```

Passed:

```text
3 passed
```

Full rehearsal:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Passed all runner steps after the evidence-number gate was added. The focused
pytest step passed 20 tests, the clean ACL build wrote an 11-page A4 PDF, the
staged packet contained only the five expected files, the local-path/private-token
scan had no matches, the acknowledgment scan had no matches, and `pdftotext`
found the required title, anonymous header, `Limitations`, `Ethical
Considerations`, and `References` markers.

## Submission Impact

`run_preupload_gate.py` is now the primary local command for the repository-side
pre-upload rehearsal. It does not replace the human/external gates: target
route lock, official policy refresh, author worksheet completion, official
OpenReview form copy, and final author/legal decisions still remain outside
automation.
