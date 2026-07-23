# 2026-07-23 AAN Scope-First Closure and Visual-Static Rigid Reset Fixes

## Why this record exists

Scenario Forge probe runs on 2026-07-23 surfaced two AAN admission defects
that blocked visual_static package delivery:

1. `.convertasset-ebench-table-20260723` (`lab_001.usd:/World/table`,
   visual_static) blocked at `aan06_block_runtime_smoke`: the reset cycle
   failed because the rigid-body reset gate evaluates an empty transform map
   as `blocked` when the visual_static scope declares zero rigid bodies.
2. `.convertasset-scene1-table-hard-probe` showed that dependency closure was
   evaluated over the whole source layer graph: an unselected sibling
   (`table_hard`) with missing textures blocked admission of the selected
   `Scene1_hard.usd:/World/lab_015` room scope at
   `aan03_block_missing_dependency`.

The downstream request asked for a single revision fixing both points and
re-exporting the `room` and `lab_001:/World/table` packages with
`overall_status: pass`.

## Changes

| File | Change |
|---|---|
| `convert_asset/asset_application_normalizer/runtime_smoke.py` | New `_build_rigid_reset_gate`: when `asset_role == "visual_static"` and the scoped rigid-body list is empty, the rigid reset gate is `not_applicable` (scope load/render/step/reset evidence still runs); any other role keeps the strict evaluation. The reset cycle status accepts `not_applicable` for the rigid gate. The isolated worker now receives `--asset-role` (parser + `build_runtime_smoke` argv). |
| `convert_asset/asset_application_normalizer/usd_closure.py` | New `_scope_dependency_filter`: for role-scoped packages (visual_static, or dynamic with a physics/interaction profile) with declared scope prims, non-USD asset dependencies are partitioned by the population-masked composed scope closure (scope prims + bound materials, same mask semantics as `_build_role_scoped_source`). USD layers stay unfiltered so the package still composes the complete source layer graph. In-scope missing/remote deps still block; out-of-scope deps are recorded under `dependency_closure.scope_dependency_filter.out_of_scope_dependencies` and are not copied into the package. When the filter cannot run (no scope, non-scoped role, or pxr unavailable) behavior is unchanged and the record is `not_applicable`. |
| `tests/test_asset_application_normalizer_physics_admission.py` | 5 new regression tests: rigid reset gate `not_applicable`/strict/evaluates-when-present, worker argv carries `--asset-role`, and an end-to-end scope-first fixture (referenced room + unselected sibling with a missing texture) asserting admission passes, the sibling texture is recorded out-of-scope and not copied, and the package preserves the parent-layer `xformOp:translate/rotateXYZ/scale`, `metersPerUnit`, and `upAxis`. |

## Behavior notes

- Parent-layer units and scope transforms were already preserved by the
  population-masked flatten; the new end-to-end test and the delivered room
  package lock this as evidence (`translate (0.0079, 0.2706, 0)`,
  `rotateXYZ (0, 0, 180)`, two `scale` ops, `metersPerUnit 1.0`, `Z`-up on
  `Scene1_hard.usd:/World/lab_015`).
- Dynamic admission semantics are unchanged: an empty scoped rigid-body set
  still fails the rigid reset gate.
- An in-scope missing texture still blocks AAN-03; only unselected siblings
  are excluded.

## Verification

- `python -m pytest tests/ -q` -> `665 passed, 4 skipped` (5 new tests).
- `python -m ruff check` on the three touched files -> clean.

## Delivered packages (overall_status: pass, all seven stage gates pass)

| Package | Source | Scope | Path |
|---|---|---|---|
| room | `Scene1_hard.usd` (SHA-256 locked, unchanged) | `/World/lab_015` | `/cpfs/user/zhuzihou/dev/scenario-forge/outputs/convertasset-scene1-hard-lab015-room-20260723` |
| table | `lab_001_localized_20260707/lab_001.usd` | `/World/table` | `/cpfs/user/zhuzihou/dev/scenario-forge/outputs/convertasset-lab001-table-visual-static-20260723` |

Both manifests live at `<package>/evidence/manifest.json` with
`overall_status: pass`, `blocked_reasons: []`, runtime smoke `pass`, rigid
reset `not_applicable`, and `scope_dependency_filter.status: applied` (room
records 13 excluded out-of-scope dependencies). Both were produced with
`--gates static,runtime` and the Isaac 4.1 runtime worker
(`embodied-eval-os-sim-isaacsim41-genmanip-py310`).

## Claim boundary

- The room package claim covers the declared `/World/lab_015` scope only;
  the unselected `table_hard` remains unadmitted (its textures are genuinely
  missing) and is listed as out-of-scope evidence, not waived.
- Both packages are visual_static admissions: no rigid-body, collision,
  articulation, or task-success claim is made; AAN-06 rigid reset is
  `not_applicable` by role, not skipped.
