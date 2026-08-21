# GPU-PBD liquid autofill producer

## Purpose

ConvertAsset owns the simulator-aware half of automatic liquid starts: inspect an exact
container prim, recover a trustworthy open cavity from its authored geometry, author the
collision/PBD overlay, and qualify that overlay in Isaac Sim. Scenario Forge does not reproduce
this geometry or physics logic.

The first recipe is deliberately pinned to the effective Task 02 r10.3 setup:
`task02_r10_3_blue_gpu_pbd_v1`. It preserves the proven particle spacing, blue appearance,
effective 9 mm rest offset, 5 mm isosurface smoothing, and live-`points` evidence semantics.

## Fail-closed admission

The producer accepts one absolute container prim per request. It rejects missing/instance-proxy,
articulated, deforming, non-upright, ambiguous, solid-looking, or over-budget candidates. A bbox
is never treated as a cavity. Two geometry routes are admitted:

- one geometry-derived axial hollow shell whose estimated volume dominates every alternative by
  at least 2×; or
- one uniquely named semantic hollow wall, such as the admitted Task 02 `Hollow_Body`, whose
  inner and outer radii are still independently recovered from mesh points.

The two-ring wall topology used by the production quantity cylinder is supported explicitly.
Walls and rims use SDF collision. Base, bottom, connector, foot, pedestal, and spout components
use convex-hull collision. Labels, graduations, and unrelated visual meshes are not promoted into
colliders. There is no hidden closed-box fallback.

Standalone dynamic vessels may opt into
`task02_visual_mesh_convex_decomposition_v1`. This keeps the source SDF and adds
an invisible, package-owned convex-decomposition copy of the selected hollow
visual mesh using the proven Task 02 voxel/contact/rest settings. Axisymmetric
non-cylindrical vessels also receive a conservative 5 mm-binned inner-radius
curve, used both for layer-wise particle authoring and containment measurement.
An evidence-calibrated initial particle count may be supplied on this route; it
does not change the pinned particle recipe.

## Qualification

The authored seed is not evidence. Qualification reads the simulated `points` attribute after
960 steps at 120 Hz in three fresh Isaac Sim 4.1 processes. Every run must satisfy:

- exact particle count;
- at least 99% target-cavity retention;
- zero particles below the recovered floor;
- target-local q95 liquid height within ±5 percentage points of the requested fill;
- target translation drift at most 2 mm and tilt drift at most 2°;
- no selected hard CUDA/GPU-PhysX errors.

An Isaac version mismatch blocks promotion even when all physical measurements pass.

When the source is a standalone dynamic asset with no support scene, the request
may declare an evidence-only kinematic container fixture. The temporary layer is
used only by qualification and full-scene integration and is excluded from the
deliverable. The source rigid body remains dynamic in the output package.

Each observation runs in its own disposable worker. After the JSON evidence has
been flushed and `fsync`ed, the worker exits directly instead of calling
`SimulationApp.close()`. Isaac Sim 4.1 can intermittently fault while unloading
Kit plugins after valid evidence is complete. Plugin teardown is not a physics
gate; the report records this shutdown policy, and no runtime error or failed
liquid check is suppressed.

## Boundary

The result claims only a qualified GPU-PBD loaded start for the selected source scene, prim,
recipe hash, and fill. It does not claim grasp, pouring, task success, metric validity, or benchmark
success. Source USD files are never edited.
