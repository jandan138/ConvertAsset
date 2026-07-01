# 2026-06-30 AAN-08 Replication Set

## Summary

Implemented and retained `AAN-08-replication-set` evidence for two non-DryingBox
LabUtopia USD assets:

- `MuffleFurnace`: non-DryingBox articulated asset with authored articulation root and
  revolute joint axis/limits.
- `Beaker_01`: transparent rigid beaker prop with local MDL mirror, collision, render
  visibility, and generated mass/inertia provenance.

Both assets produced independent AAN packages, manifests, runtime smoke evidence, render
readback PNGs, and EBench task handoff files. This proves the current AAN path is no
longer DryingBox-only.

## Code Changes

- Extended `convert_asset/asset_application_normalizer/physics_checks.py`.
  - Rigid bodies with missing, zero, non-positive, or non-finite mass/inertia now get
    package-authored `PhysicsMassAPI` values.
  - Generated values use `bbox_shell_density_template_v0`.
  - Manifest records `value_source=derived`, bbox dimensions, bbox volume, effective
    volume, density template, shell occupancy, and generated fields.
  - Articulation semantics remain strict: joint type/axis/limit are not guessed.
- Added regression tests in `tests/test_asset_application_normalizer_cli.py`.
  - Rigid prop without MassAPI generates mass/inertia and writes them into package USD.
  - Articulated body with invalid zero mass/inertia generates derived values while
    preserving authored joint axis/limit.

## Retained Evidence

Evidence directory:

`docs/records/evidence/2026-06-30-aan-08-replication-set/`

Key artifacts:

- `replication_set_summary.json`
- `muffle_furnace_manifest.json`
- `beaker_01_manifest.json`
- `contracts/muffle_furnace_contract.json`
- `contracts/beaker_01_contract.json`
- `runtime/muffle_furnace_runtime_report.json`
- `runtime/muffle_furnace_render.png`
- `runtime/beaker_01_runtime_report.json`
- `runtime/beaker_01_render.png`
- `task_files/*/{task_config.yaml,required_prims.yaml,evaluator.yaml}`
- `packages/muffle_furnace/`
- `packages/beaker_01/`

Package directories from the retained run:

- `/tmp/aan08_real_packages/muffle_furnace`
- `/tmp/aan08_real_packages/beaker_01`

The full package directories were also copied under `packages/` in the retained evidence
directory so the audit does not depend on `/tmp`.

## Observed Results

| Asset | Class | AAN-03 | AAN-04 | AAN-05 | AAN-06 | AAN-07 | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| `MuffleFurnace` | articulated | pass | pass | pass | pass | pass | 1 articulation root, 3 joints, 1 controllable DOF; 3 mass/inertia records generated from bbox template |
| `Beaker_01` | rigid transparent prop | pass | pass | pass | pass | pass | 1 local mirrored MDL, opacity strategy detected, render readback visible; mass/inertia generated from bbox template |

Runtime readback metrics:

| Asset | non-background ratio | bbox ratio | Render SHA-256 |
|---|---:|---:|---|
| `MuffleFurnace` | `0.4051857` | `0.60273743` | `3c4f6e6a58608fc5ebeddb3a66ef2a794b98ad7363c1678b7bbc22a4396df4ef` |
| `Beaker_01` | `0.30619049` | `0.41808701` | `6f55cd79e1ec19dccbdcbe041bd9dedfe6382eaddd5c541d520c86b9b48a010f` |

Local visual QA:

- `MuffleFurnace`: target cabinet/furnace body and door are visible and framed. The image
  supports runtime visibility smoke, not full visual material parity.
- `Beaker_01`: transparent beaker rim, wall, outline, and internal geometry are visible.
  It is not all-background or fully transparent.

## Verification

Commands run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_generates_mass_inertia_for_rigid_prop_without_mass_api -q
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_generates_invalid_mass_inertia_for_articulated_bodies -q
python -m pytest tests/test_asset_application_normalizer_cli.py -q
./scripts/isaac_python.sh ./main.py normalize-asset /cpfs/shared/simulation/zhuzihou/dev/_datasets/LabUtopia-Dataset/Instruments/MuffleFurnace/MuffleFurnace.usd --out /tmp/aan08_real_packages/muffle_furnace --asset-id MuffleFurnace --asset-class articulated --source-runtime isaac51 --target-runtime isaac41 --target-benchmark ebench-lift2 --task-id AAN08.MuffleFurnaceDoor --contract docs/records/evidence/2026-06-30-aan-08-replication-set/contracts/muffle_furnace_contract.json --required-prim /group_002 --required-prim /group_002/Group --required-prim /group_002/Group/mesh_000 --required-prim /group_002/Group/RevoluteJoint --gates static,runtime,benchmark --evidence-out docs/records/evidence/2026-06-30-aan-08-replication-set/muffle_furnace_manifest.json
./scripts/isaac_python.sh ./main.py normalize-asset /cpfs/shared/simulation/zhuzihou/dev/_datasets/LabUtopia-Dataset/Instruments/Beaker_01/Beaker_01.usd --out /tmp/aan08_real_packages/beaker_01 --asset-id Beaker_01 --asset-class rigid --source-runtime isaac51 --target-runtime isaac41 --target-benchmark ebench-lift2 --task-id AAN08.TransparentBeaker --contract docs/records/evidence/2026-06-30-aan-08-replication-set/contracts/beaker_01_contract.json --required-prim /group_000 --required-prim /group_000/mesh_000 --gates static,runtime,benchmark --evidence-out docs/records/evidence/2026-06-30-aan-08-replication-set/beaker_01_manifest.json
```

Additional evidence audit:

```bash
python - <<'PY'
import json
from pathlib import Path
base = Path("docs/records/evidence/2026-06-30-aan-08-replication-set")
summary = json.loads((base / "replication_set_summary.json").read_text())
assert summary["status"] == "pass"
for asset in summary["assets"]:
    assert asset["overall_status"] == "pass"
    assert all(gate["status"] == "pass" for gate in asset["stage_gates"])
    assert asset["runtime_summary"]["status"] == "pass"
    assert asset["benchmark_status"] == "pass"
PY
```

## Claim Boundary

AAN-08 pass means:

- AAN can normalize at least one non-DryingBox articulated LabUtopia USD and one transparent
  rigid Beaker USD through the same package/manifest/runtime/benchmark contract path.
- The new behavior is contract-driven: no DryingBox path or asset name was added.
- Missing or invalid mass/inertia values can be generated with explicit provenance.

It does not prove:

- official EBench leaderboard comparability;
- full visual material parity;
- exact physical parameter parity with the original source;
- arbitrary USD, URDF, MJCF, MuJoCo, or Genesis support.

## Follow-ups

- `AAN-09 Negative Gate`: retain one stable blocked/waived negative example.
- Add a drawer/prismatic asset when LabUtopia inventory has a reviewed source with real
  axis/limit/reset semantics.
- If product needs physical-parameter parity claims, replace bbox template generation with
  source-authored values or reviewed manual overrides.
