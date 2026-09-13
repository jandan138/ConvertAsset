# Chemistry test tube 18 × 150 mm — ConvertAsset producer r1

Date: 2026-09-12. Current delivery status: **PASS — fixture-scoped runtime
qualification; static validation PASS**.
Qualification scope: **Isaac Sim 4.5 Fehling r7 rack and bath prescribed fixtures**.
Robot, heat and PBD qualification remain false; geometry remains engineering-defined.
This record covers local production, independent-process Blender reopen, CPU
Cycles previews, USD static inspection and main's subsequently completed runtime
promotion. Earlier `runtime_pending` entries are historical stage records; the
final promotion confirmation below records the live status. This implementer did
not start SimulationApp/GPU or invoke live promotion. No commits or pushes were made.

## Scope, investigation and decisions

Owned new files:

- `scripts/model_chemistry_test_tube.py`: SI meridian/triangle geometry, signed
  moments, editable Blender source, CPU previews, separate-process reopen audit.
- `scripts/build_chemistry_test_tube.py`: fresh USD/package build and read-only
  asset/package static audits; heavy dependencies imported lazily.
- `tests/test_chemistry_test_tube.py`: geometry, lumen, mass, USD/material,
  source-evidence rejection, SDK-independent imports, actual package/hash checks.
- This dated record.

Owned output root:
`outputs/chemistry_test_tube_18x150_r1_20260912/`.
All delivered assets/evidence are below this root. Existing paper/research work,
conversion core, shared indexes, agent memory and Scenario Forge were not edited.
The explicit current no-commit/owned-file instructions take precedence over the
repository's generic documentation-commit/index/memory instructions. Main owns
subsequent shared-index/standards synchronization.

Read `CLAUDE.md`, `AGENTS.md`, `.codex/file-ownership.md`, both feature-implementer
and asset-validator playbooks, their memories, and `docs/index.md`. Investigated
`model_compact_powder_bottle.py`, `build_threaded_tube15_fusion.py`,
`package_scientific_workbench_beaker_sdf.py`,
`build_titration_filled_visuals_r3.py`, `promote_fehlings_open_tube.py`,
`isaac_python.sh` and existing powder-bottle tests. Reused the bottle `_moments`
signed-tetrahedron implementation and the threaded-tube material/SDF helpers.

The first USD dependency test found that the older tube helper's default MDL
source did **not** retain `OmniGlass_Opacity.mdl`. The new producer explicitly
copies both files from the existing self-contained beaker package:
`outputs/scientific_workbench_beaker_325ml_sdf_web_standard_20260824/package/deps/mdl/`.
Their NVIDIA redistribution notices remain intact. There are no textures or
additional nonstandard MDL imports; standard SDK modules are renderer built-ins.

Plan review:

- **Architecture:** one standalone producer, one dynamic asset root, one exact
  visual/collision mesh, source JSON as the geometry handoff; no conversion-core
  changes or scenario/runtime orchestration.
- **Completeness:** pole welding, consistently oriented triangulation, real open
  lumen, spherical floor, mass/COM/inertia, source reopen, local MDL closure,
  manifest/scalar/hash binding, fail-closed stale-evidence checks.
- **Risk:** fresh-only model/package builders refuse overwrite; the repeat audit
   is read-only. SDF cooking and exact r7 contact were pending at initial authoring. Runtime
  promotion must never rewrite `asset.usd` or material dependencies.

No general scene-authoring rule is changed by this artifact-specific engineering
model; this record states the validated scope and main's synchronization handoff.

## Approved modeling parameters and evidence boundary

Generic, nominal **body OD18 mm × total height150 mm**, plain unprinted clear
colorless borosilicate-style glass. No cap, printing, graduation, sleeve or label.
This is an original engineering geometry, **not an exact manufacturer replica**.

User supplied indexed product-size evidence from:

- <https://www.sigmaaldrich.com/US/en/product/sigma/z653543>
- <https://www.smithscientific.com/product/test-tubes-neutral-borosilicate-18x150-08wall-with-rim-100pcs-per-pack-6213/>

Full pages were unavailable; this task does not claim to have retrieved or
verified them. In particular, the second URL's `08wall` naming does not establish
the authored wall: **1.0 mm is the explicitly approved engineering parameter**.
Wall, lip, density and optical values are not verified vendor measurements.

| Parameter | Authored value |
|---|---|
| Units / axis / asset transform | metres / Z-up / identity, scale 1 |
| Origin | Exterior bottom pole, z=0 |
| Bottom spheres | Outer R9 mm, inner R8 mm; shared centre (0,0,9 mm) |
| Inner floor | z=1 mm, radius 0 |
| Straight body | OD18 mm, ID16 mm; 1 mm radial wall |
| Gentle outer flare | z147–149 mm, smoothstep radius9–10 mm |
| Rolled crown | Upper semicircle, minor radius1 mm, centre radius9 mm/z149 mm |
| Maximum rim diameter | 20 mm |
| Highest mouth edge | z150 mm, crown clear diameter18 mm |
| Minimum straight bore | 16 mm, including below the crown |
| Segmentation | 128 azimuth samples; 48 intervals per bottom hemisphere |
| Cavity sampling | 143 ascending [z,r] entries; 2 mm axial body spacing |
| Material density | 2230 kg/m³, engineering declaration |
| Blender | Principled BSDF transmission1, white base, IOR1.47, roughness.02, emission0 |
| Isaac material | Local OmniGlass, white glass/reflection colors, IOR1.47, frosting.02, thick-walled, opacity mode disabled |

The closed glass solid is the outer surface, rolled edge, inner wall and two
welded poles. It has **no disk across the mouth** and no overlapping torus.
There are 38,146 vertices and 76,288 triangles, with Euler characteristic2.
Smooth shading changes normals only; no subdivision changes the exported shape.

The cavity profile is the actual meridian vertex sequence, interpolated linearly
in z. Its circular envelope is discretized by angular chords: body lumen radius
can be up to **2.41 µm smaller** between azimuth samples. Consumers must account
for this plus contact margin and sample/particle radius. The scalar profile is
not a claim about a cooked SDF's exact zero set.

### Signed-solid mass properties

Calculated from exact JSON triangles using signed tetrahedral integration, not a
solid outer cylinder. Independently checked by a NumPy tetrahedral calculation.
Principal axes are XYZ by rotational/reflection symmetry.

- Volume: `8.075749058903386e-06 m³` (8.075749 cm³).
- Mass: `0.01800892040135455 kg` (18.008920 g).
- COM: `[3.873332308935796e-18, 7.056098239161675e-18, 0.07610319835919559] m`.
- Diagonal inertia: `[3.491880313180961e-05, 3.491880313180961e-05, 1.2846234823995876e-06] kg·m²`.
- Principal quaternion, wxyz: `[1, 0, 0, 0]`.

Blender's actual float mesh has signed bmesh volume
`8.07574893984374e-06 m³`; maximum coordinate difference versus JSON is
`7.152557379708213e-09 m`. USD uses the same float conversion. These are recorded
float-precision differences, not a rescaling.

## Delivery and exact source hierarchy

Absolute package:
`/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/chemistry_test_tube_18x150_r1_20260912/package/`.

```text
package/
  asset.usd
  deps/mdl/OmniGlass.mdl
  deps/mdl/OmniGlass_Opacity.mdl
  source/tube.blend
  source/geometry.json
  evidence/manifest.json
  evidence/static_validation.json
  evidence/blender_production.json
  evidence/blender_reopen.json
  evidence/preview_overview.png
  evidence/preview_mouth.png
```

Original producer files are also retained in the output root's `model/` directory.
Test scratch packages under `tests_*` are test fixtures, not delivery entrypoints.

```text
/World                                      Xform, defaultPrim
  /TestTube                                 Xform, dynamic RigidBodyAPI + MassAPI
    /Visual                                 Scope
      /GlassShell                           Mesh, visual + sole SDF collider
    /Looks                                  Untyped namespace container
      /TransparentTube                      Material
        /Shader                             Shader, local OmniGlass
```

Reference **`/World/TestTube`** explicitly when embedding under another prim;
the material is inside the referenced namespace. `/World` is the default prim.
Blender source hierarchy is `ASSET_Visuals` collection → `TestTube/GlassShell`.
`PREVIEW_Studio_not_asset` contains only preview camera, lights and floor and is
never exported to the USD asset.

Initial pre-promotion manifest contract at `package/evidence/manifest.json`
(current runtime status is recorded in the final promotion confirmation):

- `package_id = chemistry_test_tube_18x150_r1`
- `overall_status = runtime_pending`
- `parameter_status = engineering_geometry`
- `entrypoints = {root_usd: asset.usd, asset_entry_prim: /World/TestTube, default_prim: World}`
- `cavity_profile_m`: ascending from `[.001,0]` through `[.009,.008]` to `[.150,.009]`.
- `outer_radius_m = .009`, `max_rim_radius_m = .010`, `mouth_z_m = .150`.
- Mass/COM/inertia and source hashes as above/below.
- `static_validation = {path: evidence/static_validation.json, status: pass, asset_sha256: <asset digest>}`.
- Runtime evidence list empty; runtime, robot, heat, PBD and manufacturer-replica
  qualification claims false.

### SHA-256 byte identities

| File | SHA-256 |
|---|---|
| `asset.usd` | `4f7129da98db6d3307bb924834e97f001f6d7ce9e3fba95273bb95d6788cd757` |
| `source/tube.blend` | `96ed8e1a6c627317fe9a6afd7d78f84c3a024cf86fdfc6881eb3cfdc64ca3547` |
| `source/geometry.json` | `504b510d27610beaf59b1e2732990209d46cec582bb085df5570f920e176db67` |
| `evidence/manifest.json` (runtime-pending handoff) | `056c1add1ce4c35d77f388dc397cc21c78627650574af1a9eb1ebc5b70dfe8f6` |
| `deps/mdl/OmniGlass.mdl` | `d71555550deb30af245c0ec939c8647442df5709a2977549cad7f6ddcc8c1182` |
| `deps/mdl/OmniGlass_Opacity.mdl` | `c7083b339c08371c9d8b9acda49e61fec294d380a6ce2b81fa9419583c0ef86d` |
| `evidence/preview_overview.png` | `728947ab9fb26722a7731092bf28fa095cdd1c74947576479ae7b40721b39156` |
| `evidence/preview_mouth.png` | `6cbd1837464963ef1a7e0dd3c08150198909c04c269a537c54d8abb4e42c8b43` |

## Actual verification

All commands below ran from `/cpfs/user/zhuzihou/dev/ConvertAsset`.

1. **TDD RED:** `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_chemistry_test_tube.py`
   initially produced 1 failed/4 errors because both producer files did not exist.
2. Initial implementation runs: missing transitive MDL file caught; then plain
   pxr's unregistered PhysX schema filtering caught. The static auditor now checks
   authored `apiSchemas` tokens without starting Kit; it does not claim that this
   verifies runtime schema registration or cooking. Initial suite: 5 passed.
3. Added package evidence/hash regression before implementation: 6 passed/1 failed
   (`audit_package` absent), then implemented the read-only wrapper.
4. **Final tests:**

   ```bash
   PYTHONDONTWRITEBYTECODE=1 ./scripts/isaac_python.sh -m pytest -q -p no:cacheprovider --basetemp=outputs/chemistry_test_tube_18x150_r1_20260912/tests_final tests/test_chemistry_test_tube.py
   python -m ruff check --no-cache scripts/model_chemistry_test_tube.py scripts/build_chemistry_test_tube.py tests/test_chemistry_test_tube.py
   ```

   **7 passed in 4.00 s; Ruff: All checks passed.** The actual-delivery test ran,
   not skipped. It checks the production manifest and copied-package rejection of
   stale asset hashes and changed transitive MDL bytes. Unit tests also reject a
   convex-hull substitution for the shell SDF and a source without Blender proof.

5. **Actual Blender production (exit0):**

   ```bash
   PYTHONDONTWRITEBYTECODE=1 /cpfs/shared/simulation/zhuzihou/tools/blender-4.4.3-linux-x64/blender --background --factory-startup -t 8 --python-exit-code 1 --python scripts/model_chemistry_test_tube.py -- --out outputs/chemistry_test_tube_18x150_r1_20260912/model --render --samples 64
   ```

   Blender4.4.3 build `802179c51ccc`; Cycles CPU, 64 samples, 720×1080 each.
   Overview render/save20.02 s; mouth33.05 s. Actual `tube.blend` saved.
   bmesh checks: manifold and contiguous edges, nondegenerate faces, Euler2,
   positive signed volume, outward outer and inward-facing lumen surface normals.
   Two independent ray-casts from above the opening hit the true inner floor,
   including an off-axis ray, within10 µm of the analytic sphere.

6. **Independent-process reopen (exit0):**

   ```bash
   PYTHONDONTWRITEBYTECODE=1 /cpfs/shared/simulation/zhuzihou/tools/blender-4.4.3-linux-x64/blender --background --factory-startup -t 8 --python-exit-code 1 --python scripts/model_chemistry_test_tube.py -- --out outputs/chemistry_test_tube_18x150_r1_20260912/model --reopen
   ```

   Opened saved blend without regenerating geometry. Exact triangle-index
   equality, coordinate tolerance, identity transforms, hierarchy, source
   material, bmesh/ray checks all pass. Blend SHA before/after unchanged.

7. **USD package build (exit0):**

   ```bash
   PYTHONDONTWRITEBYTECODE=1 ./scripts/isaac_python.sh scripts/build_chemistry_test_tube.py --source outputs/chemistry_test_tube_18x150_r1_20260912/model --package outputs/chemistry_test_tube_18x150_r1_20260912/package
   ```

8. **Repeat read-only package audit (exit0, status pass):**

   ```bash
   PYTHONDONTWRITEBYTECODE=1 ./scripts/isaac_python.sh scripts/build_chemistry_test_tube.py --package outputs/chemistry_test_tube_18x150_r1_20260912/package --audit-only
   ```

   PASS: entry/default prim, metre/Z-up identity transform, one dynamic root,
   exact JSON mesh/triangles, right-handed and agreeing unit normals, mass/COM/
   inertia, sole SDF collider, material binding/output connections, neutral glass
   inputs, USD dependencies, local transitive MDL closure, and all source,
   preview, static report and manifest hash bindings. Unresolved dependencies:0.

The targeted checks are the relevant validation for these new standalone
producers; unrelated repository/paper tests were not run.

### Local visual review

Viewed both actual PNGs directly using the render-visual-reviewer protocol.
This was **not independently reviewed**; the separate-process Blender reopen
above is an independent *process* check, not a separate human/agent visual review.

| Image | Verdict | Visible evidence / limitation |
|---|---|---|
| `preview_overview.png` | WARN, usable | Entire slender tube, plain straight body, rolled lip and rounded bottom visible. Colorless reflective/transmissive appearance; strong white softbox reflection over upper body and low contrast at bottom. |
| `preview_mouth.png` | WARN, usable | Large, in-frame circular rolled edge and inner wall visible. Bright interior reflections obscure depth; image alone is not proof of lumen clearance. |

Confidence: high on visibility/framing, medium on depth readability. A future
presentation retake can use narrower side softboxes and a patterned external
backdrop, keeping asset glass unchanged. Lumen clearance is supported by actual
mesh winding and Blender ray tests rather than an inferred visual pass.

## Collision and remaining limitations

The visual `GlassShell` is the **only** collision mesh: `approximation=sdf`,
resolution512, contactOffset0.00025 m, restOffset0. The reused producer helper
also authors subgrid6, BitsPerPixel16, margin0.00035, narrow-band0.00035 and
remeshing disabled. These are authored settings, not evidence of a cooked field.
A full cylinder/convex hull would fill the lumen and is explicitly rejected by
tests. No compound convex alternative was authored or qualified.

The r6 Isaac4.5 GPU/SDF route informed this candidate; it did **not** confer r7
qualification. At150 mm extent /512, nominal voxel spacing is approximately
0.293 mm; actual cooked thin-wall/contact behaviour required the exact r7 fixture.
At the initial producer-only validation stage, no SDF cooking, PhysX dynamics,
RTX material compilation, robot grasp, liquid/PBD containment, heat/chemical
resistance, or manufacturing tolerance tests had run. Main's later r7 evidence
qualifies only the prescribed rack/bath fixtures described in the final section;
it does not establish the other capabilities or general thin-wall behaviour.
The round-bottom tube is not claimed to stand unsupported on a flat table.

## Main integration and metadata-only promotion handoff

At the initial producer handoff no promotion CLI was added: main owned the
integrated r7 report schema and scenario/embedded paths. The follow-up below
implements the now-specified contract. Use the **principle** from
`scripts/promote_fehlings_open_tube.py`, not that script's old root or PBD claims.

1. Copy the whole package, preserve relative `deps/mdl` paths, and reference
   `/World/TestTube`. Verify the embedded `asset.usd` SHA equals the digest above;
   verify both MDL digests against `evidence/static_validation.json`. Record
   actual scene dependency closure and source hashes before starting runtime.
2. Freeze the r7 integrated scene and this asset. Retain three distinct cold-start
   reports with distinct run identities, actual successful integrated checks,
   exact **same r7 scene SHA**, runtime identity and the embedded asset SHA from
   each run. Verify actual scene composition uses that embedded asset, rather
   than merely finding an unrelated matching file beside the scene. Bind other
   scene dependencies using main's integrated evidence contract as well.
3. Before promotion, repeat this producer's read-only package audit. Rehash the
   producer and embedded asset/material files. Reject missing passes, reused
   runs, old r6 reports, different scene bytes, different asset bytes or changed
   dependency bytes. Preserve the full original runtime reports and their hashes.
4. Only after those checks, copy the three reports under producer
   `package/evidence/runtime/`. Update **evidence metadata only**:
   `overall_status=pass`, `runtime_evidence` paths/hashes, exact scene hash,
   runtime version, and a narrow `qualification_scope` naming the tested
   **Fehling r7 integrated fixture and the specific checks actually passed**.
   `claims.runtime_qualified` may become true only with that explicit scope.
   Preserve `parameter_status=engineering_geometry`, mass/source/scalar hashes
   and static validation. Keep robot/heat/PBD/manufacturer claims false unless a
   separate explicit qualification exists; inherit none from r6 or the old tube.
5. Synchronize only the resulting evidence metadata into the embedded package
   when permitted by main's evidence workflow; do not resave/rebuild/normalize
   `asset.usd`, alter MDL, add physics overlays to the producer, or alter the
   tested scene. Rehash asset/material/scene bytes after metadata synchronization.
   Any required physical/geometric correction is a new candidate and requires
   new exact integrated passes.

At the initial handoff, all three runtime passes and promotion remained pending.

## Follow-up: producer-owned promotion CLI (implemented, not invoked live)

Main subsequently supplied the r7 promotion schema and authorized only these
additional source changes:

- `scripts/promote_chemistry_test_tube.py`
- `tests/test_chemistry_test_tube_promotion.py`
- Updates to this dated record, preserving the original findings above.

**This implementation-stage follow-up did not promote the live package.**
At that implementation stage, completed cold-start reports had not been supplied
to this implementer (see the later schema-correction record below). At this
follow-up's handoff the real producer manifest remained `runtime_pending`, with
SHA-256 `056c1add1ce4c35d77f388dc397cc21c78627650574af1a9eb1ebc5b70dfe8f6`.
Asset, blend, geometry JSON and both MDL SHA-256 values still match the table
above. No SimulationApp/GPU or live SF promotion was run; no commits/pushes.

### Main-reported diagnostic context, not new producer qualification

Main reported that the original rack at scale1 passed diagnostic stable seating
and actual dynamic velocity-guided extraction/reinsertion, and the authored mass
matched native properties. These findings were supplied by main, not independently
rerun or accepted as the three final integrated passes by this producer task.

Main also reported black stripes from glass shadows on the near-wall fake liquid.
The SF task materialization now adds only
`primvars:doNotCastShadows=true` on
`/World/obj_sample_tube/Visual/GlassShell`, following the r6 readability policy;
a diagnostic shadow-disabled render fixed the issue. **This override is owned by
the consumer scene**, not by the producer asset or material. The CLI never authors
or transfers that override. Reports must bind the final regenerated scene bytes
including the consumer override, not the earlier diagnostic scene. Original
Blender preview warnings and physical/engineering claim boundaries above remain
valid within their original scope.

### Plan review and preflight contract

- **Architecture:** reuse `build_chemistry_test_tube.audit_package()` lazily for
  USD/source/MDL checks. Add only an evidence promotion script; no changes to
  modeling, conversion core, producer USD, scene or renderer.
- **Completeness:** check producer and embedded package identities, static and
  Blender evidence, every required runtime gate, process/path uniqueness,
  archive conflicts, repeat promotion, CLI parsing and interrupted publication.
- **Risk:** perform all evidence/destination preflight before writing to either
  package. Write all archives in both folders before publishing success manifests.
  Use atomic per-manifest replacement preserving existing access mode; never
  overwrite different archived evidence. Two-folder synchronization is not a
  globally atomic filesystem transaction; exact-evidence retry handles a partial
  manifest publication without inventing new evidence.

Invocation arguments:

```text
--package PRODUCER_PACKAGE_DIRECTORY
--scene FINAL_SCENE_USD
--report COLD_START_1_JSON --report COLD_START_2_JSON --report COLD_START_3_JSON
```

The consumer copy is fixed by contract at
`scene.parent/deps/chemistry_test_tube_18x150_r1/`.
The CLI verifies that it is a separate existing copy, with the same asset bytes
and all immutable package files as the producer. It runs the existing static
package audit for **both copies**, including transitive local MDL hashes,
geometry/scalar contracts, manifest/static-report hash binding, Blender source
hashes and hashed previews. Additional gates require Blender4.4.3 passing
creation/reopen evidence, CPU Cycles overview/mouth production, the independent
reopen flag, and passing manifold/winding/outward/nondegenerate/lumen checks.
Unexpected entrypoints, non-engineering parameter status, unsupported inherited
robot/heat/PBD/manufacturer claims and symlinks inside either package fail closed.

Exactly three reports are required. Resolved report paths must be different.
Each report must contain:

| Field | Required value |
|---|---|
| `status` | `"pass"` |
| `runtime_version` | `"4.5.0"` |
| `glass_tube_r7` | boolean `true` |
| `package_id` | Same scene identity in all three reports, ending `_vr_r7` |
| `scene_sha256` | SHA-256 of the exact supplied final scene bytes |
| `tube_asset_sha256` | SHA-256 shared by producer and embedded `asset.usd` |
| `process_id` | Positive integer, nonmissing and different across all three reports; booleans are rejected; no legacy `pid` alias |
| `checks` | Object with all values exactly boolean `true`, including additional checks |

Required checks, at minimum:

```text
rack_stable
glass_body_mass
rack_extraction
rack_reinsertion
rack_guided_path_clear
cup_bottom_blocks
cup_wall_blocks
actual_materials
actual_geometry
sample_eight_ml
new_tube_dimensions
finite_actual_poses
complete_at_30
observation_success
reset_complete
```

Missing files/fields/checks, failed checks, truthy numeric/string values, duplicate
PIDs, old runtime/r6 identity and stale scene/asset digests are not promotable.
The consumer uses materialized geometry: the script relies on main's exact-scene
runtime reports and `actual_geometry`/`actual_materials` checks for the runtime
materialization; it does not pretend that finding a matching embedded asset file
alone demonstrates runtime success or independently inspect simulated behaviour.

### Metadata publication and retry semantics

Reports are sorted by `process_id`, making argument order irrelevant on an identical retry.
Both copies receive these compact summaries:

```text
evidence/runtime/fehling_r7_cold_1.json
evidence/runtime/fehling_r7_cold_2.json
evidence/runtime/fehling_r7_cold_3.json
```

Each includes `original_report_path`, `original_report_sha256`, `process_id`, all checks,
the exact scene/asset/package/runtime identities, and qualification scope. Large
snapshots/trajectories are omitted. Original reports are never edited; main must
retain those originals at their recorded paths (or in its evidence archive).

Only after full preflight and both copies' complete archives are present does the
CLI publish matching `evidence/manifest.json` files with:

- `overall_status = "pass"`
- `claims.runtime_qualified = true`
- `qualification_scope = "Isaac Sim 4.5 Fehling r7 rack and bath prescribed fixtures"`
- `runtime_version = "4.5.0"`
- Three `runtime_evidence` paths and `runtime_evidence_sha256` digests.
- `runtime_qualification` containing exact scene SHA, scene package ID, tube asset
  SHA, three process IDs, original report SHAs, embedded package path and local
  MDL hashes.

`parameter_status`, scalar profiles, physical parameters, source references,
static evidence and existing unrelated manifest fields are preserved.
Robot/heat/PBD/manufacturer flags remain false. No broad or inherited r6/PBD
qualification is introduced. The immutable package trees, raw reports and scene
are rehashed before and after publication.

An identical promotion is idempotent, including reordered report arguments. A
different previous qualification or different bytes at any target archive path
fails explicitly before writing. Replacing raw reports even with whitespace-only
changes changes their identity and is rejected after promotion. If publication
stops between the two atomic manifest replacements, rerunning with the same
package, scene and reports completes the synchronization. If an archive itself is
partially written, a retry fails explicitly rather than overwriting that archive;
main must investigate that incomplete file. The CLI exits nonzero on preflight or
I/O failure; a partially synchronized operation must not be treated as completed.

### How main invokes after all three final passes

The following is the **future invocation**, not an executed promotion command:

```bash
CA=/cpfs/user/zhuzihou/dev/ConvertAsset
R7=/cpfs/user/zhuzihou/dev/scenario-forge/outputs/scientific_workbench_fehlings_reducing_sugar_water_bath_vr_r7_20260912
PYTHONDONTWRITEBYTECODE=1 "$CA/scripts/isaac_python.sh" "$CA/scripts/promote_chemistry_test_tube.py" \
  --package "$CA/outputs/chemistry_test_tube_18x150_r1_20260912/package" \
  --scene "$R7/handoff/scientific_workbench_fehlings_reducing_sugar_water_bath_vr_r7/scene.usd" \
  --report "$R7/cold_start_1.json" \
  --report "$R7/cold_start_2.json" \
  --report "$R7/cold_start_3.json"
```

Wait for completed reports from all three distinct cold-start processes. Do not
substitute diagnostic reports or invoke against a still-changing scene. A
successful invocation prints JSON with `status=pass`, the exact hashes, scope,
process IDs and both manifest paths. It does not start a runtime.

### Actual follow-up tests

All tests used disposable copies under the owned ConvertAsset output root and
clearly synthetic runtime reports. No test invoked promotion on the real package
or accessed/wrote the live SF scene/embedded package.

1. **TDD RED:** new promotion suite stopped with the expected `FileNotFoundError`
   for the not-yet-created `scripts/promote_chemistry_test_tube.py`.
2. Initial implementation: **27 passed**, Ruff clean. Added publication-failure,
   matching-but-invalid Blender proof and actual CLI-on-copy checks. Combined
   promotion/geometry suites: **37 passed**.
3. A separate regression exposed `NamedTemporaryFile`'s mode600 replacing an
   existing mode644 manifest. Preserving the existing mode fixed that failure.
4. **Final verification, executed from ConvertAsset:**

   ```bash
   PYTHONDONTWRITEBYTECODE=1 ./scripts/isaac_python.sh -m pytest -q -p no:cacheprovider --basetemp=outputs/chemistry_test_tube_18x150_r1_20260912/promotion_tests_final_v2 tests/test_chemistry_test_tube_promotion.py tests/test_chemistry_test_tube.py
   python -m ruff check --no-cache scripts/promote_chemistry_test_tube.py tests/test_chemistry_test_tube_promotion.py
   ```

   **38 passed in 32.80 s** (31 promotion tests + 7 producer tests); Ruff:
   **All checks passed**. The tests cover metadata-only byte preservation,
   fixture-only claims, full failure gates, immutable evidence corruption,
   conflicting archive rejection, identical retries, interrupted manifest sync,
   archive I/O failure leaving both success claims unpublished, CLI success on
   copies, SDK-free CLI help and manifest access-mode preservation.

At this implementation-stage handoff, final runtime qualification and live
promotion remained main's pending work; see the completed promotion below.

## Integration correction: actual report field is `process_id`

Main's interface review identified that real SF reports use `process_id`, while
the initial promotion implementation and synthetic fixtures incorrectly used
`pid`. Corrected only the owned promotion script, its tests and this record.
The CLI arguments and fixture-scoped qualification remain as documented above.

Read all three actual reports **read-only** at:

```text
/cpfs/user/zhuzihou/dev/scenario-forge/outputs/scientific_workbench_fehlings_reducing_sugar_water_bath_vr_r7_20260912/cold_start_1.json
/cpfs/user/zhuzihou/dev/scenario-forge/outputs/scientific_workbench_fehlings_reducing_sugar_water_bath_vr_r7_20260912/cold_start_2.json
/cpfs/user/zhuzihou/dev/scenario-forge/outputs/scientific_workbench_fehlings_reducing_sugar_water_bath_vr_r7_20260912/cold_start_3.json
```

Observed report identities:

- `process_id`: **2841658**, **2846800**, **2851656**, respectively; no `pid` field.
- `status=pass`, `runtime_version=4.5.0`, `glass_tube_r7=true` in each report.
- `package_id=scientific_workbench_fehlings_reducing_sugar_water_bath_vr_r7`.
- Shared scene SHA-256:
  `71e38a115fc2b1e5fa8294224d16a3cc17474bc6015196e319c7d431ed460098`.
- Shared tube asset SHA-256:
  `4f7129da98db6d3307bb924834e97f001f6d7ce9e3fba95273bb95d6788cd757`.
- All 35 reported checks are boolean true, including the 15 required gates.
- Reports explicitly retain `robot_policy_success=false`; no robot claim is added.

The validator now **requires `process_id`**, retains it in each compact summary,
sorts summaries by it, and derives manifest/CLI `process_ids` arrays from it.
There is no legacy `pid` fallback. Missing/null, duplicate, boolean, string,
floating-point, zero and negative IDs are rejected, as are reports containing
only legacy `pid` in place of the required field.

### Regression and verification

1. Added `test_report_validation_uses_process_id_without_pid` and changed the
   disposable report fixture to the real field naming **before fixing the
   validator**. The test failed with the old `(pid) required` validation error.
2. Updated the validator, compact summaries, existing negative tests and current
   procedure/schema documentation to `process_id`. Added invalid-ID cases and a
   legacy-only rejection case.
3. Added optional `test_completed_sf_reports_read_only`, enabled through
   `CHEMISTRY_TUBE_R7_REPORT_DIR`. It calls **only `_read_reports`**, checks the
   actual reports against actual final-scene and producer-asset hashes, and
   verifies report/scene/asset bytes are unchanged. It never calls `promote()`.
   Without that environment variable, this optional external-evidence test skips;
   portable synthetic regression coverage still runs.
4. Executed from ConvertAsset:

   ```bash
   CHEMISTRY_TUBE_R7_REPORT_DIR=/cpfs/user/zhuzihou/dev/scenario-forge/outputs/scientific_workbench_fehlings_reducing_sugar_water_bath_vr_r7_20260912 PYTHONDONTWRITEBYTECODE=1 ./scripts/isaac_python.sh -m pytest -q -p no:cacheprovider --basetemp=outputs/chemistry_test_tube_18x150_r1_20260912/process_id_final tests/test_chemistry_test_tube_promotion.py tests/test_chemistry_test_tube.py
   python -m ruff check --no-cache scripts/promote_chemistry_test_tube.py tests/test_chemistry_test_tube_promotion.py
   ```

   **46 passed in 39.53 s, no skips; Ruff: All checks passed.** This includes
   read-only parsing/validation of all three actual completed reports, plus
   metadata-publication tests restricted to disposable package copies.

Producer asset, blend, geometry JSON, both MDLs and the pending manifest were
rehashed and still match the identities above. No SF report/scene/embedded
package or real producer metadata was modified. **No live promotion was run.**
This corrected and verified the report interface; main owned the subsequent
promotion invocation and its full live-package preflight.

## Final promotion confirmation — live producer metadata verified

Main has now successfully invoked the live promotion CLI. This documentation-only
follow-up read the live producer `package/evidence/manifest.json` and all three
retained `package/evidence/runtime/fehling_r7_cold_{1,2,3}.json` summaries directly.
They confirm:

| Field | Live promoted value |
|---|---|
| `overall_status` | `pass` |
| `claims.runtime_qualified` | `true` |
| `qualification_scope` | **Isaac Sim 4.5 Fehling r7 rack and bath prescribed fixtures** |
| `runtime_version` | `4.5.0` |
| `parameter_status` | `engineering_geometry` |
| `claims.robot_qualified` | `false` |
| `claims.heat_qualified` | `false` |
| `claims.pbd_qualified` | `false` |
| `claims.manufacturer_replica` | `false` |
| `static_validation.status` | `pass`, bound to the unchanged asset hash |

Exact promoted scene:

```text
/cpfs/user/zhuzihou/dev/scenario-forge/outputs/scientific_workbench_fehlings_reducing_sugar_water_bath_vr_r7_20260912/handoff/scientific_workbench_fehlings_reducing_sugar_water_bath_vr_r7/scene.usd
```

- Scene SHA-256 recorded in the manifest and each summary:
  `71e38a115fc2b1e5fa8294224d16a3cc17474bc6015196e319c7d431ed460098`.
- Unchanged producer asset SHA-256:
  `4f7129da98db6d3307bb924834e97f001f6d7ce9e3fba95273bb95d6788cd757`.
- Current promoted manifest SHA-256:
  `c7e667d8aa426836429674a71d8796a8cd6a102ccc28042cde23c9c5b2864a5d`.
  This supersedes the earlier **pending manifest** digest, not any asset identity.
- Process IDs: **2841658 / 2846800 / 2851656**.
- Each retained summary has **35 checks, all true**. Main reports **38 snapshots
  per original cold-start report**; compact producer summaries intentionally omit
  snapshots, retaining the original report path and SHA-256 instead.

Original-report SHA-256 identities retained by promotion:

| Cold start / process ID | Original report SHA-256 |
|---|---|
| 1 / 2841658 | `63d35644bfa33b257ecf95cf51b5f3adebd48ad45ceb0ea2bbb0fd043620cdeb` |
| 2 / 2846800 | `fa2c4d4b2d9568c47491df1c227c2ab071a1a99b29fcb8ff535e321a672cfeb5` |
| 3 / 2851656 | `14564c11c018e3fbdac53026d1c32159a0eaf7c57a901219e50cfe3c9fc099e6` |

### Rack/bath fixture outcome and runtime test adaptations

The retained reports pass `rack_stable`, `rack_extraction`, `rack_reinsertion`,
`rack_guided_path_clear` and `glass_body_mass`, along with the prescribed bath,
material/geometry, observation and reset checks. Main confirms that this uses the
**original rack at scale1**: stable seating and guided dynamic extraction/
reinsertion pass, with **no rack scaling required**. Guided prescribed-velocity
motion is not autonomous robot grasp or manipulation qualification.

Main supplied these runtime-test details, recorded here as fixture adaptations:

1. Upward commanded velocity is **0.25 m/s**, sufficient to exceed the per-step
   gravity loss during the prescribed extraction motion.
2. The inverted upper-only negative case is placed higher so the new 150 mm tube's
   rim does not touch the cup floor and unintentionally create a bottom contact.
3. Each independent contact case resets/reseats the **dynamic beaker** because
   negative wall-contact cases can displace it. These are fixture-session pose
   resets, not changes to packaged scene physics.

Main confirms package scene physics remains unchanged except for replacing the
tube. The pose-reset adaptations do not bake altered fixture poses into the
producer asset or change its mass, collision settings or material dependencies.

### Consumer rendering policy and visual-review attribution

The materialized task scene applies
`primvars:doNotCastShadows=true` to
`/World/obj_sample_tube/Visual/GlassShell`, using the same prior readability policy.
This task-level override is not a producer USD/Blender/MDL edit and grants no
additional physics qualification.

Main reports that the final images show a **transparent plain tube, rolled rim,
rounded base, readable five colors and no black stripes**. Main is reviewing
**all 29 final images**; this is an implementer/main review, **not an independent
reviewer**. This documentation updater has **not opened those final images** and
does not claim a personal visual pass. The earlier local Blender preview review
and its WARN findings remain separate historical evidence for those previews.

### Verification and remaining handoff

For this update, verified the live manifest and three compact summaries by
read-only inspection. Ran `sha256sum` on the producer asset, `source/tube.blend`,
`source/geometry.json`, both local MDLs, promoted manifest and all three compact
summaries. Asset/source/MDL hashes match the original table. Summary hashes match
the promoted manifest's `runtime_evidence_sha256` values:

```text
fehling_r7_cold_1.json  719067c06c0f84a8f312264024e6ed001936660ffcf4a7fec6340bacfc158b42
fehling_r7_cold_2.json  d288e75a53f65c409c8721d280975dd21917a735cea97c19336161b38a7357af
fehling_r7_cold_3.json  68ac7b468abcd965c73c1540c3ff2454616c872a5ef54f3ca108a206abddd12b
```

Only this dated Markdown record was edited in the confirmation step. No code,
asset, source, MDL, report, scene, shared index or memory changes were made, and no
promotion/runtime command or tests were rerun for this documentation-only update.
Main owns doc-index links, final image-review completion and SF packaging.

## Git closeout after live promotion

The post-promotion closeout reproduced two test-fixture assumptions: the actual
delivery test required `runtime_pending`, and synthetic promotion tests copied
the already-qualified live package before attempting a different qualification.
Neither failure was a defect in the frozen asset or its accepted runtime evidence.

The actual-delivery test now checks both valid lifecycle states and verifies
qualification scope, distinct process IDs and archived hashes when promoted.
Synthetic promotion tests start from a new temporary static build made from the
retained Blender model, then make per-test disposable copies. They never reset
the live package's status or overwrite live qualification reports.

With `CHEMISTRY_TUBE_R7_REPORT_DIR` pointing at the retained SF r7 output, the
producer and promotion tests pass after this correction: **46 passed** (11.37 s),
with no skips; targeted Ruff passes. Asset/source/MDL/scene bytes remain frozen.
This producer batch contains only the three tube scripts, two test files, this
record and its two doc-index entries. Indexed-source validation is recorded by
the consumer Git-closeout handoff; the tested source dependencies are already
tracked in ConvertAsset.
