# 2026-08-31 Articulated Relocation and IKA OVEN 125

## Investigation

The incoming OVEN 125 contains 16 joints. Fifteen used body1-only world anchors;
only the knob rotation already had both bodies. Its ScriptNode controller also
hardcoded `/World/Oven125`. The earlier fixed-benchtop package solved Task 09/12
by baking +0.755 m into 16 rigid roots, 6,197 static leaves, and world anchors.
That package worked only as a direct stage and could not be renamed, parented,
or mounted under VR `_scene`.

A rejected diagnostic candidate rebound the 15 joints to `Body`. Re-running the
producer force smoke showed the physical topology was viable: the right door
travelled approximately 0° to 180° and back, all ten buttons travelled and
returned, the mains rocker toggled and returned, the knob press/rotation stayed
decoupled, and both shelves supported their load/removal probes. The old report
called the run failed because it expected `body0=[]` and a non-rigid static
Body, not because the mechanisms failed to move.

## Implementation

- Added profile/schema validation in
  `articulated_relocation_profile.py`.
- Added the generic `normalize-articulated` candidate builder.
- Added world-to-chassis joint-frame conversion and a hash-bound
  `contextvar_node_path_v1` ScriptNode hook.
- Added strict full/task-scoped promotion policy.
- Added the pinned OVEN 125 profile, archive adapter, and three-namespace Isaac
  4.1 qualifier.

The source USD SHA-256 remains
`8bbd61f9d987a38fc582d218d01c33dd23cfe006ebaa4a1776b18b6b6d63e310`.

## Runtime result

Package:

`outputs/ika_oven_125_identity_root_r1_20260831/`

All portability checks passed at `/World/Oven125`, `/World/obj_oven`, and
`/World/_scene/obj_oven`, including translated/yawed mounts. The right-door,
button, and mains-rocker Task 09/12 subset passed at all three roots without
ScriptNode path errors.

The package is promoted as `relocatable_task_scoped`, not
`relocatable_full`. Full promotion remains withheld because the producer's
left-hinge variant and world-axis AABB/shelf probes did not pass the relocated,
yawed runs. The latter probes encode source-world direction assumptions and
need a relocation-invariant full-function qualifier before a broader claim.

## Verification

- focused tests: 7 passed;
- focused Ruff: passed;
- Isaac Sim 4.1: three namespace runs completed with subprocess return code 0;
- original source and controller hashes stayed pinned;
- robot-policy, benchmark, thermal calibration, and electrical safety remain
  explicitly unclaimed.
