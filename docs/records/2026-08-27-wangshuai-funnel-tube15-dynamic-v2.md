# Wangshuai funnel/tube dynamic v2

The exact-source package remains immutable. A new dynamic consumer set lives at
`outputs/wangshuai_funnel_tube15_dynamic_asset_set_20260827/`.

The builder removes the source kinematic opinion from the three instrument
entry roots and authors versioned provisional geometry-derived mass properties.
It does not change visual meshes, collision meshes, SDF/convex settings, MDL,
or the byte-identical 1,948-particle overlay.

Isaac Sim 4.1 qualification covers three isolated cold starts per instrument.
All three instruments respond to gravity, remain finite, settle, and follow a
10 cm fixed-joint carrier trajectory while the package root remains dynamic.
Three GPU-PBD cold starts separately qualify stationary funnel-to-tube flow at
at least 95% capture with particle identity preserved and no below-floor leak.

Loaded open-tube transport is intentionally not promoted. A 10 cm smooth lift
showed variable retention and at least one run below 90%, even when stretched
to 30 seconds. This rules out simple excessive-speed diagnosis. The set records
`dynamic_loaded_liquid_transport=false`; it does not tune particle or collision
parameters to hide the result.

Claim boundary: provisional mass/inertia, robot-free rigid motion, and the
recorded stationary PBD fixture only. No robot, task, benchmark, thread
engagement, loaded-liquid transport, or measured physical-parameter claim.
