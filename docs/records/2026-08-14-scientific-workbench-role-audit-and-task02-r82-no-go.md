# Scientific Workbench Role Audit and Task 02 r8.2 Measured No-Go

Date: 2026-08-14

## Scope

The reviewed archive is
`external_artifacts/incoming/实验室资产库.zip`, SHA-256
`ab0e286972551f728f73d62054c5b46c00e9056c99e1d402eccb6819cad5f955`.
The audit covers its 29 single assets and excludes the six combination scenes.
The archive and extracted producer sources were not modified.

The batch inventory is generated at:

```text
outputs/scientific_workbench_asset_role_admission_20260814/
  role_topology_audit.json
```

It classifies 13 Phase-1 assets as 12 `liquid_container` plus one
`liquid_conduit`, and 16 Phase-2 assets as `rigid_tool`,
`receptacle_support`, or `instrument_static`.

Source-bound identity-facade candidate batches are available at
`phase1_candidates_v1/` and `phase2_candidates_v3/` under the same output
root. The Phase-2 batch passed three cold five-update load/render baselines.
Its manifest remains `candidate_role_gates_pending`: dynamic reset, stable
support, gripper collision, support/insertion, and instrument reset gates have
not been replaced by that baseline and no Phase-2 asset is promoted.

## Topology result

The primary interaction meshes of both graduated cylinders are the only
Phase-1 meshes matching the conservative repair rule:

- 100 mL graduated cylinder: two coplanar, concentric rim loops;
- 250 mL graduated cylinder: two coplanar, concentric rim loops.

Both have 192 boundary edges before repair. The strict repair adds 96 annular
wall-rim faces, does not add or move points, preserves every source face as a
prefix, leaves the central aperture open, and produces a closed manifold. The
other ten liquid-container primary meshes and the funnel primary mesh are
already closed manifolds. Decorative labels are inventoried separately and do
not determine the primary collision status.

This confirms only the source-topology statement. It does **not** justify the
stronger statement that only graduated cylinders can fail GPU collision
cooking.

## Task 02 r8.2 experiment

The 250 mL candidate package is:

```text
outputs/scientific_workbench_container_admission_20260814/packages/
  graduated_cylinder_250ml_closed_wall_candidate/
```

It is source-bound and uses the visible repaired mesh with
`convexDecomposition`; prior hidden collision proxies are inactive. The Task 02
candidate is:

```text
outputs/scientific_workbench_task02_fluid_component_r82_gpu_20260814/
```

The qualification entrypoint uses `PhysxSceneAPI`, an explicit
`/World/PhysicsScene` binding, the EOS-managed Isaac Sim 4.1 environment, and
the LabUtopia reference convex-decomposition resolution of 500000. These are
qualification-contract corrections, not cylinder-specific consumer patches.

Measured gates:

| Gate | Result |
|---|---:|
| Three cold starts, five updates each | pass |
| GPU-compatible collision cooking | blocked |
| Minimum 8 s source retention | 58/548 = 10.58% |
| Final target reception | 0/548 = 0% |
| Tabletop spill | 548/548 = 100% |
| 960x540 RTX performance | 77.81 mean FPS |

The decisive Isaac 4.1 error is `Non-GPU-compatible convex mesh is not able to
collide with particle system`. Closing the two rim loops removes the earlier
stage-update stall, but it does not make this hollow visual mesh a valid GPU
particle collider. Performance passes while the physics gates fail.

The final report is
`evidence/qualification_report.json` inside the Task 02 candidate. Promotion is
forbidden. No Scenario Forge r8.2 task package is generated from this result.

## Contract changes

- `aan.interactive_fluid_scene_profile.v3` represents a visible,
  closed-wall-mesh `convexDecomposition` candidate and requires package-local
  topology evidence.
- `container_topology.py` owns simulator-neutral edge auditing and the strict
  dual-loop annular repair.
- runtime admission persists observations before Isaac 4.1 teardown and binds
  to the authored GPU physics scene.

## Claim boundary

The role inventory is not runtime admission. The repaired cylinder package is
not promoted. The failed Task 02 candidate proves neither robot grasp nor
policy, benchmark, or complete pouring success. Any next attempt requires a new
collision representation design; consumers must not add a local cylinder
collider or suppress the PhysX error.
