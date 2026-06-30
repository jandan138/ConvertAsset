# AAN-02 CLI Skeleton

Date: 2026-06-30

## Status

`AAN-02 CLI Skeleton` is complete for the Phase 1 Asset Application Normalizer MVP.

Commit scope:

- `convert_asset/asset_application_normalizer/`
- `convert_asset/cli.py`
- `tests/test_asset_application_normalizer_cli.py`

## Implemented

1. Added the `convert_asset.asset_application_normalizer` MVP module skeleton.
2. Added the flat `normalize-asset` subcommand to the existing `convert_asset/cli.py`
   argparse entrypoint.
3. Added a standard-library-only IR and pipeline path:
   - `NormalizeAssetRequest`
   - `NormalizeAssetResult`
   - package layout helpers
   - evidence manifest writer
   - dry-run normalization pipeline
4. Implemented MVP input gates:
   - source file must exist;
   - source extension must be `.usd`, `.usda`, or `.usdc`;
   - source runtime must be `isaac51`;
   - target runtime must be `isaac41`;
   - target benchmark must be `ebench-lift2`.
5. Implemented the AAN-02 dry-run contract:
   - `--dry-run` writes a schema-compatible evidence manifest;
   - `--dry-run` does not create target package contents;
   - non-dry-run writes a blocked manifest and returns code `5`.
6. Preserved the lazy import boundary:
   - importing `convert_asset.cli` does not import `pxr`, `omni.*`, or `isaacsim`;
   - importing `convert_asset.asset_application_normalizer` also stays runtime-clean.

## Explicit Non-Claims

AAN-02 does not implement:

- USD dependency closure;
- MDL / texture mirror;
- material fallback generation;
- physics or articulation inspection;
- package-local USD writing;
- Isaac Sim 4.1 cold load / render / step / reset;
- EBench task config or evaluator generation.

Those remain assigned to `AAN-03` through `AAN-07`.

## Verification

Focused TDD red/green:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py -q
```

Result:

```text
5 passed
```

Relevant regression and import-boundary checks:

```bash
python -m pytest \
  tests/test_asset_application_normalizer_cli.py \
  tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules \
  tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports \
  -q
```

Result:

```text
7 passed
```

Syntax check:

```bash
python -m py_compile \
  convert_asset/asset_application_normalizer/__init__.py \
  convert_asset/asset_application_normalizer/model.py \
  convert_asset/asset_application_normalizer/package_layout.py \
  convert_asset/asset_application_normalizer/evidence_manifest.py \
  convert_asset/asset_application_normalizer/pipeline.py \
  convert_asset/asset_application_normalizer/cli.py \
  convert_asset/cli.py
```

Result: exit code `0`.

## Next Milestone

Start `AAN-03 USD Closure`: implement real USD inventory and dependency package closure for
the DryingBox source USD once the source path is provided or located. The AAN-02 manifest
writer is intentionally minimal and should remain the handoff surface for later static and
runtime gates.
