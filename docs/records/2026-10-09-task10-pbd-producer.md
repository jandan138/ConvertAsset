# Task10 source-bound GPU PBD producer — 2026-10-09

The producer uses only
`/mnt/data/chenjiantong/scene_usd/task_10_titration_experiment/scene.usd` and its
local dependency tree. Its scene entries contain real GPU PBD systems and
SDK-generated isosurfaces; the original receiver solution, burette column,
meniscus and cosmetic precharge meshes are inactive. The original source is
immutable. This record is task-specific evidence, not a general liquid recipe
promotion. **No final physical qualification or final video acceptance is
claimed at the current checkpoint.**

## Source geometry and controlled-flux boundary

The receiver root is `(-0.03, -0.17674479517, 0.8267)` m. Its original visible
solution reaches local z = 0.089 m; the original inner floor is approximately
0.003684 m and mouth 0.15 m. Its sampled axial visual envelope integrates to
287.708 mL, rather than the nominal flask label capacity. The producer keeps
both the reference fill envelope and full physical cavity profile.

The burette body is at `(-0.03, -0.17674479517, 1.27)` m. Its 10 mm-ID column
ends at world z = 1.50 m; the original drop origin is z = 0.99 m. The complete
column/precharge axial envelope integrates to 31.897481 mL. A split at the
actual stopcock center z = 1.09 m separates 31.348820 mL above and 0.548661 mL
below. The small downstream taper is not claimed as resolved capillary or
microvalve flow.

The consumer explicitly authorized controlled source-to-tip transfer and
numerical closed-flux boundaries at the physical valve/outlet. The numerical
outlet cap occupies body-local z = [-0.28, -0.278]; the valve seat lies in
[-0.183, -0.18], inside the original opaque valve housing. These are invisible
collision geometry, not fake liquid surfaces. The cap displaces approximately
0.0596 mL of the original passive precharge. A small rounded valve-seat
transition inside the same housing displaces another 0.023988 mL from the upper
inventory. The visible bore and all source visual/placement geometry remain
unchanged. Exact boundaries, numerical floor, reference profiles and displaced
volumes are recorded in each manifest.

Source and passive-precharge collision shells are source-profile continuous
SDF meshes, with conservative 3 mm outward wall thickness. This approximation
is scoped to the no-robot fixture and has no grasp-clearance qualification.
The receiver collision shell is an exact copy of the original hollow mesh;
the original visible mesh's collision is disabled to avoid duplicates. The
collision copies use centered millimeter-valued mesh coordinates with a 0.001
uniform transform: world geometry is preserved while cooking uses better
scaled coordinates. Earlier convex partition candidates are retained only as
inactive diagnostic history in provisional outputs and are not active contacts.

The original baked OFF mesh is replaced by an extruded ON mesh in its original
text plane and material. The plane is recovered by PCA of the original mesh.
The consumer has rendered and confirmed the ON label. No physical stirring was
added; the original stir-bar visual remains unchanged.

## Producer interface and accounting

All fluid prims are under the default prim `/World`, so referencing that prim
does not silently omit fluids:

| Role | System / set suffix | Current nominal volume per particle |
| --- | --- | ---: |
| Upper source | `/World/Task10Fluid/SourceSystem`, `SourceParticles` | 0.003375 mL |
| Falling reagent | `FallingSystem`, `FallingParticles` | 0.003375 mL |
| Receiver | `ReceiverSystem`, `ReceiverParticles` | 0.003375 mL |
| Passive precharge | `DeadPrechargeSystem`, `DeadPrechargeParticles` | 0.000008 mL |

The main nominal spacing is 1.5 mm; passive precharge was refined from 0.4 mm
to 0.2 mm. Current inventories are receiver 85,247 particles (287.708625 mL),
upper source 9,281 (31.323375 mL), passive precharge 61,130 (0.489040 mL), and
falling zero. The source has more than 25 mL usable inventory. These are
explicit discretized volume/mass contracts; no quantitative CFD calibration is
claimed. At the assumed 1000 kg/m³ density, `physics:mass` is **total set mass**,
not per-particle mass. The consumer must update it whenever a set count changes.

`manifest.json` provides each set's body path, complete local cavity profile,
physical/numerical flux boundaries, reference free-surface height, sampling and
mass quantum, collision parameters and proposed acceptance tolerances. Initial
arrays are in `initial_particles.npz` and in USD. Clean entries explicitly author
`metersPerUnit=1`, `upAxis=Z`, `defaultPrim=World`; their particle simulation
owners are unbound until the host creates and binds a live PhysicsScene.

The source-to-tip transfer removes actual source inventory and inserts falling
particles below the original outlet. Recommended center clearance is 3 mm,
not a fake drain through the sub-particle microvalve. After emission, gravity
and PBD advance the particles. Receiver admission, indicator color, logical
valve rate, stop/hold/reset/overdose policy and complete runtime tests belong
to the Scenario Forge consumer. Passive precharge is not drawn by that ledger.

Each fluid system binds its own render material and the shared WaterPhysics
material. Render
materials reference the original clear OmniGlass water, including IOR 1.333
and color `(0.97, 0.99, 1)`. Source burette and receiver MDL files have identical
SHA256 bytes and these same inputs. Separate material instances prevent the
receiver's color change from tinting the source. Existing AAN recursive MDL
closure helpers provide both runtime helper trees, preserving root MDL bytes.
No PreviewSurface conversion was used.

## Runtime findings and rejected candidates

The earlier small-v2/simple-SDF recipes were reviewed, but their prior evidence
is specific to their 4.1 assets/materials and is not inherited here. All tests
below use independent task-specific configurations and recorded runtime bounds.

- Long slender convex wall cells failed GPU cooking. Shorter overlapping cells
  cooked, but fluid containment was inadequate. Continuous SDF shells provided
  substantially better source/receiver/passive containment.
- Early probes incorrectly read an authored `simulationPoints` array. SDK
  schema marks it read-only. The producer no longer authors it, disables particle
  smoothing, and reads live `Points.points` after explicit transform readback.
- The SDK isosurface filter sequence is a **string** (e.g. `GSRS`), not an
  integer. Mesh smoothing uses `numMeshSmoothingPasses`. Grid smoothing radius
  is dimensionless. These properties were corrected against installed schemas.
- Source/dead fine-resolution pressure experiments and genuine wall escapes
  were rejected and retained in diagnostic reports. No escaped particle was
  moved back or deleted to obtain a pass.
- Radial cavity error and actual outlet escape are reported separately. The
  proposed coarse/fine tolerances are 150/50 µm; numerical cap floors are also
  exposed so consumers can distinguish penetration into a cap from escape past
  its outer outlet plane.
- The rounded-seat 240 Hz probe had zero final-frame cavity violations in all
  sets; this was not presented as proof of the entire trajectory. The later
  30 Hz full-array audit over 30 seconds found Source and Receiver always
  contained, but passive precharge still had up to 16 violations and late
  source/passive fill heights below target. Those states were not baked.
- A 64-iteration passive-system experiment improved its height/convergence,
  but changed the other fluids' equilibria. The solver uses the highest actor
  iteration request subject to scene limits, as documented in the
  [official physics configuration reference](https://isaac-sim.github.io/IsaacLab/v2.0.2/source/api/lab/isaaclab.sim.html).
  Subsequent candidates explicitly fix the scene iteration contract rather
  than assuming an isolated per-system change.
- Receiver static containment is not motion qualification. The consumer rejected
  a teleport/zero-velocity shaking fixture and switched to swept kinematic
  targets on a path clear of the burette. Transient dynamic contact violations
  remain a separate gate, even where final particles return inside.

The consumer diagnosed and fixed a runtime scheduling error: resizing from
`OnPhysicsStep` while reading stale USD positions repeatedly restored old
falling positions. Explicit post-physics transform readback before modification
restored continuous motion and full admission in short 4.1/4.5 interface tests.
These interface passes did not qualify the old physical assets. Empty falling
sets require disabling isosurface generation while leaving their particle
system enabled; toggling system activity caused separate buffer-lifecycle
errors. Consumer reports own the corresponding observations.

## Reproduction and validation

Owned source files are `scripts/task10_pbd_producer.py`,
`tests/test_task10_pbd_producer.py`, this record, and
`outputs/task10_pbd_20261009/`. No Scenario Forge file, original scene, other
producer script or shared configuration was modified by this agent.

```bash
python scripts/task10_pbd_producer.py \
  --source /mnt/data/chenjiantong/scene_usd/task_10_titration_experiment/scene.usd \
  --out outputs/task10_pbd_20261009/candidates/NEW_REVISION
python -m pytest -q tests/test_task10_pbd_producer.py
```

The first tests failed before implementation. Nine tests currently pass:
axial sampling/volume, open annular wall geometry, watertight closed-shell
orientation/volume, total set mass, independent system material/empty falling
semantics, finer passive quantum, rigid reframing/count preservation, and physics-signature sensitivity to collision changes while excluding measured particle motion.
Both runtime entrypoints pass static dependency resolution and connect the
original MDL surface outputs. All runtime evidence to date is explicitly scoped
by its particular candidate and probe; the frozen API snapshots are marked
unqualified with their known failures.

The producer now supports measured-state import using `--settled-state` and
`--settling-report`. Import requires matching physics-configuration and state
hashes, identical particle counts, and passing tail cavity/height gates. Every
position receives the same container rigid-frame map back to the original
source placement, and every measured velocity is rotated consistently. It does
not clamp, delete or individually relocate points, and it does not zero their
velocities. The resulting initial state still requires fresh cold-start and
complete consumer qualification in both runtimes.

Probe-only scripts, raw reports, final arrays and frozen snapshots remain in
the owned output tree. They are not episode runners or new core package layers.
There is no new general standard: all numerical caps, outward collision
thickness, material rendering, particle resolution and runtime settings are
qualified only by the eventual exact-scene evidence. Final matrix, motion,
end-point/reset/overdose behavior and video review are still pending at this
checkpoint; no final video acceptance is claimed.

## Fixed-iteration and moving-receiver checkpoint

The consumer's safe swept motion test exposed transient receiver wall crossings
that were absent from final static snapshots. The next producer candidate raises
receiver particle-to-rigid rest/contact offsets to 1.5/2.0 mm while leaving the
particle-neighbor cutoff at 1.25 mm. This is an unqualified contact candidate, not
a motion pass. Snapshot `api_smoke_05` freezes it for independent motion testing.
The snapshot also fixes every particle system and the scene minimum/maximum
position iterations to 64, so additional actors cannot silently change this
part of the fluid recipe. Source and passive-fluid failures in that snapshot
remain recorded; it is not a final handoff.

Subsequent Source/Receiver rest-density calibration runs use unique candidate
directories so no running process reads a modified asset. The producer audit
now checks the passive numerical floor at local -0.278 m and records actual
exit below -0.280 m separately. The next cold-start audit checks containment
every physics step and free-surface statistics at 30 Hz. Earlier reports
retain their original 30 Hz containment cadence and are not relabeled.

The 20-second `contained_21` probe retained all coarse particles with zero
outside samples. Receiver tail surface error was +0.185 to +0.426 mm. Source
was still 8.37–9.13 mm low, so it was not accepted. Passive fluid remained above
the actual outlet but had up to five points below its numerical floor tolerance;
the final deepest point was local -0.27807093 m, 20.93 µm beyond the 50 µm
gate. Candidate 22 adds an analytic box at exactly the existing cap bounds
[-0.280, -0.278] m, retaining the same physical boundary and displaced-volume
accounting, to distinguish SDF planar-contact error from a boundary-placement
problem. This candidate has not yet been promoted.

The exact outlet plane eliminated numerical-floor crossings. At 240 Hz,
`contained_22` passed coarse-fluid containment and all tail height ranges, but
Fine still had rare radial events (up to 109 µm). Reducing only passive-fluid
maximum velocity from 0.025 to 0.01 m/s did not solve them; candidate 23 remains
rejected. A three-second localization probe placed those points in the narrow
outlet taper, not at the valve seat or the free surface.

Candidate 24 reinforced the same inner side wall over local z [-0.278, -0.270]
using normalized short convex cells. No violations remained inside that span;
all ten remaining events occurred upstream in the uncovered taper. Candidate
25 extends those contacts to the original taper endpoint z=-0.230 m: twelve
4 mm axial cells and 32 angular cells, with at most 9 µm chord inset, the same
50 µm lumen margin, and the existing 3 mm outward collision thickness. The
cells contain no internal fluid floor and do not widen the source bore. The
original SDF remains present; this is a task-specific contact refinement, not a
generic assertion that SDF is unsuitable for liquids. Every failed report is
retained. Subsequent measured seeds preserve every particle and velocity while
reframing whole sets; seed hashes distinguish these settling observations from
fresh qualification runs.

## Frozen prebalanced handoff

`outputs/task10_pbd_20261009/snapshots/prebalanced_06/` is the immutable handoff
for consumer cold-start validation. It was built with the strict measured-state
import from `probe45_taper25.npz` and `probe45_taper25.json`; configuration,
state hash, time step, counts and tail gates all matched. All 9,281 source,
85,247 receiver and 61,130 passive particles retained their measured nonzero
velocities. Whole-set rigid transforms restored the original source container
placements. No particle was deleted, clamped, individually moved or frozen.
The snapshot includes the measurement arrays, report and complete file hashes.

The 10-second 4.5 settling observation checked every one of 2,400 physics steps
at 240 Hz and found zero outside particles for every retained fluid system.
Tail free-surface errors were Source +0.143 to +0.583 mm, Receiver +0.269 to
+0.494 mm, and passive precharge -0.170 to -0.168 mm. These are measured-state
settling results; both-version cold starts, complete titration, moving-receiver
acceptance and final video review still belong to the consumer's qualification.

| System | Fluid rest offset | Rigid rest/contact offset | Neighbor cutoff | Velocity cap |
| --- | ---: | ---: | ---: | ---: |
| Source | 0.845 mm | 1.0 / 1.5 mm | 1.5 mm | 0.2 m/s |
| Receiver | 0.847 mm | 1.5 / 2.0 mm | 1.25 mm | 0.2 m/s |
| Falling | 0.9 mm | 0.4 / 1.25 mm | 1.25 mm | 3 m/s |
| Passive precharge | 0.127 mm | 0.32 / 0.45 mm | 0.18 mm | 0.01 m/s |

All systems and scene minimum/maximum position iterations are fixed at 64.
The passive velocity cap is a numerical retained-fluid setting; its particles
remain dynamic and its under-resolved outlet has no capillary-flow claim.
Physics dt is 1/240 s. The consumer must keep the particle system enabled when
Falling becomes empty and toggle only its isosurface generation, following the
observed 4.1 empty-buffer restriction.

Frozen manifest SHA256:
`68ab6c349ab5021b7c7f01cc05acbb7a317697d17550e07e17582a4e784ddb68`.
Frozen `package/pbd.usda` SHA256:
`09d75755944e2a11a4a062d92cb18453e9ab715fb83c2b6fe8f9abc41bf68fef`.
Physics-configuration signature:
`4b71410f5b78654d49c3c0cd99465d71bb52288b08b4d401d4138069286c996b`.

```bash
python scripts/task10_pbd_producer.py \
  --source /mnt/data/chenjiantong/scene_usd/task_10_titration_experiment/scene.usd \
  --out outputs/task10_pbd_20261009/NEW_PREBALANCED_REVISION \
  --settled-state outputs/task10_pbd_20261009/probe45_taper25.npz \
  --settling-report outputs/task10_pbd_20261009/probe45_taper25.json
python -m pytest -q tests/test_task10_pbd_producer.py
```

Nine producer tests pass. Both USD runtime entrypoints resolve their complete
local dependency trees. No commit was created, no original source was modified,
and no Scenario Forge file was edited by the producer agent.
