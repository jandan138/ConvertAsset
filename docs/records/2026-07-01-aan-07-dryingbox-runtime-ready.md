# 2026-07-01 AAN-07 DryingBox Runtime-Ready Refresh

## Summary

Reran the first DryingBox AAN package with `static,runtime,benchmark` gates so the
first acceptance asset has the same runtime-ready evidence level as the AAN-08
replication assets.

The earlier AAN-07 retained manifest proved the EBench task contract, but did not run
runtime smoke. This refresh keeps the same source asset, task id, target runtime,
target benchmark, contract, and required prim, and adds AAN-06 runtime evidence before
the AAN-07 benchmark contract.

Observed result:

| Field | Value |
|---|---|
| Asset | `DryingBox_01_overlay` |
| Overall status | `pass` |
| AAN-03 USD closure | `pass` |
| AAN-04 material closure | `pass` |
| AAN-05 physics static | `pass` |
| AAN-06 runtime smoke | `pass` |
| AAN-07 benchmark contract | `pass` |
| Runtime status | `pass` |
| Render readback status | `pass` |
| Render non-background ratio | `0.76343536` |
| Render bbox ratio | `0.84765625` |
| Benchmark contract status | `pass` |

## Retained Evidence

Evidence directory:

`docs/records/evidence/2026-07-01-aan-07-dryingbox-runtime-ready/`

Artifacts:

- `dryingbox_runtime_ready_manifest.json`
- `runtime_report.json`
- `render.png`
- `package/asset.usd`
- `package/task/task_config.yaml`
- `package/task/required_prims.yaml`
- `package/task/evaluator.yaml`
- `package/evidence/runtime_smoke/{report.json,render.png,stdout.log,stderr.log}`

The full package copy is retained under `package/` so the evidence does not depend on
the `/tmp` output directory.

## Verification

Command run:

```bash
./scripts/isaac_python.sh ./main.py normalize-asset /cpfs/shared/simulation/zhuzihou/dev/_datasets/EBench-Assets-Overlay/labutopia_level1_poc/assets/scene_usds/labutopia/level1_poc/lab_001/scene.usda --out /tmp/aan07_real_packages/overlay_level1_poc_dryingbox_01_runtime_ready --asset-id DryingBox_01_overlay --asset-class articulated --source-runtime isaac51 --target-runtime isaac41 --target-benchmark ebench-lift2 --task-id Lift2.DryingBox --contract docs/records/evidence/2026-06-30-aan-07-dryingbox-benchmark-contract/dryingbox_contract.json --required-prim /World/labutopia_level1_poc/obj_obj_DryingBox_01 --gates static,runtime,benchmark --evidence-out docs/records/evidence/2026-07-01-aan-07-dryingbox-runtime-ready/dryingbox_runtime_ready_manifest.json
```

Evidence audit:

```bash
python - <<'PY'
import json
from pathlib import Path
manifest = json.loads(Path("docs/records/evidence/2026-07-01-aan-07-dryingbox-runtime-ready/dryingbox_runtime_ready_manifest.json").read_text())
assert manifest["overall_status"] == "pass"
assert manifest["runtime_evidence"]["status"] == "pass"
assert manifest["runtime_evidence"]["render_readback"]["status"] == "pass"
assert manifest["benchmark_contract"]["status"] == "pass"
assert all(gate["status"] == "pass" for gate in manifest["stage_gates"])
PY
```

## 2026-07-13 Scope Correction

This retained result remains valid for the source and scope shown in the command
above: the already repaired `DryingBox_01_overlay` at
`/World/labutopia_level1_poc/obj_obj_DryingBox_01`. It does not test the raw
20260707 LabUtopia source
`/cpfs/shared/simulation/zhuzihou/dev/LabUtopia/outputs/usd_asset_packages/lab_001_localized_20260707/lab_001.usd`
or any raw DB01--DB04 family member.

The original record described this as a “DryingBox” refresh and a “first
acceptance asset.” That short form omitted two material facts: the input was a
pre-repaired overlay rather than raw `lab_001.usd`, and the evidence was only
for its declared overlay prim scope. Consequently, the result was incorrectly
reused as support for a broader “DryingBox normalization-ready” statement.

Correct interpretation:

> Retained readiness evidence applies only to the pre-repaired
> `DryingBox_01_overlay` source and its declared overlay prim scope. It does
> not establish normalization readiness for the raw LabUtopia `lab_001.usd`
> DryingBox family.

The raw-family audit and the distinct DB03 `visual_static` Scenario Forge
package are recorded in
`docs/records/2026-07-13-aan-dryingbox-family-admission-and-claim-correction.md`.
That record must retain its own source hash, scope map, output-role admission,
and Isaac Sim 4.1 runtime/warning-diff evidence before any DB03 runtime-ready
claim is made.

## PM Table Impact

After this run, the AAN-09.5 PM evidence table was regenerated with this refreshed
DryingBox manifest. The PM table now reports:

- `ready`: 3 assets (`DryingBox_01_overlay`, `Beaker_01`, `MuffleFurnace`)
- `blocked`: 1 asset (`RemoteUriBlocked`)
- `waiver_count`: 0
- failure mode: `aan03_block_remote_uri`

## Claim Boundary

This refresh proves the retained pre-repaired `DryingBox_01_overlay` package has
runtime smoke and benchmark-contract evidence at its declared overlay scope. It
does not claim readiness for raw `lab_001.usd` DB01--DB04, official EBench
leaderboard comparability, full visual material parity, full physical-parameter
parity, or exact Isaac Sim 4.1 binary conformance beyond the recorded environment
evidence.
