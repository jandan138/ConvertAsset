# 2026-06-30 AAN-07 Benchmark Contract

## Summary

Implemented `AAN-07-benchmark-contract`, the first benchmark handoff gate for Asset
Application Normalizer.

AAN-07 runs only when the caller requests the `benchmark` gate. It validates an explicit
task contract and writes the three files that a LabUtopia / EBench adapter needs to consume
the normalized package:

- `task/task_config.yaml`
- `task/required_prims.yaml`
- `task/evaluator.yaml`

The gate does not infer success predicates. Missing `--contract`, missing evaluator entrypoint,
missing metric, or required prim mappings that do not exist in the packaged USD are blocking.

## Code Changes

- Added `convert_asset/asset_application_normalizer/benchmark_contract.py`.
  - Loads JSON or simple YAML task contracts.
  - Validates task metadata, required semantic prim roles, evaluator entrypoint, and metric.
  - Opens the packaged `asset.usd` with lazy `pxr.Usd` imports to verify prim mappings.
  - Writes task handoff YAML files only after all checks pass.
- Added `MILESTONE_AAN07 = "AAN-07-benchmark-contract"`.
- Extended `evidence_manifest.py` with `benchmark_contract` and `task_contract_report`.
- Updated `pipeline.py` to run AAN-03 -> AAN-04 -> AAN-05 -> optional AAN-06 -> optional AAN-07.
- Added AAN-07 pass and blocked tests in `tests/test_asset_application_normalizer_cli.py`.
- Follow-up from EBench-01 retained evidence: `entrypoints.required_prims` is now
  written as `task/required_prims.yaml`, so downstream consumers can verify the
  full task handoff from manifest alone.

## DryingBox Evidence

Evidence directory:

`docs/records/evidence/2026-06-30-aan-07-dryingbox-benchmark-contract/`

Artifacts:

- `dryingbox_contract.json`
- `overlay_level1_poc_dryingbox_01_benchmark.json`
- `task/task_config.yaml`
- `task/required_prims.yaml`
- `task/evaluator.yaml`

Observed DryingBox result:

- AAN-03: pass
- AAN-04: pass
- AAN-05: pass
- AAN-07: pass
- Task files written: 3
- Required prim roles verified: 6
- Evaluator entrypoint: `ebench.evaluators.lift2:DryingBoxEvaluator`
- Metric: `door_state_success`

Required prim mapping used for the first DryingBox handoff:

| Role | Prim path |
|---|---|
| `asset_root` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01` |
| `manipulated_body` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01/body/Group/door/mesh` |
| `collision_root` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01/body/Group/door/mesh` |
| `spawn_anchor` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01` |
| `goal_target` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01/body/Group/door/mesh` |
| `articulation_root` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01` |

## Claim Boundary

AAN-07 pass means the normalized package now has an explicit EBench adapter handoff contract.
It does not prove:

- official EBench leaderboard comparability
- real EBench episode execution or score aggregation
- full visual material parity
- full physics parameter parity
- exact Isaac Sim 4.1 binary conformance without an environment fingerprint

Those remain separate runtime / evaluator / replication claims.

2026-07-01 follow-up: DryingBox was rerun with `static,runtime,benchmark` gates in
[AAN-07 DryingBox Runtime-Ready Refresh](2026-07-01-aan-07-dryingbox-runtime-ready.md).
That retained run adds AAN-06 runtime smoke evidence to the first acceptance asset and
lets the PM evidence table classify `DryingBox_01_overlay` as `ready`.

## Verification

Commands run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_benchmark_gate_writes_ebench_task_contract tests/test_asset_application_normalizer_cli.py::test_normalize_asset_benchmark_gate_blocks_without_evaluator_entrypoint -q
python -m pytest tests/test_asset_application_normalizer_cli.py -q
./scripts/isaac_python.sh ./main.py normalize-asset /cpfs/shared/simulation/zhuzihou/dev/_datasets/EBench-Assets-Overlay/labutopia_level1_poc/assets/scene_usds/labutopia/level1_poc/lab_001/scene.usda --out /tmp/aan07_real_packages/overlay_level1_poc_dryingbox_01_benchmark --asset-id DryingBox_01_overlay --asset-class articulated --source-runtime isaac51 --target-runtime isaac41 --target-benchmark ebench-lift2 --task-id Lift2.DryingBox --contract /tmp/aan07_real_packages/dryingbox_contract.json --required-prim /World/labutopia_level1_poc/obj_obj_DryingBox_01 --gates static,benchmark --evidence-out /tmp/aan07_real_packages/overlay_level1_poc_dryingbox_01_benchmark/manifest.json
./scripts/isaac_python.sh ./main.py normalize-asset /cpfs/shared/simulation/zhuzihou/dev/_datasets/EBench-Assets-Overlay/labutopia_level1_poc/assets/scene_usds/labutopia/level1_poc/lab_001/scene.usda --out /tmp/aan07_real_packages/overlay_level1_poc_dryingbox_01_benchmark_ebench01_rerun --asset-id DryingBox_01_overlay --asset-class articulated --source-runtime isaac51 --target-runtime isaac41 --target-benchmark ebench-lift2 --task-id Lift2.DryingBox --contract /tmp/aan07_real_packages/dryingbox_contract.json --required-prim /World/labutopia_level1_poc/obj_obj_DryingBox_01 --gates static,benchmark --evidence-out /tmp/aan07_real_packages/overlay_level1_poc_dryingbox_01_benchmark_ebench01_rerun/manifest.json
```
