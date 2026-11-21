"""Bundle writer & MuJoCo 4.0.1 live stability verifier for v0.3 sculpted deformable assets."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np

from .pbr_textures import derive_pbr_maps_from_albedo
from .sculpted_assets import V03_ASSET_SPECS, build_sculpted_v03_asset
from .skinning import build_shell_normal_skinning, build_tet_barycentric_skinning


MUJOCO4_PYTHON = Path(r"C:\Users\Administrator\Miniconda3\envs\sim-mujoco4-py312\python.exe")


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _write_obj(path: Path, verts: np.ndarray, tris: np.ndarray, uvs: np.ndarray | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# v0.3 deformable mesh"]
    for v in verts:
        lines.append(f"v {float(v[0]):.6f} {float(v[1]):.6f} {float(v[2]):.6f}")
    if uvs is not None:
        for uv in uvs:
            lines.append(f"vt {float(uv[0]):.6f} {float(uv[1]):.6f}")
        for a, b, c in tris:
            lines.append(f"f {int(a)+1}/{int(a)+1} {int(b)+1}/{int(b)+1} {int(c)+1}/{int(c)+1}")
    else:
        for a, b, c in tris:
            lines.append(f"f {int(a)+1} {int(b)+1} {int(c)+1}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_base_usda(path: Path, spec: Any, phys_pts: np.ndarray, phys_tris: np.ndarray) -> None:
    pts_str = ", ".join(f"({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f})" for p in phys_pts)
    cnt_str = ", ".join("3" for _ in range(len(phys_tris)))
    idx_str = ", ".join(str(int(i)) for t in phys_tris for i in t)
    s_metric = "polar_stretch_q95" if spec.structural_family in ("soft_solid", "rod_cable") else "edge_stretch_q95"
    usda = f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Mesh "DeformableAsset"
    {{
        custom string deformable:assetId = "{spec.asset_id}"
        custom string deformable:structuralFamily = "{spec.structural_family}"
        custom double deformable:youngsModulusPa = {spec.youngs_modulus_pa}
        custom double deformable:poissonsRatio = {spec.poissons_ratio}
        custom string deformable:strainMetric = "{s_metric}"
        custom double deformable:strainOnsetA = {spec.strain_onset_a}
        custom double deformable:strainFailureB = {spec.strain_failure_b}
        custom double deformable:damageThreshold = {spec.damage_threshold}
        custom double deformable:maxNormalForceN = {spec.max_normal_force_n}
        int[] faceVertexCounts = [{cnt_str}]
        int[] faceVertexIndices = [{idx_str}]
        point3f[] points = [{pts_str}]
    }}
}}
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(usda, encoding="utf-8")


def _write_visual_highpoly_usda(
    path: Path,
    spec: Any,
    vis_pts: np.ndarray,
    vis_tris: np.ndarray,
    vis_uvs: np.ndarray,
) -> None:
    pts_str = ", ".join(f"({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f})" for p in vis_pts)
    cnt_str = ", ".join("3" for _ in range(len(vis_tris)))
    idx_str = ", ".join(str(int(i)) for t in vis_tris for i in t)
    uv_str = ", ".join(f"({float(u):.5f}, {float(v):.5f})" for u, v in vis_uvs)
    usda = f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Scope "Looks"
    {{
        def Material "PBRMat"
        {{
            token outputs:surface.connect = </World/Looks/PBRMat/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor.connect = </World/Looks/PBRMat/AlbedoTex.outputs:rgb>
                float inputs:roughness.connect = </World/Looks/PBRMat/RoughnessTex.outputs:r>
                normal3f inputs:normal.connect = </World/Looks/PBRMat/NormalTex.outputs:rgb>
                float inputs:metallic = 0.0
                token outputs:surface
            }}

            def Shader "PrimvarReader"
            {{
                uniform token info:id = "UsdPrimvarReader_float2"
                token inputs:varname = "st"
                float2 outputs:result
            }}

            def Shader "AlbedoTex"
            {{
                uniform token info:id = "UsdUVTexture"
                asset inputs:file = @./textures/albedo.png@
                token inputs:sourceColorSpace = "sRGB"
                token inputs:wrapS = "repeat"
                token inputs:wrapT = "repeat"
                float2 inputs:st.connect = </World/Looks/PBRMat/PrimvarReader.outputs:result>
                color3f outputs:rgb
            }}

            def Shader "RoughnessTex"
            {{
                uniform token info:id = "UsdUVTexture"
                asset inputs:file = @./textures/roughness.png@
                token inputs:sourceColorSpace = "raw"
                token inputs:wrapS = "repeat"
                token inputs:wrapT = "repeat"
                float2 inputs:st.connect = </World/Looks/PBRMat/PrimvarReader.outputs:result>
                float outputs:r
            }}

            def Shader "NormalTex"
            {{
                uniform token info:id = "UsdUVTexture"
                asset inputs:file = @./textures/normal.png@
                token inputs:sourceColorSpace = "raw"
                token inputs:wrapS = "repeat"
                token inputs:wrapT = "repeat"
                float4 inputs:scale = (2, 2, 2, 1)
                float4 inputs:bias = (-1, -1, -1, 0)
                float2 inputs:st.connect = </World/Looks/PBRMat/PrimvarReader.outputs:result>
                normal3f outputs:rgb
            }}
        }}
    }}

    def Mesh "VisualHighPoly" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {{
        rel material:binding = </World/Looks/PBRMat>
        bool doubleSided = 1
        uniform token subdivisionScheme = "none"
        int[] faceVertexCounts = [{cnt_str}]
        int[] faceVertexIndices = [{idx_str}]
        point3f[] points = [{pts_str}]
        texCoord2f[] primvars:st = [{uv_str}] (
            interpolation = "vertex"
        )
    }}
}}
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(usda, encoding="utf-8")


def verify_bundle_mujoco4(bundle_dir: Path) -> dict[str, Any]:
    """Run live MuJoCo 4.0.1 CPU settle probe on the proxy mesh (0% GPU)."""
    proxy = np.load(bundle_dir / "physics_proxy.npz", allow_pickle=False)
    man = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    spec = man["source"]
    fam = spec["structural_family"]
    pts = np.asarray(proxy["rest_points"], dtype=np.float64)
    elems = np.asarray(proxy["elements"], dtype=np.int64)
    tris = np.asarray(proxy["triangles"], dtype=np.int64)

    p_str = "  ".join(f"{p[0]:.5f} {p[1]:.5f} {p[2]:.5f}" for p in pts)
    if fam in ("soft_solid", "rod_cable"):
        dim = 3
        e_str = "  ".join(f"{t[0]} {t[1]} {t[2]} {t[3]}" for t in elems)
        el_tag = f'<elasticity young="{spec["youngs_modulus_pa"]}" poisson="{spec["poissons_ratio"]}" damping="0.06"/>'
    else:
        dim = 2
        e_str = "  ".join(f"{t[0]} {t[1]} {t[2]}" for t in tris)
        el2d = "both" if fam == "shell" else "bend"
        thick = 0.007 if fam == "shell" else 0.005
        el_tag = f'<elasticity young="{spec["youngs_modulus_pa"]}" poisson="{spec["poissons_ratio"]}" thickness="{thick}" damping="0.05" elastic2d="{el2d}"/>'

    xml = f'''<mujoco>
  <option timestep="0.002" integrator="discrete" iterations="80"><flag speculative="enable"/></option>
  <worldbody>
    <geom type="plane" size="1 1 0.1" friction="0.8 0.02 0.002"/>
    <flexcomp name="obj" type="direct" dim="{dim}" pos="0 0 0.005" point="{p_str}" element="{e_str}" mass="{spec["mass_kg"]}" radius="0.002">
      <contact condim="3" friction="1.2 0.02 0.002" selfcollide="none" solref="0.005 1"/>
      <edge equality="false"/>
      {el_tag}
    </flexcomp>
  </worldbody>
</mujoco>'''

    script = f"""
import json, mujoco, numpy as np
m = mujoco.MjModel.from_xml_string({xml!r})
d = mujoco.MjData(m)
h0 = float(d.flexvert_xpos[:, 2].max() - d.flexvert_xpos[:, 2].min()) if False else 0.0
mujoco.mj_forward(m, d)
h0 = float(d.flexvert_xpos[:, 2].max() - d.flexvert_xpos[:, 2].min())
for _ in range(150):
    mujoco.mj_step(m, d)
pts_f = d.flexvert_xpos.copy()
fin = bool(np.all(np.isfinite(pts_f)))
h1 = float(pts_f[:, 2].max() - pts_f[:, 2].min()) if fin else -1.0
print(json.dumps({{"finite": fin, "h0_m": round(h0, 5), "h1_m": round(h1, 5), "nvert": int(len(pts_f))}}))
"""
    if not MUJOCO4_PYTHON.is_file():
        raise FileNotFoundError(f"MuJoCo4 Python not found: {MUJOCO4_PYTHON}")
    proc = subprocess.run([str(MUJOCO4_PYTHON), "-c", script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout.strip().splitlines()[-1])


def build_v03_bundle(
    asset_id: str,
    bundle_dir: str | Path,
    *,
    raw_textures_dir: str | Path,
    tex_size: int = 1024,
    run_mujoco_probe: bool = True,
) -> dict[str, Any]:
    """Build complete M1 v0.3 dual-mesh + PBR texture bundle for one sculpted asset."""
    out_dir = Path(bundle_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    built = build_sculpted_v03_asset(asset_id)
    spec = built["spec"]
    phys_pts = built["phys_pts"]
    phys_elems = built["phys_elems"]
    phys_tris = built["phys_tris"]
    phys_edges = built["phys_edges"]
    vis_pts = built["vis_pts"]
    vis_tris = built["vis_tris"]
    vis_uvs = built["vis_uvs"]

    # Skinning matrix / covariant shell frame
    if spec.skin_mode == "tet_bary":
        w_skin, skin_err = build_tet_barycentric_skinning(phys_pts, phys_elems, vis_pts)
        np.savez_compressed(out_dir / "skinning.npz", mode=np.array(["tet_bary"]), w_skin=w_skin)
    else:
        skin_dict, skin_err = build_shell_normal_skinning(phys_pts, phys_tris, vis_pts)
        np.savez_compressed(out_dir / "skinning.npz", **skin_dict)

    if skin_err > 1e-4:
        raise RuntimeError(f"Skinning rest error too large for {asset_id}: {skin_err:.6e}")

    raw_tex = Path(raw_textures_dir) / spec.raw_texture_name
    tex_maps = derive_pbr_maps_from_albedo(
        raw_tex,
        out_dir / "textures",
        roughness_range=spec.roughness_range,
        out_size=tex_size,
        fallback_rgb=spec.fallback_rgb,
    )

    np.savez_compressed(
        out_dir / "physics_proxy.npz",
        rest_points=phys_pts,
        elements=phys_elems,
        triangles=phys_tris,
        edges=phys_edges,
        visual_rest_points=vis_pts,
        visual_triangles=vis_tris,
        visual_uvs=vis_uvs,
    )
    _write_base_usda(out_dir / "base.usda", spec, phys_pts, phys_tris)
    _write_visual_highpoly_usda(out_dir / "visual_highpoly.usda", spec, vis_pts, vis_tris, vis_uvs)
    _write_obj(out_dir / "engines" / "mujoco4" / "mesh.obj", phys_pts, phys_tris)
    _write_obj(out_dir / "engines" / "visual_highpoly.obj", vis_pts, vis_tris, vis_uvs)

    sha_index = {}
    for rel in (
        "base.usda",
        "visual_highpoly.usda",
        "physics_proxy.npz",
        "skinning.npz",
        "textures/albedo.png",
        "textures/normal.png",
        "textures/roughness.png",
        "engines/mujoco4/mesh.obj",
    ):
        sha_index[rel] = _sha256_file(out_dir / rel)

    s_metric = "polar_stretch_q95" if spec.structural_family in ("soft_solid", "rod_cable") else "edge_stretch_q95"
    manifest: dict[str, Any] = {
        "schema_version": "deformable_v03_bundle/v0.1",
        "asset_id": asset_id,
        "source": {
            "asset_id": spec.asset_id,
            "category": spec.category,
            "structural_family": spec.structural_family,
            "dimensions_xyz_m": list(spec.dimensions_xyz_m),
            "mass_kg": spec.mass_kg,
            "youngs_modulus_pa": spec.youngs_modulus_pa,
            "poissons_ratio": spec.poissons_ratio,
            "yield_stress_pa": spec.yield_stress_pa,
            "default_color": list(spec.default_color),
            "roughness_range": list(spec.roughness_range),
            "ai_texture_source": str(raw_tex) if raw_tex.is_file() else "fallback",
        },
        "skinning": {
            "mode": spec.skin_mode,
            "n_phys_verts": int(len(phys_pts)),
            "n_phys_elems": int(len(phys_elems)),
            "n_vis_verts": int(len(vis_pts)),
            "n_vis_tris": int(len(vis_tris)),
            "max_rest_skin_err_m": float(skin_err),
        },
        "integrity_budget": {
            "fragility_tier": spec.fragility_tier,
            "strain_metric": s_metric,
            "strain_onset_a": spec.strain_onset_a,
            "strain_failure_b": spec.strain_failure_b,
            "damage_threshold": spec.damage_threshold,
            "max_normal_force_n": spec.max_normal_force_n,
            "max_shear_force_n": round(0.75 * spec.max_normal_force_n, 2),
        },
        "sha256_index": sha_index,
        "mujoco4_probe": None,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if run_mujoco_probe:
        probe = verify_bundle_mujoco4(out_dir)
        manifest["mujoco4_probe"] = probe
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

