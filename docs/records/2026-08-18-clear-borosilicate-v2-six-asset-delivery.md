# ClearBorosilicate v2 six-asset delivery

Date: 2026-08-18

## Request

Produce source-bound visual-material packages for six glass vessels using the
reviewed clear-borosilicate appearance, explicitly including the graduated
cylinder's outer hexagonal support base. Preserve ground-glass joints,
stoppers, labels, decals, source geometry, and existing interaction physics.

## Implementation

Six `aan.visual_material_profile.v2` profiles were added under
`profiles/visual/` and normalized into:

`outputs/scientific_workbench_glass_material_v2_20260818/packages/`

The package names are:

- `graduated_cylinder_250ml_glass_v2`;
- `beaker_325ml_glass_v2`;
- `flat_bottom_flask_250ml_29_42_glass_v2`;
- `beaker_dynamic_glass_v2`;
- `reagent_bottle_90x55_glass_v2`; and
- `erlenmeyer_flask_250ml_90x35_glass_v2`.

The shared visual inputs are `glass_color=(0.99,0.998,1.0)`,
`reflection_color=(1,1,1)`, `frosting_roughness=0.035`, `glass_ior=1.47`, and
`depth=0.002`. Thick-wall assets use `thin_walled=false`.

The graduated-cylinder body, inner bottom, spout, rim, and
`/World/GraduatedCylinder250ml/Visual/Source/Hex_Base/Cylinder_004` all receive
the new material. Fixed wet-room evidence found that this tall, narrow open
shell rendered with a near-black axial reflection under Isaac Sim 4.1
RayTracedLighting when thick-volume mode was used. The cylinder alone therefore
uses `thin_walled=true`; the shared appearance inputs remain identical. This is
an explicit geometry/rendering compatibility mode, not an undeclared recipe
change.

## New manual-glassware sources

`scripts/build_scientific_workbench_glass_material_v2_inputs.py` verifies and
extracts only the reagent-bottle and Erlenmeyer source members from the
producer archive, then authors deterministic facades and source-bound physics
and interaction profiles. The source USDC files are unchanged. Clear and
ground-glass GeomSubsets remain separate; only `MAT_Borosilicate_Clear` receives
the v2 override. Existing producer compound collision proxies are preserved and
made explicit in the facade rather than replaced.

The visual-profile implementation now accepts `UsdGeom.Subset` targets in
addition to whole `UsdGeom.Mesh` targets. Validation still rejects unrelated
prim types and unresolved targets.

## Qualification and rejected result

All six final packages passed static admission and isolated Isaac Sim 4.1
runtime load/render/120-frame-step/reset smoke. Each package also has
`evidence/visual_material_only_audit.json`.

For the four pre-existing assets, that audit compares their existing
source-bound facades with the final package and confirms that physics and
interaction profiles were preserved. For the two new manual-glassware assets,
the audit proves that the package delta from the newly authored source-bound
facade is visual-only; it does not claim that the facade itself is identical to
the upstream Blender/Isaac 4.5 wrapper.

The first cylinder package using `thin_walled=false` is retained only under the
diagnostics directory as a rejected visual result. It is not the promoted
package consumed by Scenario Forge.

## Claim boundary

This delivery proves source binding, dependency closure, material compilation,
scoped load/render/step/reset behavior, and preservation of the declared
physics/interaction profiles. It does not prove robot grasp success, liquid
containment or transfer, task-policy success, benchmark success, or physical
parameter calibration. The Scenario Forge handoff intentionally registers the
assets as unqualified task instances until those task-specific gates are run.
