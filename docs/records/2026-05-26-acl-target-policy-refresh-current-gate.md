# ACL Target Policy Refresh After Current Gate

Date: 2026-05-26

## Purpose

Refresh official ACL-family policy sources after the latest pushed
`run_preupload_gate.py` pass, so the ACL/ARR candidate packet is not relying on
stale target-call assumptions.

This was a policy/source verification pass. It did not change the manuscript,
experiments, or claim surface.

## Sources Reopened

- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/authorchecklist`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://acl-org.github.io/ACLPUB/review-version.html`
- `https://2027.eacl.org/`
- `https://2027.eacl.org/calls/papers/`

Official search was also used to check whether Annual ACL 2027 public
submission materials had appeared.

## Findings

- ARR Dates still lists EACL 2027 as a participating venue with final ARR
  submission date August 3, 2026 and commitment date October 11, 2026.
- The EACL 2027 home page still lists Athens, Greece, March 9-14, 2027, and
  the ARR submission deadline for long and short papers as August 3, 2026.
- The EACL 2027 main-paper page still says the comprehensive Call for Papers
  and detailed timetable are being finalized.
- ARR author and common-problem guidance still leaves author order,
  OpenReview profiles, reviewer-registration duties, dual-submission status,
  preprint-status choice, and checklist wording as author/human gates.
- ACLPUB review/formatting guidance still supports the repository's current
  PDF checks: anonymous review PDF, A4 paper, embedded/readable content,
  200-word abstract guidance, Limitations before references, optional Ethical
  Considerations before references, and no acknowledgments in review version.
- Official search still did not find an Annual ACL 2027 CFP, author kit,
  city/date page, commitment deadline, or conference-specific supplement
  policy.

## Decision

No target-policy change is needed in the repository. The current state remains:

> ACL/ARR candidate-ready; EACL 2027 via ARR is the concrete public 2027
> ACL-family route; Annual ACL 2027 is not yet an official final target in
> checked public sources.

The next blocking action is still author route lock plus private OpenReview
author-gate completion, not more unbounded experiment collection.
