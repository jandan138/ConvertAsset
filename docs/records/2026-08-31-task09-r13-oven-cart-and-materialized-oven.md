# Task 09 r13 Oven Cart and Materialized Oven

## Outcome

ConvertAsset delivered three promoted Task 09 inputs:

- `outputs/task09_r13_compact_oven_cart_20260831/`: a compact
  `0.90 x 0.76 x 0.755 m` static-support cart derived from
  `input_01_seed_250103`;
- `outputs/ika_oven_125_task09_r13_materialized_20260831/`: an OVEN 125
  stage-base package authored directly at `/World/obj_oven`;
- `outputs/task09_r13_beaker_325ml_sdf_clean_closure_r2_20260831/`: the
  admitted dynamic SDF beaker with a clean MDL closure and Hydra-compatible
  invisible collision-proxy normals.

## Cart derivation and qualification

The source frame was 1.60 m wide, 0.76 m deep, and 0.74 m tall. A piecewise X
warp preserved the 50 mm side members while shortening the center span. The
feet remained fixed and the top moved to 0.755 m. The producer's 16 frame
colliders were transformed consistently, and an invisible `0.84 x 0.72 m`
central support collider was added because the source visual tray had no
central load-bearing collider.

Isaac Sim 4.1 passed all five edge/center drops, side impact, three reset
cycles, and three independent 100 kg appliance-load runs. The load height error
was approximately `7.2e-9 m` and lateral drift approximately `2.6e-8 m` in each
run. This is a simulator support claim, not real structural certification.

## Why the oven is materialized

The identity-root oven retained correct physical joint behavior under USD
references, but the producer OmniGraph ScriptNode did not execute when the
graph was introduced solely through a consumer reference. A direct stage did
execute it. The Task 09 package therefore renames and retargets the complete
stage to `/World/obj_oven` and declares `consumer_mode = materialized_stage_base`.
Scenario Forge must copy this stage and append other scene objects; it must not
reference the oven package again.

Three producer interactive smokes passed in Isaac Sim 4.1. Each run verified
the embedded graph, physical knob rotation changing the temperature setpoint,
physical knob press starting heating, all control branches, and source
immutability.

## Beaker closure correction

The earlier package had a stronger local OmniGlass binding but retained one
stale `/data/teleop/.../OmniGlass.mdl` path in a package-local weak source layer.
The r2 closure rewrites it to `../mdl/OmniGlass.mdl`. It also gives the invisible
collision proxy one constant normal, removing a Hydra buffer-size warning
without changing topology, collision approximation, dynamics, or visible
material. `UsdUtils.ComputeAllDependencies` reports no unresolved dependency.

Robot-policy, benchmark, real load rating, and thermal calibration remain
unclaimed.
