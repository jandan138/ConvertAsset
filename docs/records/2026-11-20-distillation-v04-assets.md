# Engineering Record — Distillation Apparatus v0.4 Deformable & Borosilicate Glassware Assets (M1)

- **Date**: 2026-11-20
- **Repository**: `ConvertAsset`
- **Scope**: Milestone 1 (`distillation_v04` — 《蒸馏装置的装配与拆除》)

## Summary
Built and verified 4 volumetric 3D tetrahedral + barycentric-skinned UV PBR deformable asset bundles and 12 multi-material transparent borosilicate glassware OpenUSD apparatus components calibrated to standard 24/29 `1:10` ground-glass joint geometry:

1. **Volumetric 3D Deformable Bundles (`external_artifacts/distillation_v04_assets/`)**:
   - `v04_clamp_pad_01` (`soft_solid`): curved silicone clamp cushion pad.
   - `v04_ptfe_taper_sleeve_01` (`shell`): hollow `1:10` tapered PTFE anti-seize joint sleeve.
   - `v04_rubber_septum_01` (`soft_solid`): hollow annular thermometer adapter septum (`inner_r = 5.6 mm`).
   - `v04_dual_cooling_hoses_01` (`rod_cable`): paired hollow annular silicone cooling hoses (`rest_points` + `assembled_rest_points` for `distill_06` assembled initialization).
2. **Borosilicate Glassware & Lab Fixture OpenUSD Kit (`glassware/`)**:
   - `alcohol_lamp`, `iron_stand_left`, `iron_stand_right`, `iron_ring_gauze`, `distillation_flask`, `distillation_head` (`75°` side-arm lip at world `z = 1.007 m`), `mercury_thermometer`, `liebig_condenser` (`-18°` pitch, `45°`-downward `4°`-taper barbs), `tail_adapter`, `erlenmeyer_receiver`, `bench_water_ports`, `staging_trays`, plus `glassware_cad_specs.json`.

## Verification
- `pytest tests/test_distillation_v04_m1.py -v` -> `2 passed` (zero inverted tetrahedra `min det(Dm) > 0`, exact row-stochastic barycentric skinning weights, 2K PBR texture maps, and USD stage load checks).

