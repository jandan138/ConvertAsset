# Glass webpage-standard six-asset admission

Date: 2026-08-19

## Outcome

Six source-bound dynamic packages were admitted under
`outputs/scientific_workbench_glass_web_standard_20260819/packages/`.

Four existing vessels use explicit `aan.visual_material_profile.v2` profiles:

- `graduated_cylinder_250ml_glass_web_standard_v1`;
- `beaker_325ml_glass_web_standard_v1`;
- `flat_bottom_flask_250ml_29_42_glass_web_standard_v1`; and
- `beaker_dynamic_glass_web_standard_v1`.

The formal profile authors the six producer ClearBorosilicate inputs plus the
three values that the public Scenario Forge webpage reference inherited from
its prior glass material: `enable_opacity=false`, `cutout_opacity=0.0`, and
`roughness_texture_influence=1.0`. All four profiles therefore record the
complete nine-input visual state instead of relying on an inherited layer.

The graduated cylinder keeps `thin_walled=false`. Its body, inner bottom,
spout, rim, and requested outer hexagonal base all use the formal material.
Fixed-camera Isaac 4.1 evidence shows a legible transparent cylinder without
the black axial result seen in the incomplete six-input v2 candidate.

## Original SimReady route

The reagent bottle and Erlenmeyer flask do not receive a visual-material
override:

- `reagent_bottle_90x55_original_simready`;
- `erlenmeyer_flask_250ml_90x35_original_simready`.

`scripts/build_scientific_workbench_glass_web_standard_inputs.py` extracts the
producer's exact `simready/*.usdc` file and its exact relative
`source_usd/*.usdc` dependency from the hash-locked
`manual_glassware_v1.tar.gz`. The package preserves the producer-authored
ClearBorosilicate, GroundGlass, markings, GeomSubset membership, and material
bindings. AAN mirrors the Isaac 4.1 OmniGlass runtime dependency into the
package but does not rewrite the producer's material parameters.

This route removes the opaque white bottle neck produced by the rejected v2
facade, which retained an opaque PreviewSurface ground-glass material from the
Blender source layer instead of the producer SimReady GroundGlass material.

## Evidence

All six manifests report `overall_status: pass`, no blocked reasons, clean
dependency closure, and Isaac Sim 4.1 runtime smoke pass. The four explicit
override packages also contain
`evidence/visual_material_only_audit.json`. The two original-material packages
report `visual_material_profile.status: not_requested` and
`visual_preservation_fingerprint.status: pass`.

Scenario Forge owns the fixed-room visual comparison and final human-style
visual review. This record does not claim robot-policy, liquid containment or
transfer, physical-parameter calibration, task readiness, or benchmark
success.
