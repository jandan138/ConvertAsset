# Long-neck threaded 15 mL tube geometry admission

## Investigation

The reviewed source is
`scenario-forge/external_artifacts/incoming/from_wangshuai/tube.usd`, SHA-256
`0f279e39685656b508ed6b359f8dc56be099263364084e04ab812170c9ca3be0`.
Its raw root layer contains an unresolved anonymous metrics sublayer, so it is
not a portable consumer package. Static inspection found two independent
dynamic roots: an open tube body and a closed-top cap. Both visual meshes are
single-component welded manifolds with no boundary or non-manifold edges. The
body has about four external thread turns and the cap about four internal turns
at a nominal 1.9 mm pitch.

The 101 mm overall height, 83.76 mm neck start, and 23.2 mm fixed lower
boundary match the corrected long-neck non-threaded master. Because the source
has no producer manifest, this is recorded as an inferred geometry fingerprint,
not producer provenance.

## Decision

The body and cap are admitted as separate identity-root dynamic packages. This
keeps the parts usable for later task authoring without claiming they are
already tightened, locked, or jointly simulated. The source SDF collision is
preserved. Provisional family mass and inertia are applied and explicitly
labelled as unmeasured.

Liquid qualification was not requested. Reversible thread interaction remains
blocked, so Task 08 readiness stays false. No pre-closed rigid assembly is
published in this revision.

## Implementation

- `scripts/build_long_neck_threaded_tube15_packages.py` removes the unresolved
  stage sublayer through source-bound scope extraction and produces independent
  body/cap packages with identity entry roots, package-local physics material,
  SDF collision, named frames, provisional physics profiles, and a
  UsdPreviewSurface material closure produced by the existing no-MDL module.
- `scripts/qualify_long_neck_threaded_tube15_packages.py` runs three Isaac Sim
  4.1 cold starts per asset, preserves two true-contact thread probes, emits
  package manifests and promotion receipts, and supports evidence reuse when
  the reports already exist.
- `scripts/qualify_wangshuai_dynamic_assets.py` accepts the two new asset roles
  and resolves either `asset.usd` or legacy `asset.usda` package entries.

The consumer output is
`outputs/tube15_long_neck_threaded_geometry_v1_1_20260901/`. It supersedes the
initial v1 output by replacing the runtime-only `OmniPBR.mdl` dependency with a
package-local UsdPreviewSurface network. Geometry and physics are unchanged.

## Evidence

Both body and cap passed three of three dynamic cold starts in Isaac Sim 4.1.
The package manifests therefore claim `dynamic_geometry_ready=true` and
`sdf_collision_ready=true`.

Two physical thread-contact probes remain blocked:

- Default phase: 0.858 mm forward descent, 0.427 mm reverse rise, 4.83 degree
  maximum tilt.
- Authored cap phase: 2.098 mm forward descent, 0.607 mm reverse rise, 6.43
  degree maximum tilt.

The second probe demonstrates some rotation-coupled descent, but neither probe
meets the reversible thread gate. `thread_interaction_ready`, `task08_ready`,
`liquid_container_ready`, robot-policy success, and benchmark success therefore
remain false.

Local render review passed gross geometry after material closure. The renders
establish the open body, long neck, external thread shape, and closed cap top;
they do not establish polished material quality or thread functionality.

USD dependency closure reports zero unresolved paths for both v1.1 packages.

## Validation

```text
python -m pytest -q \
  tests/test_build_long_neck_threaded_tube15_packages.py \
  tests/test_qualify_long_neck_threaded_tube15_packages.py
# 3 passed

python -m ruff check \
  scripts/build_long_neck_threaded_tube15_packages.py \
  scripts/qualify_long_neck_threaded_tube15_packages.py \
  scripts/qualify_wangshuai_dynamic_assets.py \
  tests/test_build_long_neck_threaded_tube15_packages.py \
  tests/test_qualify_long_neck_threaded_tube15_packages.py
# All checks passed

python -m pytest tests/ -q
# 1121 passed, 8 skipped, 7 failed
```

All seven full-suite failures are pre-existing external-fixture availability
failures in the isolated worktree: two missing `assets/usd/chestofdrawers_nomdl`
fixtures, one missing prior r7 facade tree, one mis-resolved sibling
`scenario-forge` archive, and three missing ignored Wangshuai output fixtures.
None execute the new builder, qualifier, worker role, or package tests.

## Open issues

- A producer-authored lineage manifest is still absent.
- Mass and inertia remain provisional rather than measured.
- A future thread-capable revision needs a revised contact/collider design and
  must pass both forward descent and reverse rise without excessive tilt.
- Liquid containment and robot manipulation require separate qualification.
