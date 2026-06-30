# AAN-03R Resolution Records Implementation

Date: 2026-06-30

## Summary

AAN-03R is now implemented at the evidence-manifest layer. AAN still keeps the existing AAN-03
scanner and package writer, but every missing or unauthorized remote dependency gap now gets a
machine-readable final decision record:

- `mirrored`: dependency was found through local mirror search and written into the package;
- `blocked`: dependency cannot be accepted until it is mirrored, safely pruned, or explicitly
  waived with claim limits;
- `pruned` and `waived`: reserved in the summary schema for later policy-backed implementation.

This prevents a manifest from only saying "missing" or "remote" without telling product and
engineering what decision was made.

## Code Changes

- `convert_asset/asset_application_normalizer/usd_closure.py`
  - added resolution fields to dependency manifest records;
  - marks successful local mirror hits as `resolution = mirrored`;
  - writes blocked records for unresolved missing local dependencies;
  - writes blocked records for unauthorized remote URI dependencies;
  - adds `dependency_closure.resolution_records`;
  - adds `dependency_closure.resolution_summary` with stable keys:
    `mirrored`, `pruned`, `waived`, `blocked`.
- `convert_asset/asset_application_normalizer/evidence_manifest.py`
  - adds empty `resolution_records` and zeroed `resolution_summary` to dry-run manifests.
- `tests/test_asset_application_normalizer_cli.py`
  - covers missing local dependency -> `blocked`;
  - covers unauthorized remote URI -> `blocked`;
  - covers sidecar MDL mirror -> `mirrored`.

## Decision Semantics

`mirrored` is intentionally stricter than "found a local candidate". A dependency is counted as
`mirrored` only after it has a package path. If another blocker prevents package writing, local
mirror candidates are not counted as final mirrored decisions.

This keeps the product claim clean: a blocked source cannot claim package-local closure just
because AAN found some helper MDL files.

## Real DryingBox Evidence

The real evidence manifests were regenerated with the existing Isaac Python wrapper:

```text
./scripts/isaac_python.sh ./main.py normalize-asset ...
```

No conda environment was modified. The wrapper used the existing Isaac Python at:

```text
/isaac-sim/kit/python/bin/python3
```

Evidence directory:

```text
docs/records/evidence/2026-06-30-aan-03-dryingbox-real/
```

Results:

| Manifest | Status | Missing | Unauthorized remote URI | Resolution summary |
|---|---:|---:|---:|---|
| `single_dryingbox_01.json` | blocked | 1 | 0 | `mirrored=0, pruned=0, waived=0, blocked=1` |
| `labutopia_lab_001_dryingbox_01.json` | blocked | 0 | 4 | `mirrored=0, pruned=0, waived=0, blocked=4` |
| `overlay_level1_poc_dryingbox_01.json` | pass | 0 | 0 | `mirrored=6, pruned=0, waived=0, blocked=0` |

The overlay package was written to:

```text
/tmp/aan03r_real_packages/overlay_level1_poc_dryingbox_01
```

Package escape scan found no remote URI or source absolute path in that package.

USD package open check:

```text
stage_open: True
required_prim_valid: True
```

## Remaining Blocked Gaps

These are not AAN-03R implementation gaps. They are source-asset dependency gaps that remain
blocked until the asset owner provides more evidence or files:

1. `DryingBox_01.usd` still lacks:

   ```text
   ./SubUSDs/textures/UnitsAdjust-efff8189aa8b94db49f62005befc3d4e.metricsAssembler
   ```

   Required resolution: find and package the missing local dependency, prove task-scope
   prune/waiver safety, or keep this source blocked.

2. Raw `lab_001.usd` still has four unauthorized remote URI dependencies:

   ```text
   https://omniverse-content-production.s3.us-west-2.amazonaws.com/Materials/Base/Metals/Aluminum_Anodized_Charcoal.mdl
   https://omniverse-content-production.s3.us-west-2.amazonaws.com/Materials/Base/Metals/Steel_Stainless.mdl
   https://omniverse-content-production.s3.us-west-2.amazonaws.com/Materials/vMaterials_2/Metal/Stainless_Steel.mdl
   http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.2/Isaac/Props/Sektion_Cabinet/sektion_cabinet_instanceable.usd
   ```

   Required resolution: mirror with provenance, prove task-scope prune/explicit allowance, or keep
   the raw lab source blocked.

## Verification

RED check before implementation:

```text
3 failed
```

The failures were missing `resolution`, `resolution_records`, and `resolution_summary` fields.

Focused GREEN check after implementation:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_missing_local_dependency_without_package tests/test_asset_application_normalizer_cli.py::test_normalize_asset_mirrors_mdl_from_package_sidecar_root tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_unauthorized_remote_uri_without_package -q
```

Result:

```text
3 passed
```

AAN CLI regression check:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py -q
```

Result:

```text
11 passed
```

Final relevant regression check:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports -q
```

Result:

```text
13 passed
```

Syntax and whitespace checks:

```bash
python -m py_compile convert_asset/asset_application_normalizer/usd_closure.py convert_asset/asset_application_normalizer/evidence_manifest.py
git diff --check
```

Result: both exited `0`.

Overlay package smoke:

```text
stage_open: True
required_prim_valid: True
```
