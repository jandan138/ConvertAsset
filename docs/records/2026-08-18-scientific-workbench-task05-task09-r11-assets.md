# Scientific Workbench Task 05 / Task 09 r11 assets

## Outcome

ConvertAsset now provides source-bound inputs for two Scenario Forge tasks:

- Task 05 uses a 250 mL flat-bottom flask with a 29/42 ground-glass joint.
- Task 09 uses the analog gravity-convection oven from the incoming drying-box
  collection.

The producer sources were not edited.  All normalization is expressed by
package-owned facades, profiles, and evidence.

## Flat-bottom flask

The flask facade has an identity entry prim at
`/World/FlatBottomFlask2942`.  Its interaction profile records the measured
neck and joint dimensions, the stopper seat, an open compound collision
intent, and named grasp/closure frames.  The final package is:

`outputs/scientific_workbench_task05_task09_assets_r11_20260817/packages/flat_bottom_flask_250ml_29_42_r11/`

Its AAN manifest has `overall_status: pass` and no blocked reason.  The final
Isaac Sim 4.1 interaction qualification also passes cooked aperture, stable
support, root-motion parity, and bilateral gripper-proxy collision.  This
qualification covers source binding, package closure, load/render/step/reset,
and the declared provisional-geometry interaction profile.  It does not claim
a real robot grasp, robot-policy success, or a real-world calibrated stopper
fit.

## Analog oven facade

The source declares centimeter metadata while its authored geometry is
meter-like and Y-up.  The facade therefore keeps the public entry prim
`/World/AnalogGravityConvectionOven` at identity, references the source beneath
`Source`, and applies the producer-owned Y-up to Z-up mounting transform there.
The source articulation root is moved to the public entry and the fixed joint
is rebound to that entry.  The package source USD is unchanged.

The source reuses generic joint names.  Consumer code must use the qualified
joint paths and DOF indices recorded by the device profile, not bare joint
names.  The facade authors deterministic child order so AAN static inspection
and the Isaac 4.1 tensor articulation agree.

Task joints are:

- main door (`group_4`);
- power rocker (`group_5`), reset/off at -10.31324 degrees;
- upper temperature dial (`group_11`).

The chimney damper, latch, lower dial, four shelves, and indicator needle are
non-task controls.  They use a microscopic `[-1e-6, +1e-6]` legal range and a
zero reset state.  This represents an effectively locked joint while keeping
the articulation promotion schema's strict `lower < upper` invariant.  The
upper dial is gravity-disabled in the producer facade so its commanded state
does not drift during warmup.

The final promoted package is:

`outputs/scientific_workbench_task05_task09_assets_r11_20260817/packages/analog_gravity_convection_oven_r11_release3/`

The package binds its final manifest, device profile, runtime report, and
promotion receipt.  Isaac Sim 4.1 evidence passes:

- door state cycle;
- temperature-dial state cycle;
- power-rocker state cycle;
- locked-joint stability;
- sample-shelf support;
- fixed-base benchtop stability.

The benchtop run observed zero root drift, zero support gap/penetration, zero
scoped PhysX errors, and no consumer-side physics mutation.  Qualified visual
extents are 0.875 x 0.770 x 0.9332 m.  Scenario layout should distinguish the
smaller support footprint from the full visual and door-sweep envelopes.

The recorded 90-degree root rotation and 0.4666 m root offset describe the
package's already-authored, qualified mount.  A consumer that references this
package must place the wrapper at the desired support-plane position with an
identity local orientation; it must not apply that root mount a second time.
Doing so would rotate and lift the oven twice.

## Claim boundary

The oven evidence proves only the recorded fixed-base mount and commanded
articulated state/readback protocols in Isaac Sim 4.1.  It does not prove robot
contact execution, policy success, benchmark success, thermal behavior, or
real-world physical calibration.  Downstream consumers must not add oven-
specific colliders, scale changes, mass/inertia patches, or warning suppression.

## Verification

Focused unit tests cover facade structure, profiles, source hashes, joint-path
resolution, gate aggregation, and claim boundaries.  The final package was
normalized with the EOS-managed Isaac Sim 4.1 Python runtime, qualified by the
task-interaction and benchtop-stability workers, and promoted by
`finalize_articulated_package.py`.
