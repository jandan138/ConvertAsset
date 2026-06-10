# 2026-05-30 ACL Target Policy Refresh

## Scope

Rechecked the public ACL/ARR route state for the ACL-facing paper packet after
the author-gate and final-blocker documents had drifted behind the current
date.

## Findings

- ARR Dates still lists EACL 2027 with final ARR submission date August 3,
  2026 and commitment date October 11, 2026.
- EACL 2027 still lists Athens, Greece, March 9-14, 2027, and the August 3,
  2026 ARR deadline.
- The EACL 2027 main-paper page still says the comprehensive Call for Papers
  and detailed timetable are being finalized.
- Official searches still did not find a public Annual ACL 2027 CFP, author
  kit, city/date page, commitment deadline, or conference-specific supplement
  policy.

## Changes

- Updated `TARGET_CALL_POLICY_AUDIT.md` and
  `TARGET_LOCK_OPENREVIEW_REHEARSAL.md` to `Checked: 2026-05-30`.
- Updated the private author-gate filling guide and OpenReview metadata packet
  route notes to the same checked date.
- Updated `STATUS.md` with the current route-state summary.
- Updated `check_target_policy.py` and its focused test so the gate requires
  the current route-refresh date instead of the stale 2026-05-26 marker.

## Decision

The packet remains ACL/ARR candidate-ready. The concrete public route is EACL
2027 via ARR; Annual ACL 2027 should not be described as final-ready until an
official public CFP/author kit exists.

## Verification

Verification after this documentation/code sync:

```bash
python paper/venues/acl27/scripts/check_target_policy.py
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
python paper/venues/acl27/scripts/check_openreview_checklist.py
python -m pytest -q tests/test_acl_target_policy.py tests/test_acl_author_gate_prefill.py tests/test_acl_final_blockers.py
python -m pytest -q tests/test_acl_metadata_consistency.py tests/test_acl_openreview_checklist.py tests/test_acl_integrity_fingerprint.py
git diff --check -- paper/venues/acl27/TARGET_CALL_POLICY_AUDIT.md paper/venues/acl27/TARGET_LOCK_OPENREVIEW_REHEARSAL.md paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md paper/venues/acl27/STATUS.md paper/venues/acl27/scripts/check_target_policy.py tests/test_acl_target_policy.py docs/records/2026-05-30-acl-target-policy-refresh.md docs/records/README.md
```

Results: target-policy check passed with `route_status=acl_arr_candidate`,
integrity fingerprint was refreshed and rechecked with `source_count=57`, and
focused tests reported `18 passed` plus `9 passed` for metadata/checklist/
fingerprint coverage. Metadata consistency and OpenReview checklist checks
also passed.
