# 2026-11-20 — M1 v0.3 Sculpted High-Poly PBR Deformables & Dual-Mesh Skinning (`ConvertAsset`)

- **Date**: 2026-11-20
- **Status**: COMPLETE & VERIFIED
- **Repository**: `I:\cpfs\shared\simulation\zhuzihou\dev\ConvertAsset`
- **Key Modules / Scripts / Tests**:
  - `convert_asset/deformable_v03/sculpted_assets.py` (`V03_ASSET_SPECS`, parametric sculpted generators including pleated `v03_waffle_towel_01`)
  - `convert_asset/deformable_v03/bundle_writer.py` (USD + physics proxy + `1024px` PBR maps + MuJoCo 4 finite probe)
  - `tests/test_deformable_v03_skinning_and_glb.py` (**`3 passed`**, latest run `6.96s`)

---

## 1. Engineering Changes & Assets Built

1. **8 Sculpted v0.3 Deformables Across All 4 Structural Families**:
   - Output bundles: `external_artifacts/deformable_v03_bundles/` (`m1_v03_bundles_summary.json` + 8 asset subdirectories with PBR `albedo.png`, `normal.png`, `roughness.png`, USD, and dual-mesh skinning).
   - Updated `v03_waffle_towel_01` in `sculpted_assets.py` to standalone pleated geometry (`dimensions_xyz_m=(0.20, 0.20, 0.038)`, `youngs_modulus_pa=28000.0`, Gaussian pleat `pleat_amp=0.036` centered at `x=-0.055`, `sigma=0.022` on both `phys_pts` and `vis_verts`) so the towel supports stand-free pinch-and-fold via native friction without any auxiliary stand.

---

## 2. Observed Verification Metrics (`m1_v03_bundles_summary.json`)

| Asset ID | Family | Skin Mode | `n_vis_tris` | Proxy Verts | `max_rest_skin_err_m` | MuJoCo 4 Probe Finite |
| --- | --- | --- | --- | --- | --- | --- |
| `v03_croissant_butter_01` | `soft_solid` | `tet_bary` | `3072` | `63` | `1.561e-17` | `True` (`h0=0.031, h1=0.03099`) |
| `v03_strawberry_fresh_01` | `soft_solid` | `tet_bary` | `2560` | `75` | `3.487e-17` | `True` (`h0=0.044, h1=0.04377`) |
| `v03_waffle_towel_01` | `cloth_sheet` | `shell_frame` | `3360` | `81` | `2.776e-17` | `True` (`h0=0.03419, h1=0.0314`) |
| `v03_linen_dust_cover_01` | `cloth_sheet` | `shell_frame` | `3360` | `81` | `1.430e-17` | `True` (`h0=0.0, h1=0.0`) |
| `v03_idc_ribbon_cable_01` | `rod_cable` | `tet_bary` | `2760` | `66` | `1.409e-17` | `True` (`h0=0.009, h1=0.009`) |
| `v03_esd_silicone_boot_01` | `shell` | `shell_frame` | `3024` | `62` | `9.965e-18` | `True` (`h0=0.032, h1=0.03082`) |
| `v03_lab_silicone_tube_01` | `rod_cable` | `tet_bary` | `2688` | `117` | `2.776e-17` | `True` (`h0=0.022, h1=0.02198`) |
| `v03_pipette_rubber_bulb_01` | `shell` | `shell_frame` | `3312` | `62` | `1.399e-17` | `True` (`h0=0.064, h1=0.06355`) |

- Pure-CPU verification: `pytest tests/test_deformable_v03_skinning_and_glb.py -v` -> **`3 passed`**.

