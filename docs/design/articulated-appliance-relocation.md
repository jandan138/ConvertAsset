# Articulated Appliance Relocation

## Scope

`normalize-articulated` turns a pinned appliance-style USD into an unpromoted
identity-root candidate. Version 1 intentionally supports one declared chassis,
multiple dynamic links, USD physics joints, optional inline ScriptNode control,
and a jointed-rigid-graph topology. It is not a general URDF importer and does
not infer an ambiguous chassis, rewrite arbitrary Python, or waive runtime
qualification.

The producer source remains byte-for-byte unchanged in `package/deps/`. The
candidate may author only the profile-declared relocation changes:

1. apply a kinematic rigid-body mount role to the chassis;
2. replace body1-only world anchors with `body0 = chassis`;
3. convert each world joint frame into the chassis local frame;
4. apply hash-bound controller hooks; and
5. preserve an identity asset entry and local support frame.

## Why joint rebinding is necessary

A body1-only joint is anchored in world coordinates. Wrapping or translating
the appliance entry does not move that anchor, so doors and controls either
snap back or build at the wrong location. Rebinding the joint to a kinematic
chassis makes the anchor travel with the appliance. The normalizer computes

`joint_frame_body0 = joint_frame_world * inverse(chassis_world)`

rather than copying numbers. This matters when the source chassis already has
a non-identity local transform.

## Controller hooks

Controller relocation is fail-closed. A hook declares the controller prim,
old root, node suffix, strategy, and exact source-script SHA-256. The current
`contextvar_node_path_v1` strategy derives the instance root from
`db.node.get_prim_path()` and stores it in per-execution context. If the source
script hash or expected markers differ, normalization stops instead of applying
a guessed rewrite.

## Promotion tiers

Candidate creation never implies qualification. Promotion is resolved by
`resolve_promotion`:

- `relocatable_full`: every portability gate and every declared full-function
  gate passes;
- `relocatable_task_scoped`: every portability gate passes, while only the
  named task subset is claimed;
- blocked: any portability gate fails, even if a task function happens to pass.

This prevents a task-scoped claim from becoming a waiver for rename, parent
mount, local translation, reset, or controller-path defects.

## Fixed-base v2 final packages

The kinematic-chassis output above is a legacy candidate representation, not the
final shape for a newly generated VR or eBench articulated-object package. A new
final package must add a producer-owned fixed-base promotion step and satisfy:

- the public `obj_*` entry is an enabled articulation root and remains the only
  placement, uniform-scale, and randomization owner;
- the complete device subtree is below an identity `Xform` named `Instance`;
- every rigid link below `Instance` is non-kinematic;
- `Instance/Joints/BaseFixed` connects body0 at the public object root to body1
  at `Instance/Body`;
- every other internal joint body target stays below `Instance`;
- existing link, joint, control, collider, and runtime-graph paths are preserved
  when promoting a legacy asset.

`move_asset_contents_under_instance` and `author_fixed_base_articulation` own
this authoring in ConvertAsset. The corresponding fixed-base audit must pass
before runtime qualification. Scenario Forge and VR consumers may enumerate
the resulting rigid links, but they do not repair this structure.

Isaac Sim 4.1 is the formal qualification runtime. Qualification must cover the
canonical root, an arbitrary parent prefix, and `/World/_scene`; it must prove
articulation initialization, DOF discovery, fixed-base rest stability, and the
task-scoped controls being claimed. A later-runtime compatibility probe does not
replace the 4.1 evidence.

## Unsupported v1 cases

Multiple chassis candidates, closed-loop/cyclic joint graphs, cross-entry joint
targets, negative-scale entry transforms, non-identity entries, and controller
scripts without a declared hook remain blocked. A future profile version may
add explicit strategies; consumers must not patch these cases downstream.
