# Task 02 r8 interactive-fluid measured no-go

Date: 2026-08-13

## Outcome

ConvertAsset now owns a simulator-neutral `interactive_fluid_scene` profile and
a source-bound Task 02 component.  The component combines the already admitted
250 mL graduated cylinder and 325 mL beaker, directly authors 548 PhysX PBD
particles, and exposes separate 30 Hz qualification and 60 Hz consumer
entrypoints.

The package is **blocked**, not admitted.  Isaac Sim 4.1 on an RTX 4090 could
not cook the graduated cylinder visual mesh's `convexDecomposition` into a
GPU-compatible convex representation.  PhysX therefore reports that it cannot
collide with the particle system.  Loosening decomposition error, hull limits,
and voxel resolution did not remove the blocker.

## Contract and evidence

- Package: `outputs/scientific_workbench_task02_fluid_component_r8_20260813`
- Profile: `interactive_fluid_scene_profile.json`
- 30 Hz entrypoint: `qualification_30hz.usda`
- 60 Hz entrypoint: `consumer_60hz.usda`
- Runtime report: `evidence/runtime_qualification/report.json`
- Manifest: `evidence/manifest.json`

The runtime report is included in the manifest hash closure.  Existing r7
container collision proxies are explicitly disabled; the r8 candidate uses the
reviewed visual meshes with `convexDecomposition`.  No invisible inner-wall
fallback was added.

## Claim boundary

The package demonstrates portable composition, deterministic particle
authoring, and a reproducible negative Isaac 4.1 observation.  It does not
demonstrate eight-second retention, visible transfer, 40+ FPS, robot grasp,
policy success, benchmark success, or a calibrated 250 mL liquid volume.
