# IKA OVEN 125 Task 09/12 fixed-benchtop admission

## Outcome

ConvertAsset promoted a source-bound direct-stage package for the incoming IKA
OVEN 125 interactive v3 asset:

`outputs/ika_oven_125_task0912_fixed_benchtop_r1_20260831/package/`

The original archive and primary USD remain byte-identical.  Their SHA-256
values are respectively
`c3549ad1ed967e79b5ec3612e04da1acb70479d6528a8a0b144ad93acf379de1`
and
`8bbd61f9d987a38fc582d218d01c33dd23cfe006ebaa4a1776b18b6b6d63e310`.

## Why the package is scoped

The source has 16 joints but only one explicit `physics:body0`; the other 15
are world-anchored.  Its inline ScriptNode also fixed its root to
`/World/Oven125`.

Generic empty/kinematic chassis, static-body binding, translated parent, nested
reference, flattened renamed fixture, full PhysicsScene and redundant-identity
removal routes were tested.  They either locked the DriveAPI controls or left
them at zero motion in Isaac 4.1.  The byte-identical source itself passed the
same 4.1 producer smoke, so the failure was correctly attributed to relocation,
not to the original device implementation.

## Promoted construction

The final package keeps `/World/Oven125` as a direct-stage entry and bakes the
standard `0.755 m` benchtop height into a package clone:

- 16 rigid-body roots shifted by `+0.755 m`;
- 6197 static geometry/collision/light leaves shifted by `+0.755 m`;
- 15 world joint anchors shifted by `+0.755 m`;
- no parent transform on the oven root;
- the original archive and extracted source retained as provenance.

The ScriptNode replaces its hard-coded root constant with instance discovery
through `db.node.get_prim_path()` and a context-local path proxy.

## Isaac Sim 4.1 evidence

The producer 12-branch physical-input smoke passed in the promoted direct-stage
entry.  It covers the rocker, boot/Home/shutdown, knob rotation and press, all
ten buttons, all nine pages, Fan/Vent/Timer, heater hysteresis, timer completion
and dynamic UI.  Example motions were about `8.41 deg` rocker, `54.00 deg` knob
rotation and `1.614 mm` knob press.

Aggregate report:

`outputs/ika_oven_125_task0912_fixed_benchtop_r1_20260831/qualification/full_report.json`

## Consumer contract

- consumer mode: `direct_stage_only`;
- required prim: `/World/Oven125`;
- entry has no parent xform stack;
- oven randomization and VR `_scene` mounting are forbidden;
- Task 09 + Task 12 and full fixed-mount controller parity are admitted;
- arbitrary translation, robot policy, thermal calibration, safety and
  benchmark success are not claimed.

Scenario Forge may add the table and task vessels to the same `/World`, but it
must not rename, reference-wrap, transform, randomize or patch the oven.
