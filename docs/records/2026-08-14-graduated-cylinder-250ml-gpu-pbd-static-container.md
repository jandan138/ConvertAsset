# Graduated Cylinder 250 mL GPU-PBD Static Container

Date: 2026-08-14

## Outcome

ConvertAsset produced a source-bound `gpu_pbd_static_container` package for the
250 mL graduated cylinder:

`outputs/graduated_cylinder_250ml_gpu_pbd_remesh_20260814_v3/final_package/graduated_cylinder_250ml_gpu_pbd_static_r2_visual_bound`

The package uses 31 source-derived wall wedges plus one source-derived bottom
piece. Each piece is a closed triangle mesh cooked with
`convexDecomposition`. The maximum sampled inner-surface deviation is
0.0985 mm. This is not a primitive cup, hidden box cage, or consumer-authored
collider patch.

## Root cause and repair

The original thin, open-boundary visual mesh could not be cooked as one useful
GPU-compatible concave vessel. A source-derived convex partition removed that
cooking blocker, but a regular 5.82 mm particle lattice still ejected most of
the 548 particles. One- and ten-particle probes stayed in the vessel, proving
that the collider was active. Temporarily disabling particle self-collision
retained 96.7%, isolating the remaining failure to the initial particle state.

Isaac 4.1 resolves the LabUtopia `liquid_0812/test.usd` reference as
`fluid=true`, `selfCollision=true`, and particle group 0. The final fixture
keeps those semantics. Its initial state is a volume-preserving radial fit of
the reference's settled particle cloud into the narrower cylinder: radial
compression is compensated by vertical expansion. No beaker mesh is copied or
warped.

## Runtime evidence

The bound qualification report is
`evidence/gpu_pbd_static_qualification_report.json` inside the promoted
package. Three independent Isaac Sim 4.1 cold runs each observed:

- 548 particles and 100% minimum eight-second retention;
- zero particles below the support plane;
- `fluid=true` and `selfCollision=true`;
- no GPU mesh-cooking or CUDA hard error;
- 960 x 540 RTX throughput of 90.56, 91.62, and 88.74 FPS.

The package also contains the exact fixture profile, normalized initial
particle state, promotion receipt, and three 960 x 540 runtime-smoke views
rendered from the final promoted package. The final-package runtime-smoke
report passed; the views were also reviewed for framing, geometry, and material
visibility before being bound into r2. The earlier r1 remains immutable and is
superseded for handoff by r2.

## Claim boundary

The admitted claim is only `gpu_pbd_static_container` with the bound initial
particle state. It is not evidence of pouring, grasping, robot-policy success,
benchmark success, arbitrary liquid initial states, or calibrated real fluid
parameters. Downstream consumers must not add cylinder-specific collider,
scale, rest-offset, mass/inertia, or warning-suppression fixes.
