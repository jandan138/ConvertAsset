# ACL Packet Checksum Sidecar

Date: 2026-05-26

## Context

The ACL/ARR staging script already enforced a minimal anonymous review packet,
but the final upload rehearsal did not leave a machine-checkable digest record
for the exact five staged files. Recording digests inside
`supplemental/manifest.json` would create a self-hash problem for the manifest
itself, and adding a checksum file inside the packet would widen the safe
five-file upload boundary.

## Change

- Updated `paper/venues/acl27/scripts/stage_submission_packet.py` to write an
  adjacent ignored checksum sidecar after staging:
  `paper/submissions/acl27_arr_candidate_20260526.sha256`.
- Kept the anonymous packet directory unchanged with exactly five files.
- Updated `paper/venues/acl27/scripts/run_preupload_gate.py` to validate the
  sidecar immediately after the exact packet-inventory check.
- Added focused tests in `tests/test_acl_submission_staging.py` and
  `tests/test_acl_preupload_gate.py`.
- Updated ACL status, checklist, readiness, staging, next-goal, and goal-audit
  records.

## Behavior

The sidecar is outside the packet directory and is not intended for upload. It
contains one SHA-256 line per safe packet file:

- `main.pdf`
- `openreview/METADATA.md`
- `openreview/RESPONSIBLE_NLP_CHECKLIST.md`
- `supplemental/README.md`
- `supplemental/manifest.json`

The pre-upload gate now rejects a missing, malformed, incomplete, extra, unsafe,
or mismatched checksum sidecar. This makes the exact upload rehearsal easier to
compare with a later final upload without adding raw assets, videos, author
data, or extra packet files.

## Verification

TDD red checks were run before implementation:

```bash
python -m pytest -q tests/test_acl_submission_staging.py
python -m pytest -q tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging tests/test_acl_preupload_gate.py::test_packet_checksum_sidecar_must_match_expected_files
```

The first failed because the sidecar was missing. The second failed because the
pre-upload plan did not include `packet_checksum_sidecar` and the validator did
not exist yet.

After implementation:

```bash
python -m pytest -q tests/test_acl_submission_staging.py
python -m pytest -q tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging tests/test_acl_preupload_gate.py::test_packet_checksum_sidecar_must_match_expected_files
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Current result: pass. The full gate now includes packet checksum-sidecar
validation, 31 focused tests, a five-file staged packet, a valid adjacent
checksum sidecar, a 12-page A4 PDF 1.5, and 306187 bytes.

## Remaining Gate

The sidecar proves local file integrity for the staged packet. It does not close
the human gates: route lock, private author worksheet, official OpenReview form
copy, runtime/AI-assistance approval, or optional media legal review.
