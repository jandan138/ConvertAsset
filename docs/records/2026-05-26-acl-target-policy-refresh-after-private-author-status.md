# ACL Target Policy Refresh After Private Author Status

Date: 2026-05-26.

## Context

After the final blocker and goal-completion reports gained
`private_author_gate_status`, the remaining ACL/ARR blocker became more
actionable but the external route still needed to stay current. The policy
refresh rechecked the official route sources before treating the packet as an
ACL/ARR candidate.

## Sources Reopened

- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/authorchecklist`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://acl-org.github.io/ACLPUB/review-version.html`
- `https://www.aclweb.org/adminwiki/index.php/ACL_Resolutions`
- `https://2027.eacl.org/`
- `https://2027.eacl.org/calls/papers/`

## Findings

- ARR Dates still lists EACL 2027 with final ARR submission date
  August 3, 2026 and commitment date October 11, 2026.
- The EACL 2027 home page still lists Athens, Greece, March 9-14, 2027 and
  the August 3, 2026 ARR deadline.
- The EACL 2027 main-paper page still says the comprehensive CFP and detailed
  timetable are being finalized.
- ACLPUB still provides the generic review-version formatting boundary: long
  papers have 8 content pages plus unlimited references, A4 paper is required,
  and Limitations must appear before references.
- ACL Resolutions now gives a useful negative-control source: it confirms the
  `2027 ACL Conference Branding` resolution and the ACL 2027 name, but it is
  not an Annual ACL 2027 CFP, author kit, OpenReview form, deadline page, or
  supplement policy.

## Code And Documentation Changes

- `paper/venues/acl27/scripts/check_target_policy.py`
  - Now requires the ACL Resolutions URL and the
    `2027 ACL Conference Branding` marker in target-policy notes.
- `tests/test_acl_target_policy.py`
  - Added a regression test that rejects policy notes where the ACL 2027
    branding-resolution marker is missing.
- `paper/venues/acl27/TARGET_CALL_POLICY_AUDIT.md`
  - Records the refreshed official-source state and explains why the ACL
    branding resolution does not make the packet Annual-ACL-final.
- `paper/venues/acl27/TARGET_LOCK_OPENREVIEW_REHEARSAL.md`
  - Adds the same author-decision-facing route interpretation.

## Verification

RED:

```bash
python -m pytest -q tests/test_acl_target_policy.py -q
```

The new branding-resolution regression test failed because the target-policy
checker did not yet require the marker.

GREEN:

```bash
python -m pytest -q tests/test_acl_target_policy.py -q
python paper/venues/acl27/scripts/check_target_policy.py
```

Result: the focused target-policy test suite passes and the checker reports
`route_status=acl_arr_candidate`, `annual_acl_final_ready=false`,
`eacl_arr_public_route=true`, and no missing required URLs or markers.

## Remaining Gates

This refresh does not choose the route for the authors. The practical next
human decision remains: submit through EACL 2027 via ARR now, or keep waiting
for an official Annual ACL 2027 CFP/author kit.
