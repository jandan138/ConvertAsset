# Traditional titration r2 90 mm stopcock handle

## Motivation

The unchanged r1 stopcock has a 40 mm collision wing and an approximately
50 mm visible span.  Lift2 reached it but produced unilateral contact: it could
push the valve open and could not retain the handle for the reverse stroke.

## Package transform

`build_traditional_titration_assets.py` now accepts
`--package-revision r2 --handle-visible-span-m 0.09`.  The transform is
source-bound to the original producer archive and changes only children of
`stopcock_handle_link`:

- the two wing lengths and offsets are doubled along local Y;
- the existing visible endpoint spheres move to Y = +/-40 mm;
- matching 5 mm endpoint collision spheres are authored;
- the final visible and collision endpoint span is 90 mm.

The rigid-body root is not scaled.  The joint path, X axis, anchors, 0–90 degree
limits, mass, inertia, damping, force limit, and controller behavior are
unchanged.  The original archive and r1 packages are not modified.

## Validation

The structural tests compare r1 and r2 joint attributes and verify the exact
child geometry.  Eight focused tests pass.  Three Isaac Sim 4.5 cold starts
also pass the one-DOF fixed-base audit, 0→90→0 state sequence, 15 mL endpoint,
overshoot path, reset, and base-stability gates.

Delivered output:

`outputs/traditional_titration_assets_r2_long_handle_20260905/`

The package remains an articulated-asset qualification.  It does not claim
Lift2 policy success, benchmark success, true chemistry, or Isaac Sim 4.1
compatibility; those belong to downstream task/runtime validation.
