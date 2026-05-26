# ACL Reviewer-Risk Audit

Date: 2026-05-26.

## Summary

Added `paper/venues/acl27/ACL_REVIEWER_RISK_AUDIT.md` to turn the user's ACL
submission intent into a reviewer-facing next-goal decision.

The practical next large goal is now stated as: lock the ACL-family route,
harden the current packet against likely ACL reviewer objections, and then run
the final integrity/upload gate.

## Decision

Use EACL 2027 via ARR as the current actionable ACL-family target if the authors
want a 2027 ACL-family submission now. ARR and the EACL 2027 site list the
August 3, 2026 ARR deadline. Annual ACL 2027 remains a candidate target only,
because no official Annual ACL 2027 CFP/author kit was found in the checked
official sources.

Official sources checked:

- https://aclrollingreview.org/dates
- https://2027.eacl.org/calls/papers/

## Reviewer-Risk Framing

The paper should be presented as a VLM grounding and embodied-data reliability
paper under controlled 3D material perturbations. ConvertAsset is the
intervention mechanism, not the whole contribution.

The audit identifies the main reviewer risks:

- ACL fit risk if the paper reads like a simulation-tool paper;
- narrow evidence risk from 15 clean pairs, 30 stress pairs, and 99 scoped
  InternNav episodes;
- narrative-fragmentation risk across proxy metrics, VLM probes, material
  bins, NVIDIA selected cases, and InternNav sanity evidence;
- over-reading selected NVIDIA and clearcoat evidence;
- coordinate-contract confusion for Qwen;
- embodied-navigation overclaim risk;
- optional media and venue-policy drift.

## Implementation

Updated the ACL status and next-goal documents so the route and reviewer-risk
interpretation are discoverable from the main paper workspace and the global
docs index.

## Verification

This was a documentation-only update. Verification performed:

```bash
git diff --check
rg -n "ACL Reviewer-Risk Audit|reviewer-risk|Lock the ACL-family route" \
  paper/venues/acl27 docs/index.md docs/records/README.md
```

## Remaining Work

The active paper goal is not complete. The remaining gates are target-route
lock, private author-gate completion, final policy refresh, final PDF rebuild,
OpenReview form copy, and anonymization scans over the exact upload packet.
