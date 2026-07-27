# 2026-07-27 External Room Facade Admission and Zone Profiles (3FO4K5C9JD44)

## Why this record exists

Scenario Forge requested admission of the restricted external room
`3FO4K5C9JD44` (`world.usda`, hash-bound) as a `visual_static_environment`
package with a consolidated consumer facade, plus v0.2 workspace zone
profiles. The raw stage is multi-root: default prim `/world` (Looks, ground,
PhysicsScene), room geometry under `/Root` (7134 prims), render settings
under `/Render`, with 181 cross-namespace material bindings `/Root ->
/world/Looks`. Consuming raw `/world` alone yields an almost empty room.

## Producer-owned facade (raw tree immutable)

`outputs/external_environment_3fo4k5c9jd44/facade/`:

- `facade.usda`: defaultPrim `World`, mounting `/world`, `/Root`, `/Render`
  via relative references into `/World/world`, `/World/Root`, `/World/Render`;
  records the raw-root namespaces as custom data.
- `binding_fix.usda`: stronger overlay retargeting all 181 cross-namespace
  `material:binding` targets from `/world/Looks/...` to
  `/World/world/Looks/...` (merged single prim tree; relationship targets
  verified 2738/2738 resolvable after composition).
- `facade_provenance.json`: raw->facade namespace mapping and source hash
  (`world.usda` SHA-256 `03aa64f2...`, re-verified unchanged after the run).

## AAN code fix (this delivery)

`_scope_bound_material_paths` now skips binding targets whose material prim
is **inactive** (`usd_closure.py`). The raw source carries 65 inactive
material variants with lingering bindings; the population-masked flatten
drops inactive prims, so requiring them falsely blocked scope extraction
(`Scoped USDA lost required visual/material prims`). Regression test:
`test_scope_extraction_skips_bindings_to_inactive_materials`.

## Admission result (gates static,runtime, Isaac 4.1 worker)

Package `outputs/external_environment_3fo4k5c9jd44/package`:
`overall_status: pass`, all seven stage gates pass,
`blocked_reasons: []`, 1223 package-local deps (0 remote, 0 missing).
Manifest entrypoints exactly as required (`root_usd: asset.usd`,
`default_prim: World`, `asset_entry_prim: /World`, scope `[/World]`,
consumer `scenario-forge`), and
`visual_preservation_fingerprint.package_after_role.scope_world_transforms`
contains the facade `/World` transform. Runtime render passes at 0.9994
non-background via an interior probe and shows the complete lab room.
`evidence/facade_provenance.json` carries the raw hash for the
`preserve_source_usd_sha256` requirement.

## Zone profiles (v0.2)

`zone_profiles/` with `zone_profile_manifest.json`:

| Zone | Status | Assembly | Yaw | Notes |
|---|---|---|---|---|
| north_bench_pair_east | profiled | LabEquipment Actor_0002+0003 | 90 | Cleanest: only 4 counter-prop actors as optional inactives |
| north_bench_pair_west | profiled | LabEquipment Actor_0009+0000 | 90 | 9 test-tube/tray prop actors as optional inactives |
| south_table_b | profiled | Table Actor_0002 | 0 | Table + 17 complete prop-actor roots (faucets, jars, chairs, laptop, microscope...) |
| east_bench | **not_applicable** | — | — | 0.84 m benches narrower than the 2.345 m workbench; clearance overlaps neighbor bench, wardrobe, and 14 dense prop actors |

Anchors are source-composed (metric, `source_composed_meters_per_unit: 1.0`);
yaw follows the validated compositions (x-axis rows 90 deg like 083, y-axis
table 0 deg like 066/059). Before/after Isaac 4.1 renders per profiled zone
under `zone_profiles/evidence/`.

## Claim boundary

- visual_static_environment only: no task success, background interaction
  physics, or liquid transfer claims.
- Raw tree, packages, robot, tabletop, and task poses unchanged; facade
  layers and zone profiles are producer-owned sidecars.

## Verification

- Binding resolution 2738/2738 after facade composition.
- Raw `world.usda` SHA-256 unchanged post-run.
- `python -m pytest tests/ -q` -> `675 passed, 4 skipped` (1 new test).
