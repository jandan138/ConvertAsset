# 2026-07-14 AAN DryingBox Dynamic Physics Profile

## Why this record exists

The 2026-07-13 delivery intentionally admitted raw `DryingBox_03` only as
`visual_static`: it preserved the appearance for a Scenario Forge background
object by removing physics from the ConvertAsset-owned output package. That was
the safe role for the then-current use case, but it was not a repair of the
original dynamic physics.

This record documents the separate dynamic-physics admission path. The goal is
not to put a DB03-only number into a scene patch. It is to make the physical
interpretation, the parameter source, package ownership, static admission, and
Isaac Sim runtime evidence all explicit, so a future measured parameter set can
replace the current candidate without changing LabUtopia or Scenario Forge.

## Scope and immutable source

| Field | Value |
|---|---|
| Raw source | `/cpfs/shared/simulation/zhuzihou/dev/LabUtopia/outputs/usd_asset_packages/lab_001_localized_20260707/lab_001.usd` |
| Raw source SHA-256 | `b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2` |
| Family scopes | `/World/DryingBox_01`, `/World/DryingBox_02`, `/World/DryingBox_03`, `/World/DryingBox_04` |
| Profile | `profiles/physics/labutopia_lab001_dryingbox_20260707.provisional.json` |
| Profile identity | `labutopia.lab_001.dryingbox.20260707.provisional@r1` |
| Profile SHA-256 | `37b1024418fbcfcf3c3148cce9daf96437d0b3cf157f0c4a0a6b4723b24b8940` |
| Quality tier | `provisional_geometry` |

The source SHA-256 was checked before and after packaging and is unchanged. The
raw LabUtopia USD is never edited. ConvertAsset copies the profile into the
package and authors changes only into the package-owned overlay.

## What the old evidence did and did not prove

The retained `DryingBox_01_overlay` evidence was a valid test of an already
repaired EBench overlay at its declared overlay scope. It was nevertheless
incorrect to use that result as support for a broad “DryingBox
normalization-ready” claim: the source hash, scope, and physics authoring were
not the raw 20260707 LabUtopia family.

The safe historical wording remains:

> Retained readiness evidence applies only to the pre-repaired
> `DryingBox_01_overlay` source and its declared overlay prim scope. It does
> not establish normalization readiness for the raw LabUtopia `lab_001.usd`
> DryingBox family.

The new dynamic evidence is also deliberately scoped. It establishes a
ConvertAsset-owned package with explicit provisional physics for the declared
scope; it does not turn the immutable raw source ledger from blocked to clean,
and it does not establish calibrated real-world physics.

## Root cause: physical frame drift plus invalid auto-mass inputs

The raw stage uses `metersPerUnit=1`, `kilogramsPerUnit=1`, Z-up, 60 time codes
per second, and 24 frames per second. The old package entry layer contained only
`defaultPrim` and sublayers. A composed entry stage therefore fell back to USD
defaults of `0.01` metres per unit, Y-up, and 24 time codes per second.

That is a physical bug, not a harmless metadata difference. The same numeric
mesh coordinates, COM, mass, and inertia are interpreted in a different frame;
a geometry-based repair could be numerically positive while describing an object
100 times too small. It also changes the interpretation of gravity direction.

The raw DB03 representative bodies have RigidBody, Collision, and MassAPI
semantics, but door and handle have no effective positive mass, the base has an
authored mass with invalid inertia/COM/axes, and the density authoring is not a
valid automatic-mass input at the raw stage scale. PhysX consequently reports
negative-mass and small-sphere/inertia fallback warnings. The same class of
defect appears across the actual DB01--DB04 family; this is not a synthetic
fixture finding.

## Design: a source-bound, package-owned physics profile

The dynamic path is a five-part contract:

```text
raw source SHA + stage metrics
  -> exact profile resolution for every active rigid body
  -> package-owned full mass-property bundles
  -> static physical-frame/provenance admission
  -> Isaac 4.1 runtime and scoped PhysX-warning admission
```

### 1. Preserve the stage physical frame

`asset.usd` now explicitly authors the source stage metrics. Static admission
compares source and composed-package `metersPerUnit`, `kilogramsPerUnit`,
`upAxis`, time codes per second, and frames per second. It also compares the
declared scopes' world bounds after converting them to metres. Any mismatch
blocks the package.

### 2. Bind input data to the exact source

The JSON schema is `aan.physics_profile.v1`. A profile must bind the raw source
SHA-256 and stage metrics, then exactly match every active rigid body below the
declared package scope. An unmatched body, ambiguous rule, invalid profile
field, source hash mismatch, or metric mismatch is a hard block. There is no
automatic `bbox_shell_density_template_v1` fallthrough for Scenario Forge
dynamic admission.

The profile carries a complete `mass_properties` bundle rather than unrelated
per-attribute patches:

- mass and diagonal inertia are canonical SI values;
- COM is explicitly `body_local_usd`;
- principal axes have a declared quaternion;
- once the explicit bundle is present, the strong package-owned overlay authors
  `physics:density = 0` to disable the invalid auto-compute input; it does not
  delete or ValueBlock the source density;
- provenance records profile/source hashes, revision, SI-to-USD conversion,
  quality tier, and the mass basis used for inertia.

The profile is read as immutable bytes exactly once. AAN hashes those bytes,
parses and resolves that same payload, authors from the resolved payload, then
copies the same bytes to `physics/profile.json` and rechecks the packaged hash.
A parse/author/copy hash disagreement blocks admission rather than allowing an
edited profile file to race into the package.

If source mass is already positive and finite but inertia is absent or invalid,
the profile uses `preserve_authored_mass`. It retains that source mass and
authors inertia/COM/axes against the retained mass. The profile must also state
positive finite `authored_mass_kg`; AAN converts the currently authored
`physics:mass` through the stage's `kilogramsPerUnit` and requires an exact
within-tolerance match before it accepts that inertia basis. It must not swap in
a template mass simply to make an inertia calculation convenient.

`provisional_geometry` requires an explicit claim boundary and replacement
contract, but is not a measurement. To declare `approved_estimate` or
`measured`, a future profile must name SHA-256-hashed evidence artifacts; an
approved estimate additionally needs review metadata (`approved_by`,
`reviewed_at`), while a measured profile needs measurement metadata (`method`,
`recorded_at`). A mixed-tier profile retains the strict provisional claim
boundary for the whole asset. These checks require traceable artifact/hash and
metadata fields; a tier label or a syntactically valid hash is not, by itself,
automatic proof that the underlying measurement is physically correct.

### 3. Keep the repair in the package

The package is layered as follows:

```text
asset.usd                         # defaultPrim + preserved stage metrics
  subLayers = [
    overlays/physics_profile.usda, # ConvertAsset-owned strong overlay
    deps/usd/scoped_source.usda    # package-local dynamic snapshot
  ]
physics/profile.json              # immutable packaged copy of input profile
```

Scenario Forge consumes this package and manifest. It does not add a local
mass/inertia/COM fix, a physics API deletion, or a warning suppressor.

### 4. Treat topology as part of the repair

The first trial marked the body/base as kinematic. Isaac Sim reported that the
existing articulated/joint configuration does not support a kinematic body and
also exposed static-joint failures. The final provisional profile instead keeps
the base as `dynamic` and relies on the existing fixed joint to its
collision-only static anchor. This is a runtime-validated topology decision,
not a claim that the asset has a calibrated, controllable articulation.

The profile's `motion_role` is data (`dynamic` or `fixed_child` for this family)
rather than a name-specific code path. DB04's non-uniform scale is handled by
its explicit profile bundle; the normalizer does not infer its inertia from a
world AABB with identity axes.

### 5. Verify the instantiated runtime, not only a USD file

Isaac runtime evidence is metric-aware: the smoke world reads the composed
stage's `metersPerUnit`. It records transforms for each scoped rigid body,
runs 120 physics frames, performs two reset cycles, and requires finite state
and reset restoration. The warning gate parses only three blocking classes:

- `negative mass`;
- `invalid inertia`; and
- `small sphere approximated inertia`.

When the package is instantiated at a different absolute path, ConvertAsset can
consume the consumer's log with `--runtime-physx-log` plus repeated
`--runtime-scope-binding PACKAGE_SCOPE=RUNTIME_SCOPE`. The external log always
requires an explicit complete one-to-one binding; a non-identity binding without
that log blocks admission. The resulting external consumer-log gate is conjoined
with the direct package gate, rather than replacing it. Matching is exact-prefix,
so `DryingBox_03` cannot accidentally match `DryingBox_030`; unparseable or
ambiguous warnings fail closed. This is ConvertAsset evidence parsing, not a
Scenario Forge repair or warning suppressor.

## Family coverage and static admission

The profile covers the real raw family, not only DB03:

| Scope | Active rigid bodies | Profile result |
|---|---:|---|
| DB01 | 4 | exact coverage |
| DB02 | 3 | exact coverage |
| DB03 | 3 | exact coverage |
| DB04 | 4 | exact coverage |
| **Total** | **14** | **14/14 exact; zero output-invalid bodies** |

The family static package manifest passes dynamic physics admission: source and
package metrics/bounds match, profile admission has 14 resolved bodies with no
unmatched or ambiguous body, and the output bundles are positive, finite and
fully attributed. The raw-source audit remains separately blocked with the
original 14 invalid bodies. This distinction prevents output repair from
laundering the raw source into a false source-family pass.

The rules live in
`profiles/physics/labutopia_lab001_dryingbox_20260707.provisional.json`; there
is no DB02/DB03/DB04 special branch in ConvertAsset normalizer code. The profile
uses data selectors, including one family regex for DB01/DB03 and explicit scope
rules where their topology differs.

## DB03 runtime evidence

The dedicated DB03 physics package at `/World/DryingBox_03` recorded the
following Isaac Sim 4.1 results in Kit
`4.1.0-rc.7+4.1.14801.71533b68.gl`:

| Gate | Result |
|---|---|
| Cold load | pass |
| Render readback | pass |
| Physics step | pass; 120 frames |
| Reset | pass; two cycles |
| Dynamic visual-preservation fingerprint | pass; scoped mesh visibility, material bindings, and world transforms match source composition |
| Scoped negative-mass / invalid-inertia / small-sphere gate | pass; all candidate counts are zero |
| Warning diff | baseline scoped 12, candidate scoped 0, removed 12, introduced 0 |

The raw source SHA-256 remained
`b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2`.
The physics-focused DB03 manifest is `pass`; that result is evidence that the
declared dynamic physics package loads, renders, steps, resets, and no longer
emits the three scoped mass/inertia warning categories. The visual-preservation
pass is a USD-stage fingerprint, not a source/candidate pixel-level image
comparison; render evidence does not change the separate no-full-visual-parity
claim boundary.

## Scoped material evidence and claim boundary

The final scoped DB03 package is not material-blocked: its
`static_material_report.status` and `static_material_runtime_report.status` are
both `pass`, and its runtime compiler gate has `error_count=0` and
`mdlc_count=0`. This is scoped evidence that the package-local material closure
and compiler gate pass for `/World/DryingBox_03` in the recorded runtime.

It is still not evidence of full visual-material parity, pixel-perfect render
parity, or a family-wide material runtime result. An earlier combined
DB01--DB04 runtime composition exposed an additional MDL compiler issue; that
different family-wide composition is not used as a DB03 material failure, nor
as a family material-ready claim.

Safe wording is:

> The source-bound `provisional_geometry` profile produces a ConvertAsset-owned
> dynamic package whose recorded DB03 physics admission and scoped material
> closure/runtime compiler gates pass in Isaac Sim 4.1. It is a
> simulation-safe provisional parameter set, not a measured or calibrated
> real-physics model, and it does not claim full visual-material parity or
> family-wide material runtime readiness.

The manifest also carries machine-readable forbidden claims. For this
`provisional_geometry` profile (and for an unknown or mixed-tier profile), it
forbids claims of calibrated/BOM/CAD/real-world physical-parameter parity and
of recovering a real material density from MDL appearance names or textures.

Forbidden wording includes “the raw DryingBox family is physically calibrated,”
“the entire DryingBox family is material-runtime ready,” “full visual material
parity is proven,” “real density/mass has been recovered,” or “the old
`DryingBox_01_overlay` proves the raw family.”

## Evidence and verification

Retained artifacts are copied under
[`evidence/2026-07-14-aan-dryingbox-dynamic-physics-profile/`](evidence/2026-07-14-aan-dryingbox-dynamic-physics-profile/).
They include the profile-owned package(s), static family manifest, DB03 runtime
manifest/report, render, PhysX logs, warning diff, and source-integrity records.

The TDD regression for profile binding, metric preservation, authored-mass
preservation, exact coverage, and scope mapping is:

```bash
./scripts/isaac_python.sh -m pytest tests/test_asset_application_normalizer_dynamic_physics_profile.py -q
```

The recorded runtime command is stored verbatim in the retained manifest. Its
worker contract explicitly uses 120 step frames, two reset cycles, a 1 mm reset
tolerance, and the declared Isaac 4.1 runtime fingerprint.

## Remaining risks and next step

The current profile deliberately does not infer a real material density from
MDL appearance names. It has no BOM, weighing, wall thickness, CAD inertia, or
measured joint/friction evidence. DB02's non-closed body mesh and DB04's
non-uniform scale are precisely why generic world-AABB mass inference is not a
future calibration strategy.

To replace this candidate with real physics, publish a new source-bound profile
revision with a complete mass/inertia/COM/axes bundle and the measurement/CAD
evidence that justifies an `approved_estimate` or `measured` tier. That profile
must supply hashed artifacts plus the required review/measurement metadata;
the tier label alone has no evidentiary force. Re-run the same static and
runtime gates; do not edit the raw USD and do not add a Scenario Forge special
case.

## References

- [OpenUSD `UsdPhysicsMassAPI`](https://openusd.org/release/api/class_usd_physics_mass_a_p_i.html)
- [NVIDIA rigid-body mass requirements](https://docs.omniverse.nvidia.com/kit/docs/asset-requirements/1.11.2/capabilities/physics_bodies/physics_rigid_bodies/requirements/rigid-body-mass.html)
- [PhysX rigid-body dynamics](https://nvidia-omniverse.github.io/PhysX/physx/5.5.1/docs/RigidBodyDynamics.html)
