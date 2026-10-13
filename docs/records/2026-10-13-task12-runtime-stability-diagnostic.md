# Task12: standard SDF and coarse bath diagnostic, 2026-10-13

Status: diagnostic candidates only; no delivery promotion or new runtime qualification yet.
User scope: keep weighing LeRobot rendering running, defer only waterbath LeRobot, and finish the four-category waterbath runtime package without GenManip core/SDK/robot changes.

## Investigation

Consumer working root is `/mnt/data/zhuzihou/GenManip-Sim/saved/repair_20261010/task12_liquid_color_20261012` (R).
The installed128MiB candidate completed background3 but failed mixed5 around3060 logged steps with a GPU articulation kernel error. Same-case64MiB once completed7000; warnings alone are not causal evidence (64341 faceIndex lines in failed128MiB versus482563 in completed64MiB). A fresh unchanged replay is currently running.

Read-only collision audit confirmed the robot is covered by the RigidScene group. Tube120 straight-wall and353 bottom cells are complementary, not a justification for restoring obsolete particle-filter lists. The beaker has two original SDFs plus257 supplementary fluid hulls.

The standard asset at `outputs/task09_r13_beaker_325ml_sdf_clean_closure_r2_20260831/package/asset.usd` has exactly matching beaker body/rim/spout vertices, topology, collision approximations and SDF256 resolution. R/evidence/standard_beaker_geometry_comparison.json binds this comparison. This supports reusing the original beaker geometry, not transferring its runtime qualification to current liquid settings.

## User-directed simplification

The user recalled the standard shared SDF liquid/rigid route and asked to avoid a near100k-particle bath where existing liquid tasks use hundreds/thousands. Prioritize that route over adding further hybrid collision patches.

Read-only source USD inventories:

| Task | Particles | particleContactOffset / restOffset | maxVelocity |
| --- | ---: | --- | --- |
| task01 |1531|5/5mm|0.6m/s|
| task02 |244+189|5/9mm|0.6m/s|
| task03 |465|5/6mm|0.6m/s|

All use width5.94mm; no explicit particle solver iteration count was found. This table is static configuration evidence only.
The earlier969-particle beaker was186.908mL, one quick/provisional run; its6.5368s observation duration is not simulation time. It cannot qualify this349.095mL task.

## Candidate outputs and boundaries

All new assets are under `outputs/sciben_waterbath_120hz_20261010/`:

- `task12_bath_sdf_filter_diagnostic_20261013`: changes only two particle filteredPairs lists, excluding original beaker SDFs while retaining hulls. Static-only; not run or prioritized after user steering.
- `task12_bath_sdf_only_diagnostic_20261013`: disables only257 supplemental bath hulls; original SDF body/rim, spout, tube/rack and particles remain unchanged. Cold/lift control queued after the owned native replay releases GPU.
- `task12_bath_coarse_recipe_diagnostic_20261013_v3`: bath only uses canonical `convert_asset.liquid_autofill.recipe_payload()` Task02 r10.3 physical recipe, spacing5.82mm, particleContactOffset5mm, restOffset9mm, maxVelocity0.3m/s. Bath count96649→1670; sample13905 unchanged. Total bath mass349.095g retained instead of copying recipe ParticleSet mass0.00045kg. SDK4.1 schema default auto offsets/solver16/CCDfalse replace task-specific fine-bath values. Original transparent material retained; isosurface spacing scales with lattice and uses canonical8mm surface distance/5mm smoothing. Reset arrays, spacing, mass-per-particle and bath-count/visible-surface metadata are updated consistently. Reaction logic/timing is unchanged.

The first coarse authoring attempt lacked a local Points type for the stronger layer and failed before any runtime launch; its directory is retained. v2 did not yet refresh reset metadata and is superseded by v3, never delivered.
The diagnostic package references its immutable consumer source and is not portable delivery; probe entry supplies explicit PhysicsScene owners at120Hz/128MiB. Static relationship-scope warnings in the reference-only scene are resolved by that probe owner override.

Authoring scripts and supervisors are external production tools under R/tools, not consumer dependencies. They do not implement conversion in Scenario Forge core. Every static candidate compares composed attributes/relationships to constrain its changes. R/evidence/*diagnostic.json and per-output receipts record exact scope. An unchanged replay, SDF-only bounded control, then coarse-bath bounded test run serially on the dedicated4090; no automatic release follows.

## Pending gates and documentation handoff

Actual settled bath volume/height, containment during cold/lift, rendering, reset/heat guards, and complete original-core replay remain required. A particle-count reduction alone does not pass those gates. Final release needs repeated mixed5 and all five documented task12 cases, full engine logs, four-camera audit and clean installation from the four allowed categories.

Scene standards require no general changes: ASSET-001/003/005, MAT-001/003 and VAL-001/002/003/004 already cover producer qualification and scoped evidence. Do not promote these task-specific choices into universal physics defaults. Consumer operations/current-state notes are synchronized in Scenario Forge's2026-10-13 runtime-closeout record; actual results will be appended here.

## Runtime results and volume correction

Fresh unchanged128MiB mixed5 completed7000/.15/success0, all6542 source actions plus458 holds, four7001-frame videos decoded, no engine error,588 baseline files unchanged. Its prior failure remains; one successful repeat is not a repair proof.

SDF-only beaker with original96649 bath particles passed1202-step cold and2042-step lift tests with both phases0outside/count loss and no engine errors/downgrades. The1670 bath version passed three independent1202-step cold runs and one2042-step lift run. These are bounded physics evidence, not full native acceptance.

Visual preview is transparent without obvious particle spheres but surface readability was insufficient to certify volume. Following actual SDK4.1 `PhysxParticleIsosurfaceAPI.py` tests, the read-only probe captures `<ParticleSystem>/Isosurface` points/indices/transforms. Existing isaac41 Python/trimesh measured the unchanged closed, consistently wound bath envelope as252.971mL, central top median94.297mm, versus target349.095mL and original90.132mm surface. **1670 is rejected for volume**, despite passing containment. Sample signed envelope is7.669mL (main7.686mL plus small inward cavity surfaces); no absolute-value summation, clipping or hole filling was used. Rendered envelope volume is not a physical incompressibility guarantee.

`task12_bath_coarse_volume_fit_20261013` therefore uses2320 bath points from5.25mm seeding inside the original liquid profile (linear volume/count estimate2305), and the existing task01 collider-rest5mm value instead of9mm. All other bath physical recipe and isosurface/material settings, sample physics, rigid geometry and reaction logic remain unchanged. Bath total mass stays349.095g. New cold/render measurement is in progress; previous1670 qualifications cannot be assigned to this variant. Scripts/receipts preserve both versions and the failed volume measurement.

The2320 variant subsequently passed three independent1202-tick cold tests and one2042-tick lift test, both phases0outside and unchanged counts, no engine errors/downgrades. The captured single closed bath envelope is350.1096mL, central surface median97.519mm (+7.387mm over original static shape). Natural render remains transparent with no obvious particle balls; the water/glass interface is subtle (WARN). This level difference is explicit; an optional user preference question is pending and the recommended assumption is used for continued validation, not falsely recorded as approval.

Consumer integrated20 scenes and rebuilt only BathParticles arrays in41 metadata records. Archive703 offline members plus unchanged metric was installed into an original-base isolated receiver with complete hash equality. First installed mixed5 is running under original120Hz/7000-step conditions; no complete-native or release qualification is claimed yet. Producer mesh-volume evidence measures the rendering envelope only, not exact incompressible chemistry.
