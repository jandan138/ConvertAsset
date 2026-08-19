# 2026-08-18 LICHEN front-door block contact opening

## Outcome

ConvertAsset now admits a source-bound LICHEN analytical-balance package whose
front sliding door can be opened and closed by physical contact in Isaac Sim
4.1. A session-only kinematic block presses `Front_Door_Handle` along +X to
open, then presses the opened handle's +X face back to close. The block is
not written into the admitted USD.

The promoted package is:

`outputs/scientific_workbench_analytical_balance_lichen_r1_20260818/packages/analytical_balance_lichen_r1_release5/`

AAN-06 `overall_status` is `pass`. Static closure still records one
articulation root, nine joints, four controllable DOFs, and nine rigid bodies.

Isaac 4.1 evidence passes:

- `front_door_contact_cycle`: open readback 0.10499 m, close readback 0.0 m,
  no rest-pose handle/housing overlap, no `set_joint_positions` during the
  sweep;
- the existing four door state cycles, front-handle follow, and benchtop
  stability.

release4 remains valid for commanded travel only. Consume release5 when
contact opening is required. Incoming USDA was not modified. Scenario Forge
Task 15 was not rebound.

## Claim boundary

This proves Isaac 4.1 **block-on-handle contact opening** of the front
sliding door, plus commanded travel and a fixed-base benchtop mount. It does
not claim robot grasp, robot-policy success, left/right/top contact opening,
tare, weighing readout, or button press.

## Package change

The facade enables `convexHull` collision on `Front_Door_Handle` / `Cube_021`
only. Housing and platform colliders stay. The four glass doors and the other
three handles remain without collision. Prismatic joints stay free (no stiff
position drive). Handle welds are unchanged.

The front door slides **+X** (operator's right when facing the balance). Open
target is 0.105 m.

## Isaac 4.1 qualification

Runtime: Isaac Sim 4.1.0
(`/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python`).
Do not use `./scripts/isaac_python.sh` as the qualify interpreter.

Contact and door-cycle report:

`outputs/scientific_workbench_analytical_balance_lichen_r1_20260818/evidence/lichen_r1_release5_qualification/report.json`

Merged benchtop report:

`outputs/scientific_workbench_analytical_balance_lichen_r1_20260818/evidence/lichen_r1_release5_benchtop/runtime_report_final.json`

Benchtop AABB remains
`[0.17827999591827393, 0.28356999158859253, 0.27254000771790743]` m with zero
root drift.

## Hashes

| Artifact | SHA-256 |
| --- | --- |
| Incoming USDA | `c5162d560380a9586f9cd5952e4961c27503877e7346ac0ea2ed040a238141b8` |
| Facade USDA | `52c8b59c3f87a35c5dc0e74cddd76bb36ac4d3f6cae646c02a860fc7ea107c3a` |
| Device profile | `1583091e56efa88a41c571b209433aa2d774980041a10eac901bdd88216fb01a` |
| Composed source_root | `9450c0cb1407ec0f14d4720c5bdde75974af2f706ff43016d8da250895b47756` |
| Prequalification manifest | `8714f8d4ad071e8246e28a85e8bbf2fbc4fe9f3d7ec2ccb6aa4bdc1ef5cc29f6` |
| Qualification report | `82ffbbcaeb546eaf90d88eab26b55f46ef3c0a5a1ff2116662411e5d9a4c0467` |
| Runtime report | `1107b0a65ed462b844eb798fa30beb8ffdab748e2f345e394f4f300b0aaec984` |
| Final manifest | `64fef3b3a3a55c13fc100bae7cd1a0166d7df77298dfb0df080289aa50731a2e` |

`asset.usd` is a composition root and keeps the same bytes as release4. The
front-handle collider lives in the referenced facade/`source_root` layer.

## Scripts

- `scripts/build_analytical_balance_lichen_r1_assets.py`
- `scripts/qualify_analytical_balance_lichen_task_interactions.py`
- `scripts/qualify_articulated_benchtop_stability.py`
- `scripts/finalize_articulated_package.py`

Design: `docs/superpowers/specs/2026-08-18-lichen-front-door-contact-opening-design.md`
