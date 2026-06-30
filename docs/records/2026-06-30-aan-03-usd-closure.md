# AAN-03 USD Closure

Date: 2026-06-30

## Status

`AAN-03 USD Closure` is implemented for the first static package-closure path.

Commit scope:

- `convert_asset/asset_application_normalizer/usd_closure.py`
- `convert_asset/asset_application_normalizer/pipeline.py`
- `convert_asset/asset_application_normalizer/evidence_manifest.py`
- `convert_asset/asset_application_normalizer/model.py`
- `tests/test_asset_application_normalizer_cli.py`
- `docs/superpowers/plans/2026-06-30-aan-03-usd-closure.md`

## Implemented

1. Non-dry-run `normalize-asset` now runs the AAN-03 USD closure path instead of the AAN-02
   placeholder block.
2. The closure scanner inventories:
   - root layer and defaultPrim;
   - required prim existence through lazy `pxr.Usd`;
   - sublayers;
   - references and payloads;
   - variant references and payloads;
   - value clip asset and manifest paths;
   - generic asset-valued properties and `@...@` asset-token fallbacks.
3. The packager writes a package-local USD tree:
   - root layer at `asset.usd`;
   - USD dependencies under `deps/usd/`;
   - MDL files under `deps/mdl/`;
   - texture files under `deps/textures/`;
   - other local asset files under `deps/assets/`.
4. Text USD layers are rewritten by exact asset-token replacement so packaged layers point to
   package-local relative paths instead of the source tree.
5. Non-text USD layers with dependencies are exported through lazy `pxr.Sdf` to text and then
   rewritten with the same package-relative token policy. If a layer cannot be exported, AAN-03
   still blocks rather than leaving source-tree escapes.
6. Missing MDL/texture/helper dependencies are resolved from deterministic local mirror roots
   before blocker evaluation, including package sidecar roots such as `assets/miscs/mdl` and
   existing Isaac MDL roots such as `/isaac-sim/kit/mdl/core`.
7. Blocking gates now distinguish:
   - unauthorized remote URI: `aan03_block_remote_uri`;
   - missing local dependency: `aan03_block_missing_dependency`;
   - missing required prim: `aan03_block_required_prim_missing`;
   - non-text USD layer with dependencies that cannot be safely rewritten:
     `aan03_block_unrewritable_usd_dependency`.
8. The evidence manifest now records `milestone = AAN-03-usd-closure`, dependency closure,
   static USD report, stage gate, and AAN-03 claim boundaries.

## Explicit Non-Claims

AAN-03 does not implement:

- material semantic closure or UsdPreviewSurface fallback;
- physics, articulation, collision, mass, inertia, joint, or reset-pose checks;
- Isaac Sim 4.1 cold load, render readback, step, or reset evidence;
- EBench task config or evaluator output;
- remote URI fetching or remote URI waivers;
- semantic material parity beyond preserving and packaging referenced MDL/texture files.

Those remain assigned to `AAN-04` through `AAN-07`.

## DryingBox Source Status

The implementation is validated on synthetic DryingBox-shaped USD fixtures that include
required prims, USD dependencies, MDL, texture, variants, clips, missing dependencies, and
remote URI blockers.

Real DryingBox sources were then located outside the ConvertAsset repository and exercised with
the AAN-03 CLI. The normalizer now produces real evidence manifests and correctly reports
required prim presence even when dependency closure is blocked:

| Input | Required prim result | Dependency result | Evidence |
|---|---|---|---|
| LabUtopia single asset `DryingBox_01.usd` | `/group_009` exists | blocked: missing `UnitsAdjust-*.metricsAssembler` helper sublayer | `docs/records/evidence/2026-06-30-aan-03-dryingbox-real/single_dryingbox_01.json` |
| LabUtopia lab scene `lab_001.usd` | `/World/DryingBox_01` exists | blocked: unauthorized remote MDL/USD URI | `docs/records/evidence/2026-06-30-aan-03-dryingbox-real/labutopia_lab_001_dryingbox_01.json` |
| Existing EBench overlay `scene.usda` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01` exists | pass: all USD/MDL/texture dependencies are package-local | `docs/records/evidence/2026-06-30-aan-03-dryingbox-real/overlay_level1_poc_dryingbox_01.json` |

This means AAN-03 now has a real DryingBox `pass` package path for the existing EBench overlay.
The raw single-asset and full-lab inputs remain useful negative evidence: they show source defects
or policy decisions that AAN-03 must block instead of silently repairing.

## Required Prim Evidence Fix

The first real DryingBox probe exposed one evidence bug: when any dependency blocker existed,
AAN-03 skipped required prim checks and reported `status = not_run`. The scanner now:

1. attempts composed `Usd.Stage.Open` when there is no remote URI risk;
2. falls back to root-layer `Sdf` prim-spec evidence when composition is skipped or unavailable;
3. keeps dependency blockers intact while still recording `exists = true` for authored required
   prims.

This keeps blocked manifests useful for product and engineering triage: the manifest can now say
"the task prim exists, but the dependency/material/package closure is not yet complete" instead
of mixing those two concerns.

## Real DryingBox Verification

The real-source commands used the existing Python environment at `/usr/bin/python`, which already
provides `pxr`. `conda` was not present on the current PATH, and no environment packages were
installed or modified.

Evidence generation summary after local mirror lookup and Sdf export support:

```text
single_dryingbox_01 return_code=5
labutopia_lab_001_dryingbox_01 return_code=5
overlay_level1_poc_dryingbox_01 return_code=0
```

The two return code `5` values are expected AAN-03 blocker exits, not crashes. The overlay return
code `0` wrote a package at `/tmp/aan03_real_packages/overlay_level1_poc_dryingbox_01`.

## Verification

TDD red check:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py -q
```

Initial result after adding AAN-03 tests:

```text
3 failed, 4 passed
```

Focused variant red check:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_inventories_variant_usd_dependency -q
```

Initial result:

```text
1 failed
```

Focused clip red check:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_inventories_value_clip_dependencies -q
```

Initial result:

```text
1 failed
```

Green check after implementation:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py -q
```

Result:

```text
9 passed
```

Required-prim evidence regression red checks:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_missing_local_dependency_without_package -q
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_unauthorized_remote_uri_without_package -q
```

Initial result:

```text
1 failed
1 failed
```

Green check after the required-prim evidence fix:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_missing_local_dependency_without_package tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_unauthorized_remote_uri_without_package -q
```

Result:

```text
2 passed
```

Local mirror and Sdf export red check:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_mirrors_mdl_from_package_sidecar_root tests/test_asset_application_normalizer_cli.py::test_normalize_asset_exports_binary_usd_dependency_with_rewritten_paths -q
```

Initial result:

```text
2 failed
```

Green result:

```text
2 passed
```

Full focused regression check:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports -q
```

Result:

```text
13 passed
```

Real package checks:

```text
overlay manifest overall_status: pass
overlay missing dependencies: 0
overlay unauthorized remote URI: 0
overlay unrewritable layers: 0
package absolute source path / remote URI scan: no matches
Usd.Stage.Open(package asset.usd): pass
required prim /World/labutopia_level1_poc/obj_obj_DryingBox_01: valid
```

## Next Milestone

Start `AAN-04 Material Closure`: upgrade the static MDL/texture package mirror into material
closure records with source preservation evidence, channel provenance, fallback policy, and
blocked/waived material semantics. Separate follow-ups should decide whether the raw full-lab
remote URI dependencies are mirrored, waived, or left blocked, and whether the single-asset
`UnitsAdjust-*.metricsAssembler` missing helper is recoverable from source data.
