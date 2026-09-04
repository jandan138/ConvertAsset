# OVEN 125 r17 teleoperation knob hardening

## Investigation

The VR operator reported intermittent physical knob motion without a display
update. The proposed diagnosis was that Isaac Sim 4.5 could not return a live
pose for articulation links through `get_rigidbody_transformation`, causing the
controller to fall back to a static USD pose.

The structural part of that report was correct: r16 added an articulation root,
changed `Instance` from Scope to Xform, changed only `Body` from kinematic to
dynamic, and added `Instance/Joints/BaseFixed`. The categorical pose claim was
not correct. Under the same Isaac 4.5 physical-drive protocol, r15 and r16 both
changed the setpoint and display from 60 to 63. The interface returned live r16
articulation-link poses; it emitted a deprecation warning in the test harness,
not an invalid-handle error.

The real robustness gap was in the embedded controller and qualification:

- a missing PhysX sample fell back to the static USD pose;
- the next valid sample could therefore look like a discontinuity;
- every single-frame delta above 60 degrees cleared the accumulated motion;
- the original promotion only ran the full knob/display chain in Isaac 4.1,
  while 4.5 received articulation/rest checks only.

## r17 design

r17 preserves every r16 prim path, collider, joint, mass, material, fixed-base
property, and the 15-degree detent. Only the embedded controller and four custom
diagnostic attributes change.

- Runtime knob input reads PhysX poses only. Missing samples skip the frame and
  retain the last valid angle and pending detent accumulator.
- Valid motion is never cleared because a frame exceeds 60 degrees.
- At most four detents are applied per controller tick; remaining motion drains
  on later ticks.
- Sub-threshold forward/reverse jitter continues to cancel in the accumulator.
- Each knob records physical-sample validity, miss count, last valid delta, and
  total emitted detents.

The ScriptNode trust boundary is unchanged. A trusted internal package must be
allowed by the operator/runtime. The qualification includes an explicit denied
trust negative control and does not attempt to bypass Isaac's security policy.

## Verification

Isaac Sim 4.5 is the primary r17 controller runtime. Primary and auxiliary knobs
each passed three cold starts. Every run exercised sub-threshold jitter, smooth
rotation, rapid rotation, and pause/resume:

- jitter: zero setpoint change in all six runs;
- smooth: +2 to +3 detents;
- rapid: +16 to +22 detents, with no accumulator clear;
- pause/resume reverse motion: -1 to -3 detents;
- physical pose sample remained valid and miss count stayed zero.

The denied ScriptNode negative control kept the setpoint at 60 and event sequence
at zero, as expected. Isaac Sim 4.1 regressions passed for both physical knob
rotation/press chains, 16-DOF articulation initialization, fixed-base stability,
and the 60-degree door with zero-degree closing residual.

Static and logic tests cover one-to-three missing samples, recovery of a 45-degree
net rotation, rate-limited draining of a 90-degree burst, sub-threshold jitter,
path preservation, diagnostic attributes, and honest pending claims.

Evidence and the standalone handoff are under
`outputs/ika_oven_125_task09_r17_teleop_hardened_20260904/`.

## Claim boundary

The package is qualified for deterministic VR-like joint-drive profiles in
Isaac Sim 4.5 and the listed 4.1 regressions. No real headset/controller contact,
VR extension integration, robot policy, benchmark success, or arbitrary missing
sample occurrence in PhysX is claimed.
