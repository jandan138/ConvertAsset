# 2026-07-01 AAN-09 Negative Gate

## Summary

Implemented and retained `AAN-09-negative-gate` evidence for a stable blocked negative
case. The negative source is a minimal USD with an unauthorized remote URI reference:

`docs/records/evidence/2026-07-01-aan-09-negative-gate/sources/remote_uri_block.usda`

The run proves AAN does not silently accept required remote dependencies. It produces a
blocked manifest, keeps later gates as `not_run`, records a blocking reason and required
resolution, and writes a weekly-summary JSON that can aggregate failure modes and waiver
counts.

## Code Changes

- Added `convert_asset/asset_application_normalizer/negative_gate.py`.
  - Reads one or more negative manifests.
  - Accepts only `blocked` or `ready_with_waivers` negative outcomes.
  - Requires blocked cases to include `blocked_reasons` and a blocked stage gate.
  - Requires waiver cases to include complete waiver fields:
    `waiver_id`, `owner`, `reason`, `expires_or_review_by`, `impact`,
    `claims_forbidden`.
  - Aggregates `failure_modes`, `waiver_count`, status counts, representative artifacts,
    and whether `not_run` was incorrectly treated as pass.
- Added AAN-09 regression tests in `tests/test_asset_application_normalizer_cli.py`.

## Retained Evidence

Evidence directory:

`docs/records/evidence/2026-07-01-aan-09-negative-gate/`

Artifacts:

- `sources/remote_uri_block.usda`
- `contracts/remote_uri_block_contract.json`
- `remote_uri_block_manifest.json`
- `negative_gate_summary.json`
- `return_code_probe.json`

Observed result:

| Field | Value |
|---|---|
| Manifest status | `blocked` |
| ConvertAsset CLI return code | `5` |
| Blocker | `aan03_block_remote_uri` |
| AAN-03 gate | `blocked` |
| AAN-04/AAN-05/AAN-06/AAN-07 gates | `not_run` |
| Waiver count | `0` |
| Summary status | `pass` |
| Package written | no |

The direct shell wrapper can print a generic nonzero status when `main.py` exits with
`5`, so `return_code_probe.json` records the value returned by `convert_asset.cli.main()`
inside the Isaac Python environment.

## Verification

Commands run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_negative_gate_summary_accepts_blocked_manifest_with_failure_modes tests/test_asset_application_normalizer_cli.py::test_negative_gate_summary_rejects_false_ready_negative_manifest tests/test_asset_application_normalizer_cli.py::test_negative_gate_summary_requires_complete_waiver_fields -q
python -m pytest tests/test_asset_application_normalizer_cli.py -q
./scripts/isaac_python.sh ./main.py normalize-asset docs/records/evidence/2026-07-01-aan-09-negative-gate/sources/remote_uri_block.usda --out /tmp/aan09_negative_gate/remote_uri_block --asset-id RemoteUriBlocked --asset-class rigid --source-runtime isaac51 --target-runtime isaac41 --target-benchmark ebench-lift2 --task-id AAN09.RemoteUriBlocked --contract docs/records/evidence/2026-07-01-aan-09-negative-gate/contracts/remote_uri_block_contract.json --required-prim /World/RemoteBlockedAsset --gates static,runtime,benchmark --evidence-out docs/records/evidence/2026-07-01-aan-09-negative-gate/remote_uri_block_manifest.json
python -m convert_asset.asset_application_normalizer.negative_gate docs/records/evidence/2026-07-01-aan-09-negative-gate/remote_uri_block_manifest.json --out docs/records/evidence/2026-07-01-aan-09-negative-gate/negative_gate_summary.json
```

Evidence audit:

```bash
python - <<'PY'
import json
from pathlib import Path
base = Path("docs/records/evidence/2026-07-01-aan-09-negative-gate")
summary = json.loads((base / "negative_gate_summary.json").read_text())
manifest = json.loads((base / "remote_uri_block_manifest.json").read_text())
probe = json.loads((base / "return_code_probe.json").read_text())
assert summary["status"] == "pass"
assert summary["status_counts"] == {"blocked": 1}
assert summary["waiver_count"] == 0
assert "aan03_block_remote_uri" in summary["failure_modes"]
assert summary["claim_boundary"]["not_run_treated_as_pass"] is False
assert manifest["overall_status"] == "blocked"
assert probe["convert_asset_cli_return_code"] == 5
assert probe["consistent"] is True
PY
```

## Claim Boundary

AAN-09 pass means:

- blocked negative cases can be retained and summarized without looking ready;
- unauthorized remote URI dependencies remain blocking until mirrored, safely pruned,
  explicitly waived, or left blocked;
- `not_run` downstream gates are preserved as not-run evidence, not pass evidence;
- weekly reporting can aggregate failure modes, waiver count, and representative artifacts.

It does not mean waiver execution is implemented end-to-end. The verifier validates waiver
record completeness for future `ready_with_waivers` manifests, but this retained run uses
a clean blocked case with `waiver_count=0`.
