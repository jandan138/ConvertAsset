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

The tube15 receiver remains blocked. A source-bound facade preserved the
admitted visual/material and explored the colleague bottom-Cube method with
small-recipe-scaled offsets and a unified SDF. Best static retention was about
92.7%, below the 99% reservoir policy, and funnel-to-tube gravity feed captured
0% after the particles legally exited the funnel. No tube reservoir or pair
claim was promoted.
