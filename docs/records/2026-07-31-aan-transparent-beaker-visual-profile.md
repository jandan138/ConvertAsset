# 2026-07-31 AAN Transparent Beaker Visual Profile

## Decision

Keep the screened `data_buy_BCI762450811977342-6` beaker geometry and its
existing source-bound dynamic physics/interaction profiles.  Replace only its
opaque white `gltf_material` visual binding through a new, explicit visual
profile:

```text
profiles/visual/scientific_workbench_beaker_bci762450811977342_6.transparent_glass.json
```

The profile binds only this exact mesh:

```text
/World/Beaker/Visual/Source/Obj3d66_11490791_6_932/Obj3d66_11490791_6_932
```

It is bound to the immutable beaker facade SHA-256
`b66829acfcf0fd7f83c52b25c170e8272b34811cc00a87e92bab78962f5045e6` and
packages `OmniGlass.mdl` locally.  It does not modify the source USD, mesh,
colliders, mass, inertia, rigid-body semantics, interaction frames, or task
pose.

## Why

The prior material named `shader_glass` was visually opaque: its source shader
was `gltf/pbr.mdl:gltf_material`, with `alpha_mode=0`, `base_alpha=1`, white
base colour, and a high emitter strength.  Its name was not evidence of glass.
The old LabUtopia `Beaker_01` is intentionally not substituted because it is a
different source/physical asset lineage.

## AAN behavior

`--visual-material-profile` is valid only for a Scenario Forge dynamic package.
It requires an exact source SHA, existing package-local MDL source, a named MDL
subidentifier, one or more unique absolute mesh targets, and a written claim
boundary.  AAN writes the profile copy and a dedicated visual overlay below the
physics and interaction overlays but above the immutable scoped source.

The dynamic visual-preservation check still compares all source/package
visibility and world transforms.  With a declared profile it records full
material fingerprints for audit, while excluding the intentionally changed
material binding from the equality signature.  The normal material closure
records the profile-owned package-local MDL rather than inventing source
provenance for it.

## Delivery and verification

```text
outputs/scientific_workbench_task_assets_20260731/beaker_transparent_r2/package
```

The r2 manifest reports `overall_status: pass`, no blockers, visual-profile
stage pass, material-runtime closure pass, and Isaac 4.1 runtime-smoke pass.
The runtime material-view render shows a transparent vessel.

Verification completed:

```text
./scripts/isaac_python.sh -m pytest -q tests/test_visual_material_profile.py tests/test_asset_application_normalizer_cli.py
3 passed, 36 passed

./scripts/isaac_python.sh ./main.py normalize-asset ... --gates static,runtime
pass

./scripts/isaac_python.sh -m pytest -q
785 passed, 4 skipped
```

## Claim boundary

This proves only the declared visual material profile is source-bound,
package-local, and loadable in the recorded runtime.  It does not prove liquid
appearance, refractive physical accuracy, a calibrated glass material, robot
policy success, pouring, benchmark success, or task completion.
