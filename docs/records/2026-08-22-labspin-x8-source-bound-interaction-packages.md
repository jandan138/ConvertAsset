# 2026-08-22 LABSPIN X8 Source-bound Interaction Packages

## Context

The intake `离心机.zip` contains exported OBJ/GLB/URDF/USD assets rather than
generator source.  The visual model contains 24 rotor sleeves, a lid, rotor,
encoder and two buttons, but its shipped USD has no effective CollisionAPI and
its rigid links retain Blender presentation time samples.

## Decision / Change

`build_labspin_x8_assets.py` preserves consumed archive members byte-for-byte,
creates a derived animation-free visual facade, and authors an identity-root
articulation package.  The rotor uses 24 open eight-panel sleeve colliders plus
physical floors, never the monolithic high-poly visual mesh.  A native snap-lip
closed tube package and a source-bound compatibility facade for the existing r7
15 mL closed tube are emitted.  The latter inherits geometry, collider sizes,
mass and inertia unchanged and only adds small-clearance contact offsets and a
low-friction insertion material.

## Validation

- `python -m pytest -q tests/test_labspin_x8_assets.py tests/test_record_labspin_x8_operation_videos.py`: pass.
- Isaac Sim 4.1 native-tube free drop: pass, bottom error `1.984 mm`.
- Isaac Sim 4.1 existing-r7-15mL free drop: pass, bottom error `3.249 mm`.
- Open-lid visual low-speed rotor demo: pass at target `5 rad/s`; the balanced
  pair remained retained.

Videos and hash-bound evidence are under
`outputs/labspin_x8_centrifuge_r1_20260822/evidence/`.

## Known limitations

The spin clip is an open-lid visibility demonstration and makes no safety
interlock or rated-speed claim.  The native cap is snap-lip, not threaded.  The
package does not establish Lift2 policy success, canonical Task 10 success or a
benchmark result.

