# Task12 / Task18 source-bound waterbath 120 Hz producer

Status: candidate13 is qualified for the stated Isaac4.1 cold/vertical-motion physical scope; visual review is WARN. Work owned by ConvertAsset; robot replay, reaction eligibility and metric integration owned by GenManip consumer. The chronology below retains rejected candidates and is not a statement that those candidates became qualified.

## Sources and investigation

Read the ConvertAsset agent/feature implementation ownership instructions and Scenario Forge scene standards (ASSET-001/002, MAT-001/002/003/005, USD-002/008, VAL-002/003). Sources are the immutable chenjiantong `task_12_fehling_test/scene.usd` and `task_z4_silver_mirror_reaction/scene.usd` under `/mnt/data/chenjiantong/scene_usd`.

Both share a glass 18×150 mm sample tube, authored axial cavity profile, 8 mL visual solution and waterbath beaker. Existing tube SDF contact offset is 10 mm, comparable to its 9 mm outer radius. Existing rack is static SDF with hole-preserving geometry. Bath visual-water profile integrates to 349.094989 mL; it is inset from the actual glass cavity. Candidate03 derives the bath physical floor/walls from actual hollow-body mesh ring coordinates (3 mm floor, top at 113.49 mm), preserving the liquid source profile separately.

## Implementation

`scripts/sciben_waterbath_geometry.py` implements validated profile integration, lattice seeding, exact declared particle mass and cavity tests. `scripts/sciben_waterbath_producer.py` copies source dependencies, creates a stronger relative USD layer, dynamic PBD sample and bath surfaces, and a separate PhysicsScene probe entry. Original visual glass and task object transforms are untouched. Source visual bulk-water/sample meshes become invisible while original material paths and reaction graphs remain available. Fehling SampleSystem binds Layer0; a single dynamic phase replaces five rigid visual regions. Silver wall-coating geometry remains separate and unmodified. These are rendering differences requiring downstream image review, not claims of equivalent chemistry.

Added source-profile convex wall cells and original-floor contacts; static rack triangle collision retains holes. Tiny (<0.1 mm) source profile cells cannot cook as GPU convexes and are omitted as supplementary colliders; original glass SDF retains these rim/bevel regions. Tube/beaker contact offsets are task-specific 0.8 mm, rack 0.5 mm. These are candidates, not repository defaults.

## Evidence and failures

Output root: `outputs/sciben_waterbath_120hz_20261010`.

- Unit tests: initial red test for absent geometry module, then `python -m pytest tests/test_sciben_waterbath_producer.py -q`: 5 passed.
- Candidate02 first physical probe was **INVALID**: World defaults disabled GPU dynamics; unchanged particle positions passed the old insufficient report gate. `fehling_cold02/INVALID.json` explicitly rejects that report. Probe corrected to `set_defaults=False`, forced GPU policy, explicit native PhysX callback sampling, USD particle readback, and PhysX error gate.
- Correct GPU Candidate03 cold run **FAILED**, bath 10 outside particles at first measured step and bath 87104/sample 13631 by step 240 (1 mm cavity tolerance). Run stopped after established failure to add pose/point diagnostics; `fehling_cold03/aborted.json` preserves reason. No deletion or teleport of particles used.
- USD dependency closure on Candidate02: 2 USD layers, 14 asset dependencies, no unresolved files. Recursive MDL/runtime/render closure still needs qualification.

## Outstanding

Resolve cold containment before promotion, measure every native step including SDK warmup, verify visible liquid height, then run prescribed bounded container motion and silver counterpart. Preserve dynamic liquid and exact declared mass; do not use frozen particles or claim arbitrary anti-leak motion. Consumer must remap world-space seeds to per-object initial poses before simulation when applying metadata. Source reaction graphs still require consumer heat/metric integration. No robot, rendered appearance, or complete task success has been qualified.

Standards need no general rule change: this is a scoped application and candidate diagnosis under existing physical/visual evidence boundaries. Root maintainer will link this dated record from navigation when accepted.

### Later diagnostics

Candidate04 normalized convex floor alone still failed;05 disabled duplicate original hollow-body SDF and explicitly set scene 64 iterations, but still failed. These are retained comparisons, not evidence that SDF alone caused leakage. Candidate07 jointly introduced per-axis normalized cells (retaining all source profile knots), task-specific larger particle contact/rest offsets and 0.2 m/s maximum speed. Both sets remained contained through2.1 s, but settled surfaces were too low. Candidate08 adjusted fluid rest offsets, and its3.1 s cold run **passed containment/clock/count gates**, including all374 native callbacks and12 post/fetch comparisons; its surface height was not accepted (bath up to102.75 mm, sample transient54.05 mm). Separate fluid systems have separate materials and do not claim cross-phase mixing.

The currently authored script uses native post-step callbacks and dynamic-control body poses, explicitly updates USD particle readback, measures SDK warmup, and records PhysX errors. A bounded motion probe uses native tensor kinematic targets for the tube while the liquid remains dynamic; it is not arbitrary robot motion evidence. Candidate09 is undergoing15 s settling with bath/sample fluidRestOffset0.87/0.516 mm, keeping declared total mass and volume unchanged. Optional `--seed-from` preserves measured local particle positions and velocities in a newly built package; it does not continuously constrain particles during simulation.

### Frozen11 candidates and final gates in progress

A full Kit-log audit found96 cooking errors in09/10 despite an empty runtime PhysX error event stream. Their runtime results are containment-only diagnostics, not collision qualification. Frozen11 coalesces adjacent <0.1 mm bevel/rim intervals into contiguous cells: original tube semantic profile has139 knots, collision profile118 knots, maximum interpolated radial difference0.131653 mm. Visible glass vertices/topology remain exact. There are3745 supplementary tube cells and257 bath cells. Original hollow tube/body SDF collision is disabled; original geometric visuals, lip/spout and support paths remain. This replaces the earlier incomplete “skip tiny cells” approach.

Both `fehling_frozen11` and `silver_frozen11` copy the settled10 measured positions **and velocities**, reframed to each original container pose. Bath/sample rest offsets are0.858/0.516 mm, and system maximum speed0.2 m/s. These limit the admissible movement scope; the consumer must not infer arbitrary fast hand motion qualification. Source mass349.094989 g bath and8 g sample and particle counts96649/13905 are unchanged. Samples remain dynamic throughout execution.

Exact initial source visual mesh attributes and top-level object xforms compare equal for134 Fehling /135 silver meshes. Each final candidate has3 USD layers and19 resolved asset dependencies entirely inside the package; the existing recursive MDL helper closes5 MDL roots against Isaac4.1. Static audits are saved as `fehling_frozen11_static_audit.json` and `silver_frozen11_static_audit.json`. Frozen11 runtime cold, bounded-motion and image gates remain in progress; filenames do not imply qualification.

### Native bounded motion and consumer metadata

Frozen11/12 cold containment does not extend to120 mm withdrawal:11 failed242 sampleparticles,12 (restored original tube glass SDF) failed65. Bath remained contained. Candidate13 additionally changes only supplemental tube wall contact/rest to1.4/0.5 mm, retaining the exact original tube glass SDF and source visuals. It passed17 s prescribed120 mm vertical withdrawal/return in Fehling:2042 native120 Hz callbacks, allparticles retained inside1 mm cavity tolerance, count unchanged, no PhysX or Kit cooking errors. Silver13 repeated the protocol with explicit30 Hz `World.render()` queue draining; callbackcount remained2042 with no additionalphysics, bothsets0outside. Native tensor kinematic targets move the held tube; liquid remains dynamic. This does not prove robotgrasp, arbitraryspeed, sideways bath insertion or scenevariant correctness.

The maximum sample-particle height varied29.6–78.3 mm during bounded motion; do not interpret the qualified containment/count as physically exact hydrodynamics or constantvisualheight. Original tube placement is6.63 mm above its rack-seat floor, causing a smallfreebodysettle and startupfluidtransient; sourcepose was preserved. Consumer metadata may choose a differentinitialpose, which requires remappingseeds and revalidation.

`consumer_geometry.json` provides22 rack aperture centers, mesh-measured radii, top0.0936 m and authoredseatbottom0.0234 m inracklocalcoordinates. Actual15mL/50mL hole radii0.01023/0.019415 m differ from nominal `rack:slotDiametersMeters` by1.1; do not confuse these localmeasurements with the additional1.1 objectroot scale. Heaterplate localcenter is(0,0.012)m, top0.071 m,bottom0.065 m,radius0.073 m. Meshgeometry matches betweenFehling/silver. Rootconsumer owns contactguard,5°upright/10mmcentering/5mmsupportgap choices and originalreactiontime schedules. SingleFehlingPBDmaterial should receive volume-weighted originalfive-layercolors fromconsumer, not finish early byreadingonlyLayer0 progress.

Corrected camera nearplane0.01 m showsapparatus; old1mdefaultclippedneartargets and itsimages were rejected. Subsequent image reviews remain explicitly scoped: clearbathfree-surface is subtle under sourceglassoptics; renderappearance and reactedstates requireconsumer review. Finalfreebodycold13 gates are stillinprogress atthisrecordpoint.


## Final handoff

Current entries are `outputs/sciben_waterbath_120hz_20261010/fehling_candidate13/scene.usda` and `silver_candidate13/scene.usda`. They contain no PhysicsScene; `probe.usda` is separate. The producer does not modify the colleague directory or GenManip repository.

`qualification13.json` SHA-256: `06fba7f5d1de48dd9cad0291cf1939f4d37f0ee8e5afe82ec6f10f5d97388a0e`.

| Case | Native steps | Bath / sample outside | Result |
|---|---:|---:|---|
| Fehling cold 10 s | 1202 | 0 / 0 | PASS |
| Fehling lift/return 17 s | 2042 | 0 / 0 | PASS |
| Silver cold 10 s | 1202 | 0 / 0 | PASS |
| Silver lift/return 17 s | 2042 | 0 / 0 | PASS |

All actual callback dt values were `0.008333333767950535` seconds. Every callback including the two SDK warmup steps was checked; particle counts remained96649/13905. Each run had12 post/fetch comparisons, no PhysX callback errors and no Kit cooking errors. Probe scenes author120 Hz and scene min/max position iterations64; both particle systems author64 iterations. The three refreshed runs drain graphics at30 Hz and assert no extra physics callbacks. These physical results are bound to exact scene/manifest hashes and34-file inventories. Relocated USD and recursive MDL closure checks passed for both entries.

- Fehling scene SHA-256: `dea1be8bd1ff2416f4d05ab9676d8b890bae4f8693646b22c225983153e95092`.
- Silver scene SHA-256: `58b412c57d55baf410417db8c3ffd3331713f059bb1340bf3d0212a841445cb5`.
- Unit suite: `python -m pytest tests/test_sciben_waterbath_producer.py -q` —6 passed.
- Handoff, invocation and limits: `outputs/sciben_waterbath_120hz_20261010/HANDOFF.md`.
- Consumer local geometry: `consumer_geometry.json`; physical reports, exact validator snapshots and static audits sit beside it.

The local image review is WARN, not independent approval: blue Fehling liquid and transparent containers are visible; the clear bath free surface is subtle under source optics. Consumer reacted states, weighted five-region color, deep immersion, robot replay, per-layout reset and thermal guard remain outside this producer qualification. Existing scene standards apply without a new general rule: these collision offsets and bounded motion results are task-specific. Documentation index/navigation synchronization is handed to the root maintainer because this agent's explicit write scope contains only this dated record.

## Follow-up: articulated robot contact crash investigation

The consumer's remote `repair_task12_v3_positive_20261010T131742_697163Z` run failed with CUDA700. The first reported kernel failure was `mArtiSolveBlockPartitionFunction`; later broadphase and rendering errors were cascading symptoms. A previous particle-contact capacity overflow had already been addressed by the consumer with4194304 contacts. **Collider density was a hypothesis, not an established cause.** Candidate13's earlier qualification remains limited to its bare-scene cold and prescribed kinematic motion scope.

Added `robot_probe` to the owned producer script, using the exact Lift2 robot USD and mixed_1 metadata/LMDB actions directly, without importing GenManip. It applies the same initial pose, arm/gripper joint mapping, source hold pattern1,2,300 warmup steps, robot friction2.5 with max combine, armature0.01, max depenetration1m/s, lift drive gains, native120/render120, scene64 iterations, aggregate capacities16384 and particle-contact capacity4194304. Diagnostic fixtures add ContactReportAPI before reset and set particle-system simulationOwner explicitly. These are local fixture changes; no GenManip file or candidate13 package was changed.

| Local comparison | Scope | Result |
|---|---|---|
| `robot13_baseline_b` | Original source scene; exact Lift2 grasp/lift/hold; no tube–beaker tensor contact view | PASS through source599 |
| `robot13_composed_contacts128` | Full consumer `unseen_scene_1/scene.usda` composition; same replay; tube–beaker contact view capacity128 | PASS through source599 |

Each run completed900 replay physics steps plus300 warmup steps and2 SDK reset callbacks:1202 callbacks, all0.008333333767950535s, finite joint states, no PhysX error events and no `[Error]` lines in the complete log. The actual articulated fingers grasped, lifted and held the tube in the bath. The full-composition contact view was valid but observed **zero** tube–beaker contacts during centered suspended insertion. Therefore this does **not** qualify128-contact capacity for wall collisions, full-episode success, reaction correctness or robot-driven liquid containment.

Both logs contain repeated `getMaterialFromInternalFaceIndex(0xffffffff)` warnings (36349 and36088 respectively), retained as warnings rather than silently discarded or relabeled clean logs. They did not produce a CUDA error in these comparisons.

Conclusion: the reported failure was not reproduced locally with unchanged candidate13 geometry. Missing ContactReportAPI/invalid contact-view setup remains a consumer hypothesis pending the root's fixed remote replay; local passes do not establish that as the unique CUDA root cause. No new producer geometry revision was promoted. A collection-based `separate_tube_contacts` helper and `--filter-tube` diagnostic option were authored/tested statically as a possible comparison tool, but **were not used in either passing run and have no runtime qualification**.

Evidence: `outputs/sciben_waterbath_120hz_20261010/robot_contact_diagnosis13.json`, the two report/progress JSONs, full logs and fixture layers. Setup failures (`robot13_baseline`, NumPy2 pickle compatibility; `robot13_composed_observability`, missing local Sdf parent spec) are preserved and excluded from runtime evidence. Reproduction uses:

```bash
# Use the same cleared SDK environment and Isaac4.1 interpreter documented above.
python scripts/sciben_waterbath_producer.py robot_probe \
  --package outputs/sciben_waterbath_120hz_20261010/fehling_candidate13 \
  --episode /mnt/data/zhuzihou/GenManip-Sim/saved/tasks/scientific_experiments/task_12_fehling_test/mixed_1/000 \
  --out <new-output> --steps 900 --contact-capacity 0
# Full composition adds these options instead of --contact-capacity0:
# --composed-scene /mnt/data/zhuzihou/GenManip-Sim/saved/assets/scene_usds/scientific_experiments/task_12_fehling_test/unseen_scene_1/scene.usda
# --contact-capacity 128
```

Final pure test suite:7 passed; Python compilation passed. Candidate13's34-file inventories and original `qualification13.json` remain unchanged. Root owns the full remote consumer qualification and any resulting integration changes. No new general scene-authoring rule is inferred from these scoped comparisons.

## Bounded actual bottom/side contact capacity comparison

Added the `wall_probe` diagnostic on unchanged candidate13. Before Play, it moves the tube and its particle seed above the beaker. Native kinematic targets then lower the upright tube to bottom contact, raise it, approach the side wall, hold contact and withdraw. The beaker and both fluids remain dynamic. All original collision geometry remains enabled; no collision filtering is applied. This is a12-second controlled fixture, not a robot action or reaction test.

Both runs used ContactReportAPI on both bodies, explicit simulation owners, native120 Hz,64 scene/particle position iterations,4194304 GPU particle contacts and the same tube–beaker rigid contact view except its data capacity.

| Contact-view capacity | Bottom-hold peak | Side-hold peak | Overall peak | SDK truncation warnings | Capacity result |
|---|---:|---:|---:|---:|---|
|128|1290|2839|2839|392|FAIL|
|8192|1290|2848|2854|0|PASS for this fixture|

Each run produced1442 native callbacks (1440 trajectory steps plus2 SDK reset steps), all0.008333333767950535s. Particle positions stayed finite and counts unchanged; beaker positions stayed finite. Neither run produced CUDA700 or a PhysX error. The dynamic beaker moved laterally by about1.8 mm under the side push.

The128 run originally reported PASS for contact existence, finite positions and native-clock gates; that original JSON is retained. Its separate `wall13_contacts128/capacity_audit.json` explicitly marks `FAIL_CONTACT_BUFFER_CAPACITY`. The probe now includes the capacity gate in its result, and the8192 run passed both the programmatic gate and complete-log audit. No historical report was overwritten to hide this distinction.

Recommendation: use8192 for the consumer contact view and fail clearly if its reported count exceeds capacity. This is approximately2.87 times the observed2854 peak, not a guarantee for arbitrary poses or every future wall-contact workload. The128 overflow is confirmed, but truncation alone did **not** reproduce the remote CUDA crash and is not established as its unique cause. No liquid-containment, hydrodynamic, reaction or robot-wall-contact qualification is implied.

Receipt: `outputs/sciben_waterbath_120hz_20261010/wall_contact_capacity13.json`, SHA-256 `21954e1b3cced41a71492c5e223af2bb436256a87c19c25120268b5b61751284`. Exact report/log/validator hashes and both failures/successes are retained. Candidate13 package inventories and its previous physical qualification receipt remain unchanged.

```bash
# Same cleared Isaac4.1 SDK environment as above.
python scripts/sciben_waterbath_producer.py wall_probe \
  --package outputs/sciben_waterbath_120hz_20261010/fehling_candidate13 \
  --out <new-output> --contact-capacity 8192
```

The diagnostic and this record are the only substantive source changes in this follow-up. Unit suite remains7 passed; compilation and diff checks passed. These measured capacities are scoped operational evidence, not a new general scene-authoring rule.

## Source-recording rack audit and full-return diagnostics

The read-only `recording_rack_audit` output examines all60 original Task12 JSON/NPZ recordings using the converter's lexicographic index order. All60 final poses pass the exact current consumer insertion predicate, including all40 training-eligible indices10–49. Extracted predicate AST checks found no discrepancies; matrix construction agrees with pxr to4.44e-16. Actual glass mesh intersections at all four rack-plate surfaces fit the measured apertures in every final recording, with worst physical clearance+0.883 mm.

Original `15.json` is training index11. Its final origin is1.014 mm above the seat, tilt1.068°, predicate radial margin+1.407 mm and physical upper-aperture clearance+0.908 mm. The final86 source frames are valid. It is not an originally hovering tube. Its opening interval near return is frames3864–3887, followed by empty closed fingers. The audit does not justify changing the origin convention or relaxing the metric.

The source-pose ranking is in `ranked_training.csv`; `budget7000.json` also applies the unmodified1/2 hold pattern. Source40/index42 reaches its stable final insertion at replay tick6831, leaving169 nominal valid ticks within7000. Source36/index39 begins its final valid tail at6282. These are source-pose screens only, not new replay or reaction success.

### Source15: candidate13 baseline

A direct-SDK replay of the full source15 training episode against the consumer's seen_scene_1 composition completed7000 replay steps plus300 warmup and2 reset callbacks (7302 native120 Hz callbacks), without an engine error. Reaction graphs were disabled. However, the actual rack-return predicate failed: the tube ended89.57° tilted, its visual lowest point0.358 mm above the upper rack plate, with6.01 mm origin XY offset from the intended nearby aperture. Dynamic-control and USD positions agreed exactly. The tube had missed the opening and come to rest on the rack, rather than remaining upright in its slot. The engine-only PASS in the primary report is explicitly distinguished from `FAIL_RACK_RETURN` in `return_audit.json`.

Divergence began during grasp: held finger gaps were approximately9.22 mm versus the original9.97 mm, and the held tube differed vertically and laterally from the recorded pose. This motivated a controlled contact-offset comparison, not a predicate change or action rewrite.

### Candidate14: original SDF offsets restored, not promoted

`fehling_candidate14` changes exactly two composed attributes: original tube SDF restOffset1 mm and contactOffset10 mm are restored from the immutable source. Supplemental contacts, particles, velocities, counts, masses, materials and every other property/relationship are unchanged. Only scene.usda and manifest.json differ from13; `candidate14_change_audit.json` verifies this.

Candidate14 passed the10 s cold and17 s prescribed lift/return containment tests (1202/2042 native callbacks, both liquids0 outside under the existing1 mm tolerance, no errors). Its full source15 countercomparison explicitly applied those two offsets at the mounted consumer paths. Held finger gaps returned to approximately9.94 mm, but the mechanical rack return still failed: after7302 callbacks the tube lay nearly horizontally (89.80°) beside the rack/table. No actual/USD position mismatch was observed. Restoring the offsets alone is insufficient.

**Candidate14 is not promoted. Candidate13 remains the primary asset with its previously stated cold/lift scope.** `candidate14_countercomparison.json` preserves both full-return failures and the exact applied offsets. Successful robot demonstrations and positive regenerated training data are not inferred from the bare physical passes.

The already-authorized backup source40/index42 was converted under producer outputs only, using the original converter and unchanged actions; no GenManip file was written. Its bounded7000-step diagnostic is tracked separately. Following the clarified delivery boundary, producer/test/conversion scripts remain development tools in this repository; they are not deployment dependencies. Final baseline-GenManip acceptance belongs to the root integration work, restricted to task YAML, USD, task data, scientific_experiments metrics and LeRobot data. Prior core-modified consumer runs remain diagnostic evidence.

### Backup40 bounded diagnostic completed (2026-10-11)

The unchanged candidate13 replay of source40/index42 completed the agreed7000 replay steps,300 warmup steps and2 reset callbacks without an engine error (7302 native120 Hz callbacks). At the cutoff, the tube was geometrically inserted in `slot_15ml_r02_c04`: origin0.865 mm above the seat, visual minimum0.859 mm above the seat, tilt2.263°, radial margin+0.964 mm, and zero dynamic-control/USD position difference.

This is a **successful final mechanical placement**, not a qualified successful task demonstration. Reaction graphs were disabled; the full consumer metrics were not executed. The final continuous valid-insertion run was95 physics steps, and the first return-valid tick was6828, so the result does not establish the100-count consumer criterion. The7000-tick budget ends at source frame4666, before the end of the4888-frame recording. No action, metric, timestep pattern or geometry was changed to manufacture a pass.

Evidence is `robot13_source40_return/return_audit.json`, SHA-256 `bf762156f1ce6fd7c171d5039bc8eedcde342517703a8c8ec6f76c11b7cf4809`. The converted episode has an explicit diagnostic-only usage marker. `return_diagnostics_handoff.json`, SHA-256 `98947251c0c51e65cbe1a66c0222a7dd5ed7c6416aaa48f33f4f963319d5789e`, summarizes the source60 audit, two source15 return failures, unpromoted14, and bounded40 result. Both candidate13 inventories and its original qualification receipt remain unchanged.

As requested, further geometry/trajectory exploration stops here. First delivery may explicitly lack a qualified successful waterbath demonstration or regenerated positive training sample, pending baseline five-item acceptance and, if necessary, recapture. The producer does not reinterpret this diagnostic as a positive LeRobot training result. Candidate13 remains the primary bounded cold/lift asset;14 is retained only as a failed-return counterexample.
