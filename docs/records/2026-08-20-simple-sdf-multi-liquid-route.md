# 2026-08-20 Simple-SDF multi-liquid route

Implemented the colleague-derived narrow route as an owned ConvertAsset
producer rather than a Scenario Forge USD patch. The route disables old
container-scope colliders, applies SDF collision to one reviewed visual mesh,
and permits only an explicitly approved invisible bottom Cube. Initial liquid
is a separate build stage.

The multi-liquid stage bakes a deterministic closed-mesh interior lattice. Each
sampler becomes its own ParticleSet and unique particle group; all sets share a
single ParticleSystem. Small containers select the scene-wide 1 mm-spacing
recipe with a 0.2 m/s maximum particle velocity and bounded per-set/total
particle counts.

## Real golden evidence

The Scenario Forge golden output contains a reagent bottle and a 15 mL tube.
All three eight-second Isaac Sim 4.1 cold runs retained 50,000/50,000 bottle
particles and 2,640/2,640 tube particles, with zero below-floor particles and
no hard errors. This supports `qualified_gpu_pbd_loaded_start`.

During integration, the regression exposed and fixed three composition issues:
the new root layer had to author source stage units, exact PhysX SDF schemas had
to match the working colleague scene, and consuming a collision package had to
preserve its stronger collision overlay rather than rebuild a reduced closure.

Claim boundary: source-bound collision authoring and validated initial liquid
only. Robot interaction, pouring, metrics, and benchmark success remain out of
scope.
