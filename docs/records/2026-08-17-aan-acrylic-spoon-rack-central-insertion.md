# Acrylic spoon rack: central insertion package and evidence

Date: 2026-08-17

## Outcome

The transparent acrylic spoon rack is available as the source-bound
`package_v4` package under:

`outputs/scientific_workbench_acrylic_spoon_rack_r1_20260817/package_v4`

Its entry prim is `/World/AcrylicSpoonRack` with an identity root transform. The
fixture is a kinematic rigid body with provisional mass/inertia metadata and a
compound Cube collision proxy. The proxy preserves all seven upper apertures and
provides named frames for the central (`04`) socket.

`stable_support` is `not_applicable`, not waived: this package is a kinematic
fixture, so a dynamic-object settling gate would test the wrong role. Central rod
insertion is qualified separately.

## Insertion evidence

The 120 Hz central insertion protocol passed all gates in
`insertion_qualification_v6.json`: source integrity, composition identity,
side clearance, dynamic insertion, and bottom contact.

An additional 60 Hz, 960-step observation is recorded in
`insertion_qualification_60hz_960_v7.json`. The rod remained inside the central
upper aperture and on the solid lower shelf, with 8.709 degrees axis tilt and
941 side-contact samples. It moved off the deliberately small central bottom
probe, so the narrow `bottom_contact` detector reports blocked at the end. This is
a bounded long-horizon observation, not a reason to enlarge the collider or add
a consumer-side patch.

The generic insertion qualifier now accepts `minimum_observation_steps`, allowing
long observations without changing the default protocol.

## Implementation and testing

- Added `scripts/build_acrylic_spoon_rack_r1.py` and its source-binding/collider
  regression test.
- Extended `scripts/qualify_tube_rack_insertion.py` with the bounded
  `minimum_observation_steps` option and an invalid-window regression test.
- `python -m pytest -q`: 920 passed, 4 skipped.
- Focused builder/qualifier suite after the final regression test: 18 passed.
- Focused Ruff checks for the changed scripts/tests passed. A repository-wide
  Ruff invocation still reports 72 legacy findings in unrelated historical
  scripts; those files were not changed as part of this delivery.

## Ownership and claim boundary

ConvertAsset owns the source-bound facade, collider proxy, named frames, and
qualification reports. Consumers must not add rack-specific collision, scale,
mass/inertia, or warning-suppression logic. The evidence covers fixture geometry
and the recorded insertion protocols; it does not prove robot grasping, stirring,
return policy success, or benchmark completion.
