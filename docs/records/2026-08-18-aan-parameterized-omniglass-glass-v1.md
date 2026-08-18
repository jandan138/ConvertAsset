# Parameterized OmniGlass glass_v1 delivery

Date: 2026-08-18

## Outcome

ConvertAsset admitted four immutable, source-bound `_glass_v1` dynamic packages:

- `graduated_cylinder_250ml_glass_v1`
- `beaker_325ml_glass_v1`
- `flat_bottom_flask_250ml_29_42_glass_v1`
- `beaker_dynamic_glass_v1`

They live under
`outputs/scientific_workbench_glass_material_v1_20260818/packages/`. All four
static gates and Isaac Sim 4.1 runtime smoke gates pass. Existing source packages
and source USDs were not changed.

## Donor interpretation

`Collected_new_render_change.zip` contains a saved Task 02 runtime scene, not a
clean replacement asset. It also contains particles, scene-state edits and other
runtime content. The only admitted experience is the explicit
`/World/Looks/OmniGlass/Shader` parameter set:

| Input | Explicit value |
| --- | --- |
| `reflection_color` | `(0.86629593, 0.97533488, 0.98841697)` |
| `frosting_roughness` | `0.0` |
| `roughness_texture_influence` | `1.0` |
| `enable_opacity` | `false` |
| `cutout_opacity` | `0.0` |

The OmniGlass defaults such as IOR are runtime module defaults and are not
misreported as donor-authored values.

## Scope

The new `aan.visual_material_profile.v2` contract authors typed MDL inputs and
mirrors declared helper MDLs. `OmniGlass.mdl` and `OmniGlass_Opacity.mdl` come
from the same managed EOS Isaac Sim 4.1 environment and are package-local.

For the flat-bottom flask, the body and rolled rim change. The frosted female
ground joint intentionally remains frosted. The glass stirring rod and stopper
are outside this delivery.

## Preservation evidence

Each package contains `evidence/visual_material_only_audit.json`. The report
requires all of the following:

- source package admission and Isaac 4.1 runtime admission pass;
- the v2 profile is present;
- the visual overlay contains no geometry, xform, collision, mass or inertia
  authoring;
- packaged physics and interaction profiles are byte-identical to their
  declared pre-change inputs.

This proves a material-only package delta. It does not prove robot policy,
liquid transfer or benchmark success. Scenario Forge may consume these packages
as assets, but must not recreate the MDL conversion or patch task packages in
place.
