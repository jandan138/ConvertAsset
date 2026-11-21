"""Unit tests for ConvertAsset v0.3 dual-mesh skinning, PBR synthesis, and GLB compiler."""

from __future__ import annotations

import math
from pathlib import Path
import sys

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from convert_asset.deformable_parity.contracts import ALLOWED_STRUCTURAL_FAMILIES
from convert_asset.deformable_v03 import (
    V03_ASSET_SPECS,
    build_sculpted_v03_asset,
    build_shell_normal_skinning,
    build_tet_barycentric_skinning,
    build_v03_bundle,
    compile_glb_to_deformable_proxy,
    deform_shell_skinned_points,
    deform_tet_skinned_points,
)


def test_rod_cable_in_allowed_families_and_all_8_sculpts_valid() -> None:
    assert "rod_cable" in ALLOWED_STRUCTURAL_FAMILIES
    assert len(V03_ASSET_SPECS) == 8

    for asset_id, spec in V03_ASSET_SPECS.items():
        built = build_sculpted_v03_asset(asset_id)
        phys = built["phys_pts"]
        elems = built["phys_elems"]
        tris = built["phys_tris"]
        vis = built["vis_pts"]
        uvs = built["vis_uvs"]

        assert len(built["vis_tris"]) >= 2400, f"{asset_id} low poly count: {len(built['vis_tris'])}"
        assert len(uvs) == len(vis)
        assert abs(float(phys[:, 2].min())) < 1e-4
        assert float(np.linalg.norm(phys[:, :2].mean(axis=0))) < 0.015

        if spec.skin_mode == "tet_bary":
            # Every tetrahedron must have strictly positive volume
            p0 = phys[elems[:, 0]]
            dm = np.stack([phys[elems[:, 1]] - p0, phys[elems[:, 2]] - p0, phys[elems[:, 3]] - p0], axis=-1)
            dets = np.linalg.det(dm)
            assert np.all(dets > 1e-10), f"{asset_id} has inverted/degenerate tet: min det={dets.min()}"
            w_skin, err = build_tet_barycentric_skinning(phys, elems, vis)
            assert err < 1e-6
            # Verify rigid rotation equivariance of skinned visual mesh
            ang = 0.61
            rot = np.array(
                [
                    [math.cos(ang), -math.sin(ang), 0.0],
                    [math.sin(ang), math.cos(ang), 0.0],
                    [0.0, 0.0, 1.0],
                ],
                dtype=np.float64,
            )
            def_vis = deform_tet_skinned_points(w_skin, phys @ rot.T)
            assert float(np.linalg.norm(def_vis - vis @ rot.T, axis=1).max()) < 1e-5
        else:
            skin, err = build_shell_normal_skinning(phys, tris, vis)
            assert err < 1e-6
            ang = 0.78
            rot = np.array(
                [
                    [1.0, 0.0, 0.0],
                    [0.0, math.cos(ang), -math.sin(ang)],
                    [0.0, math.sin(ang), math.cos(ang)],
                ],
                dtype=np.float64,
            )
            def_vis = deform_shell_skinned_points(phys @ rot.T, skin)
            assert float(np.linalg.norm(def_vis - vis @ rot.T, axis=1).max()) < 1e-5


def test_build_v03_bundle_outputs_pbr_and_usda(tmp_path: Path) -> None:
    out_dir = tmp_path / "croissant_bundle"
    manifest = build_v03_bundle(
        "v03_croissant_butter_01",
        out_dir,
        raw_textures_dir=tmp_path / "missing_raw",
        tex_size=128,
        run_mujoco_probe=False,
    )
    assert manifest["skinning"]["max_rest_skin_err_m"] < 1e-6
    for rel in (
        "manifest.json",
        "base.usda",
        "visual_highpoly.usda",
        "physics_proxy.npz",
        "skinning.npz",
        "textures/albedo.png",
        "textures/normal.png",
        "textures/roughness.png",
        "engines/mujoco4/mesh.obj",
    ):
        assert (out_dir / rel).is_file(), f"Missing {rel}"

    from pxr import Usd

    stage = Usd.Stage.Open(str(out_dir / "visual_highpoly.usda"))
    prim = stage.GetPrimAtPath("/World/VisualHighPoly")
    assert prim and prim.IsValid()


def test_glb_compiler_handles_real_glb_mesh(tmp_path: Path) -> None:
    glb = Path(r"I:\cpfs\shared\simulation\zhuzihou\dev\ConvertAsset\assets\glb\output_blanket.glb")
    assert glb.is_file()
    meta = compile_glb_to_deformable_proxy(
        glb,
        tmp_path / "compiled_blanket",
        asset_id="compiled_blanket",
        structural_family="cloth_sheet",
        target_max_extent_m=0.22,
    )
    assert meta["n_vis_tris"] >= 1000
    assert meta["n_phys_verts"] >= 25
    assert meta["max_rest_skin_err_m"] < 1e-5
    assert (tmp_path / "compiled_blanket" / "skinning.npz").is_file()
    assert (tmp_path / "compiled_blanket" / "physics_proxy.npz").is_file()
