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
12. PDF profile guard for current candidate shape: at most 12 pages, A4 page
    size, and PDF 1.5
13. `pdftotext` title, anonymous-header, limitation, ethics, and reference scan
    with `Limitations`, `Ethical Considerations`, and `References` in order

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

PDF profile refresh:

The runner now includes a `pdf_profile` step after `pdfinfo`. It parses the
staged PDF profile and rejects silent drift from the current ACL/ARR candidate
shape: more than 12 total pages, non-A4 page size, or a PDF version other than
1.5. The `pdftotext` step also checks that `Limitations`, `Ethical
Considerations`, and `References` appear in that order.

This is a repository-side candidate guard, not a substitute for the final
selected-venue policy check.

Current rerun after this refresh:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Passed. The focused pytest step now covers 23 tests, the clean staged PDF is 12
A4 pages / PDF 1.5 / 306187 bytes, the new `pdf_profile` step completed, and
the staged packet still contains exactly the five safe files.

## Submission Impact

`run_preupload_gate.py` is now the primary local command for the repository-side
pre-upload rehearsal. It does not replace the human/external gates: target
route lock, official policy refresh, author worksheet completion, official
OpenReview form copy, and final author/legal decisions still remain outside
automation.
