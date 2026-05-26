# ACL Target Lock And OpenReview Rehearsal

Date: 2026-05-26

## Purpose

Convert the remaining ACL/ARR upload blockers into an executable author-decision
and OpenReview rehearsal packet. This does not choose the target venue for the
authors; it makes the remaining choices explicit and keeps the repository from
pretending that a human-gated submission step is already complete.

## Changes

- Added `paper/venues/acl27/TARGET_LOCK_OPENREVIEW_REHEARSAL.md`.
- Refreshed the official ARR/EACL/ACLPUB policy state against public pages.
- Added author-only decisions that repository evidence cannot complete:
  target route, author list/order, OpenReview profiles, reviewer-registration
  commitment, dual-submission/resubmission status, preprint status,
  runtime/AI-assistance wording, and optional media approval.
- Linked the rehearsal packet from the ACL status docs and repository docs
  index.

## Findings

- EACL 2027 remains the concrete public 2027 ACL-family ARR route, with
  August 3, 2026 as the ARR paper deadline and October 11, 2026 as the
  commitment date in ARR Dates.
- The EACL 2027 main-paper page still says the comprehensive CFP and detailed
  timetable are being finalized.
- Annual ACL 2027 remains unavailable as a final public target in checked
  official sources.
- The repository can provide a clean anonymous PDF, OpenReview checklist source,
  staged minimal packet, citation/provenance audits, and claim/data integrity
  delta, but it cannot complete author profiles, reviewer registration,
  preprint status, or official form submission.

## Remaining Gates

- Author chooses EACL 2027 via ARR or waits for Annual ACL 2027.
- Author confirms OpenReview author/profile/reviewer-registration duties.
- Author approves runtime and AI-assistance disclosure wording.
- Author keeps optional scene-derived media excluded, or explicitly approves a
  separate legal/anonymization route.
- Final build, staging, anonymization, and integrity checks are rerun on the
  exact upload packet.
