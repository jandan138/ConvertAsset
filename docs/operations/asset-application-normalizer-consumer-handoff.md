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

The role-scoped Scenario Forge path is narrower: immutable LabUtopia USD goes
through a ConvertAsset-owned package-local closure and `visual_static` overlay
before Scenario Forge consumes it as a background object. It is not a
dynamic-physics, articulated, or source-family readiness profile.

Supported input format:

- `.usd`
- `.usda`
- `.usdc`

Supported runtime/profile values:

- `--source-runtime isaac51`
- `--target-runtime isaac41`
- `--target-benchmark ebench-lift2`
- `--target-benchmark scenario-forge` only with an explicit role-specific
  admission contract

Supported asset classes:

- `rigid`
- `articulated`
- `auto`, when the static checks can infer enough evidence

Unsupported as ready package input:

- MJCF / URDF
- deformable, liquid, cloth, particle, granular assets
- USD assets whose required dependencies cannot be mirrored, safely pruned, waived, or
  blocked with evidence
- dynamic/EBench assets without an explicit benchmark task contract

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

## Scenario Forge Visual-Static Admission

Scenario Forge may consume an AAN package with
`--target-benchmark scenario-forge --asset-role visual_static` only when the
manifest declares its exact package scope through `asset_scope_prim_paths`.
This profile is for a background object; it does not request an EBench evaluator
or AAN-07 task contract.

The producer must provide:

- an immutable upstream source USD and its before/after SHA-256 integrity result;
- `--asset-scope-prim` values that identify the output asset scope explicitly;
- the `visual_static` role, which preserves visual/material/transform semantics
  while removing active scoped articulation, joint, rigid-body, and collision
  semantics only in the ConvertAsset-owned package overlay;
- `--runtime-python` and `--expected-runtime-version 4.1` for a final
  Isaac Sim 4.1 runtime claim; and
- if comparing a Scenario Forge integration log, a baseline log plus its composed
  `--warning-baseline-scope-prim` mapping.

The source physics audit and output-role admission are deliberately separate.
For example, a raw source can remain physics-blocked while its declared
`visual_static` package output passes with no active physics semantics. That
does not make the raw source dynamic-ready, articulated-ready, or family-ready.

AAN-03 isolates this role-specific package before the runtime gate. It composes
the package-local source closure, discovers the declared scope’s effective bound
material prims, opens a population-masked composed stage for those roots, and
writes a flattened package-local snapshot. The owned `asset.usd` overlay then
sublayers that snapshot rather than the full source scene. The manifest’s
`dependency_closure.scope_extraction` record identifies the strategy, retained
scope subtrees, retained material prims, and stage metadata.

Scope isolation is fail-closed: if the declared source scope cannot compose, a
bound material root is lost, or the scoped USDA cannot reopen, AAN blocks the
package. Collection bindings, external relationship targets, and instancing are
not grounds for a best-effort whole-scene fallback; they require explicit
composition and visual-preservation evidence before admission.

### Retained DB03 reference admission

The retained 2026-07-13 reference package is
[`LabUtopia_lab001_DryingBox_03_visual_static`](../records/evidence/2026-07-13-aan-dryingbox-family-admission/manifest.json).
It admits only `/World/DryingBox_03` as a Scenario Forge background
`visual_static` output. Its immutable raw source SHA-256 is
`b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2`; before
and after values are equal. The separate real DB01--DB04 source-family audit is
blocked (4/3/3/4 invalid rigid bodies, 14 total), so this manifest must not be
used to claim a dynamic-ready or family-ready DryingBox asset.

For the declared package scope, the output-role audit has zero active physics
residue and the visual-preservation fingerprint passes. The final runtime report
uses Isaac Sim Kit `4.1.0-rc.7+4.1.14801.71533b68.gl`: cold load, render, step,
and reset pass; the candidate has zero scoped negative-mass, invalid-inertia, or
small-sphere inertia events. Its warning diff records the composed Scenario
Forge baseline as 12 scoped events and the package candidate as 0 (12 removed,
0 introduced). The source-family audit, static report, package, render, and
warning diff are retained beside the [manifest](../records/evidence/2026-07-13-aan-dryingbox-family-admission/).

The runtime worker uses `os_exit_after_evidence` only after persisting the gate
report, to isolate an Isaac 4.1 native-plugin-unload crash. It is not evidence
of graceful `SimulationApp.close()` shutdown and it does not waive gates: a
missing report, failed gate, or nonzero worker/protocol result remains blocking.
This retained worker exited 0. Scenario Forge must consume this package and
manifest as-is, with no local physics repair or warning suppression.

## Input Contract

The caller owns:

| Input | Requirement |
|---|---|
| source USD | Must exist and use a supported USD extension |
| `asset_id` | Stable asset name for manifest, evidence, and downstream reports |
| `asset_class` | `rigid`, `articulated`, or `auto`; articulated assets require joint evidence |
| required prims | At least the asset root; a `visual_static` package also needs an explicit output scope |
| task contract | Required for dynamic EBench admission; JSON or simple YAML containing task metadata, required semantic prim roles, evaluator entrypoint, and metric |
| gates | Use `static,runtime,benchmark` for dynamic EBench ready packages; a Scenario Forge visual-static package uses `static,runtime` when runtime evidence is requested |

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
  asset.usd              # ConvertAsset-owned strong entry overlay
  deps/                 # present when USD/MDL/texture dependencies are copied
    usd/
      source_root.usd    # package-local immutable-source mirror used to compose closure
      scoped_source.usda # visual_static only: population-masked scope/material snapshot
    mdl/
    textures/
  task/                  # required for EBench; not applicable to visual_static Scenario Forge
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

The exact `deps/` contents are asset-dependent. Consumers should not hard-code MDL,
texture, source-root, or scoped-snapshot filenames. Read the manifest instead.
For `visual_static`, `asset.usd` composes the scoped snapshot, not the full
source root. The source mirror is not permission to edit the upstream LabUtopia
source; only the package overlay is owned by ConvertAsset.

## Manifest Contract

The manifest is the main machine-readable interface.

Required top-level fields for consumers:

| Field | Consumer use |
|---|---|
| `schema_version` | Must be `asset_application_normalizer.v1` for the current MVP |
| `asset_id`, `task_id`, `asset_role` | Report identity, task routing, and whether the package is dynamic or visual-static |
| `source` | Source path/hash/format/runtime lineage |
| `source_integrity` | Source SHA-256 before/after normalization; `unchanged` must be true |
| `target` | Runtime and benchmark profile |
| `entrypoints` | Package root USD and task file paths |
| `required_prim_paths` | Required prim records for the package |
| `asset_scope_prim_paths` | Exact output admission scope; required for role-scoped claims |
| `dependency_closure` | Missing, remote, mirrored, blocked, waived dependency state |
| `dependency_closure.scope_extraction` | For `visual_static`, population-masked scope/material snapshot strategy and retained roots |
| `material_closure` | Source material preservation, MDL/texture mirror, fallback/waiver/block state |
| `material_runtime_closure` | AAN-11 MDL transitive dependency, binding scope, runtime material compiler, and view evidence when the profile requires material runtime closure |
| `physics_closure` | Rigid body, collision, mass, inertia, and provenance records |
| `articulation_closure` | Articulation root, joint type/axis/limit/DOF records |
| `source_physics_audit` | Raw source-scoped diagnostic; a blocked source audit must not be relabeled as a family pass |
| `output_role_admission` | Role-specific package result, including zero active physics residue for `visual_static` |
| `normalization_actions`, `visual_preservation_fingerprint` | Package-overlay changes and source/package visual-preservation comparison |
| `stage_gates` | Per-stage pass/block/not-run evidence |
| `runtime_evidence` | Cold load, render readback, physics step, reset smoke |
| `runtime_evidence.physics_warning_gate`, `warning_diff` | Scoped PhysX warning categories, scope map, and baseline/candidate comparison |
| `benchmark_contract` | Task file and evaluator handoff status |
| `waivers`, `blocked_reasons` | Risk and blocker records |
| `claims_allowed`, `claims_forbidden` | Reporting boundary |

Consumers must not rely only on `overall_status`. They must inspect the relevant gate
records and claim boundary.

## Ready Decision

The following checklist is the dynamic EBench handoff checklist. A downstream
adapter may treat that kind of package as AAN-ready only when all checks below
pass:

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

For a Scenario Forge `visual_static` package, do not require or invent an
EBench task contract. Instead require all of the following:

1. `asset_role == "visual_static"` and the manifest declares
   `asset_scope_prim_paths`.
2. `source_integrity.unchanged == true`.
3. `output_role_admission.status == "pass"`, with no active rigid-body,
   collision, articulation, or joint semantics in the declared output scope.
4. `visual_preservation_fingerprint.status == "pass"`.
5. The manifest still exposes `source_physics_audit`; a source failure remains a
   diagnostic boundary and forbids dynamic/family claims.
6. If runtime is requested, the recorded actual runtime version satisfies the
   explicit Isaac Sim 4.1 profile gate and cold load, render, step, and reset
   all pass.
7. `runtime_evidence.physics_warning_gate` has zero scoped or unattributed
   negative-mass, invalid-inertia, and small-sphere-approximated-inertia events.
   A requested `warning_diff` must record zero candidate scoped events; a
   baseline cannot waive a candidate warning.

If any visual-static check fails, Scenario Forge must reject the package or ask
ConvertAsset to re-admit it. It must not repair the scene locally.

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
| `route_decision` | `source_mdl_native`, `source_mdl_mirrored`, `targeted_preview_fallback`, `package_preview_fallback`, or `blocked` |
| `source_material_completeness` | Whether the source package has missing helper MDL or MDL-internal textures, and whether they are active |
| `target_runtime_viability` | Required/background scoped runtime compiler and render verdict for the target Isaac profile |
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
- missing dependency cannot be assigned to active required, active background,
  inactive/residue, or unbound scope;
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

Consumers must not convert a raw `missing_material_refs` or `missing_textures` list
directly into a PreviewSurface/no-MDL decision. Use the AAN `route_decision` plus the
binding-scope and runtime-visual evidence. If a dependency is registry residue or
background-only and required surfaces render correctly, the consumer should preserve
the MDL route and retain the scoped warning. If the consumer registry cannot represent
that distinction, it should keep the asset blocked or request a re-export rather than
hand-editing USD/MDL paths downstream.

For Phase12 clean registry mapping, `passed` still means the exported fields are clean:
`missing_material_refs: []` and `missing_textures: []`, or an explicitly versioned
registry schema that can carry scoped background warnings without presenting them as
required-scope defects. A visually acceptable render can reject automatic fallback,
but it cannot by itself produce clean pass; the AAN evidence must also include active
dependency scope, required material binding, runtime compiler counters, and retained
target views.

When the consumer registry cannot represent scoped background warnings, request or use
an AAN clean re-export package instead of hand-editing USD/MDL/texture paths. The
soap-to-dish S2D-12 handoff is the reference pattern: native MDL is retained for the
required target, raw background missing refs are removed from the registry candidate,
`gltf/pbr.mdl` is recorded as an approved Isaac runtime module, and Phase13 compile
can reach `phase13_static_candidate_ready` with only downstream 13.6/13.8 gates left.

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
- a raw missing dependency list alone proves that no-MDL fallback is required;
- physical parameter parity with the source asset is achieved;
- runtime smoke is an EBench score.
- a passing pre-repaired overlay establishes readiness for a raw LabUtopia
  asset family;
- a `visual_static` background package is dynamic-physics-ready,
  articulated-ready, or family-ready;
- a baseline warning diff permits a scoped warning in the output package.

## Minimal Consumer Pseudocode

`load_aan_ready_package` below is intentionally an EBench dynamic-package
example: it requires AAN-07 task files. A Scenario Forge consumer must branch by
`asset_role` and apply the visual-static checklist above instead of fabricating
task files or restoring local physics.

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
