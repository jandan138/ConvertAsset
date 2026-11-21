# Task09 solid mass audit and candidate profiles — 2026-10-08

This producer audits the five grains in
`/mnt/data/chenjiantong/scene_usd/task_09_solid_weighing/scene.usd` and provides
independent mass overlays for Scenario Forge's requested stability sweep. It
makes no runtime qualification claim and does not change source inputs.

## Investigation and choices

Read `AGENTS.md`, `CLAUDE.md`, `.codex/file-ownership.md`, the feature-implementer
playbook/memory, and `docs/index.md`. The source stage is in meters and kilograms.
Each `/World/obj_grain_01` through `05` has one closed triangular `CrystalMesh`
under a world scale of 0.5. Each source grain has an authored mass approximately
10 g and zero diagonal inertia, which asks the simulator to calculate inertia.
Material prims are named `SaltWhite`. That name suggests salt; it does not prove
chemical composition or porosity.

The reference density is **2160 kg/m³ at 25 °C**, from the primary manufacturer
[Sigma-Aldrich S7653 sodium chloride product page](https://www.sigmaaldrich.com/US/en/product/sial/s7653)
(accessed 2026-10-08). Reference masses assume homogeneous, nonporous NaCl. They
are engineering estimates for this modeled geometry, not measured specimens.

Actual transformed mesh volumes use the signed triangle tetrahedral sum after
applying the complete USD world transform and `metersPerUnit`; translating the
vertices about their centroid improves numerical conditioning. Edge and vertex
manifoldness, coherent triangle winding, nondegeneracy and a single connected
shell are checked before accepting volume. Bounding boxes are reported for scale
inspection only and are not used for mass. Globally reversed winding is recorded
and accepted through absolute volume. This audit does not test geometric
self-intersection; the current five meshes passed the stated topology checks.

| Grain | Volume (mm³) | Reference mass (g) | Source mass / reference |
| --- | ---: | ---: | ---: |
| 01 | 427.367119 | 0.923112977 | 10.833 |
| 02 | 273.711488 | 0.591216815 | 16.914 |
| 03 | 340.933486 | 0.736416330 | 13.580 |
| 04 | 429.675832 | 0.928099798 | 10.775 |
| 05 | 638.839784 | 1.379893933 | 7.247 |

The reference total is **4.558739853 g**, versus the source's approximately 50 g.
The independent candidate layers are reference multipliers 1, 2, 5, 10 and 20,
with **each body capped at 10 g**, plus the original uniform 10 g baseline. The
x20 layer intentionally equals the baseline, but retains a separate ID to keep
the sweep endpoint and source comparison explicit. At x10 only grain 05 reaches
the cap. Candidate totals are 4.558739853, 9.117479705, 22.793699263, 41.788459196,
50 and 50 g before USD float authoring. Consumers should read the actual USD
mass values when calculating expected LCD values.

## Implementation and consumption

New files:

- `scripts/task09_solid_mass_profile.py`: lazy USD/NumPy imports, geometry audit,
  candidate sequence, mass-only overlay export and source-bound provenance.
- `tests/test_task09_solid_mass_profile.py`: geometry, topology, unit conversion,
  candidate cap, independent overlay and explicit inertia regressions.
- This dated record.

Generate artifacts using the repository's Isaac Python wrapper:

```bash
./scripts/isaac_python.sh scripts/task09_solid_mass_profile.py \
  --source /mnt/data/chenjiantong/scene_usd/task_09_solid_weighing/scene.usd \
  --out outputs/task09_solid_mass_profile_20261008
```

The output directory contains `mass_profiles.json` and six `.usda` files. Compose
exactly one candidate layer **stronger than** the scene, retaining the five body
paths, or copy its mass opinions into the consumer's physics profile. The layers
have no sublayers, references, dependencies, geometry, collision changes or
transforms. They contain `PhysicsMassAPI` and `physics:mass`; if an input has
positive explicit diagonal inertia, it is scaled in proportion to mass. For the
actual source grains no inertia overrides are emitted because all source
inertias are zero. Source `kilogramsPerUnit` is honored when authoring mass.

`mass_profiles.json` records each body path, volume/topology checks, complete
world transform, source mass/inertia, density reference, reference ratios,
candidate masses and total, hashes of the producer and used source layers, and
hashes of every output layer. `runtime_qualified` is explicitly false. Recompute
profiles if source geometry or scale changes. Downstream USD mass rounding is
approximately single precision; display precision does not imply measurement
precision.

## Validation evidence

The first test run was intentionally failing at collection because the producer
script did not exist. After implementation:

```bash
./scripts/isaac_python.sh -m pytest -q tests/test_task09_solid_mass_profile.py
```

**7 passed.** Cases include tetrahedron volume instead of box volume, translation
invariance, nonuniform scale plus centimeter-stage conversion, open/inconsistently
wound mesh rejection, globally reversed winding, disconnected shell rejection,
per-body candidate caps, portable overlay contents and explicit inertia scaling.
All six actual generated layers were additionally composed ahead of the original
source in anonymous stages; the resulting five masses matched candidate values
within 1e-9 kg. The source stage was only opened for reading.

The wrapper resolves `/isaac-sim`, whose `VERSION` reports
`4.5.0-rc.36+release.19112.f59b3005.gl`. No SimulationApp, GPU scene, collision
sweep or render was run by this producer task. Physics stability, load/unload
readings, two-runtime equivalence and video remain consumer integration work.

## Related findings and limits

Existing reusable MDL trees were located at:

```text
outputs/task09_powder_bottle_r3_20260910/candidate_r1/deps/balance/materials/isaac41/deps/mdl/
outputs/task09_powder_bottle_r3_20260910/candidate_r1/deps/balance/materials/isaac45/deps/mdl/
```

Both contain OmniGlass, OmniSurface, OmniPBR, pbr, limits and NVIDIA support
imports. These were discovered, not copied or independently qualified for the
new task14 balance. Dependency closure and visual fidelity must be checked for
the exact consumer scene.

Other source mass findings: `obj_plate` is 5 kg, `obj_weighing_boat` is 10 g,
`obj_weighing_bottle_body` is about 49.727 g, and the old analytical balance
Chassis is 1,000,000 kg. These are reported rather than modified; task14 replaces
the old balance. Collision geometry was not altered. A stable minimum mass
cannot be selected from static mass audit alone.

This is task-specific evidence, not a new general asset rule. No core package,
API or general producer standard changes. The team lead owns integration and
any broader documentation navigation updates; this task was explicitly limited
to the assigned files and output directory and did not commit changes.

## Follow-up: source-preserved MDL closure

Added `scripts/task09_solid_material_closure.py` after the consumer identified
nested MDL imports missed by USD asset-path discovery. This orchestration uses
ConvertAsset's existing AAN `_mirror_mdl_runtime_dependencies` and
`build_material_runtime_closure` helpers; it does not implement a new MDL parser
or converter. Source root MDLs are copied byte-for-byte and checked by SHA256.
Runtime-specific helper modules are mirrored from the selected runtime. No root
substitution, material input edit or PreviewSurface conversion is performed.

```bash
python scripts/task09_solid_material_closure.py \
  --sources /mnt/data/chenjiantong/scene_usd \
  --out outputs/task09_solid_mass_profile_20261008/material_closure
```

The output has `{isaac41,isaac45}/{task09,task14}/materials.usda` overlays with
sibling `deps/mdl/` trees. Each runtime provides 16 task09 sourceAsset opinions
(excluding its superseded balance) and 24 task14 balance sourceAsset opinions.
The consumer copies the complete material_closure tree and composes its selected
runtime's two overlays stronger than the assembled scene. All authored texture
paths in the original USD remain supplied by the consumer's existing SubUSDs
closure; textures referenced inside MDL are covered by the recursive helper.

Four closure checks passed, including a second scan with **no source records and
no approved external runtime roots**, ensuring all nonnative helpers resolve
inside each package. All 40 overlay asset paths per runtime resolved locally,
all root MDL hashes matched the source, and overlays contained only sourceAsset
opinions. Task09 contains 17 MDL files for each runtime; task14 contains 10 for
4.1 and 12 for 4.5. `material_closure/validation.json` records these checks.
`anno`, `base`, `df`, `math`, `state` and `tex` are native MDL standard modules.
The 4.1 helper root is `site-packages/omni/mdl/core`, outside the sibling
`site-packages/isaacsim` folder. Compiler compatibility and visual parity have
not been tested here and must be assessed from the consumer's runtime logs and
renders. Static complete closure alone does not prove shader compatibility.

## Follow-up: rigid origins are not collision geometry

The consumer reported some settled grain rigid origins below 0.750 m. A raw
source-only inspection establishes that this alone is not table penetration.
The table collision cube's **actual transformed vertices** span z = 0.705 to
0.755 m, matching the visible tabletop. Grain body origins are displaced from
their mesh geometry:

| Grain | Mesh vertex centroid relative to root (mm) | Root distance outside convex hull (mm) |
| --- | --- | ---: |
| 01 | (5.215, 2.542, 0.298) | 0.043 |
| 02 | (15.717, 17.384, 0.274) | 18.904 |
| 03 | (15.639, 0.232, 0.110) | 12.049 |
| 04 | (0.109, 0.278, −0.103) | 0; root is inside |
| 05 | (6.980, 8.087, 0.232) | 3.906 |

For example, rotating grain 02 can place its rigid origin as low as about
0.73610 m while its convex shape stays above the 0.755 m tabletop, ignoring the
small rest separation. Grain 03 similarly permits about 0.74295 m. These are
geometric possibility bounds, not predicted settled orientations. Penetration
checks should use transformed collider vertices / contact separation, not a
fixed rigid-root z threshold. Moving the root to repair this false check is
unnecessary and would change the integration coordinate convention.

All five grain colliders are visible-mesh convex hulls with authored contact
5 mm and rest 1 mm offsets, zero initial velocity, 32 position / 4 velocity
solver iterations, linear/angular damping 0.04/0.08, sleep and stabilization
thresholds approximately 1e-5. Source body scale is 0.5. The boat's root is
z = 0.76594 m while its visual minimum is 0.75950 m. Its collision floor is only
1 mm thick (z = 0.759978 to 0.760978 m), with contact 5 mm / rest 1 mm offsets.
Five convex side colliders have no authored offsets; their runtime defaults
need runtime inspection. Some side collision bounds reach z = 0.79925 m,
beyond the visual maximum 0.78750 m. Thus the authored geometry and offsets
justify inspecting contact-driven rocking, but cannot establish the cause of
consumer velocity residuals without physics evidence.

If corrected geometric checks still show jitter, a producer candidate reducing
grain/boat authored contact margins to approximately 1 mm and rest offsets to
zero should be tested against the source baseline before adoption. No such
physical adjustment has been made by this static follow-up.

Evidence and reproducible inspector are
`outputs/task09_solid_mass_profile_20261008/source_collider_audit.json` and
`inspect_source_colliders.py`. The inspector reads the raw colleague scene and
writes only this producer output directory. It uses source convex hull equations
and constrained nearest-point minimization for the origin-to-hull distances;
it does not open or alter the generated Scenario Forge scene or run GPU physics.

## Follow-up: optional contact and sleep candidates

At the consumer's explicit request, added
`scripts/task09_solid_contact_profile.py` and extended the existing test file.
The new test first failed because the producer did not yet exist; after
implementation the complete suite passed **8 tests** under the Isaac Python
wrapper. The regression checks enabled-collider filtering, excluded table and
disabled geometry, exact allowed-property scopes, source immutability and
independent grain-only sleep parameters.

```bash
python scripts/task09_solid_contact_profile.py \
  --source /mnt/data/chenjiantong/scene_usd/task_09_solid_weighing/scene.usd \
  --out outputs/task09_solid_mass_profile_20261008/contact_candidates
```

The `contact_candidates/` directory contains:

- `contact_1mm.usda`: contactOffset = 0.001 m and restOffset = 0 on exactly
  `/World/obj_grain_01/CrystalMesh` through `obj_grain_05/CrystalMesh`, plus
  `/World/obj_weighing_boat/Cube` and `Cube_01` through `Cube_05` (11 enabled
  collider prims total).
- `grain_sleep.usda`: sleepThreshold = 5e-4 and stabilizationThreshold = 5e-5
  only on the five `/World/obj_grain_NN` rigid roots.
- `contact_profiles.json`: source/producer/overlay hashes, original source
  values and exact prim scopes.

The two layers have disjoint opinions and can be used independently or together,
stronger than the scene and mass profile. They prepend the relevant PhysX API
schema and author only their stated properties. No mass, inertia, geometry,
transform, initial velocity, gravity or kinematic flag changes; no runtime wake,
freeze or pose-rewrite code. Sleep thresholds are specific-energy parameters,
not direct velocity cutoffs. They still require natural contact/physics
qualification and should not be confused with forced freezing.

An additional anonymous-stage composition of both layers over the raw source
checked every existing attribute and confirmed all changes belonged to the
four intended contact/sleep properties. All 11 composed collider offsets match
requested values. This evidence is in
`contact_candidates/static_composition_validation.json`. Source hashes were
checked before and after producer execution. Both candidates remain
`runtime_qualified: false`; no GPU run or stability claim was made here.

## Follow-up: source-bound 64/32 solver candidate

The consumer's A/B observations identified loaded-pan raw velocity residuals
with small pose drift; those runtime observations are not independently
requalified by this producer. At the consumer's request, the contact producer
now also offers a solver-only candidate, explicitly bound to **both** original
scenes. No pose-derived speed criterion or runtime acceptance threshold was
changed by this work.

```bash
python scripts/task09_solid_contact_profile.py \
  --source /mnt/data/chenjiantong/scene_usd/task_09_solid_weighing/scene.usd \
  --balance-source /mnt/data/chenjiantong/scene_usd/task_14_fixed_weight_weighing/scene.usd \
  --out outputs/task09_solid_mass_profile_20261008/solver_candidates
```

`solver_candidates/solver64_32.usda` authors only position iteration count 64
and velocity iteration count 32 on eight targets:

- Task09 five grain roots and `/World/obj_weighing_boat`, using PhysxRigidBody.
- Task14 `/World/obj_analytical_balance`, using PhysxArticulation.
- Task14 `/World/obj_analytical_balance/Instance/WeighingPan`, using PhysxRigidBody.

The source grain and articulation counts are 32/4, pan counts 32/1, and boat
counts are not authored. Expected source body/articulation API types are checked
before export. USD customLayerData binds both scene hashes and points to
`solver_profiles.json`, which records original settings, target scopes, source
layer hashes, producer hash and output hash. This layer is independent of mass,
contact and sleep candidates. It makes no joint, geometry, mass, inertia,
velocity, gravity or kinematic edits.

The new regression first failed with the missing solver producer function.
After implementation, the complete wrapper-based suite passed **9 tests**,
including both-source hash binding/immutability and the exact 16 solver-property
opinions. Separate anonymous compositions over each real source verified all
eight targets resolve to 64/32. Evidence is
`solver_candidates/static_validation.json`. The candidate remains static-only,
with `runtime_qualified: false`; no GPU run or stability claim was made here.

## Follow-up: black salt render investigation

The consumer subsequently rejected the 64/32 solver candidate after its own
runtime A/B found no improvement; the solver overlay remains diagnostic and is
not promoted by this record. The consumer also provided the rendered
`preview3/frame_1326.png`, showing five black grains in a white boat.

Static inspection of the raw source and final delivery scene excludes several
specific failure modes:

- Every grain's explicit uniform face normals match the outward triangle
  cross-product normal (dot products about 0.9999999 to 1.0000001), with
  right-handed winding and positive volume. No normal flip is warranted.
- All face-varying `st` UV arrays have exactly the triangle-corner count.
- Every final salt MDL and texture asset resolves locally and matches its
  source SHA256. Albedo mean RGB is approximately (185, 180, 170), not black;
  normal texture mean is approximately (127.5, 127.5, 254.25), with sensible
  forward-facing blue values.
- The grain material retains opaque white/warm color, metalness zero, diffuse
  reflection weight 0.77, and roughness 0.68. It also enables diffuse
  transmission and subsurface weight 0.32 with `thin_walled=false` and
  subsurface scale 0.001 m. Its custom scattering preset value 12 is valid.
- The shipped 4.5 OmniSurfaceBase and OmniShared helpers exactly match the
  installed runtime. The preserved root OmniSurface wrapper differs from the
  installed version only by omitted round-edge controls and forwarding; those
  controls default to zero radius in the installed version.
- The inspected preview3 log contains no MDLC compile, missing-texture or
  failed-shader error. This does not prove renderer feature parity.

The black appearance's cause is **not established by static evidence**. The
consumer is first testing a direct DistantLight in the demo environment. To
support controlled rendering A/B without changing any final assets, the producer
created three optional scalar-only diagnostic layers under
`outputs/task09_solid_mass_profile_20261008/salt_visual_diagnostics/`:

- `salt_no_sss.usda`: diffuse transmission disabled, subsurface weight zero.
- `salt_no_normalmap.usda`: geometry normal strength zero.
- `salt_no_sss_no_normalmap.usda`: both ablations combined.

These target only `/World/obj_grain_NN/Looks/SaltWhite/OmniSurface` inputs. They
retain source albedo textures, color, roughness and opacity, and do not alter
source shader code, mesh normals, geometry, physical materials or runtime
physics. They are diagnostic candidates with no rendered-fix claim. The
reproducible `build_diagnostics.py` and `static_audit.json` in that output folder
record source hashes, final resolved assets, normal agreement, texture statistics
and candidate changes. No GPU was run and no final Scenario Forge asset was
modified by this task.

## Downstream integration evidence: selected profile and renderer

The Scenario Forge consumer completed six independent qualification processes
(three Isaac Sim 4.1 and three 4.5), at actual PhysX dt = 1/120 s. This producer
read the six reports, aggregate summary and two runtime mass-parity reports,
and independently checked the packaged scene hash. Evidence is scoped to:

```text
Scenario Forge package:
/cpfs/user/zhuzihou/dev/scenario-forge/outputs/task09_solid_weighing_r1_20261008/handoff/scientific_workbench_solid_weighing_task09_r1

assets/composed/scene.usdc SHA256:
99c0b70ab7fba410281bc73eb10e8f9f344c127799dc0318ff537b8fe53d5fe8

Consumer evidence root:
/cpfs/user/zhuzihou/dev/scenario-forge/outputs/task09_solid_weighing_r1_20261008/qualified
```

The selected composition is **reference_x1 + contact_1mm + grain_sleep**.
`solver64_32` and all salt material diagnostic layers were rejected. The
runtime mass reports `qualified/mass41.json` and `mass45.json` both record exact
configured-versus-PhysX parity for all five grains, bound to the scene hash
above. Thus the reference total is about 4.55874 g and rounds to a 4.56 g LCD
reading in this fixture; no mass amplification was needed for this qualified
composition.

`qualified/{41,45}_run{1,2,3}/report.json` all report pass for empty balance,
empty boat, button tare, incremental loads, five-grain completion, partial
unloads, unloaded zero, negative tare, reset, hover exclusion and the consumer's
stability checks. `qualified/summary.json` records:

| Runtime | Maximum loaded drift (mm) | Maximum per-step vertex-motion speed (mm/s) | Maximum raw engine speed (mm/s) |
| --- | ---: | ---: | ---: |
| Isaac Sim 4.1 | 0.003077 | 0.734280 | 7.099104 |
| Isaac Sim 4.5 | 0.004191 | 0.572908 | 6.092743 |

The consumer assesses physical-step transformed-vertex motion and drift for its
geometry stability gate, and preserves raw engine velocity as an independent
measurement. **These are different metrics.** The loaded case does not pass a
raw-engine-speed-below-1-mm/s criterion, and the reported geometry-motion pass
must not be presented as that stronger result. Initial layout and 5/20 mm
clear-table release observations also pass in the six selected-profile runs.
The consumer reports that the 20 mm release can continue edge rolling without
`grain_sleep`, while the selected sleep/stabilization profile settles. This is
fixture-specific consumer evidence, not a general minimum mass or sleep rule.

The black salt preview was resolved by selecting **PathTracing** for rendering
with the original source material. Consumer A/B found that RayTracedLighting
still darkened grain top faces after adding direct illumination and disabling
SSS/normal-map diagnostics. PathTracing displayed the original light salt
material correctly. No salt material or normal override was adopted. This
establishes a rendering-mode workaround for the tested scene; it does not
establish the internal cause of the RayTracedLighting discrepancy.

The consumer record is
[2026-10-08-task09-supported-solid-weighing.md](../../../scenario-forge/docs/records/2026-10-08-task09-supported-solid-weighing.md).
This entry records downstream acceptance for the exact package and evidence
above, without promoting the standalone producer candidates generically or
rewriting their original static-only qualification statements. At the time of
this entry, the final video was still encoding; **final video review is not
claimed here**. No producer scripts, source scenes or consumer assets were
modified during this evidence synchronization.
