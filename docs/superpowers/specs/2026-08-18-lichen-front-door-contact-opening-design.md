# LICHEN Front-Door Contact Opening

Date: 2026-08-18

## Goal

Admit a new ConvertAsset package where the LICHEN analytical-balance **front
sliding door can be opened and closed by physical contact** in Isaac Sim 4.1.

Success is a session-only kinematic block that presses `Front_Door_Handle`
along **+X** and backdrives the front prismatic joint to the existing open
band, then reverses to close. This is not a robot policy, gripper, or
Scenario Forge Task 15 rebind.

## Decisions

- Physical contact opening, not command-only qualification.
- Front door only. Left, right, and top stay commandable.
- Puller is a colliding box, not a two-finger gripper.
- Work stays in ConvertAsset. Do not edit the incoming USDA.
- Promote a new package (`analytical_balance_lichen_r1_release5`). Do not
  overwrite release4.

## Package changes

Enable `convexHull` collision on `Front_Door_Handle` / `Cube_021` only.

Keep housing (`White_Main_Housing` / `Cube_001`) and platform
(`Black_Lower_Platform` / `Cube`) colliders. Leave the four glass doors and
the other three handles without collision.

Joints stay as in release4: free prismatic doors, handle `PhysicsFixedJoint`
welds, no stiff position drive. The puller is **not** authored into the
admitted USD.

Rest-pose overlap between the front handle and housing/platform AABBs is a
hard fail. Do not add filtered pairs in this cut.

Front door travel remains **+X**, open command/contact target **0.105 m**,
joint limit 0.125 m. Z-up metres. Standing in front of the balance (looking
toward +Y), +X is the operator's right.

## Qualification

Isaac 4.1 interpreter:

`/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python`

Do not use `./scripts/isaac_python.sh` as the qualify interpreter.

New required gate: `front_door_contact_cycle`.

Protocol:

1. Rest pose: front handle does not overlap housing/platform AABBs; front
   joint near 0.
2. Spawn a kinematic box in the qualification session only, against the
   handle's −X face, and translate it along +X far enough that contact travel
   is 0.105 m after the approach gap. Do not `set_joint_positions` during this
   sweep.
3. Front prismatic readback must reach ≥ 0.105 m (band 0.100–0.125 m).
4. Detour the box in −Y around the handle, place it on the opened handle's
   +X face, and translate −X until the joint returns to the closed band.
5. Existing four door state cycles, handle-follow, and benchtop stability
   still pass on the same package. Benchtop reloads the package without the
   session puller.

Fail the package if any of those gates fail. Write the runtime report before
any `SimulationApp.close()`.

## Claim boundary

This proves Isaac 4.1 **block-on-handle contact opening** of the front
sliding door, plus the existing commanded travel and benchtop mount.

It does not claim robot grasp, robot-policy success, left/right/top contact
opening, tare, weighing, button press, or Task 15.

## Tests

- Builder authors `Cube_021` collision and does not author collision on the
  other door/handle meshes.
- Device profile lists `front_door_contact_cycle`.
- Contact-gate helper passes only when open/close readback succeeds without
  a joint command and without rest overlap.
