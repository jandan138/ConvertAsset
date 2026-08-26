# Small-particle recipe selection and funnel conduit qualification

`fluid-interaction-qualify` now accepts `--liquid-recipe`. The selected recipe
is copied into the package and its ID/SHA are propagated through the fluid
profile, runtime fixture, cold observations and aggregate report. Particle
seeding, ParticleSystem authoring and conduit outlet tolerance consume the same
payload instead of independently falling back to the Task 02 recipe.

The exact colleague recipe is preserved as `colleague_small_gpu_pbd_v1`. One
Isaac 4.1 diagnostic loaded and stepped 9750 particles without hard errors, but
its 5 mm rest offset jammed every particle above the 7 mm throat. The controlled
`scientific_workbench_small_gpu_pbd_v2` changes only contact/rest offsets to
0.7/0.55 mm. The glass/SDF funnel then passed three fresh cold runs with legal
outlet ratio 1.0, zero structural leakage and no hard errors.

The conduit outlet judge now derives the outer outlet radius from the reviewed
inner/outer shell ratio when no partition profile exists. The previous fallback
used the inner throat radius and falsely classified two legal near-wall outlet
crossings as structural leaks.

The first tube15 receiver attempts remained blocked because constant-radius
seeding placed particles inside the round bottom and because separate Cube
colliders did not form a reliable GPU-PBD container. The final source-bound
route removes the Cube and uses one connected visual-topology collision copy.
Its bottom is thickened, its inner wall is offset inward by 1 mm, and an exact
axisymmetric retention profile drives both seeding and judging. Three Isaac 4.1
runs passed with 0.99237 static retention, 0.96004 motion retention, 0.98801
pour outflow and zero structural leaks. The final funnel-to-tube gravity fixture
measured 1.0 legal funnel outlet ratio and 0.98632 tube capture with zero
structural leaks.

The durable human-readable parameter card is
[`docs/operations/funnel-tube15-small-particle-pbd.md`](../operations/funnel-tube15-small-particle-pbd.md).
The JSON recipe remains the sole machine source of truth.
