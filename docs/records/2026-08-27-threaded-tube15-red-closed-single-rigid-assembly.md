# Threaded 15 mL red closed single-rigid assembly

## Investigation

The original colleague `shiguan.usd` cap is an open threaded sleeve. The later
`lixinguan_funnel_liquid.usd` cap retained the internal thread profile and added
a source-geometry closed top. The promoted Wangshuai dynamic set exposes the
real-scale body and closed cap as separate dynamic packages.

Task 11 requires a permanently closed tube, not a cap-tightening episode. A
FixedJoint would still create two simulated bodies and could introduce solver
jitter. The selected representation therefore has exactly one dynamic rigid
root with body and cap visual/collision subtrees beneath it.

## Implementation

`scripts/build_threaded_tube15_red_closed_assembly.py` produces
`outputs/threaded_tube15_red_closed_assembly_20260827/`. It copies the promoted
body and cap packages byte-for-byte under package-local dependencies, removes
their child rigid/mass APIs at the composite layer, and authors one root mass
profile. Source SDF/convex collision geometry is unchanged.

The fixed cap pose is coaxial at `z=0.1074 m`, yaw `255 deg`, based on the
scaled source gravity-seated phase. The cap uses the existing Task 11 red PP
PreviewSurface values: diffuse `(0.56, 0.004, 0.008)`, roughness `0.42`, IOR
`1.47`. Combined provisional mass is `0.017 kg`; COM and inertia use a
parallel-axis merge of the existing body and cap profiles.

## Qualification

Three independent Isaac Sim 4.1 cold starts passed. Every run observed gravity
response, finite settled state, 10 cm fixed-carrier transport, zero hard
PhysX/CUDA errors, and invariant cap-to-body pose. The promoted package entry
is `/ThreadedTube15RedClosed` and has no authored kinematic opinion.

## Claim boundary

The package qualifies robot-free motion of a permanently closed single rigid
assembly. It does not claim real-scale screw tightening, reversibility,
centrifuge/rack insertion, robot policy, task, benchmark, or measured material
parameters. The separate body and cap packages remain available for future
thread-interaction work.
