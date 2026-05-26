# ACL Evidence-Number Check

Date: 2026-05-26.

## Summary

Added an automated evidence-number consistency gate for the ACL/ARR candidate.
The checker turns the manual data-claim section in
`FINAL_INTEGRITY_DELTA_AUDIT.md` into a reproducible command that reads the
local evidence artifacts, computes the current numeric snapshot, and verifies
that the ACL manuscript and OpenReview metadata source still contain the
matching claim numbers.

## Files Added

- `paper/venues/acl27/scripts/check_evidence_numbers.py`
- `tests/test_acl_evidence_numbers.py`

## Coverage

The checker currently covers the highest-risk numerical claims:

- proxy metrics: four assets, 24 matched render pairs, PSNR, SSIM, LPIPS, CLIP,
  and DINOv2 means;
- clean GRScenes pool: 15 PASS pairs, Gemma4 point hits, and Qwen parser/raw
  point diagnostics;
- expanded30 stress set: Gemma4 answer and normalized-point counts, Qwen raw
  and normalized-point diagnostics;
- official KuJiaLe InternNav sanity run: 99 paired episodes, three official
  scenes, and SR/SPL/NE/TL original/noMDL means;
- official-scene stability: 18/18 required original/noMDL fresh-process
  load/render runs and zero aggregate failures;
- appendix coordinate-only baselines: raw center/oracle saturation and the
  normalized-1000 bbox-center oracle.

The command is now part of `run_preupload_gate.py`, so numeric drift becomes a
pre-upload failure before packet staging.

## TDD Evidence

RED:

```bash
python -m pytest -q tests/test_acl_evidence_numbers.py tests/test_acl_preupload_gate.py
```

Failed because the checker did not exist and the pre-upload plan did not yet
include `evidence_numbers`:

```text
AssertionError: ACL evidence-number checker is missing
```

GREEN:

```bash
python -m pytest -q tests/test_acl_evidence_numbers.py tests/test_acl_preupload_gate.py
python paper/venues/acl27/scripts/check_evidence_numbers.py
```

Passed:

```text
5 passed
"ok": true
"violations": []
```

## Submission Impact

This gate does not prove every possible semantic claim in the paper. It does
make the most visible ACL-facing numbers harder to accidentally desynchronize
from local evidence during final edits. Citation context, policy freshness, and
author-only OpenReview decisions remain separate final gates.
