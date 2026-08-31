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

## Unsupported v1 cases

Multiple chassis candidates, closed-loop/cyclic joint graphs, cross-entry joint
targets, negative-scale entry transforms, non-identity entries, and controller
scripts without a declared hook remain blocked. A future profile version may
add explicit strategies; consumers must not patch these cases downstream.
