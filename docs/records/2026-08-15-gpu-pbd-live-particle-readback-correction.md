# GPU-PBD Live Particle Readback Correction

Date: 2026-08-15

## Outcome

The graduated-cylinder and 325 mL beaker source-derived collision candidates
are **not qualified GPU-PBD static containers**. Their earlier promotion
reports read `physxParticle:simulationPoints`, which Isaac Sim 4.1 keeps as the
authored rest-state buffer. Live PBD positions are written to `points` when
particle USD readback is enabled. The old reports therefore measured the input
cloud instead of the simulated cloud.

The qualifier now reads `points` first and records
`particle_readback_attribute: points`. The promotion gate rejects any report
that does not explicitly bind that live attribute. The historical promoted
directories remain byte-preserved for provenance but must not be consumed.

## Corrected three-cold evidence

Graduated cylinder report:

`outputs/graduated_cylinder_250ml_gpu_pbd_remesh_20260814_v3/static_admission_live_points_r3/report.json`

Final inside counts were 45, 43, and 44 of 548. Minimum retention ratios were
approximately 8.21%, 7.85%, and 8.03%.

Beaker report:

`outputs/beaker_325ml_gpu_pbd_20260815/static_admission_live_points_r3/report.json`

Final inside counts were 167, 170, and 170 of 548. Minimum retention ratios
were approximately 30.47%, 31.02%, and 31.02%.

Both assets remained above the qualification support and ran at more than 40
FPS without a GPU-cooking hard error. The failure is therefore continuous
container containment, not GPU activation, renderer performance, or support
plane collision.

The bounded transfer report is:

`outputs/task02_cylinder_to_beaker_gpu_pbd_transfer_20260815/admission_r1/report.json`

It is blocked. No prescribed-transfer package, robot claim, Task 02 r8.3
package, or benchmark claim is promoted from this work.

## Repair boundary

Do not tune liquid `restOffset`, suppress warnings, add hidden primitive walls,
or patch Scenario Forge. A future repair must change the source-derived
container collision geometry so that the *live* `points` cloud passes three
cold static runs before transfer search resumes. The LabUtopia 0812 particle
parameters remain unchanged for this correction.
