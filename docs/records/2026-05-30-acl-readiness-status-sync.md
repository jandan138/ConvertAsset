# 2026-05-30 ACL Readiness Status Sync

## Scope

This record synchronizes submission-facing status documents after the latest
target-policy, reviewer-risk, full-PDF visual, Figure 3 red-material, and
first-page fit rechecks.

## Current External Route State

Official sources were checked on 2026-05-30:

- ARR Dates lists the August 2026 cycle submission deadline as August 3, 2026
  and lists EACL 2027 with final ARR submission date August 3, 2026 and
  commitment date October 11, 2026.
- The EACL 2027 home page lists Athens, Greece, March 9-14, 2027, and the ARR
  deadline as August 3, 2026.
- The EACL 2027 main-paper call lists the August 3, 2026 AoE ARR deadline and
  says the complete CFP and detailed timetable are still forthcoming.

Public official search still did not find an Annual ACL 2027 CFP or author kit.

## Changes

Updated:

- `paper/venues/acl27/STATUS.md`
- `paper/venues/acl27/SUBMISSION_READINESS_AUDIT.md`
- `paper/venues/acl27/FINAL_SUBMISSION_PACKET_CHECKLIST.md`
- `paper/venues/acl27/GOAL_COMPLETION_AUDIT.md`
- `docs/records/README.md`

The updates add the 2026-05-30 first-page ACL-fit evidence, current visual
review evidence, and current route status to the documents that authors will
read immediately before a final upload rehearsal.

## Decision

No manuscript source, figure source, or imagegen asset was changed in this
sync. The accepted Figure 1 v18 still passes the first-page/page-2 visual-fit
review, so another imagegen iteration would add risk without a concrete visual
defect to correct.

## Verification

Commands:

```bash
python paper/venues/acl27/scripts/check_target_policy.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
python paper/venues/acl27/scripts/report_final_blockers.py
git diff --check -- paper/venues/acl27/STATUS.md paper/venues/acl27/SUBMISSION_READINESS_AUDIT.md paper/venues/acl27/FINAL_SUBMISSION_PACKET_CHECKLIST.md paper/venues/acl27/GOAL_COMPLETION_AUDIT.md docs/records/2026-05-30-acl-readiness-status-sync.md docs/records/README.md
```

Expected status remains `human_blocked` with `repo_blockers=[]`, because final
route lock, private author-gate fields, OpenReview form copy, runtime/AI/media
approvals, and final upload decision are intentionally human-gated.
