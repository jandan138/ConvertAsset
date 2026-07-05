# 2026-07-05 Official EBench Soap-to-Dish Material Closure Plan

## Summary

This record plans the ConvertAsset-side repair for the official EBench
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

Current status: planning only. No repaired official package has been produced by this
record yet.

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
| Architecture planner | Record this as an official asset material-closure case, not as `AAN-12`. Use AAN-03R/AAN-04/AAN-11 mechanisms and keep Scenario Forge/EOS out of scope. AAN internal status remains `pass`; Phase12 export may map that to `passed`. |
| Static asset validator | `O.mdl` and the three JPGs are hard blockers if they are bound to required soap/dish materials. Waiver is not a closure fix for this acceptance target. Every material ref and texture needs raw path, owning layer/MDL, resolved path, package path, exists flag, sha256, and binding-scope trace. |
| Isaac runtime reviewer | Gate order should be static closure first, then headless runtime smoke, then multi-view material render review. Required counters for MDLC, failed shader node, missing texture, and missing module must be zero. Red/pink fallback on soap or dish blocks acceptance. |

## Repair Route Decision

Two legal repair routes are allowed. The implementation should choose the first route
that can pass clean closure without inventing fake source data.

### Route A: Source-Preserving Mirror

Use this when official `O.mdl` and the three real JPG textures can be located from an
approved source package.

Acceptance:

1. Mirror `O.mdl` into the package as a package-local MDL dependency.
2. Mirror the three JPGs into the package so the MDL-owned relative paths resolve,
   for example `deps/mdl/O.mdl` plus `deps/textures/<hash>.jpg` for
   `../textures/<hash>.jpg` semantics.
3. Preserve source material authoring as much as possible.
4. Record source path, package path, sha256, owning material, bound required prim,
   and mirror action for every dependency.
5. AAN-04 and AAN-11 both pass.

### Route B: Formal no-MDL / OmniPBR / UsdPreviewSurface Compatibility Package

Use this when exact official source dependencies cannot be obtained, or when the target
Isaac 4.1 runtime cannot compile the source MDL graph cleanly. This route is preferred
over keeping a temporary `/tmp` no-MDL artifact.

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

For the current Phase13 blocker, Route B is the likely default unless S2D-00 locates
approved exact copies of `O.mdl` and the three JPGs.

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
5. Runtime material compiler evidence has:
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
2. Any of the three known JPG texture paths remains unresolved.
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

## Planned Artifact Layout

Large generated package artifacts should stay outside git under the canonical
ConvertAsset research workspace:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/
  source_lock/
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

Route B sketch, with required prims filled after S2D-00/S2D-01:

```bash
export WORK=/cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705
export SOURCE_SNAPSHOT=$WORK/source_lock/task3/scene.usd
export NOMDL_USD=$WORK/source_lock/task3/scene_noMDL.usd
export PKG=$WORK/package
export MANIFEST=$PKG/evidence/manifest.json
export SOAP_PRIM=/path/to/soap/prim
export DISH_PRIM=/path/to/dish/prim
```

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
`--material-policy native-or-mirror`, after approved `O.mdl` and JPG files are
available and mirrored package-locally.

## Registry Handoff Fields

The final `registry_handoff.yaml` should include at minimum:

```yaml
asset_id: official_ebench_scene_e1cf0d5b4d76_soap_to_dish
source_package:
  root: /cpfs/shared/simulation/zhuzihou/dev/_datasets/EBench-Assets/assets/scene_usds/ebench/simple_pnp/task3
  source_usd_sha256: 62f62e8c71dabd7e79589414e2e9f8058c12d0509ad23f329ba26cf5c817adde
repair_route: formal_nomdl_preview_fallback
package:
  root: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/ebench/official_asset_closure/soap_to_dish_e1cf0d5b4d76_20260705/package
  root_usd: asset.usd
closure:
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

Exact paths and hashes must be regenerated from the actual repaired package before
Phase12 registry writeback.
