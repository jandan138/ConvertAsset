# Multi-liquid Hydra display-primvar compatibility

The multi-liquid producer no longer authors `primvars:displayColor` or
`primvars:displayOpacity` on PhysX ParticleSet `UsdGeom.Points` prims. Isaac
Sim 4.5 Hydra reported those authored values as unrecognized primvars during
rendered simulation. The shared ParticleSystem material is now the single
render-color authority and remains bound to every ParticleSet.

An optional request `preview_color` now overrides the shared material's
`diffuseColor`. Because one ParticleSystem has one shared material, requests
with multiple distinct preview colors are rejected instead of producing a
misleading package. Independent ParticleSets and particle groups remain
unchanged.

Runtime qualification now renders the first 60 physics steps and treats Hydra
`displayColor` or `displayOpacity` diagnostics as hard failures. The
`scientific_workbench_stir_bar_beaker_dual_liquid_hydra_compat_20260825`
package passed this Isaac Sim 4.1 gate. Its manifest records
`color_source: shared_particle_system_material` and
`particle_display_primvars_authored: false`.

This change claims render compatibility for the targeted particle primvars;
it does not claim all-scene warning freedom, robot-policy success, liquid
transfer success, or benchmark success.
