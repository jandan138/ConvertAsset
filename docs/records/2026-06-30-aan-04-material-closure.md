# AAN-04 Material Closure

Date: 2026-06-30

## Summary

AAN-04 material closure is implemented for the source-preserving MVP path. After AAN-03 writes a
package-local USD tree, AAN-04 opens the package `asset.usd`, inventories `UsdShade.Material`
prims, correlates their MDL and texture assets with `dependency_closure.local_files`, and writes
per-material evidence records into the manifest.

The implementation does not delete MDL, does not silently replace source materials, and does not
claim render/runtime material parity. PreviewSurface fallback remains a recorded policy path, but
this milestone only generates fallback records when a future fallback implementation exists. For
the current DryingBox overlay, all material assets are preserved as package-local MDL/texture
inputs, so `local_mirror` is the correct closure mode.

## Code Changes

- `convert_asset/asset_application_normalizer/material_closure.py`
  - new AAN-04 scanner with lazy `pxr` imports;
  - enumerates material and shader prims from the package USD;
  - records shader ids, MDL source assets, texture paths, extracted channel provenance,
    transparency strategy, residual MDL status, fallback status, and visibility-evidence boundary;
  - computes package SHA-256 for material assets;
  - uses package-relative shader asset references to handle referenced child layers whose composed
    material path differs from the source layer prim path.
- `convert_asset/asset_application_normalizer/pipeline.py`
  - runs AAN-04 after AAN-03 package success;
  - emits AAN-04 `not_run` when AAN-03 dependency closure is blocked;
  - upgrades non-dry-run manifests to milestone `AAN-04-material-closure`.
- `convert_asset/asset_application_normalizer/evidence_manifest.py`
  - accepts `material_closure` and `static_material_report`.
- `convert_asset/asset_application_normalizer/model.py`
  - adds `MILESTONE_AAN04`.

## Manifest Fields

Each material record includes:

- `closure_mode`: one of `native_resolved`, `local_mirror`, `preview_surface_fallback`,
  `explicit_waiver`, `blocked`;
- `source_mdl_assets`: raw path, resolved source path, package path, package hash, source hash when
  available, shader prim, and detected MDL effect tags;
- `texture_paths`: raw path, resolved source path, package path, package hash, and shader prim;
- `extracted_channels`: baseColor, roughness, metallic, normal, and opacity provenance;
- `transparency_strategy`: `opaque` or `opacity_input` in the current MVP;
- `preview_surface_fallback`: currently `not_generated` when source assets are preserved;
- `residual_mdl`: explicit local/external/blocked counts;
- `visibility_evidence`: `not_run`, assigned to AAN-06 runtime smoke.

`static_material_report` summarizes material count, closure-mode counts, MDL/texture asset counts,
blocked material count, and transparency strategy counts.

## Real DryingBox Evidence

Evidence directory:

```text
docs/records/evidence/2026-06-30-aan-04-dryingbox-material-closure/
```

The real runs used the existing wrapper:

```text
./scripts/isaac_python.sh ./main.py normalize-asset ...
```

No conda environment or package installation was modified.

| Manifest | Overall status | AAN-04 gate | Missing deps | Remote URI | Materials | Closure summary |
|---|---:|---:|---:|---:|---:|---|
| `single_dryingbox_01.json` | blocked | not_run | 1 | 0 | 0 | AAN-03 blocked before material closure |
| `labutopia_lab_001_dryingbox_01.json` | blocked | not_run | 0 | 4 | 0 | AAN-03 blocked before material closure |
| `overlay_level1_poc_dryingbox_01.json` | pass | pass | 0 | 0 | 27 | `local_mirror=27, blocked=0` |

Overlay package:

```text
/tmp/aan04_real_packages/overlay_level1_poc_dryingbox_01
```

Package escape scan found no `http://`, `https://`, `omniverse://`, `/cpfs/...`, or `/isaac-sim/...`
strings in the generated package.

## Remaining Boundaries

- AAN-04 records material closure evidence; it does not run render readback or visibility tests.
  Transparent visibility remains assigned to AAN-06.
- AAN-04 preserves source MDL/texture assets. It does not yet synthesize PreviewSurface fallback
  networks.
- Full material visual parity is not claimed. The manifest only claims package-local source
  preservation and recorded channel provenance.

## Verification

RED checks:

```text
3 failed for initial AAN-04 tests before implementation
1 failed for referenced child-layer material asset correlation before the package-path fix
```

Focused GREEN checks:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_writes_material_closure_for_packaged_mdl_and_texture tests/test_asset_application_normalizer_cli.py::test_normalize_asset_reports_native_preview_surface_material tests/test_asset_application_normalizer_cli.py::test_normalize_asset_writes_package_local_usd_closure -q
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_links_material_assets_from_rewritten_child_layers -q
```

Results:

```text
3 passed
1 passed
```

AAN CLI regression check:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py -q
```

Result:

```text
14 passed
```

Final relevant regression check:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports -q
```

Result:

```text
16 passed
```

Syntax and whitespace checks:

```bash
python -m py_compile convert_asset/asset_application_normalizer/material_closure.py convert_asset/asset_application_normalizer/pipeline.py convert_asset/asset_application_normalizer/evidence_manifest.py convert_asset/asset_application_normalizer/model.py
git diff --check
```

Result: both exited `0`.

AAN-04 evidence audit:

```text
AAN-04 evidence audit passed
```

Overlay package smoke:

```text
stage_open: True
required_prim_valid: True
```
