# ACL Target Policy Refresh After Final-Blocker Handoff

Date: 2026-05-26

## Purpose

Refresh official ACL-family policy sources after the final blocker report was
updated to include the author-gate initializer command. This keeps the
target-route evidence current without changing the manuscript or experiment
claim surface.

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

- ARR Dates still lists EACL 2027 with final ARR submission date August 3,
  2026 and commitment date October 11, 2026.
- The EACL 2027 home page still lists Athens, Greece, March 9-14, 2027, and
  the ARR submission deadline for long and short papers as August 3, 2026.
- The EACL 2027 main-paper page still says the comprehensive Call for Papers
  and detailed timetable are being finalized.
- ARR author/common-problem guidance still leaves author order, OpenReview
  profiles, reviewer-registration duties, dual-submission status,
  preprint-status choice, and checklist wording as human gates.
- ACLPUB review/formatting guidance still supports the current repository
  checks around anonymous review PDF, A4 paper size, 200-word abstract
  guidance, Limitations before references, optional Ethical Considerations
  before references, and no acknowledgments in review version.
- Official search still did not find an Annual ACL 2027 CFP, author kit,
  city/date page, commitment deadline, or conference-specific supplement
  policy.

## Decision

No target-policy change is needed in the manuscript. The current state remains:

> ACL/ARR candidate-ready; EACL 2027 via ARR is the concrete public 2027
> ACL-family route; Annual ACL 2027 is not yet an official final target in
> checked public sources.

The next blocking action remains author route lock plus private OpenReview
author-gate completion. More experiments are not the default next step for
target-policy closure.

## Verification

Updating `TARGET_CALL_POLICY_AUDIT.md` and
`TARGET_LOCK_OPENREVIEW_REHEARSAL.md` intentionally changed protected
final-integrity sources. The fingerprint checker first reported those two
files as changed, then the fingerprint was refreshed with:

```bash
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
```

The final verification commands were:

```bash
python paper/venues/acl27/scripts/check_target_policy.py
python -m pytest -q tests/test_acl_target_policy.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Results: the target-policy checker reported `route_status=acl_arr_candidate`
with no missing URLs, no missing markers, and no forbidden Annual ACL 2027
final-ready wording; the focused target-policy tests passed 3 tests; the full
consolidated pre-upload gate passed with 53 focused ACL tests, a valid
41-source integrity fingerprint, the final blocker report still at
`status=human_blocked` with `repo_blockers=[]`, and a staged 12-page A4 PDF
1.5 packet whose `main.pdf` remained 306187 bytes.
