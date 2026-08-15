# 0812-style GPU-PBD containers and Task 02 transfer

Date: 2026-08-15

## Outcome

The LabUtopia `inputs/usd/scene/liquid_0812/test.usd` behavior was reduced to a
source-bound, repeatable container recipe and applied to the 325 ml beaker and
250 ml graduated cylinder. Both static containers and their composed Task 02
cylinder-to-beaker transfer have promoted packages with hash-locked evidence.

This work did not modify the source visual assets. Container collision geometry,
particle state and admission evidence live in the ConvertAsset packages.

## Container packages

Beaker:

```text
outputs/beaker_325ml_gpu_pbd_0812_promotable_closed_20260815_r15/
  final_package/beaker_325ml_gpu_pbd_static_r2/
```

All three 8-second cold runs retained 548/548 particles, with zero outside and
zero below support. Mean rendered performance was 90--91 FPS.

Graduated cylinder:

```text
outputs/graduated_cylinder_250ml_gpu_pbd_0812_promotable_20260815_r51/
  final_package/graduated_cylinder_250ml_gpu_pbd_static_r4/
```

The three 8-second cold runs retained at least 546/548 particles. Maximum outside
was 1, 2 and 1 respectively; one run observed one below-support particle, already
included in the outside count. Mean rendered performance was 87--88 FPS. The
final admission policy is the single `maximum_outside <= 10` gate; it does not
add a redundant below-support-zero requirement.

Both reports read the live PBD `points` attribute. Authored
`physxParticle:simulationPoints` is retained only as rest-state data and cannot
serve as qualification evidence.

## Geometry decision

The source cylinder is an open-edge thin shell that does not cook into a usable
GPU convex decomposition. The accepted package therefore follows the 0812
behavioral pattern with producer-owned, closed container collision geometry
rather than pretending the failed source-mesh cook was a GPU result. The visible
mesh remains the source-bound visual asset. The beaker keeps the corresponding
closed, source-bound collision treatment.

This is a topology-specific container fix, not a global rule that every asset in
the incoming ZIP needs replacement geometry. Consumer projects must not add
their own collider, scale, rest-offset, mass/inertia or warning-suppression
patches.

## Correct-direction transfer

Promoted pair:

```text
outputs/task02_cylinder_to_beaker_gpu_pbd_transfer_20260815_r6/
  final_package/task02_cylinder_to_beaker_gpu_pbd_transfer_pair_r1/
```

Package ID:
`scientific-workbench.task02-cylinder-to-beaker.gpu-pbd-transfer.r1`.

The selected `c03` trajectory uses zero lateral rim offset, a 10 mm rim gap,
-115 degree tilt and 3 second dwell. The search observation delivered 528/548
particles (96.4%). Frozen cold-run results were 518, 519 and 526 particles in the
target (94.5%, 94.7%, 96.0%), with zero spill, zero below support, 85--87 FPS and
no hard runtime errors.

The important trajectory correction was not another collider or rest-offset
change. Earlier trials left the source root at table height during lateral motion,
so it slid across the support and lost liquid before pouring. The final sequence
lifts the source by 0.2 m, performs the upright lateral move, pre-tilts to -20
degrees, then approaches and tilts over the target.

`scripts/promote_gpu_pbd_transfer_pair.py` freezes the component, exact particle
state, selected fixture profile, admission report and complete dependency tree.
Scenario Forge consumes this contract through its inbound adapter instead of
copying conversion logic.

## Claim boundary

Static packages prove only 8-second static GPU-PBD containment. The pair package
proves prescribed-kinematic transfer feasibility. None of these results proves a
robot grasp or trajectory, policy success, liquid-volume metric correctness,
full-scene eBench performance, or benchmark success.
