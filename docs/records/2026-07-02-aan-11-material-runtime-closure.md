# 2026-07-02 AAN-11 Material Runtime Closure Follow-up

## Summary

Open `AAN-11 Material Runtime Closure` as a numbered follow-up after AAN Phase 1
closeout. This does not reopen the whole AAN plan, nor does it rename completed
`AAN-04 Material Closure` or `AAN-06 Runtime Smoke`.

The problem being closed is narrower and concrete: retained runtime evidence can pass
AAN-06 load/render/step/reset while required materials still have runtime MDLC helper
module, MDL-internal texture, shader-node, binding-scope, or red/error fallback
problems. AAN-11 turns those material runtime gaps into explicit static and runtime
gates with evidence.

## Numbering Decision

The multi-agent review proposed three names:

- `AAN-04R`: accurate for the static MDL transitive dependency part.
- `AAN-06R`: accurate for the runtime compiler/log/render evidence part.
- `AAN-11`: cleanest product and project numbering because AAN Phase 1 is already
  closed and should not be reopened.

Decision: use `AAN-11-material-runtime-closure` externally, with numbered internal
steps `AAN-11.1` to `AAN-11.7`. In future pipeline execution, AAN-11 logically sits
after AAN-04 source material closure and before, or alongside, AAN-06 runtime smoke
evaluation.

## Scope

AAN-11 owns:

- recursive MDL `import` / `using` graph inventory for package materials;
- MDL-internal texture literal closure, including case-sensitive path handling;
- deterministic helper MDL and texture mirror into package-local paths;
- tightly scoped MDL rewrite when mirror alone cannot preserve runtime semantics;
- required prim to effective material binding-scope audit;
- runtime compiler/log parsing for MDLC, USD_MDL, failed shader node, and missing
  texture errors;
- front/door-facing, orbit, and transparent-object material visibility evidence.

AAN-11 does not own:

- arbitrary visual material parity or pixel-perfect comparison;
- rewriting source dataset files;
- downstream EBench/LabUtopia local material repair;
- full-scene background material perfection when the task scope only requires target
  asset surfaces;
- MJCF / URDF / Genesis adapters.

## Planned Steps And Acceptance

| Step | Name | Acceptance criteria | Blocked criteria |
|---|---|---|---|
| `AAN-11.1` | MDL Runtime Graph Inventory | Roots come from `material_closure[*].source_mdl_assets` and package `deps/mdl/**/*.mdl`; recursive scan covers `import`, `using`, and non-empty `texture_2d("...")`; native MDL stdlib modules are classified without mirroring | Required material import/texture not scanned; comments or empty uniforms become false missing deps; graph can loop forever |
| `AAN-11.2` | Transitive Mirror | Every dependency is `mirrored`, `native_runtime_module`, `waived`, or `blocked`; source path, package path, sha256, and `mirror_actions` are recorded; mirror preserves owning MDL relative path semantics where possible | `local_missing` remains in pass manifest; same-name different-hash ambiguity is ignored; required deps rely on external source tree at runtime; unproven Isaac runtime modules are hard-coded as native |
| `AAN-11.3` | Safe Rewrite | Rewrites are only used for package escape, conflict, or known-safe import fixes; every rewrite has rule, before/after hash, affected lines, and risk note; source tree is unchanged | Generic import rewriting without evidence; KooPbr-specific fix generalized blindly; source files are modified |
| `AAN-11.4` | Binding Scope Audit | Required prim/render mesh effective materials are traced, including direct/inherited binding and binding strength; compiler errors can be grouped by required vs background scope | Required material binding cannot be traced; unintended override hides the intended material; background error blocks required asset without scope evidence |
| `AAN-11.5` | Runtime Compiler Gate | Runtime logs record counters for stderr bytes, error/warning, MDLC, USD_MDL, failed shader node, missing texture, and exemplar line hashes; required material error count is zero | Required material has module, texture, shader-node, USD_MDL invalid, or red/error fallback evidence |
| `AAN-11.6` | Multi-view Material Evidence | Adds front/door-facing or transparent-object views in addition to orbit; records camera pose, bbox source, render hash, foreground RGB/chroma, non-background ratio, bbox ratio, and relevant red/transparent metrics | Render is blank/all-background; expected material visibility fails; views are not reproducible or cannot be linked to target prim |
| `AAN-11.7` | Replication And Negative Gate | DryingBox passes first; MuffleFurnace proves MDL-internal texture closure; Beaker_01 proves empty texture uniforms do not false-block; a missing helper/texture fixture blocks cleanly | Only DryingBox works; replication needs manual USD/MDL edits; negative case is marked ready |

## First Acceptance Assets

1. `DryingBox_01_overlay`: first acceptance. It must close current helper MDL and
   texture gaps exposed by retained runtime logs, including `ad_3dsmax_maps.mdl`,
   `ad_3dsmax_materials.mdl`, `vray_maps.mdl`, `vray_materials.mdl`,
   `OmniPBR_ClearCoat.mdl`, `image1.JPG`, `image3.jpg`, `image4.jpg`,
   `Steel_Stainless_ORM.png`, `Steel_Stainless_N.png`, and other image/metal
   texture files discovered by recursive scan. The implementation must classify the
   whole discovered graph, not hard-code only this list.
2. `MuffleFurnace`: articulated replication asset. It must prove AAN-11 is not
   DryingBox-specific by catching MDL-internal texture paths such as nested folder
   resources.
3. `Beaker_01`: transparent rigid replication asset. Empty MDL texture uniforms must
   not be treated as missing files, and render evidence must show rim/outline or
   equivalent target visibility.

## Hard Blockers

- Required helper MDL, MDL-internal texture, or effective required material binding is
  unresolved.
- Package USD/MDL text still references unauthorized absolute paths, `/cpfs/...`,
  `omniverse://`, `http(s)://`, or package escapes.
- Runtime log has MDLC/module/texture/shader-node error for required materials.
- Required material shows red/error fallback evidence.
- Rewrite lacks before/after hash and rule provenance.
- The workflow requires modifying source dataset files.
- EBench/LabUtopia must hand-edit USD, MDL, texture path, or material binding.

## Temporary Waivers

Temporary waiver is allowed only when it is scoped and changes forbidden claims:

- background-only or unbound material warnings when required material evidence is clean;
- renderer/plugin/deprecation warnings unrelated to material resolution;
- unsupported advanced material features such as clearcoat, anisotropy, or procedural
  noise when source assets are preserved and PreviewSurface fallback is explicit;
- material visibility pass without material parity, provided full visual material
  parity remains forbidden.

## Environment Policy

AAN-11 can use the existing Isaac 4.1 environment through:

```bash
./scripts/isaac_python.sh ./main.py normalize-asset ...
```

The environment remains read-only. Do not run `pip install`, `pip uninstall`,
`conda install`, `conda update`, `conda env update`, or modify the Isaac installation.
Unit tests for log parsing and image metrics should use retained stderr fixtures and
small synthetic RGB arrays before any headless Isaac integration run.

## Downstream Handoff

Downstream projects consume `material_runtime_closure` in the manifest. They must not
repair package USD/MDL/texture/material binding locally. If AAN-11 is required and does
not pass, the downstream adapter reports a structured blocker and preserves AAN
`claims_forbidden`.

Safe product wording:

> AAN Phase 1 remains closed for bounded package/runtime/benchmark handoff. AAN-11 is
> the next material runtime closure follow-up, focused on making required target
> surfaces compile and render without hidden MDL dependency failures.

Unsafe product wording:

> AAN-06 render smoke already proves full material parity.

## Verification

The initial version of this record was documentation-only. The section below tracks
the first implemented slice and its verification.

## Implementation Progress

### 2026-07-02 Static Graph And Manifest Slice

Implemented the first AAN-11 code slice in ConvertAsset:

- Added `convert_asset/asset_application_normalizer/mdl_runtime_closure.py`.
- Added pure-Python MDL `import` / `using` / non-empty `texture_2d("...")` parsing.
- Added support for relative MDL module syntax such as `.::KooPbr::KooPbr`, covering
  the import form seen in the previous material-redness fix path without generalizing
  that old rewrite rule.
- Added native runtime module classification for `df`, `base`, `state`, `tex`,
  `anno`, and `math`.
- Added package-local MDL root discovery from `deps/mdl/**/*.mdl` and
  `material_closure[*].source_mdl_assets`.
- Added nested MDL module path resolution for forms such as
  `.::templates::mdl_0001::*`, mapping them to package paths such as
  `deps/mdl/templates/mdl_0001.mdl`.
- Added source-context mirror for helper MDL and relative MDL-internal texture paths
  when AAN-04 provides the root MDL `resolved_path`. Missing deps are copied into
  package-local paths and recorded as `mirror_actions`; unresolved deps still block.
- Added approved runtime MDL root resolution for Isaac-provided modules under
  `/isaac-sim/kit/mdl/core/mdl`, including `debug`, `limits`, `scene`,
  `nvidia::core_definitions::*`, and `OmniSurface::*`. These are not hard-coded as
  native; each record carries `runtime_root`, `runtime_path`, `runtime_module`, and
  `runtime_sha256`.
- Added static material runtime closure report with helper MDL and MDL-internal
  texture classification.
- Added hard blocking for unresolved helper MDL, missing MDL texture, and package
  escape texture paths.
- Added `material_runtime_closure` and `static_material_runtime_report` to the AAN
  manifest.
- Inserted AAN-11 after AAN-04 and before AAN-05 in the static pipeline.
- Added runtime material log parser and merge helper for MDLC / USD_MDL / failed
  shader node / missing texture evidence.
- Wired AAN-06 `stdout_path` / `stderr_path` into AAN-11 `runtime_compiler`; a runtime
  smoke pass with MDLC material compiler errors now blocks `material_runtime_closure`
  and prevents the package from being reported as ready.
- Added effective UsdShade binding-scope tracing for required prims and descendant
  render meshes. The report records direct versus inherited binding, bound material
  prim, binding source prim, and separates existing non-render required prims such as
  joints into `non_render_required_prims` instead of treating them as unknown material
  gaps.
- Added multi-view material evidence schema helper.

Verification:

```bash
python -m pytest tests/test_asset_application_normalizer_mdl_runtime_closure.py tests/test_asset_application_normalizer_cli.py tests/test_asset_application_normalizer_pm_and_mjcf.py -q
```

Result: `47 passed`.

Additional verification:

```bash
python -m compileall convert_asset/asset_application_normalizer
git diff --check
```

Result: both completed with exit code 0.

### 2026-07-02 Retained Static AAN-11 Audit

The current retained packages were re-audited on temporary package copies with the
static AAN-11 closure builder after nested module path support, recursive
`deps/mdl/**/*.mdl` discovery, source-context mirror, and approved runtime MDL root
resolution were enabled. The audit does not mutate retained evidence directories.

| Asset | Static AAN-11 status | Root MDL count | Imported module records | Texture records | Mirror actions | Approved runtime modules | Current blockers |
|---|---:|---:|---:|---:|---:|---:|---|
| `DryingBox` | `pass` | 23 | 199 | 12 | 17 | 9 | No static blockers on the temp copy; runtime-root evidence covers `debug`, `limits`, `scene`, `nvidia::core_definitions::*`, and `OmniSurface::*` |
| `MuffleFurnace` | `pass` | 8 | 89 | 1 | 5 | 1 | No static blockers on the temp copy; `limits` resolves through approved runtime-root evidence |
| `Beaker_01` | `pass` | 3 | 16 | 0 | 2 | 0 | No static blockers on the temp copy; empty texture uniforms still do not false-block |

This means AAN-11.2 now closes the retained static dependency graph on package copies.
The result is still a static material runtime closure claim only. It does not replace
real runtime compiler evidence, binding-scope proof, or multi-view render evidence.

### 2026-07-02 Retained Runtime Compiler Evidence

DryingBox, MuffleFurnace, and Beaker_01 were rerun with `--gates static,runtime`
against the current AAN-11 implementation, including effective binding-scope tracing.
Full package outputs were written under `/tmp/aan11_real_packages_final/*_runtime`;
retained evidence copied into this record keeps the manifest, runtime stdout/stderr,
single runtime-smoke render PNG, and multi-view material PNGs, but not the full package
tree.

Retained evidence paths:

- `docs/records/evidence/2026-07-02-aan-11-material-runtime-closure/runtime/dryingbox/`
- `docs/records/evidence/2026-07-02-aan-11-material-runtime-closure/runtime/muffle_furnace/`
- `docs/records/evidence/2026-07-02-aan-11-material-runtime-closure/runtime/beaker_01/`

Commands:

```bash
./scripts/isaac_python.sh ./main.py normalize-asset /cpfs/shared/simulation/zhuzihou/dev/_datasets/EBench-Assets-Overlay/labutopia_level1_poc/assets/scene_usds/labutopia/level1_poc/lab_001/scene.usda --out /tmp/aan11_real_packages_final/dryingbox_runtime --asset-id DryingBox_01_overlay --asset-class articulated --source-runtime isaac51 --target-runtime isaac41 --target-benchmark ebench-lift2 --task-id Lift2.DryingBox --required-prim /World/labutopia_level1_poc/obj_obj_DryingBox_01 --gates static,runtime --evidence-out /tmp/aan11_real_packages_final/dryingbox_runtime_manifest.json
./scripts/isaac_python.sh ./main.py normalize-asset /cpfs/shared/simulation/zhuzihou/dev/_datasets/LabUtopia-Dataset/Instruments/MuffleFurnace/MuffleFurnace.usd --out /tmp/aan11_real_packages_final/muffle_furnace_runtime --asset-id MuffleFurnace --asset-class articulated --source-runtime isaac51 --target-runtime isaac41 --target-benchmark ebench-lift2 --task-id AAN11.MuffleFurnaceDoor --required-prim /group_002 --required-prim /group_002/Group --required-prim /group_002/Group/mesh_000 --required-prim /group_002/Group/RevoluteJoint --gates static,runtime --evidence-out /tmp/aan11_real_packages_final/muffle_furnace_runtime_manifest.json
./scripts/isaac_python.sh ./main.py normalize-asset /cpfs/shared/simulation/zhuzihou/dev/_datasets/LabUtopia-Dataset/Instruments/Beaker_01/Beaker_01.usd --out /tmp/aan11_real_packages_final/beaker_01_runtime --asset-id Beaker_01 --asset-class rigid --source-runtime isaac51 --target-runtime isaac41 --target-benchmark ebench-lift2 --task-id AAN11.TransparentBeaker --required-prim /group_000 --required-prim /group_000/mesh_000 --gates static,runtime --evidence-out /tmp/aan11_real_packages_final/beaker_01_runtime_manifest.json
```

Runtime evidence summary:

| Asset | Overall | AAN-11 status | Runtime compiler | Error | MDLC | Failed shader node | Missing texture | Required material records | Non-render required prims | Front render sha256 |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| `DryingBox_01_overlay` | `pass` | `pass` | `pass` | 0 | 0 | 0 | 0 | 31 | 0 | `1d7fa73cfc27cde018a964431150b29fc86ad90b702c517e55bb921f9e0c7a8d` |
| `MuffleFurnace` | `pass` | `pass` | `pass` | 0 | 0 | 0 | 0 | 19 | `/group_002/Group/RevoluteJoint` | `2d0329a2a5568a1b94a3bac3f0d7f081fc84ca4b4c72f531b0c6119a2c97dcd3` |
| `Beaker_01` | `pass` | `pass` | `pass` | 0 | 0 | 0 | 0 | 2 | 0 | `33d7fbd4fc539b4ae2a0be24db832827e7c37e2de988183a154b597cd39ef646` |

Multi-view material evidence summary:

| Asset | View count | View ids | Non-background ratio range | BBox ratio range |
|---|---:|---|---:|---:|
| `DryingBox_01_overlay` | 3 | `front`, `orbit_3q`, `side` | 0.68141937-0.76353836 | 0.77148438-0.84765625 |
| `MuffleFurnace` | 3 | `front`, `orbit_3q`, `side` | 0.37005234-0.40489578 | 0.44107056-0.60417938 |
| `Beaker_01` | 3 | `front`, `orbit_3q`, `side` | 0.27865601-0.29436874 | 0.38160324-0.39653778 |

Audit command:

```bash
python - <<'PY'
import json
from pathlib import Path
base = Path("docs/records/evidence/2026-07-02-aan-11-material-runtime-closure/runtime")
for asset in ["dryingbox", "muffle_furnace", "beaker_01"]:
    manifest = json.loads((base / asset / "manifest.json").read_text(encoding="utf-8"))
    closure = manifest["material_runtime_closure"]
    rt = closure["runtime_compiler"]
    binding = closure["binding_scope"]
    assert manifest["overall_status"] == "pass"
    assert closure["status"] == "pass"
    assert rt["status"] == "pass"
    assert rt["counters"]["error_count"] == 0
    assert rt["counters"]["mdlc_count"] == 0
    assert rt["counters"]["failed_shader_node_count"] == 0
    assert rt["counters"]["missing_texture_count"] == 0
    assert binding["status"] == "effective_binding"
    assert binding["required_materials"]
    assert binding["unknown_required_prims"] == []
    if asset == "muffle_furnace":
        assert binding["non_render_required_prims"] == ["/group_002/Group/RevoluteJoint"]
    views = closure["view_evidence"]
    assert len(views) == 3
    assert {view["view_id"] for view in views} == {"front", "orbit_3q", "side"}
    assert all(view["non_background_ratio"] > 0 for view in views)
    assert (base / asset / "render.png").stat().st_size > 0
    assert {path.name for path in (base / asset / "material_views").glob("*.png")} == {
        "front.png",
        "orbit_3q.png",
        "side.png",
    }
PY
```

This completes retained AAN-11.4 effective binding-scope evidence, AAN-11.5 runtime
compiler evidence, and AAN-11.6 multi-view material evidence for the first three
assets. It still does not claim full material parity, source-vs-target pixel parity,
or official EBench score equivalence.

Package URI audit note: a raw text grep can find `http://blog.selfshadow.com/...`
inside copied MDL comments. That is not a runtime asset dependency. The retained
completion audit strips MDL `//` comments before checking `omniverse://`, `http(s)://`,
and `/cpfs/`; the three final package trees have no non-comment unauthorized URI or
absolute source path in USD/MDL text.

Remaining work:

- Promote retained `/tmp` package outputs to full retained package trees only if a
  future consumer needs package-local multi-view replay instead of retained manifest,
  logs, and PNG artifacts.
