# AAN-04 DryingBox Material Closure Evidence

Date: 2026-06-30

This directory records the first real DryingBox AAN-04 material closure runs.

AAN-04 runs only after AAN-03 writes a package-local USD tree. If AAN-03 is blocked by a missing
dependency or unauthorized remote URI, the material gate is recorded as `not_run`.

| Manifest | Source | Required prim | Overall status | AAN-04 gate | Material result |
|---|---|---|---|---|---|
| `single_dryingbox_01.json` | LabUtopia single `DryingBox_01.usd` | `/group_009` exists | blocked | not_run | AAN-03 still lacks `UnitsAdjust-*.metricsAssembler` |
| `labutopia_lab_001_dryingbox_01.json` | LabUtopia `lab_001.usd` | `/World/DryingBox_01` exists | blocked | not_run | AAN-03 still has 4 unauthorized remote URI dependencies |
| `overlay_level1_poc_dryingbox_01.json` | existing EBench overlay `scene.usda` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01` exists | pass | pass | 27 materials, all `local_mirror`, 0 blocked |

Overlay material summary:

```text
material_count = 27
local_mirror = 27
native_resolved = 0
preview_surface_fallback = 0
explicit_waiver = 0
blocked = 0
mdl_asset_count = 30
texture_asset_count = 4
transparency_strategy_counts = opacity_input:22, opaque:5
```

The pass package for the overlay run was written to:

```text
/tmp/aan04_real_packages/overlay_level1_poc_dryingbox_01
```

Package escape scan found no remote URI or absolute source path strings in the generated package.
