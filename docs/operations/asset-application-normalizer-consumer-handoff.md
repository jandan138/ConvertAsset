# Asset Application Normalizer Consumer Handoff

This document is the public handoff contract for downstream projects that consume
AAN output, such as EBench, EOS, LabUtopia, GenManip, or future benchmark adapters.

Do not treat ConvertAsset's internal module layout as the integration surface. The
integration surface is the CLI, the package directory, the manifest path, and the task
files.

## Supported Scope

Current supported path:

```text
Isaac 5.1-oriented USD source
  -> ConvertAsset AAN package
  -> EBench / Isaac Sim 4.1 target profile
```

Supported input format:

- `.usd`
- `.usda`
- `.usdc`

Supported runtime/profile values:

- `--source-runtime isaac51`
- `--target-runtime isaac41`
- `--target-benchmark ebench-lift2`

Supported asset classes:

- `rigid`
- `articulated`
- `auto`, when the static checks can infer enough evidence

Unsupported as ready package input:

- MJCF / URDF
- deformable, liquid, cloth, particle, granular assets
- USD assets whose required dependencies cannot be mirrored, safely pruned, waived, or
  blocked with evidence
- assets without an explicit benchmark task contract

## Producer Command

Use the existing Isaac Python wrapper. Do not modify the Isaac / conda environment for
AAN handoff runs.

```bash
./scripts/isaac_python.sh ./main.py normalize-asset <source_usd> \
  --out <package_dir> \
  --asset-id <asset_id> \
  --asset-class rigid|articulated|auto \
  --source-runtime isaac51 \
  --target-runtime isaac41 \
  --target-benchmark ebench-lift2 \
  --task-id <task_id> \
  --contract <task_contract.json|yaml> \
  --required-prim <prim_path> \
  --gates static,runtime,benchmark \
  --evidence-out <package_or_records_manifest.json>
```

Use `--gates static,runtime,benchmark` for a ready handoff. `static,benchmark` can
prove task files exist, but it does not prove runtime readiness.

## Official Soap-To-Dish Handoff Example

2026-07-05 soap-to-dish is the first official EBench scene repair that uses the
formal no-MDL + AAN package route instead of a temporary `/tmp` artifact.

Registry update handoff:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/evidence/registry_handoff.yaml
```

Canonical package:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/package
```

Key acceptance values:

| Field | Value |
|---|---|
| prior registry entry | `official_ebench_scene@e1cf0d5b4d76` |
| replacement candidate | `official_ebench_scene@18bf1ffa8d13` |
| `dependency_closure.missing_material_refs` | `[]` |
| `dependency_closure.missing_textures` | `[]` |
| `material_runtime_closure.status` | `pass` |
| `physics_closure.status` | `pass` |
| `runtime_evidence.status` | `pass` |
| `runtime_evidence.render_readback.status` | `pass` |

The route intentionally does not claim full material parity. It claims that the
package has no active missing MDL or texture dependency, opens in the target runtime,
renders nonblank readback evidence, and preserves the no-full-parity boundary.

## Input Contract

The caller owns:

| Input | Requirement |
|---|---|
| source USD | Must exist and use a supported USD extension |
| `asset_id` | Stable asset name for manifest, evidence, and downstream reports |
| `asset_class` | `rigid`, `articulated`, or `auto`; articulated assets require joint evidence |
| required prims | At least the asset root; more roles should be expressed in the task contract |
| task contract | JSON or simple YAML containing task metadata, required semantic prim roles, evaluator entrypoint, and metric |
| gates | Use `static,runtime,benchmark` for ready packages |

Do not rely on AAN to infer success predicates. The benchmark contract must provide the
task/evaluator meaning.

## Output Package Contract

A ready handoff is a pair:

```text
package_dir + manifest_path
```

`manifest_path` may live inside the package, for example `evidence/manifest.json`, or
in a retained records directory. Consumers must receive it explicitly and must not infer
it from `/tmp` paths.

A ready package must contain:

```text
<package_dir>/
  asset.usd
  deps/                 # present when USD/MDL/texture dependencies are copied
    usd/
    mdl/
    textures/
  task/
    task_config.yaml
    required_prims.yaml
    evaluator.yaml
  evidence/
    runtime_smoke/
      report.json
      render.png
      stdout.log
      stderr.log
```

The exact `deps/` contents are asset-dependent. Consumers should not hard-code MDL or
texture filenames. Read the manifest instead.

## Manifest Contract

The manifest is the main machine-readable interface.

Required top-level fields for consumers:

| Field | Consumer use |
|---|---|
| `schema_version` | Must be `asset_application_normalizer.v1` for the current MVP |
| `asset_id`, `task_id` | Report identity and task routing |
| `source` | Source path/hash/format/runtime lineage |
| `target` | Runtime and benchmark profile |
| `entrypoints` | Package root USD and task file paths |
| `required_prim_paths` | Required prim records for the package |
| `dependency_closure` | Missing, remote, mirrored, blocked, waived dependency state |
| `material_closure` | Source material preservation, MDL/texture mirror, fallback/waiver/block state |
| `material_runtime_closure` | AAN-11 MDL transitive dependency, binding scope, runtime material compiler, and view evidence when the profile requires material runtime closure |
| `physics_closure` | Rigid body, collision, mass, inertia, and provenance records |
| `articulation_closure` | Articulation root, joint type/axis/limit/DOF records |
| `stage_gates` | Per-stage pass/block/not-run evidence |
| `runtime_evidence` | Cold load, render readback, physics step, reset smoke |
| `benchmark_contract` | Task file and evaluator handoff status |
| `waivers`, `blocked_reasons` | Risk and blocker records |
| `claims_allowed`, `claims_forbidden` | Reporting boundary |

Consumers must not rely only on `overall_status`. They must inspect the relevant gate
records and claim boundary.

## Ready Decision

A downstream adapter may treat a package as AAN-ready only when all checks below pass:

1. `schema_version == "asset_application_normalizer.v1"`.
2. `target.target_runtime_profile == "isaac41"`.
3. `target.target_benchmark_profile == "ebench-lift2"`.
4. `overall_status == "pass"` or the project explicitly supports
   `ready_with_waivers`.
5. AAN-03 / AAN-04 / AAN-05 / AAN-06 / AAN-07 stage gates are present and `pass`.
6. `runtime_evidence.status == "pass"`.
7. `runtime_evidence.render_readback.status == "pass"`.
8. `benchmark_contract.status == "pass"`.
9. `entrypoints.root_usd`, `entrypoints.task_config`, `entrypoints.required_prims`,
   and `entrypoints.metric_evaluator` resolve inside the package.
10. `blocked_reasons` is empty.
11. No required dependency is unresolved, unauthorized, or package-escaping.
12. Any waiver is explicitly accepted by the consuming project and its
    `claims_forbidden` entries remain enforced.
13. If the target profile or handoff explicitly requires `AAN-11`, then
    `material_runtime_closure.status == "pass"`, required-material MDLC/module/texture/
    shader-node error counts are zero, and `full_material_parity_claimed` remains
    `false` unless a separate parity experiment exists.

If any required check fails, the consumer should produce a structured blocker instead
of applying local USD/MDL/physics fixes.

## AAN-11 Material Runtime Closure

`AAN-11 Material Runtime Closure` is a post-closeout follow-up. It does not reopen
the Phase 1 AAN handoff, but a consumer profile may require it for assets whose
material appearance matters or whose retained runtime logs show MDLC/shader/texture
errors.

When present, consumers should read `material_runtime_closure` as the material runtime
handoff surface:

| Field | Consumer meaning |
|---|---|
| `status` | `pass` means required target materials have closed runtime dependency evidence |
| `claim_level` | Scope of the material runtime claim, usually required surfaces only |
| `full_material_parity_claimed` | Must stay `false` unless a separate source-vs-target parity experiment was run |
| `root_mdl_assets` | Source/package MDL files that seeded the runtime dependency graph |
| `imported_mdl_modules` | Helper MDL modules mirrored or resolved through approved runtime-root evidence, including runtime path/hash when native |
| `mdl_texture_assets` | MDL-internal texture files mirrored with package path and hash |
| `mirror_actions` | Source-to-package helper MDL or MDL-internal texture copies performed by AAN |
| `rewrite_actions` | Any MDL text rewrite, including before/after hash and rule |
| `binding_scope` | Required prim to effective material binding graph; `unknown_required_prims` blocks required render surfaces, while `non_render_required_prims` records existing joint/helper prims that do not need material binding |
| `runtime_compiler` | MDLC, USD_MDL, failed shader node, and missing texture counters grouped by required/background scope |
| `view_evidence` | Front/door-facing/orbit/transparent render artifacts and material visibility metrics |

Consumer hard blockers when AAN-11 is required:

- required material helper MDL or MDL-internal texture is unresolved;
- runtime compiler log contains MDLC/module/texture/shader-node errors for a required
  material;
- package USD/MDL text still references `/cpfs/...`, `omniverse://`, `http(s)://`,
  unauthorized absolute paths, or package escapes;
- required render prim material binding cannot be traced to the material that was
  checked;
- the adapter would need to hand-edit USD, MDL, texture paths, or material bindings.

`non_render_required_prims` is not itself a material blocker. It exists so articulated
tasks can keep joint/helper paths in `required_prims.yaml` while AAN-11 still checks
materials only on renderable target surfaces.

Allowed warnings must stay scoped: background-only material warnings, renderer
deprecation warnings, or explicit PreviewSurface fallback are acceptable only when
`claims_forbidden` preserves the no-full-material-parity boundary.

## Task File Contract

Consumers may read these files directly:

```text
task/task_config.yaml
task/required_prims.yaml
task/evaluator.yaml
```

Expected consumer behavior:

- use `task_config.yaml` for task id, asset id, runtime, benchmark, and package root;
- use `required_prims.yaml` for role-to-prim mapping;
- use `evaluator.yaml` for evaluator entrypoint and metric name;
- verify referenced prim paths exist in `asset.usd`;
- preserve AAN `claims_forbidden` in downstream evidence.

Consumers should not hand-edit these files for DryingBox-specific paths. If the mapping
is wrong, rerun AAN with a corrected task contract or mark the package blocked.

## Return Codes

| Code | Meaning |
|---:|---|
| `0` | Pass, or pass-with-waiver if a future waiver path explicitly allows it |
| `2` | Invalid arguments or unsupported input/profile |
| `3` | Runtime/open exception |
| `4` | Contract or gate failure |
| `5` | Blocked; requires mirror, prune, waiver, manual contract, or code support |

Downstream automation should retain the manifest even for code `5` when AAN writes one.
Blocked manifests are useful evidence, not a failed handoff protocol.

## PM Evidence Table

Use the PM table for reports and acceptance dashboards:

```bash
python -m convert_asset.asset_application_normalizer.pm_evidence_table \
  --manifest <ready_or_blocked_manifest.json> \
  --negative-summary <negative_gate_summary.json> \
  --json-out <pm_evidence_table.json> \
  --markdown-out <pm_evidence_table.md>
```

Current retained table:

`docs/records/evidence/2026-07-01-aan-09-5-pm-evidence-table/pm_evidence_table.md`

The table status is report-facing:

| PM status | Meaning |
|---|---|
| `ready` | Runtime smoke and benchmark contract evidence are present |
| `contract_ready_runtime_pending` | Task contract exists, but runtime smoke is not present |
| `ready_with_waivers` | Only scoped claims are allowed; waiver boundary applies |
| `blocked` | Do not hand to EBench as ready |

## MJCF Scout Boundary

`convert_asset.asset_application_normalizer.mjcf_scout` is not a ready-package
producer. It only emits an MJCF inventory and semantic gap manifest:

```bash
python -m convert_asset.asset_application_normalizer.mjcf_scout <source.xml> \
  --out <mjcf_scout_manifest.json>
```

Consumers must not treat `overall_status=semantic_gap_report_only` as an EBench-ready
asset. It is planning evidence for future MJCF adapters.

## Claims

Allowed downstream claim:

> This project consumes AAN-ready packages and preserves AAN evidence, waivers,
> blockers, and claim boundaries.

Forbidden downstream claims unless separately proven:

- arbitrary USD conversion is supported;
- MJCF / URDF conversion is supported;
- AutoBio official reproduction is supported;
- official EBench leaderboard comparability is achieved;
- full visual material parity is achieved;
- AAN-06 render smoke alone proves material runtime compiler cleanliness;
- physical parameter parity with the source asset is achieved;
- runtime smoke is an EBench score.

## Minimal Consumer Pseudocode

```python
from pathlib import Path
import json


def load_aan_ready_package(package_dir: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    gate_status = {
        gate["stage"]: gate["status"]
        for gate in manifest.get("stage_gates", [])
    }
    required_gates = [
        "usd_closure",
        "material_closure",
        "physics_static",
        "runtime_smoke",
        "benchmark_contract",
    ]
    if any(gate_status.get(stage) != "pass" for stage in required_gates):
        raise RuntimeError(f"AAN package is not ready: {gate_status}")
    if manifest.get("blocked_reasons"):
        raise RuntimeError(f"AAN package is blocked: {manifest['blocked_reasons']}")
    for key in ("root_usd", "task_config", "required_prims", "metric_evaluator"):
        rel = manifest["entrypoints"][key]
        if not (package_dir / rel).exists():
            raise FileNotFoundError(f"missing AAN entrypoint {key}: {rel}")
    return manifest
```

This pseudocode is intentionally strict. Downstream projects can add waiver support
only when they also preserve forbidden claims.
