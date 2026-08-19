# 2026-08-18 LICHEN analytical-balance r1 sliding doors

## Outcome

ConvertAsset now admits a source-bound, Isaac Sim 4.1 articulated package for
the LICHEN procedural analytical balance. The four sliding windshield doors
are commanded prismatic DOFs. Sibling handles are welded to those doors.
Buttons stay visual-static.

The commanded-travel package is:

`outputs/scientific_workbench_analytical_balance_lichen_r1_20260818/packages/analytical_balance_lichen_r1_release4/`

Front-handle **contact opening** is a later package, release5; see
[2026-08-18 LICHEN front-door block contact opening](2026-08-18-analytical-balance-lichen-r1-front-door-contact.md).

AAN-06 `overall_status` is `pass`. Static closure records one articulation
root, nine joints, four controllable DOFs, and nine rigid bodies.

Isaac 4.1 evidence passes:

- front/left/right/top door state cycles at 0.105 m open, 0 m reset;
- front-handle follow, including preserved rest pose and handle offset;
- fixed-base benchtop stability.

A Playable sidecar USDA sequences the four-door open/close cycle. It does not
bake `timeSamples` into the admitted `asset.usd`. This headless host has no
GLFW display, so viewport frames and `doors_open_close.mp4` were not captured.

The incoming USDA was not modified. Scenario Forge Task 15 was not rebound.

## Claim boundary

This proves commanded door travel/readback, handle weld follow, and a
fixed-base benchtop mount in Isaac 4.1. It does not claim robot-contact
opening, tare, weighing readout, button press, robot-policy success, or
real-world instrument calibration.

## Source

Read-only incoming USDA:

`/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/scientific_workbench_asset_library_20260810/实验室资产库/05_实验仪器/LICHEN电子分析天平_程序化版本/analytical_balance_lichen.usda`

- SHA-256: `c5162d560380a9586f9cd5952e4961c27503877e7346ac0ea2ed040a238141b8`
- Z-up metres, bottom at Z=0
- no UsdPhysics in the source
- handles are siblings of doors, not children
- URDF listed four prismatic joints but `links/*.glb` were not shipped, so
  this admission authors USD Physics from the USDA rest poses and URDF limits
  rather than importing URDF

Door travel used for animation and qualification is 0.105 m, inside the URDF
limits (front 0.125 m on X; left/right 0.135 m on +Y; top 0.120 m on +Y).

Public entry: `/World/AnalyticalBalanceLichen`
Source ref: `/World/AnalyticalBalanceLichen/Source`

## Producer repairs

The facade authors:

- `PhysicsArticulationRootAPI` on the public entry;
- a world-fixed `PhysicsFixedJoint` with `body0` at the entry and `body1` at
  `Source`, which is the benchtop fixed-base contract;
- four `PhysicsPrismaticJoint`s with explicit `physics:localPos0` from the
  source rest translates, so PhysX does not collapse door origins onto the
  base origin;
- four handle `PhysicsFixedJoint`s with `localPos0` equal to the source
  handle-to-door offset;
- `!resetXformStack!` on nested rigid bodies;
- housing and platform convex-hull colliders only.

Door and handle meshes have no collision. A single convex hull on the housing
would trap the glass panels inside the chamber and drive the free axes to
their limits.

## Isaac 4.1 qualification

Runtime: Isaac Sim 4.1.0
(`/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python`).
Do not use `./scripts/isaac_python.sh` as the qualify interpreter; that path
resolves Isaac 4.5 in this environment.

Door-cycle and handle-follow report:

`outputs/scientific_workbench_analytical_balance_lichen_r1_20260818/evidence/lichen_r1_release4_qualification_final/report.json`

After commanding 0.105 m, the front door world delta was 0.105 m on X, the
handle offset stayed 12.5 mm on -Y, and the rest pose
`(0, -0.024855, 0.168565)` was preserved. Earlier release2 evidence showed
identity `localPos` plus housing collision collapsing that pose to the joint
origin and slamming the front door to the 0.125 m limit; that package is
retained as failed evidence and must not be consumed.

Benchtop observation measured AABB
`[0.17827999591827393, 0.28356999158859253, 0.27254000771790743]` m. Those
values are bound in the device profile `aan.articulated_mounting.v1`
candidate. The merged six-gate report recorded zero root drift, zero support
gap/penetration, zero scoped PhysX errors, and no session physics mutation.

Merged runtime report:

`outputs/scientific_workbench_analytical_balance_lichen_r1_20260818/evidence/lichen_r1_release4_benchtop/runtime_report.json`

## Hashes

| Artifact | SHA-256 |
| --- | --- |
| Incoming USDA | `c5162d560380a9586f9cd5952e4961c27503877e7346ac0ea2ed040a238141b8` |
| Facade USDA | `ddcce04a507bd82abb71a9ab2fa85cb2ec5059796e97e74c019523dc16eff4c6` |
| Device profile | `eae2aa725b1c95cb424dc33b82d8b444fd5da8b940d54f64f167328c0bc08dff` |
| Package `asset.usd` | `e91264d2704c305496816753fd8ff932cc4d284fae0ef04c87514a39845c2f18` |
| Prequalification manifest | `7c12db4a58fd59f6ee5949840b9cd487726e4250f67244e658342bf8e0543bca` |
| Runtime report | `42138b02b34c4b30d89a38bf3f51c4c817959faf9dd554e75cc42d21de31ab1b` |
| Final manifest | `26b3a402a40fa530e4057e2b7de63642a5e69a6cdca67573c2bdb42a44ff3166` |
| Door timeline USDA | `b52bdbac9520850947f4b0399049cd419f2056eeda5d503894cd16366dfd99d4` |

Consumer placement is identity: put the wrapper at the desired support-plane
position with identity local orientation. Qualified visual extents are about
0.178 × 0.284 × 0.273 m.

## Animation

Sidecar (open in Isaac Sim and press Play):

`outputs/scientific_workbench_analytical_balance_lichen_r1_20260818/evidence/door_animation/demo_timeline.usda`

It references the promoted `asset.usd` and authors sequential
`state:linear:physics:position` samples at 0.105 m for front, left, right,
then top. Capture status is recorded in `record_status.json` in the same
directory.

## Scripts

- `scripts/build_analytical_balance_lichen_r1_assets.py`
- `scripts/qualify_analytical_balance_lichen_task_interactions.py`
- `scripts/qualify_articulated_benchtop_stability.py`
- `scripts/finalize_articulated_package.py`
- `scripts/record_analytical_balance_lichen_door_animation.py`
