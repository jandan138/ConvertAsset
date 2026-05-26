# 2026-05-26 ACL OpenReview Checklist Packet

## Purpose

Move the Responsible NLP work from a loose draft into a copy-ready
OpenReview/ARR form packet tied to the current anonymous ACL PDF. This closes
another practical submission gate: the paper now has a form-answer source with
section/page anchors instead of only a checklist reminder.

## Changes

- Added `paper/venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`.
- Updated `paper/venues/acl27/scripts/stage_submission_packet.py` so the ignored
  candidate packet stages the checklist under
  `openreview/RESPONSIBLE_NLP_CHECKLIST.md`.
- Updated the staging test to require the OpenReview checklist file in the
  generated packet.
- Updated ACL status, readiness, final packet, and Responsible NLP draft docs to
  point to the new form packet.

## Evidence Used

- Current ACL PDF anchors from `paper/venues/acl27/build/main.pdf`:
  `Limitations` on pages 7-8, `Ethical Considerations` on page 8, and
  `References` starting on page 8.
- Source-section anchors from `paper/venues/acl27/sections/*.tex`.
- Existing provenance and compute drafts:
  `ARTIFACT_PROVENANCE_DRAFT.md` and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`.
- Current ARR public guidance pages checked on 2026-05-26:
  `aclrollingreview.org/static/responsibleNLPresearch.pdf`,
  `aclrollingreview.org/responsibleNLPresearch/`,
  `aclrollingreview.org/authorchecklist`, and
  `aclrollingreview.org/responsible-nlp-checklist-appendices`.

## Remaining Gates

- Re-check target-call wording before upload.
- Copy answers into the official OpenReview form after the final PDF build.
- Replace local model/checkpoint references with public model IDs and hashes
  where available.
- Confirm InteriorAgent / KuJiaLe terms before redistributing selected videos or
  scene-derived media.
