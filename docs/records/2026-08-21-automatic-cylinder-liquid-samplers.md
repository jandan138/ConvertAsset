# 2026-08-21 Automatic cylindrical liquid samplers

Added `aan.multi_liquid_sample_request.v2` without changing the version 1
explicit-mesh route. ConvertAsset now detects a trustworthy axial cavity,
highest concentric inner opening, and repeated main-body wall rings; it rejects
short lip rings as capacity evidence. It authors a closed 32-segment cylinder
as package-local evidence and bakes one independent ParticleSet per container
against the existing shared ParticleSystem.

Two initial layouts are supported. `mouth_drop` uses the detected opening,
keeps the established liquid recipe, and extends the above-mouth column until
its discrete lattice reaches the requested volume. `inside_fill` reproduces
the proven narrow-tube practice: a radially inset column is suspended in the
upper cavity and settles after simulation begins. The dense small-particle
recipe retains its empirically established settling correction; no PhysX
particle parameter is changed.

Isaac Sim 4.1 quick evidence on the source-bound golden collision package:

- reagent bottle, `mouth_drop`, target 40%: 1,939 particles, 100% retention,
  zero below-floor particles, settled ratio 42.25%, pass;
- 15 mL centrifuge tube, `inside_fill`, target 40%: 1,430 particles, 100%
  retention, zero below-floor particles, settled ratio 43.62%, pass.

During validation, the evidence fixture was corrected to copy the source
`metersPerUnit` and `upAxis`; otherwise a Z-up scene could be measured as a
default Y-up centimetre stage. Claims remain limited to loaded-start liquid
validation, not robot, pour, metric, or benchmark success.
