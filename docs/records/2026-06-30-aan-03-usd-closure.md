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
5. Blocking gates now distinguish:
   - unauthorized remote URI: `aan03_block_remote_uri`;
   - missing local dependency: `aan03_block_missing_dependency`;
   - missing required prim: `aan03_block_required_prim_missing`;
   - non-text USD layer with dependencies that cannot be safely rewritten:
     `aan03_block_unrewritable_usd_dependency`.
6. The evidence manifest now records `milestone = AAN-03-usd-closure`, dependency closure,
   static USD report, stage gate, and AAN-03 claim boundaries.

## Explicit Non-Claims

AAN-03 does not implement:

- material semantic closure or UsdPreviewSurface fallback;
- physics, articulation, collision, mass, inertia, joint, or reset-pose checks;
- Isaac Sim 4.1 cold load, render readback, step, or reset evidence;
- EBench task config or evaluator output;
- safe binary/USD crate rewriting for layers that contain asset dependencies.

Those remain assigned to `AAN-04` through `AAN-07`.

## DryingBox Source Status

The implementation is validated on synthetic DryingBox-shaped USD fixtures that include
required prims, USD dependencies, MDL, texture, variants, clips, missing dependencies, and
remote URI blockers. A real LabUtopia DryingBox source USD was not present in the ConvertAsset
repository. The first real DryingBox package run still requires the source USD path.

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

## Next Milestone

Start `AAN-04 Material Closure`: upgrade the static MDL/texture package mirror into material
closure records with source preservation evidence, channel provenance, fallback policy, and
blocked/waived material semantics.
