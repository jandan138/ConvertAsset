# 2026-07-05 Official EBench Soap-to-Dish Material Closure Plan

## Summary

This record tracks the ConvertAsset-side repair for the official EBench
`soap-to-dish` scene asset selected as `official_ebench_scene@e1cf0d5b4d76`.
The downstream Phase13 batch is currently blocked because the selected asset package
does not satisfy material dependency closure:

- missing material ref: `O.mdl`
- missing textures:
  - `../textures/bf77ddc86c270d02747e7d0517103514ab51d0f.jpg`
  - `../textures/c00e97e58585d8ddb0f8b16a724d05a13eae31.jpg`
  - `../textures/c9c274d4ea1de7d059cec0a795b3b27e3941935.jpg`

This is not an `AAN-12` batch-admission milestone. It is a single official-asset
closure case that should reuse AAN-03R dependency resolution, AAN-04 material
closure, AAN-11 material runtime closure, and the existing no-MDL / PreviewSurface
compatibility path where source-preserving closure is impossible.

Current status: S2D-08 through S2D-12 evidence is retained. The raw `O.mdl` and
three-JPG missing list is not a valid reason to downgrade the whole package to
UsdPreviewSurface. `O.mdl` is inactive registry residue, the three JPGs are
background washing-machine texture gaps, and the required `/root/obj__01` target
container passes native-MDL runtime and visual gates after the KooPbr import fix.

S2D-12 closes the Phase12 clean-registry handoff by selecting a native-MDL
Phase12-clean re-export rather than package-wide no-MDL fallback. The re-export
removes raw background missing refs and binary registry residue, retains the target
MDL route, maps `gltf/pbr.mdl` through approved Isaac runtime-module evidence, and
passes a Phase13 compile smoke with only expected downstream 13.6/13.8 gates left.

## Scope Boundary

ConvertAsset owns:

1. USD / MDL / texture dependency closure for the asset package.
2. Package-local material mirror or formal no-MDL / OmniPBR / UsdPreviewSurface
   compatibility output.
3. Closure report with source paths, package paths, sha256 hashes, and provenance.
4. Isaac Sim 4.1 render/runtime evidence proving no missing material module, missing
   texture, shader-node failure, or red/pink fallback on required soap/dish surfaces.
5. Registry handoff fields that Phase12 can ingest.

Scenario Forge / EOS / EBench own:

1. Phase12 registry update after ConvertAsset provides the package and handoff.
2. Phase13 soap-to-dish compile.
3. 13.6 visual, 13.8 execution predicate, and 13.9 batch gate.
4. Layout generation, task generation, episode runner, evaluator, and scoring logic.

Downstream consumers must not hand-edit USD, MDL, texture paths, or material bindings
inside Scenario Forge to bypass this blocker.

## Evidence Inputs

The Phase13 blocker evidence is retained outside this repository:

```text
/cpfs/user/zhuzihou/dev/scenario-forge/docs/records/evidence/2026-07-05-phase13-image-grounded-task-factory/phase13_batch_rc_20260705/blocked_probes/phase13_tabletop_photo_goal_soap_to_dish/handoff/asset_intake_blockers.yaml
```

It records `status: blocked` with the missing `O.mdl` material ref and the three
missing JPG textures above.

Known source and prior temporary evidence:

| Item | Path / hash |
|---|---|
| Official source root | `/cpfs/shared/simulation/zhuzihou/dev/_datasets/EBench-Assets/assets/scene_usds/ebench/simple_pnp/task3` |
| Source `scene.usd` sha256 | `62f62e8c71dabd7e79589414e2e9f8058c12d0509ad23f329ba26cf5c817adde` |
| Source `scene.usda` sha256 | `343e73aea9056510231da9b2588ce54c78aaa02d121f96eb227c79469ae7d138` |
| Prior temporary no-MDL output | `/tmp/ebench-soap-to-dish-canary/assets/official_ebench_scene/scene_noMDL.usd` |
| Prior temporary no-MDL sha256 | `e1cf0d5b4d76cdc32cb57459be501e55e736f533effe17838191fa63ee107840` |

Local source inspection found the three JPG literals inside MDL files under the
official source root, while the JPG files themselves were not present in that source
tree. A direct text search did not locate `O.mdl`; the repair task must identify
whether it is an active composed dependency, a Phase12 registry artifact, or an
inactive residual reference from a previous generated USD.

## Multi-Agent Review

| Review angle | Conclusion |
|---|---|
| Architecture planner | Record this as an official asset material-closure case, not as `AAN-12`. Use AAN-03R/AAN-04/AAN-11 mechanisms and keep Scenario Forge/EOS out of scope. Split `source material completeness` from `target Isaac 4.1 material viability`; missing strings alone must not force no-MDL fallback. |
| Static asset validator | `O.mdl` is not an active PXR dependency in current evidence and should be treated as registry residue unless a later active traversal proves otherwise. The three JPG literals are real missing MDL-internal texture refs, but they are localized to washing-machine materials and must be traced through material binding and task relevance before selecting whole-package fallback. |
| Isaac runtime reviewer | A sidecar MDL-preserving render is required before fallback when static closure is ambiguous. The initial `KooPbr` / `KooPbr_maps` failure matches the known absolute-import/search-path issue from `usd-scene-physics-prep`; an external candidate copy can rewrite only those imports to same-directory relative imports and mirror `KooPbr_maps.mdl`. Required soap/dish counters for MDLC, failed shader node, missing texture, and missing module must be zero for native MDL pass; background-only compiler/texture errors can be scoped warnings, not automatic no-MDL triggers. |
| Independent visual reviewer | After the import-fixed render, target views A-C are `PASS`: the dish/container is visible and has no red, pink, pure-black, or missing-material fallback. Full-scene D is `WARN` only because the target is too distant for material judgment. |

## Repair Route Decision

Route selection is fidelity-first. A missing MDL/JPG report is an intake blocker, not
by itself a decision to downgrade all materials to UsdPreviewSurface. The
implementation should choose the first route that can pass the required-scope gates
without inventing fake source data.

### Route A0: MDL-Preserving Runtime Candidate

Use this before any fallback when the missing dependency report may be registry
residue, background-only, or not bound to task-required surfaces.

Acceptance:

1. Classify every reported missing dependency by this join chain:
   `missing dep -> owning USD/MDL literal -> Shader -> Material ->
   material:binding consumer -> task contract / visibility`.
2. Prove `O.mdl` is active or inactive with pxr-level traversal, not raw registry
   metadata alone.
3. Render the source-preserving MDL scene in Isaac 4.1 with an explicit MDL search
   path and retain stdout/stderr, image hashes, and view metrics.
4. Required soap/dish surfaces have traceable effective material bindings.
5. Required-scope runtime counters are zero for MDLC, missing module, missing texture,
   `USD_MDL` invalid module, and failed shader-node errors.
6. Multi-view renders are nonblank and show no required soap/dish red, pink, black,
   invisible, or corrupted material fallback.
7. Background-only problems are recorded as scoped warnings, with
   `full_material_parity_claimed=false`.

### Route A: Source-Preserving Mirror

Use this when exact missing source dependencies can be located from an approved source
package and the native MDL route should remain the final route.

Acceptance:

1. Mirror active missing MDL dependencies into the package as package-local MDL files.
2. Mirror the missing JPGs into the package so the MDL-owned relative paths resolve,
   for example `deps/mdl/O.mdl` plus `deps/textures/<hash>.jpg` for
   `../textures/<hash>.jpg` semantics.
3. Preserve source material authoring as much as possible.
4. Record source path, package path, sha256, owning material, bound required prim,
   and mirror action for every dependency.
5. AAN-04 and AAN-11 both pass.

### Route B: Formal no-MDL / OmniPBR / UsdPreviewSurface Compatibility Package

Use this only when the required-scope MDL-preserving route fails: exact required
dependencies cannot be obtained, the target Isaac 4.1 runtime cannot compile required
MDL materials cleanly, required surfaces visibly fall back, or the target benchmark
profile does not accept native MDL. This route is preferred over keeping a temporary
`/tmp` no-MDL artifact, but it remains a compatibility fallback, not a full material
parity route.

Acceptance:

1. Generate the no-MDL / PreviewSurface-compatible USD from a source snapshot under a
   canonical ConvertAsset workspace, not inside the official source tree and not as a
   final `/tmp` artifact.
2. Preserve available source textures where they exist; do not synthesize placeholder
   JPGs to hide missing source data.
3. Remove active runtime dependency on `O.mdl` and the missing JPGs from the package
   entrypoint.
4. Ensure every remaining `UsdUVTexture.inputs:file` or material asset path resolves
   package-locally.
5. Keep `full_material_parity_claimed=false` and explicitly claim compatibility
   rendering, not pixel-perfect or source-material parity.

For the current Phase13 blocker, the existing formal no-MDL package remains a useful
registry-unblock compatibility fallback. It is not the fidelity-first route. S2D-11
selects `source_mdl_native_import_fixed` for required scope because:

1. `O.mdl` is inactive registry residue, not an active PXR dependency.
2. The three reported JPGs are real missing MDL-internal texture literals, but S2D-08
   binds them only to background washing-machine materials, not `/root/obj__01`.
3. The `KooPbr` / `KooPbr_maps` failure is fixed in an external candidate copy by
   relative import rewrite plus `KooPbr_maps.mdl` mirror.
4. Required `/root/obj__01` runtime smoke passes cold load, render readback, physics
   step, and reset.
5. Required target material views show no red/pink/black fallback.

The remaining JPG errors are background material completeness warnings. They do not
justify whole-package no-MDL fallback, but they still prevent a naive Phase12 clean
`missing_textures: []` export unless Phase12 consumes scoped warnings or the package
is re-exported to remove raw background missing refs.

## Numbered Work Plan

| Step | Name | Output | Acceptance criteria |
|---|---|---|---|
| `S2D-00` | Source Intake And Ref Origin Lock | Source lock record and dependency-origin report | Official source files are copied or referenced read-only; source sha256 values are recorded; composed USD/MDL audit identifies where `O.mdl` and the three JPG refs originate; source tree is not modified. |
| `S2D-01` | Static Closure Reproduction | Minimal blocker report from ConvertAsset tools | ConvertAsset reproduces the missing-material/missing-texture blocker or proves the refs are inactive residual strings that Phase12 should not count. `O.mdl` origin is classified as active material ref, registry artifact, or inactive residue. |
| `S2D-02` | Repair Route Selection | Route A or Route B decision note | If exact official dependencies exist, Route A is selected. If not, Route B is selected with no-MDL / PreviewSurface fallback and no full-parity claim. No placeholder textures are introduced. |
| `S2D-03` | Formal Package Build | Stable package under canonical external workspace | Package contains `asset.usd`, package-local deps, closure reports, evidence directory, sha256 sidecar, and provenance. No final deliverable lives only under `/tmp`. |
| `S2D-04` | Static Closure Gate | `closure_report.json` / manifest static sections | `material_closure.status` maps to Phase12 `passed`; `missing_material_refs: []`; `missing_textures: []`; no unresolved USD asset paths; no unauthorized remote URI; no package escape; no `/cpfs` dependency from package entrypoint. |
| `S2D-05` | Isaac Runtime And Render Gate | Runtime smoke logs, render PNGs, material-view evidence | Isaac 4.1 cold open succeeds; render readback is nonblank; required soap/dish prims exist; MDLC/module/texture/shader-node counters are zero; front/orbit/side or equivalent views show no red/pink fallback on soap or dish. |
| `S2D-06` | Registry Handoff | `registry_handoff.yaml` plus hashes | Handoff includes asset id, package root USD, package sha256, source package info, closure report path, runtime/render evidence paths, route decision, claim boundary, and Phase12 status mapping. |
| `S2D-07` | Downstream Recheck Boundary | Handoff note for Scenario Forge / Phase12 | ConvertAsset stops after package and evidence. Downstream reruns Phase12 registry closure, Phase13 compile, 13.6 visual, 13.8 execution predicate, and 13.9 batch gate without local repair patches. |
| `S2D-08` | Dependency Relevance Trace | Missing dep to material binding table | `O.mdl` is classified as active/inactive with pxr traversal; each JPG has owning MDL, parameter, Material, bound prim, visibility/task relevance, and waiver/block status. |
| `S2D-09` | MDL-Preserving Runtime Candidate | Source-preserving render logs and PNGs | Isaac 4.1 can render the native-MDL scene without blank output; stdout/stderr counters are parsed; image hashes and foreground metrics are retained. |
| `S2D-10` | Visual Review Gate | Human/agent visual verdict over retained renders | Verdict is PASS/WARN/FAIL; WARN requires explicit follow-up. Red/pink/black/invisible required target surfaces block native MDL. |
| `S2D-11` | Fidelity Route Finalization | Route A0/A/B final decision | Keep native MDL when required-scope runtime and visual gates pass. Use no-MDL only when required-scope evidence fails or target profile disallows native MDL. The decision records `full_material_parity_claimed=false` unless separate parity evidence exists. |
| `S2D-12` | Phase12 Clean Registry Mapping | Status projection from AAN scoped evidence to Phase12 fields | Clean `passed` requires `missing_material_refs: []` and `missing_textures: []`, or an explicit registry schema that can represent scoped background warnings. A waiver must not be hidden as clean pass. |
| `S2D-13` | Native MDL Acceptance Gate | Required-scope native-MDL acceptance checklist | Native MDL can be kept only when active dependency trace, required material binding trace, runtime compiler counters, and target visual review all pass. Render-only "looks OK" evidence is supportive but not sufficient alone. |
| `S2D-14` | Registry Residue And Background Warning Handling | Policy for inactive residue and background-only material gaps | Inactive registry residue should be re-exported or represented as residue, not used to trigger fallback. Background-only missing textures stay scoped warnings unless they affect task-required surfaces or the consumer cannot represent them. |

## Closure Acceptance

The fixed package is accepted by ConvertAsset only when all of these are true:

1. `asset.usd` opens with `pxr.Usd.Stage.Open`.
2. Required soap and dish prims exist and have traceable effective material bindings
   or documented PreviewSurface fallback material bindings.
3. Phase12-facing closure fields can be exported as:
   - `material_closure.status: passed`
   - `missing_material_refs: []`
   - `missing_textures: []`
4. AAN manifest fields use internal status vocabulary:
   - `dependency_closure.status == "pass"`
   - `material_closure.status == "pass"`
   - `material_runtime_closure.status == "pass"`
5. Runtime material compiler evidence has required-scope clean counters:
   - `error_count == 0`
   - `mdlc_count == 0`
   - `failed_shader_node_count == 0`
   - `missing_texture_count == 0`
   - `missing_modules == []`
6. Package scans find no active `O.mdl` reference unless it resolves package-locally
   with provenance.
7. Package scans find no active refs to the three missing JPG paths unless they resolve
   package-locally with provenance.
8. Front/orbit/side or equivalent material renders are retained and show no required
   soap/dish red or pink fallback.

## Blocker And Waiver Policy

Hard blockers for this target:

1. `O.mdl` remains unresolved on a material bound to required soap/dish prims.
2. Any of the three known JPG texture paths remains unresolved on a required
   soap/dish material, or cannot be classified by binding scope and task relevance.
3. A required material has no binding-scope trace.
4. Runtime logs contain MDLC, missing module, missing texture, USD_MDL invalid, or
   failed shader-node errors for required surfaces.
5. Required soap/dish foreground shows contiguous red/pink fallback.
6. Package entrypoint relies on `/tmp`, `/cpfs`, `omniverse://`, `http(s)://`, or a
   package-escaping relative path.
7. The repair modifies the official source dataset in place.
8. Phase13 would still need a local USD/MDL/texture patch after consuming the package.

Temporary waivers are allowed only for:

1. Background-only or unbound material warnings outside required soap/dish scope.
2. Renderer/plugin/deprecation warnings unrelated to material resolution.
3. Advanced material feature differences after an explicit no-MDL / PreviewSurface
   fallback, with `full_material_parity_claimed=false`.
4. Inert residual byte strings in a binary USD only if pxr-level dependency traversal,
   package closure, and runtime logs prove they are not active dependencies. If Phase12
   raw scanning still counts them, the package must be re-exported to remove the raw
   residual string instead of waiving it.

For the requested Phase12 clean registry closure, a waiver must not produce
`material_closure.status: passed` unless the consumer explicitly changes the target
status to `ready_with_waivers`. The current target is clean `passed`, so required
`O.mdl` and required JPG gaps are not waiverable.

## Current MDL-Preserving Render Evidence

The 2026-07-05 sidecar render used the source snapshot directly:

```bash
EXP=/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705
./scripts/isaac_python.sh ./main.py render-single "$EXP/source_lock/task3/scene.usd" \
  --out "$EXP/evidence/mdl_preserving_render" \
  --views 4 \
  --naming-style view \
  --overwrite \
  --warmup-steps 100 \
  --render-steps 8 \
  --renderer RayTracedLighting \
  --mdl-path "$EXP/source_lock/task3/SubUSDs/materials"
```

Retained images:

| View | sha256 prefix | Size bytes | Non-background ratio | Pink fallback ratio |
|---|---:|---:|---:|---:|
| `back.png` | `2f5ac5e7ab3cc16a` | 59783 | 0.241329 | 0.0 |
| `front.png` | `aa3b25a4ffeeb626` | 35343 | 0.243660 | 0.0 |
| `left.png` | `2d769b93cf7af59c` | 43201 | 0.265362 | 0.0 |
| `right.png` | `eb76225f72ee3734` | 40676 | 0.256916 | 0.0 |

Runtime log summary:

- `O.mdl`: no runtime log hits in the MDL-preserving render.
- Three reported JPG files: no direct runtime log hits; the files are still real
  missing literals in two washing-machine MDLs.
- MDLC lines: 132.
- USD_MDL invalid/module lines: 46.
- Failed shader-node lines: 23.
- Missing module lines: 66, with missing modules `::KooPbr` and `::KooPbr_maps`.
- Missing texture lines: 0, likely because MDL import compilation fails before texture
  resolution for the affected materials.

Visual review verdict: `WARN`. The render is nonblank and not globally corrupted; the
front view looks acceptable. The back view has a localized bright red/pink panel, so
the native MDL route cannot be accepted until binding scope proves this is background
or the relevant MDL resolver/material issue is fixed.

Interpretation: this evidence rejects automatic whole-package no-MDL fallback from the
raw `O.mdl`/JPG missing list. It does not yet prove native MDL pass. The next action is
to resolve or scope the `KooPbr`/`KooPbr_maps` MDL runtime errors and identify whether
the red panel belongs to a task-required soap/dish surface.

## S2D-09 To S2D-11 Import-Fixed Native MDL Evidence

The higher-fidelity candidate is retained outside git:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/source_mdl_import_fixed/task3
```

It does not modify the official source dataset. It copies the source lock and applies
the known KooPbr import repair only inside the candidate:

1. `import ::KooPbr::...` and `import ::KooPbr_maps::...` were rewritten to
   same-directory relative `using .::...` imports.
2. `KooPbr_maps.mdl` was mirrored from the approved EBench misc MDL root.
3. `scene.usd` remains byte-identical to the source lock:
   `62f62e8c71dabd7e79589414e2e9f8058c12d0509ad23f329ba26cf5c817adde`.

Import fix report:

| Item | Value |
|---|---:|
| Candidate MDL files modified | 23 |
| Import replacements | 33 |
| Residual absolute `import ::KooPbr` | 0 |
| `KooPbr.mdl` sha256 | `b1d41faaf98d0047f7f19ea826e122557b40ee99ca1e1466900b78d11931d959` |
| `KooPbr_maps.mdl` sha256 | `993bddbf7ae067b261512c4ffbe668cc77ee9e905ace9e751b272107becb460c` |

After this fix, the full-scene render no longer reports KooPbr module, `USD_MDL`,
MDLC, or failed shader-node errors. Four retained full-scene views are nonblank and
have zero red/pink fallback metric in the deterministic scan:

| View | sha256 prefix | Size bytes | Red ratio | Pink ratio |
|---|---:|---:|---:|---:|
| `back.png` | `c81777a9cadc3ac` | 59993 | 0.0 | 0.0 |
| `front.png` | `23499be0dabac678` | 34941 | 0.0 | 0.0 |
| `left.png` | `04f08f4153732415` | 43827 | 0.0 | 0.0 |
| `right.png` | `0922e0d3d6c72f7c` | 41250 | 0.0 | 0.0 |

Target-focused runtime smoke on `/root/obj__01` passed:

| Gate | Status |
|---|---|
| cold load | pass |
| required prim exists | pass |
| render readback | pass |
| physics step | pass |
| reset | pass |

Required-scope compiler counters after the import fix:

| Counter | Value |
|---|---:|
| `MDLC` | 0 |
| `USD_MDL` | 0 |
| failed shader node | 0 |
| missing module | 0 |
| `KooPbr` hits | 0 |
| `KooPbr_maps` hits | 0 |
| `O.mdl` hits | 0 |
| required-scope missing texture | 0 |
| reported JPG texture errors | 12 background warnings, scoped to washing-machine materials by S2D-08 |

Target material binding evidence:

- required prim: `/root/obj__01`;
- effective material: `/root/obj__01/Looks/material0`;
- target texture: `./tmp/92f3f2624c4ee2e7/textures/1_texture0.png`;
- target texture sha256:
  `2fb5c14672d87be26ee1d31dc171148f6662581152f36be0069aef92d25971a5`;
- target material does not use the three reported missing JPGs.

Independent clean-room visual review:

- target front/orbit/side views: `PASS`;
- no visible red, pink, pure-black, or missing-material fallback on the target
  dish/container;
- full-scene back view: `WARN` only because the target is distant, not because of a
  blocking material artifact.

S2D-11 route decision:

```text
selected_route_for_required_scope: source_mdl_native_import_fixed
blanket_nomdl_from_reported_missing_refs: rejected
package_wide_preview_fallback: not_selected_for_required_scope
status: pass_required_scope_with_scoped_background_texture_warnings
full_material_parity_claimed: false
```

Retained machine-readable evidence:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/evidence/s2d11_mdl_preserving_route_decision.json
```

## S2D-12 Phase12 Clean Registry Mapping

Phase12 / Phase13 currently has no clean-pass field for scoped background texture
warnings. The existing registry material audit can approve runtime MDL modules such
as `gltf/pbr.mdl`, but any missing texture still fails the selected asset. Therefore
S2D-12 does not hide the background JPG warnings as waivers; it produces a follow-up
native-MDL re-export that removes the raw background missing refs from the candidate
package while preserving the required target material route.

Selected package candidate:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/source_mdl_phase12_clean/task3/asset.usda
```

Key package facts:

| Item | Value |
|---|---|
| Representation | native MDL, Phase12-clean re-export |
| Root USD sha256 | `1fedd44093435591458cf10c303bdf2e856e20b18608307ed7e7dc59b71f0673` |
| Root USD size | 780 MB ASCII USD |
| Official source modified | false |
| Package-wide no-MDL fallback selected | false |
| Full material parity claimed | false |
| `O.mdl` / three JPG raw scan after cleanup | 0 matches |

The root was re-exported as ASCII USD to remove inactive binary residue and raw
background texture attrs that Phase12 raw scanning would otherwise count. Future
packaging can binary re-pack it only after proving the same `O.mdl` / JPG / missing
texture scans stay clean.

Phase12-facing material projection:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/evidence/s2d12_phase12_material_closure_projection.json
```

Projected fields:

| Field | Value |
|---|---|
| `material_closure.status` | `passed` |
| `missing_material_refs` | `[]` |
| `missing_textures` | `[]` |
| `package_local_missing_material_refs` | `asset.usda -> gltf/pbr.mdl` |
| `approved_runtime_mdl_dependencies` | `gltf/pbr.mdl` resolved by Isaac runtime module evidence |

The underlying raw package audit still reports `gltf/pbr.mdl` as package-local
missing before runtime approval. This is expected for the current Phase12 code path:
the registry projection applies the existing approved-runtime-MDL protocol, leaving
the exported missing lists clean without downgrading the asset.

Runtime and render evidence for the Phase12-clean candidate:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/evidence/runtime_native_phase12_clean_target_container/report.json
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/evidence/s2d12_runtime_phase12_clean_summary.json
```

Runtime status is `pass`. The retained log summary has zero `Error`, `MDLC`,
`USD_MDL`, failed shader-node, missing texture, missing module, KooPbr, KooPbr_maps,
`O.mdl`, and known-JPG hits. Retained front/orbit/side/render PNG metrics all have
red and pink fallback ratios of `0.0`.

Phase13 compile smoke:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/evidence/s2d12_phase13_compile_smoke/s2d12_phase13_compile_smoke_report.yaml
```

Result:

| Field | Value |
|---|---|
| Return code | 0 |
| `overall_status` | `phase13_static_candidate_ready` |
| Phase13 material gate | `passed` |
| Remaining blockers | expected 13.6 overview render and 13.8 EOS execution/predicate gates |

This proves Phase13 compile is no longer blocked by USD / MDL / texture material
closure for the soap-to-dish target container. It does not claim that downstream
13.6, 13.8, or 13.9 are complete; those remain Scenario Forge / EOS / EBench gates.

Registry handoff:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/evidence/s2d12_phase12_clean_registry_mapping.yaml
```

Downstream should write the replacement registry entry as
`official_ebench_scene@e1cf0d5b4d76_native_phase12_clean` /
`source_package_id=s2d12_native_mdl_phase12_clean`, copy the projected material
closure fields, and rerun Phase12 registry closure -> Phase13 compile -> 13.6 visual
-> 13.8 execution predicate -> 13.9 batch gate without local USD/MDL/texture/material
binding patches.

## Planned Artifact Layout

Large generated package artifacts should stay outside git under the canonical
ConvertAsset research workspace:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/
  source_lock/
  source_mdl_import_fixed/
  source_mdl_phase12_clean/
  package/
    asset.usd
    deps/
    evidence/
      manifest.json
      closure_report.json
      runtime_smoke/
      material_views/
  registry_handoff.yaml
  SHA256SUMS
```

Only lightweight records, manifests, small reports, and selected PNG evidence should
be copied into this repository if needed.

## Command Sketch

Use the existing Isaac wrapper and environment. Do not modify conda or Isaac
installations.

Route A0 sketch, with required prims filled after S2D-08:

```bash
export WORK=/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705
export SOURCE_SNAPSHOT=$WORK/source_lock/task3/scene.usd
export NOMDL_USD=$WORK/source_lock/task3/scene_noMDL.usd
export PKG=$WORK/package
export MANIFEST=$PKG/evidence/manifest.json
export SOAP_PRIM=/path/to/soap/prim
export DISH_PRIM=/path/to/dish/prim
export MDL_DIR=$WORK/source_lock/task3/SubUSDs/materials
```

```bash
./scripts/isaac_python.sh ./main.py render-single "$SOURCE_SNAPSHOT" \
  --out "$WORK/evidence/mdl_preserving_render" \
  --views 4 \
  --naming-style view \
  --renderer RayTracedLighting \
  --mdl-path "$MDL_DIR" \
  --overwrite
```

If Route A0 fails required-scope runtime or visual gates, build the formal Route B
compatibility package:

```bash
./scripts/isaac_python.sh ./main.py no-mdl "$SOURCE_SNAPSHOT" --only-new-usd
./scripts/isaac_python.sh ./main.py normalize-asset "$NOMDL_USD" \
  --out "$PKG" \
  --asset-id official_ebench_scene_e1cf0d5b4d76_soap_to_dish \
  --asset-class rigid \
  --source-runtime isaac51 \
  --target-runtime isaac41 \
  --target-benchmark ebench-lift2 \
  --task-id official_ebench_scene.soap_to_dish \
  --material-policy preview-fallback \
  --required-prim "$SOAP_PRIM" \
  --required-prim "$DISH_PRIM" \
  --gates static,runtime \
  --evidence-out "$MANIFEST"
```

Optional render review:

```bash
./scripts/isaac_python.sh ./main.py render-single "$PKG/asset.usd" \
  --out "$PKG/evidence/render_single" \
  --naming-style view \
  --overwrite
```

Route A uses the same `normalize-asset` command with the source-preserving USD and
`--material-policy native-or-mirror`, after active dependency relevance, resolver
closure, and required-scope runtime/visual gates pass. Active missing files must be
available and mirrored package-locally if they are required.

## Registry Handoff Fields

The final `registry_handoff.yaml` should include at minimum:

```yaml
asset_id: official_ebench_scene_e1cf0d5b4d76_soap_to_dish
source_package:
  root: /cpfs/shared/simulation/zhuzihou/dev/_datasets/EBench-Assets/assets/scene_usds/ebench/simple_pnp/task3
  source_usd_sha256: 62f62e8c71dabd7e79589414e2e9f8058c12d0509ad23f329ba26cf5c817adde
repair_route: source_mdl_native
allowed_repair_routes:
  - source_mdl_native
  - source_mdl_mirrored
  - package_preview_fallback
  - blocked
package:
  root: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/package
  root_usd: asset.usd
closure:
  source_material_completeness:
    o_mdl: registry_residue_not_active_dependency
    missing_jpgs: scoped_missing_mdl_internal_literals
  target_runtime_viability:
    status: pass
    allowed_statuses:
      - pass
      - warn
      - blocked
    required_scope_mdlc_count: 0
    background_scope_mdlc_count: 0
  material_closure:
    status: passed
    missing_material_refs: []
    missing_textures: []
  material_runtime_closure:
    status: pass
claims:
  full_material_parity_claimed: false
  official_score_equivalence_claimed: false
```

For S2D-12 the exact current handoff is
`evidence/s2d12_phase12_clean_registry_mapping.yaml`. Regenerate that handoff if the
candidate root, hash, runtime approval metadata, or Phase13 smoke package changes
before Phase12 registry writeback.
