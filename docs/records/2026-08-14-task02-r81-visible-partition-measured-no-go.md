# Task 02 r8.1 visible-partition collision measured no-go

Date: 2026-08-14

## Outcome

Task 02 r8.1 is **not promoted**. The requested route—copying the graduated
cylinder's render-visible hollow-body mesh into 12, 24, or 48 angular
partitions and applying `convexDecomposition` to every visible partition—does
not pass the Isaac Sim 4.1 stage-update admission gate. The existing Task 02 r8
blocked package remains the current Scenario Forge state; no r8.1 package was
handed downstream.

This is a measured no-go for the specified partition design, not a claim that
all visual-mesh convex decomposition is impossible. The LabUtopia
`liquid_0812/test.usd` reference uses one substantially denser beaker mesh per
container. The Task 02 graduated-cylinder source mesh is a thin open shell
(384 points, 288 quads, 192 boundary edges). Splitting that shell produces many
open thin sectors, a materially different cooking problem.

## Contract and implementation

The producer-side work introduced:

- `aan.interactive_fluid_scene_profile.v2`, retaining v1 compatibility while
  requiring the exact candidate set `[12, 24, 48]`, visible collision meshes,
  three cold runs, strict retention/transfer/spill gates, and the fixed oracle;
- `scripts/build_task02_r81_fluid_component.py`, which copies every source face,
  normal, orientation, and material binding into exactly one visible sector;
- a package-local `diagnostic_no_partitions.usda` negative control;
- `scripts/probe_task02_r81_stage_update.py` and
  `scripts/run_task02_r81_stage_update_sweep.py`, which start the EOS-managed
  Isaac 4.1 runtime in a fresh HOME/XDG tree for every run and record each of
  five RTX updates separately;
- `scripts/qualify_task02_r81_fluid_component.py`, the later static/oracle/FPS
  qualifier. It was not allowed to manufacture downstream results after the
  earlier stage-update gate failed.

The candidate builder does not add hidden collision geometry and does not
modify the source-bound vessel packages. It disables their earlier compound
proxies only inside the candidate component. Scenario Forge and GenManip were
not modified.

## Runtime evidence

Runtime: EOS-managed Isaac Sim 4.1 GenManip environment, NVIDIA RTX 4090,
independent HOME/TMP/XDG directories per cold launch, 45 s probe timeout plus a
10 s forced-termination allowance.

| Candidate | Cold runs | Updates completed before timeout | Result |
| --- | ---: | ---: | --- |
| p12 | 3 | 1, 1, 1 | blocked |
| p24 | 3 | 1, 1, 1 | blocked |
| p48 | 3 | 1, 1, 1 | blocked |
| p12 with `VisibleCollisionPartitions` inactive | 1 | 5 | negative control passed |

In each partition candidate, stage open returned in about 0.24–0.28 s and the
first update completed in about 1.17–1.29 s. The second update did not complete
before the timeout. With only the new partition root made inactive, all five
updates completed. This isolates the failure to the partitioned collision
composition at this admission boundary; it does not prove a specific internal
PhysX cooker defect because no explicit cooker/CUDA error was emitted before
termination.

Committed summary evidence:

- `docs/records/evidence/2026-08-14-task02-r81-visible-partition-no-go/summary.json`
- SHA-256: `25f8078df9cb2a0fe6ee7a09cf58786254e3787713f490d223c28cf6beeb44f5`

Full ignored evidence, including stdout/stderr and per-run observations:

- `outputs/scientific_workbench_task02_fluid_component_r81_20260814/evidence/five_update_sweep_20260814_012535/`

## Verification

```bash
PYTHONPATH=$PWD /usr/bin/python3 -m pytest -q \
  tests/test_interactive_fluid_scene_profile.py \
  tests/test_build_task02_r81_fluid_component.py \
  tests/test_qualify_task02_r81_fluid_component.py
# 15 passed

/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-isaacsim41-py310/bin/ruff \
  check convert_asset/asset_application_normalizer/interactive_fluid_scene.py \
  scripts/build_task02_r81_fluid_component.py \
  scripts/probe_task02_r81_stage_update.py \
  scripts/qualify_task02_r81_fluid_component.py \
  scripts/run_task02_r81_stage_update_sweep.py \
  tests/test_interactive_fluid_scene_profile.py \
  tests/test_build_task02_r81_fluid_component.py \
  tests/test_qualify_task02_r81_fluid_component.py
# All checks passed

PYTHONPATH=$PWD /usr/bin/python3 -m pytest -q
# 835 passed, 4 skipped
```

## Claim boundary and follow-up

No static 8 s retention, oracle transfer, 960×540 FPS, robot grasp, policy, or
benchmark pass is claimed. Per the agreed promotion rule, all three candidate
failures stop the chain before Scenario Forge integration.

A future attempt should be a new design review rather than an unrecorded r8.1
parameter tweak. The most plausible direction is a producer-authored, single
render-visible watertight vessel mesh derived from the same visual source and
validated for visual equivalence before applying one convex decomposition. It
must not be introduced in Scenario Forge as a hidden or task-specific physics
patch.
