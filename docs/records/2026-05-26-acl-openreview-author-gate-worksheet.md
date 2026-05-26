# ACL OpenReview Author Gate Worksheet

Date: 2026-05-26.

## Summary

Added a blank, commit-safe worksheet for the human-only ARR/OpenReview fields:

- `paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_WORKSHEET.md`

The worksheet covers route choice, author list/order, OpenReview profiles,
reviewer-registration commitment, dual-submission/resubmission status,
preprint status, checklist/disclosure approvals, optional media approval, and
final pre-upload evidence.

## Privacy Boundary

The tracked worksheet is a template only. It now instructs authors to create a
private local copy with the safe initializer:

```bash
python paper/venues/acl27/scripts/init_author_gate.py
git check-ignore -v paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
```

The initializer refuses to overwrite an existing private worksheet and reports
only path/status metadata. The filled local copy is ignored by `.gitignore`; it
must not be uploaded as review supplemental material and should not be
committed.

## Why This Matters

The paper already has manuscript, metadata, checklist, staging, claim-boundary,
and integrity artifacts. The remaining upload risk is mostly human and
submission-system state. This worksheet makes those gates explicit without
putting private author information into the tracked anonymous paper packet.

## Files Updated

- `paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_WORKSHEET.md`
- `paper/venues/acl27/NEXT_LARGE_GOAL.md`
- `paper/venues/acl27/TARGET_LOCK_OPENREVIEW_REHEARSAL.md`
- `paper/venues/acl27/FINAL_SUBMISSION_PACKET_CHECKLIST.md`
- `paper/venues/acl27/STATUS.md`
- `docs/index.md`
- `docs/records/README.md`
- `.gitignore`

## Verification

- `git diff --check`
- `git check-ignore -v paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md`

## Sources

- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/authorchecklist`
- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/areas`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://2027.eacl.org/calls/papers/`
