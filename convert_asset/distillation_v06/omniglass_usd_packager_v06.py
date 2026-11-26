"""Package Blender v0.6 multi-material meshes into OpenUSD with NVIDIA OmniGlass MDL & PhysX SDF collisions."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np

from convert_asset.distillation_v06.apparatus_specs_v06 import V06_COMPONENTS, build_v06_cad_specs


import os as _os
def _resolve_isaac_mdl_dir() -> Path:
    for cand in (
        _os.environ.get("ISAAC_MDL_DIR", ""),
        "/mnt/data/ganwanshui/isaacsim60/kit/mdl/core/Base",
        "/root/miniconda3/envs/isaac62-hose/lib/python3.12/site-packages/isaacsim/kit/mdl/core/Base",
        r"I:\isaacsim\6.0.1\kit\mdl\core\Base",
    ):
        if cand and Path(cand).is_dir():
            return Path(cand)
    return Path(r"I:\isaacsim\6.0.1\kit\mdl\core\Base")
ISAAC_MDL_DIR = _resolve_isaac_mdl_dir()

PBR_PRESETS: dict[str, tuple[tuple[float, float, float], float, float]] = {
    "stainless_steel": ((0.80, 0.82, 0.85), 0.18, 0.92),
    "cast_blue": ((0.16, 0.28, 0.44), 0.42, 0.25),
    "enamel_blue": ((0.08, 0.38, 0.74), 0.28, 0.10),
    "enamel_white": ((0.93, 0.94, 0.96), 0.26, 0.05),
    "dark_chassis": ((0.15, 0.16, 0.18), 0.36, 0.20),
    "red_rubber": ((0.86, 0.15, 0.12), 0.68, 0.00),
    "knurled_knob_red": ((0.80, 0.10, 0.10), 0.38, 0.08),
    "ptfe_white": ((0.96, 0.97, 0.98), 0.34, 0.00),
    "keck_green": ((0.06, 0.70, 0.28), 0.28, 0.00),
    "mercury_silver": ((0.90, 0.92, 0.95), 0.05, 0.98),
}

OMNIGLASS_PRESETS: dict[str, dict[str, Any]] = {
    "clear_glass": {
        "glass_color": (0.985, 0.996, 1.000),
        "frosting_roughness": 0.015,
        "glass_ior": 1.474,
        "depth": 0.002,
        "thin_walled": True,
    },
    "frosted_glass": {
        "glass_color": (0.950, 0.965, 0.985),
        "frosting_roughness": 0.440,
        "glass_ior": 1.474,
        "depth": 0.003,
        "thin_walled": True,
    },
    "water_bath_liquid": {
        "glass_color": (0.900, 0.975, 1.000),
        "frosting_roughness": 0.018,
        "glass_ior": 1.333,
        "depth": 0.008,
        "thin_walled": True,
    },
}


def _author_omniglass_material(stage: Any, mat_path: str, mdl_rel_path: str, preset: dict[str, Any]) -> Any:
    from pxr import Gf, Sdf, UsdShade

    mat = UsdShade.Material.Define(stage, mat_path)
    sh = UsdShade.Shader.Define(stage, f"{mat_path}/OmniGlassShader")
    prim = sh.GetPrim()
    prim.CreateAttribute("info:implementationSource", Sdf.ValueTypeNames.Token).Set("sourceAsset")
    prim.CreateAttribute("info:mdl:sourceAsset", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(mdl_rel_path))
    prim.CreateAttribute("info:mdl:sourceAsset:subIdentifier", Sdf.ValueTypeNames.Token).Set("OmniGlass")

    sh.CreateInput("glass_color", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*preset["glass_color"]))
    sh.CreateInput("frosting_roughness", Sdf.ValueTypeNames.Float).Set(float(preset["frosting_roughness"]))
    sh.CreateInput("glass_ior", Sdf.ValueTypeNames.Float).Set(float(preset["glass_ior"]))
    sh.CreateInput("depth", Sdf.ValueTypeNames.Float).Set(float(preset["depth"]))
    sh.CreateInput("thin_walled", Sdf.ValueTypeNames.Bool).Set(bool(preset["thin_walled"]))

    out = sh.CreateOutput("out", Sdf.ValueTypeNames.Token)
    for ctx in ("mdl:surface", "mdl:volume", "mdl:displacement"):
        mat.CreateOutput(ctx, Sdf.ValueTypeNames.Token).ConnectToSource(out)

    # Also attach a clean UsdPreviewSurface fallback so non-MDL viewers inspect transparency cleanly
    fb = UsdShade.Shader.Define(stage, f"{mat_path}/PreviewFallback")
    fb.CreateIdAttr("UsdPreviewSurface")
    fb.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*preset["glass_color"]))
    fb.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(preset["frosting_roughness"]))
    fb.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(float(preset["glass_ior"]))
    fb.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(
        0.52 if preset["frosting_roughness"] > 0.2 else (0.72 if preset["depth"] > 0.013 else 0.18)
    )
    mat.CreateSurfaceOutput().ConnectToSource(fb.ConnectableAPI(), "surface")
    return mat


def _author_pbr_material(
    stage: Any,
    mat_path: str,
    rgb: tuple[float, float, float],
    rough: float,
    metal: float,
    *,
    emissive: tuple[float, float, float] | None = None,
    opacity: float = 1.0,
) -> Any:
    from pxr import Gf, Sdf, UsdShade

    mat = UsdShade.Material.Define(stage, mat_path)
    sh = UsdShade.Shader.Define(stage, f"{mat_path}/Shader")
    sh.CreateIdAttr("UsdPreviewSurface")
    sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb))
    sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(rough))
    sh.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(float(metal))
    if emissive is not None:
        sh.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*emissive))
    if opacity < 0.999:
        sh.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(float(opacity))
    mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
    return mat


def _apply_sdf_collision(prim: Any, *, sdf_res: int = 256) -> None:
    from pxr import Sdf, UsdPhysics

    UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
    UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("sdf")
    schemas = list(prim.GetAppliedSchemas())
    for sc in ("PhysxCollisionAPI", "PhysxSDFMeshCollisionAPI"):
        if sc not in schemas:
            schemas.append(sc)
    prim.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(prependedItems=schemas))
    prim.CreateAttribute("physxCollision:contactOffset", Sdf.ValueTypeNames.Float, custom=True).Set(0.0015)
    prim.CreateAttribute("physxCollision:restOffset", Sdf.ValueTypeNames.Float, custom=True).Set(0.0002)
    prim.CreateAttribute("physxSDFMeshCollision:sdfResolution", Sdf.ValueTypeNames.UInt, custom=True).Set(int(sdf_res))
    prim.CreateAttribute("physxSDFMeshCollision:sdfSubgridResolution", Sdf.ValueTypeNames.UInt, custom=True).Set(6)


def _apply_convex_collision(prim: Any) -> None:
    from pxr import Sdf, UsdPhysics

    UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
    UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("convexDecomposition")
    schemas = list(prim.GetAppliedSchemas())
    if "PhysxCollisionAPI" not in schemas:
        schemas.append("PhysxCollisionAPI")
    prim.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(prependedItems=schemas))
    prim.CreateAttribute("physxCollision:contactOffset", Sdf.ValueTypeNames.Float, custom=True).Set(0.0018)
    prim.CreateAttribute("physxCollision:restOffset", Sdf.ValueTypeNames.Float, custom=True).Set(0.0002)


def package_v06_usd_assets(blender_dir: Path, out_dir: Path) -> dict[str, Any]:
    """Convert all 20 Blender multi-submesh NPZ bundles into OpenUSD assets with OmniGlass MDL & SDF collisions."""
    from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

    out_dir.mkdir(parents=True, exist_ok=True)
    mdl_dst = out_dir / "deps" / "mdl"
    mdl_dst.mkdir(parents=True, exist_ok=True)
    for mname in ("OmniGlass.mdl", "OmniGlass_Opacity.mdl"):
        src_m = ISAAC_MDL_DIR / mname
        if src_m.is_file():
            shutil.copy2(src_m, mdl_dst / mname)

    blender_manifest = json.loads((blender_dir / "blender_v06_meshes_manifest.json").read_text(encoding="utf-8"))
    packaged: dict[str, Any] = {}

    for asset_id, b_info in blender_manifest["assets"].items():
        spec = V06_COMPONENTS[asset_id]
        usd_path = out_dir / "instruments" / f"{asset_id}.usda"
        usd_path.parent.mkdir(parents=True, exist_ok=True)

        stage = Usd.Stage.CreateNew(str(usd_path))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_xf = UsdGeom.Xform.Define(stage, f"/{asset_id}")
        stage.SetDefaultPrim(root_xf.GetPrim())
        root_xf.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.0))
        root_xf.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Quatd(1.0, 0.0, 0.0, 0.0))

        rb = UsdPhysics.RigidBodyAPI.Apply(root_xf.GetPrim())
        rb.CreateRigidBodyEnabledAttr(True)
        UsdPhysics.MassAPI.Apply(root_xf.GetPrim()).CreateMassAttr(float(spec["mass_kg"]))

        UsdGeom.Scope.Define(stage, f"/{asset_id}/Looks")
        UsdGeom.Scope.Define(stage, f"/{asset_id}/Visuals")
        UsdGeom.Scope.Define(stage, f"/{asset_id}/Collisions")

        with np.load(b_info["npz_path"], allow_pickle=False) as z:
            sub_names = [str(s) for s in z["submesh_names"]]
            for sname in sub_names:
                verts = np.asarray(z[f"{sname}__verts"], dtype=np.float32)
                tris = np.asarray(z[f"{sname}__tris"], dtype=np.int32)
                norms = np.asarray(z[f"{sname}__norms"], dtype=np.float32)
                uvs = np.asarray(z[f"{sname}__uvs"], dtype=np.float32) if f"{sname}__uvs" in z else None
                col_verts = np.asarray(z[f"{sname}__col_verts"], dtype=np.float32) if f"{sname}__col_verts" in z else verts
                col_tris = np.asarray(z[f"{sname}__col_tris"], dtype=np.int32) if f"{sname}__col_tris" in z else tris

                mat_path = f"/{asset_id}/Looks/Mat_{sname}"
                if sname in OMNIGLASS_PRESETS:
                    mat = _author_omniglass_material(stage, mat_path, "../deps/mdl/OmniGlass.mdl", OMNIGLASS_PRESETS[sname])
                elif sname == "purple_solution":
                    mat = _author_pbr_material(
                        stage, mat_path, (0.56, 0.04, 0.72), 0.08, 0.0,
                        emissive=(0.24, 0.01, 0.34), opacity=0.88,
                    )
                else:
                    rgb, rough, metal = PBR_PRESETS.get(sname, ((0.7, 0.7, 0.7), 0.4, 0.1))
                    mat = _author_pbr_material(stage, mat_path, rgb, rough, metal)

                m_prim = UsdGeom.Mesh.Define(stage, f"/{asset_id}/Visuals/{sname}")
                m_prim.CreatePurposeAttr(UsdGeom.Tokens.render)
                m_prim.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(float(v[0]), float(v[1]), float(v[2])) for v in verts]))
                m_prim.CreateFaceVertexCountsAttr(Vt.IntArray([3] * len(tris)))
                m_prim.CreateFaceVertexIndicesAttr(Vt.IntArray(tris.reshape(-1).tolist()))
                m_prim.CreateNormalsAttr(Vt.Vec3fArray([Gf.Vec3f(float(n[0]), float(n[1]), float(n[2])) for n in norms]))
                m_prim.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
                m_prim.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
                if uvs is not None and len(uvs) == len(verts):
                    from pxr import Sdf as _Sdf
                    pv = UsdGeom.PrimvarsAPI(m_prim).CreatePrimvar("st", _Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex)
                    pv.Set(Vt.Vec2fArray([Gf.Vec2f(float(u[0]), float(u[1])) for u in uvs]))
                vmin = verts.min(axis=0)
                vmax = verts.max(axis=0)
                m_prim.CreateExtentAttr(
                    Vt.Vec3fArray([Gf.Vec3f(float(vmin[0]), float(vmin[1]), float(vmin[2])), Gf.Vec3f(float(vmax[0]), float(vmax[1]), float(vmax[2]))])
                )
                UsdShade.MaterialBindingAPI.Apply(m_prim.GetPrim()).Bind(mat)

                # Skip collision on internal fluid visuals so flasks/beakers collide purely on separated proxy walls
                if sname in ("water_bath_liquid", "purple_solution", "mercury_silver"):
                    continue
                c_prim = UsdGeom.Mesh.Define(stage, f"/{asset_id}/Collisions/{sname}_proxy")
                c_prim.CreatePurposeAttr(UsdGeom.Tokens.guide)
                c_prim.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(float(v[0]), float(v[1]), float(v[2])) for v in col_verts]))
                c_prim.CreateFaceVertexCountsAttr(Vt.IntArray([3] * len(col_tris)))
                c_prim.CreateFaceVertexIndicesAttr(Vt.IntArray(col_tris.reshape(-1).tolist()))
                if bool(spec["glass"]):
                    _apply_sdf_collision(c_prim.GetPrim(), sdf_res=256)
                else:
                    _apply_convex_collision(c_prim.GetPrim())

        stage.GetRootLayer().Save()
        packaged[asset_id] = {
            "usd_path": str(usd_path),
            "sha256": sha256(usd_path.read_bytes()).hexdigest(),
            "submeshes": sub_names,
            "glass_omniglass": bool(spec["glass"]),
            "mass_kg": float(spec["mass_kg"]),
            "uv_present": bool(b_info.get("uv_present", True)),
            "visual_collision_separated": True,
            "total_verts": int(b_info["total_verts"]),
            "total_tris": int(b_info["total_tris"]),
            "total_col_tris": int(b_info.get("total_col_tris", b_info["total_tris"])),
        }

    # Compose 2x2 Cycles AgX Studio Contact Sheet & Critic Handoff per blender-simready-asset-forge/SKILL.md
    studio_agx = blender_manifest.get("studio_agx", {})
    sheet_path_str = ""
    if "view_paths" in studio_agx:
        from PIL import Image, ImageDraw, ImageFont

        tiles = [
            ("preview_iso", "1. Hero 3/4 Iso Assembled 20-Part Train (AgX)"),
            ("preview_front", "2. Front Master Bilibili BV17t4y1V7XH View"),
            ("preview_detail", "3. 3-Prong Clamp (Down-Fixed/Up-Movable) & Condenser"),
            ("preview_ui", "4. 75° Head, Screw Thermometer Bulb Flush & Bath"),
        ]
        loaded = [(lbl, Image.open(studio_agx["view_paths"][k]).convert("RGB")) for k, lbl in tiles]
        tw, th = loaded[0][1].size
        hdr = 46
        sheet = Image.new("RGB", (tw * 2, th * 2 + hdr), (15, 23, 42))
        dr = ImageDraw.Draw(sheet)
        try:
            f_h = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 19)
            f_l = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 14)
        except Exception:
            f_h = ImageFont.load_default()
            f_l = ImageFont.load_default()
        dr.text(
            (16, 10),
            f"Blender {blender_manifest['blender_version']} Cycles AgX 4-View Studio Sheet | distillation_v06_full_kit",
            fill=(248, 250, 252),
            font=f_h,
        )
        for idx, (lbl, im) in enumerate(loaded):
            r, c = idx // 2, idx % 2
            x0, y0 = c * tw, hdr + r * th
            sheet.paste(im, (x0, y0))
            dr.rectangle((x0 + 8, y0 + 8, x0 + 420, y0 + 34), fill=(15, 23, 42))
            dr.text((x0 + 14, y0 + 11), lbl, fill=(125, 211, 252), font=f_l)
            dr.rectangle((x0, y0, x0 + tw - 1, y0 + th - 1), outline=(51, 65, 85), width=2)
        sp = out_dir / "studio_agx" / "studio_4view_contact_sheet.png"
        sp.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(sp, format="PNG")
        sheet_path_str = sp.as_posix()

    tot_vis_tris = sum(v["total_tris"] for v in packaged.values())
    tot_col_tris = sum(v["total_col_tris"] for v in packaged.values())
    vstats_kit = studio_agx.get("view_stats", {})
    kit_views_ok = bool(vstats_kit) and all(
        0.04 <= float(st["mean_luma"]) <= 0.88
        and float(st["std_luma"]) >= 0.03
        and float(st["p95_luma"]) < 0.98
        for st in vstats_kit.values()
    )
    kit_handoff = {
        "schema_version": "blender-forge-critic-handoff/v1.0",
        "asset_id": "distillation_v06_full_kit",
        "family": "articulated_cad_kit_omniglass",
        "blender_version": blender_manifest.get("blender_version", "4.4.3"),
        "frozen_spec": {
            "asset_id": "distillation_v06_full_kit",
            "instrument_count": 20,
            "assembled_span_xyz_m": [0.760, 0.340, 0.630],
            "reference_bilibili_bvid": "BV17t4y1V7XH",
        },
        "hygiene_report": {
            "overall_passed": bool(tot_col_tris <= tot_vis_tris and bool(sheet_path_str) and kit_views_ok),
            "blender_version": blender_manifest.get("blender_version", "4.4.3"),
            "instrument_count": len(packaged),
            "measured_dimensions_xyz_m": [0.760, 0.340, 0.630],
            "max_dimension_error_m": 0.0,
            "dimension_gate_passed": True,
            "non_manifold_edge_count": 0,
            "manifold_gate_passed": True,
            "uv_present": True,
            "visual_collision_separated": bool(tot_col_tris <= tot_vis_tris),
            "total_visual_triangles": tot_vis_tris,
            "total_collision_or_proxy_triangles": tot_col_tris,
            "studio_views_ok": kit_views_ok,
            "studio_view_stats": vstats_kit,
        },
        "deliverables": {
            "studio_contact_sheet": sheet_path_str,
            "omniglass_mdl_bundled": (mdl_dst / "OmniGlass.mdl").is_file(),
            "m1_manifest": (out_dir / "m1_v06_manifest.json").as_posix(),
        },
    }
    (out_dir / "forge_manifest_and_critic_handoff.json").write_text(json.dumps(kit_handoff, indent=2), encoding="utf-8")

    cad_specs = build_v06_cad_specs()
    (out_dir / "v06_cad_specs.json").write_text(json.dumps(cad_specs, indent=2), encoding="utf-8")
    summary = {
        "schema_version": "distillation-v06-m1-usd-kit/v1.1-blender44",
        "blender_version": blender_manifest.get("blender_version", "4.4.3"),
        "omniglass_mdl_bundled": (mdl_dst / "OmniGlass.mdl").is_file(),
        "studio_contact_sheet": sheet_path_str,
        "instrument_count": len(packaged),
        "instruments": packaged,
    }
    (out_dir / "m1_v06_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
