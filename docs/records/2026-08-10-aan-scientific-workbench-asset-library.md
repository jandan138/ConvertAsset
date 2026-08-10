# AAN Scientific Workbench Asset Library Admission

Date: 2026-08-10

## Request and investigation

Scenario Forge requested source-bound packages for newly supplied rigid and
support assets needed by Scientific Workbench Tasks 4, 7, 8, 14, and 15. The
source archive contained geometry but did not by itself establish task-scale
interaction semantics, support, material behavior, or runtime stability.

The admission work examined the source hierarchy, visual material path,
candidate rigid root and colliders, task-facing frames, and the 50 mL tube/rack
fit. The rack could not be accepted from visual similarity alone, so its uniform
scale was selected by a dedicated fixed-rack insertion protocol.

## Design decisions

Object interaction profile v2 adds optional, authoritative cylindrical
`interaction_regions`. A region binds to an existing named frame and declares
its body-local axis, radius, half-height, and purpose (`containment` and/or
`tool_motion`). The authored region participates in the interaction-contract
closure digest; consumers cannot change it without invalidating the manifest.

The runtime qualifier now treats closed or non-open-top objects according to
their declared contract. Aperture/opening-frame probes become not applicable,
and non-required probes do not block admission. Stable support uses the declared
body-up direction for non-open-top assets. These are contract-general changes,
not per-asset warning suppression.

The visual profile accepts an explicit `usd_preview_surface` mode for assets
whose portable appearance is authored directly in USD. This was used for the
red tube cap. The transparent tube body and beaker retain source-bound visual
profiles rather than downstream material patches.

## Delivered packages

The source-bound delivery is rooted at:

```text
outputs/scientific_workbench_asset_library_20260810/
```

It contains packages for:

- transparent beaker r3 with an authoritative interior interaction region;
- 300 mm glass stirring rod;
- 50 mL centrifuge-tube body and red cap;
- aluminum tube rack at uniform scale k=1.25;
- magnetic stir bar;
- analytical balance as `static_support`;
- Petri dish;
- 250 mm micro-spatula as `visual_static`.

The dedicated rack/tube report is:

```text
outputs/scientific_workbench_asset_library_20260810/
  evidence/tube_rack_k125_50ml_fit/report.json
```

It passed the recorded protocol with 12 bottom contacts and no side
penetration. This evidence selects k=1.25 for the delivered rack/tube pair; it
does not authorize consumer-side rescaling.

## Consumer contract

Scenario Forge must consume `package/manifest` pairs through the strict handoff
loader. It must not add asset-specific colliders, scale, mass, inertia, material
repairs, or PhysX-warning suppression. The analytical balance owns only its
qualified static-support behavior; buttons and display are noninteractive. The
micro-spatula is visual static and cannot support a dynamic transfer claim.

## Testing

Focused profile, authoring, material, and runtime-qualification tests:

```text
python -m pytest -q \
  tests/test_object_interaction_profile_v2.py \
  tests/test_visual_material_profile.py \
  tests/test_asset_application_normalizer_object_interaction_profile.py \
  tests/test_asset_application_normalizer_interaction_runtime_qualification.py

33 passed
```

Repository-wide regression:

```text
python -m pytest -q
804 passed, 4 skipped
```

Isaac Sim 4.1 runtime qualification and the rack/tube fit protocol are retained
inside the delivered output manifests and evidence report.

## Open issues and claim boundary

These packages establish only their recorded asset-role, material, collider,
support, reset, and interaction-region gates. They do not establish robot
reachability, grasp or insertion policy success, threaded closure, stirring,
liquid transfer, weighing, benchmark score, or full-scene physical consistency.
Those capabilities remain downstream task evidence.
