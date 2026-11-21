# OVEN 125 r16 fixed-base articulation

## Investigation

The promoted r15 oven kept every existing link and joint below
`/World/obj_oven/Instance`, but the assembly root had no
`PhysicsArticulationRootAPI`. Its `Body` link was kinematic and no fixed-base
joint existed. This explained the downstream failure: manually adding an
articulation root left a kinematic body inside the articulation, while simply
disabling kinematic mode left the assembly unconstrained and allowed its links
to scatter. The admitted centrifuge uses the correct contrasting pattern: a
root articulation, a non-kinematic base link, and a fixed joint from the root
to that base.

The r15 `Instance` was a `Scope`. Its record documents that choice as a
workaround for an identity-Xform interaction problem in the former
non-articulation assembly. Downstream post-processing requires a transformable
assembly boundary, so r16 revalidates an identity `Xform` after establishing a
real articulation.

## Design and implementation

- Preserve r15 and create a new r16 package.
- Keep every existing oven prim path unchanged.
- Change only the type of `/World/obj_oven/Instance` from `Scope` to identity
  `Xform`.
- Apply `PhysicsArticulationRootAPI` and the enabled PhysX articulation
  property at `/World/obj_oven`.
- Set all 19 rigid links, including `Instance/Body`, to non-kinematic.
- Add `/World/obj_oven/Instance/Joints/BaseFixed` from the object root to
  `Instance/Body`.
- Keep all existing door, shelf, button, rocker, knob, material, collider, and
  runtime graph paths.

The reusable implementation lives in
`convert_asset/asset_application_normalizer/articulated_instance_layout.py`.
New packages default to an identity-Xform `Instance`; the historical r15
builder explicitly requests legacy `Scope` mode.

## Verification

Static tests:

```bash
python -m pytest -q \
  tests/test_articulated_instance_layout.py \
  tests/test_build_ika_oven_r15_instance_layout.py \
  tests/test_build_ika_oven_r16_fixed_articulation.py
```

Runtime qualification uses Isaac Sim 4.1 as the formal runtime and checks
canonical, arbitrary-prefix, and VR mount namespaces. Each mount initializes
through both `Articulation` and Dynamic Control, exposes 16 DOFs, and keeps the
fixed base and every link within the declared rest-drift thresholds. The
existing primary/auxiliary knob physical rotation and press-to-start paths are
exercised at uniform root scales 0.85, 1.0, and 1.15. The 60-degree door test is
articulation-safe: it drives the hinge rather than trying to assign velocity to
a non-root link. Isaac Sim 4.5 receives an initialization/rest-stability
compatibility check, not a full control qualification.

Final evidence is under
`outputs/ika_oven_125_task09_r16_fixed_articulation_20260904/qualification/`.

## Claim boundary

The package claims fixed-base articulation construction, namespace and scale
composition, rest stability, the selected task controls, and the 60-degree
door behavior. It does not claim robot-policy success, benchmark success, or a
full Isaac 4.5 control qualification. Duplicate short link and DOF names from
the two physical knobs remain a non-blocking tensor metadata warning; stable
prim paths are the control ABI and were intentionally not renamed.
