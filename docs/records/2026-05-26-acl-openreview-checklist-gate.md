# ACL OpenReview Checklist Gate

Date: 2026-05-26.

## Summary

Added an automated copy-readiness check for the ACL/ARR OpenReview Responsible
NLP checklist packet. The gate validates that the local checklist copy source
covers the expected ARR question set, includes policy inputs and current PDF
anchors, avoids placeholder text, avoids bare yes/no/N/A answers, and includes
the anonymous-review AI-assistance disclosure wording.

This does not copy the checklist into OpenReview and does not replace final
author or venue-policy review. It prevents the tracked copy source from drifting
into an incomplete or placeholder state before the final human form-copy step.

## Changed Files

- Added `paper/venues/acl27/scripts/check_openreview_checklist.py`.
- Added `tests/test_acl_openreview_checklist.py`.
- Updated `paper/venues/acl27/scripts/run_preupload_gate.py` so the
  consolidated pre-upload gate validates the checklist copy source before
  citation, evidence, build, and staging checks.
- Updated `paper/venues/acl27/scripts/report_final_blockers.py` so an invalid
  checklist copy source becomes a repo-side blocker.
- Updated ACL readiness and submission-checklist docs.

## Current Report

The current checklist report is copy-source ready:

```json
{
  "ok": true,
  "question_count": 17,
  "missing_questions": [],
  "placeholder_hits": [],
  "bare_answer_questions": [],
  "missing_policy_inputs": [],
  "current_pdf_anchors_present": true,
  "ai_disclosure_present": true
}
```

## Verification

RED:

```bash
python -m pytest -q tests/test_acl_openreview_checklist.py
```

Failed because `check_openreview_checklist.py` did not exist.

GREEN:

```bash
python -m pytest -q tests/test_acl_openreview_checklist.py
python paper/venues/acl27/scripts/check_openreview_checklist.py
python -m pytest -q tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging tests/test_acl_openreview_checklist.py
```

## Remaining Gates

- Re-check selected venue instructions before upload.
- Copy the final checklist answers into the real OpenReview form.
- Refresh PDF anchors if the paper layout changes.
- Keep optional media excluded unless authors approve a separate
  license/anonymization path.
