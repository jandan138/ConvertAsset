# ACL Evidence-Gate Table

Date: 2026-05-26.

## Summary

Added a compact evidence-gate registry table to the ACL/ARR manuscript method
section. The table maps each evidence stream to the claim it can support and
the promotion that remains forbidden without new evidence.

This hardens the manuscript against the reviewer risk that proxy metrics, VLM
grounding, NVIDIA material cases, InternNav runs, and official-scene stability
could look like disconnected experiments.

## Files Updated

- `paper/shared/tables/tab_acl_evidence_gate_registry.tex`
- `paper/venues/acl27/sections/method.tex`
- `paper/venues/acl27/ACL_REVIEWER_RISK_AUDIT.md`
- `paper/venues/acl27/GOAL_COMPLETION_AUDIT.md`
- `paper/venues/acl27/STATUS.md`
- `docs/index.md`
- `docs/records/README.md`

## Claim Boundary

The table is deliberately scoped:

- Proxy similarity supports visual and feature screening only.
- GRScenes supports bounded VLM answer and point-grounding evidence only.
- Material-effect/NVIDIA evidence supports selected material-boundary analysis
  only.
- InternNav and official-scene load/render runs support scoped downstream
  usability and stability only.

The table does not add new experiments, new evidence numbers, broad embodied
benchmark claims, NVIDIA population failure rates, procedural-texture success,
or speedup claims.

## Verification

Executed after the edit:

```bash
git diff --check
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The consolidated ACL pre-upload gate passed claim-boundary,
metadata, evidence-number, focused pytest, clean build, LaTeX log, staging,
packet inventory, anonymization, acknowledgment, `pdfinfo`, and `pdftotext`
checks. The refreshed staged PDF is 12 A4 pages and 306187 bytes.
