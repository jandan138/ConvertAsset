# 2026-07-01 AAN-09.5 PM Evidence Table

## Summary

Implemented and retained `AAN-09.5-pm-evidence-table`, a product-facing evidence
aggregation layer over AAN manifests. The table is meant for PM review, weekly
reports, and acceptance meetings: it explains which assets are runtime-ready, which
are only contract-ready, which are blocked, and where the evidence lives.

The current retained table aggregates:

- AAN-07 DryingBox runtime-ready refresh manifest.
- AAN-08 `MuffleFurnace` runtime/benchmark manifest.
- AAN-08 `Beaker_01` runtime/benchmark manifest.
- AAN-09 unauthorized remote URI blocked manifest and negative summary.

Observed PM status counts:

| PM status | Count | Meaning |
|---|---:|---|
| `ready` | 3 | Runtime smoke and benchmark contract evidence are present. |
| `blocked` | 1 | The asset must not be handed to EBench as ready. |

## Code Changes

- Added `convert_asset/asset_application_normalizer/pm_evidence_table.py`.
  - Builds a JSON evidence table from one or more AAN manifests.
  - Renders a Markdown table for PM/weekly reporting.
  - Aggregates status counts, waiver counts, and failure modes.
  - Distinguishes clean runtime-ready assets from contract-only manifests.
- Added regression tests in `tests/test_asset_application_normalizer_pm_and_mjcf.py`.

## Retained Evidence

Evidence directory:

`docs/records/evidence/2026-07-01-aan-09-5-pm-evidence-table/`

Artifacts:

- `pm_evidence_table.json`
- `pm_evidence_table.md`

Important result:

- `DryingBox_01_overlay`, `Beaker_01`, and `MuffleFurnace` are `ready`.
- `RemoteUriBlocked` is `blocked` with failure mode `aan03_block_remote_uri`.
- Waiver count is `0`.

2026-07-13 scope correction: the `DryingBox_01_overlay` row is a ready row for
the pre-repaired overlay manifest only. It is not a count or status for the raw
LabUtopia `lab_001.usd` DryingBox family. The table must not be used to infer
DB01--DB04 family readiness from that row.

## Verification

Commands run:

```bash
python -m pytest tests/test_asset_application_normalizer_pm_and_mjcf.py::test_pm_evidence_table_maps_ready_and_blocked_rows tests/test_asset_application_normalizer_pm_and_mjcf.py::test_pm_evidence_table_marks_contract_only_manifest_runtime_pending -q
python -m convert_asset.asset_application_normalizer.pm_evidence_table --manifest docs/records/evidence/2026-07-01-aan-07-dryingbox-runtime-ready/dryingbox_runtime_ready_manifest.json --manifest docs/records/evidence/2026-06-30-aan-08-replication-set/muffle_furnace_manifest.json --manifest docs/records/evidence/2026-06-30-aan-08-replication-set/beaker_01_manifest.json --manifest docs/records/evidence/2026-07-01-aan-09-negative-gate/remote_uri_block_manifest.json --negative-summary docs/records/evidence/2026-07-01-aan-09-negative-gate/negative_gate_summary.json --json-out docs/records/evidence/2026-07-01-aan-09-5-pm-evidence-table/pm_evidence_table.json --markdown-out docs/records/evidence/2026-07-01-aan-09-5-pm-evidence-table/pm_evidence_table.md
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_asset_application_normalizer_pm_and_mjcf.py -q
python -m compileall convert_asset/asset_application_normalizer
git diff --check
```

Evidence audit:

```bash
python - <<'PY'
import json
from pathlib import Path
table = json.loads(Path("docs/records/evidence/2026-07-01-aan-09-5-pm-evidence-table/pm_evidence_table.json").read_text())
assert table["summary"]["asset_count"] == 4
assert table["summary"]["status_counts"] == {
    "blocked": 1,
    "ready": 3,
}
assert table["summary"]["waiver_count"] == 0
assert table["summary"]["failure_modes"] == {"aan03_block_remote_uri": 1}
PY
```

## Claim Boundary

AAN-09.5 pass means product reporting can consume a single table instead of manually
opening separate manifests. If a future table includes `contract_ready_runtime_pending`,
that status must remain separate from `ready`; the current table has no pending runtime
asset after the DryingBox refresh.

The historical “DryingBox refresh” wording refers to the already repaired
`DryingBox_01_overlay`, not the raw 20260707 source family. Any future PM row
for `lab_001.usd:/World/DryingBox_03` must carry the source SHA-256, output
asset role, declared prim scope, source-physics-audit status, output-role
admission status, and (when runtime is requested) the scoped PhysX
negative-mass/inertia warning result. A `visual_static` DB03 row may only be
reported as ready for its declared Scenario Forge background scope; it cannot
upgrade DB01--DB04 to dynamic, articulated, or family ready.
