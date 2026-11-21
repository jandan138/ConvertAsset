"""Unit and asset-contract tests for M1 distillation_v04 bundles & borosilicate glassware CAD (0% GPU)."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import numpy as np

from convert_asset.distillation_v04 import (
    DISTILLATION_COMPONENT_SPECS,
    V04_DEFORMABLE_SPECS,
)
from convert_asset.distillation_v04.cad_glassware_v04 import compute_nominal_apparatus_layout


_REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLES_ROOT = _REPO_ROOT / "external_artifacts" / "distillation_v04_bundles"
CAD_ROOT = _REPO_ROOT / "external_artifacts" / "distillation_v04_cad"


def _is_watertight_manifold(tris: np.ndarray) -> tuple[bool, int]:
    edge_counts: Counter[tuple[int, int]] = Counter()
    for a, b, c in tris:
        for u, v in ((int(a), int(b)), (int(b), int(c)), (int(c), int(a))):
            edge_counts[(u, v) if u < v else (v, u)] += 1
    bad = sum(1 for cnt in edge_counts.values() if cnt != 2)
    return bad == 0, bad


def test_v04_deformable_bundles_exist_watertight_positive_tet_and_pbr() -> None:
    assert set(V04_DEFORMABLE_SPECS.keys()) == {
        "v04_clamp_pad_01",
        "v04_ptfe_taper_sleeve_01",
        "v04_rubber_septum_01",
        "v04_dual_cooling_hoses_01",
    }
    for aid in V04_DEFORMABLE_SPECS:
        bdir = BUNDLES_ROOT / aid
        assert (bdir / "base.usda").is_file()
        assert (bdir / "visual_highpoly.usda").is_file()
        assert (bdir / "physics_proxy.npz").is_file()
        assert (bdir / "skinning.npz").is_file()
        assert (bdir / "manifest.json").is_file()
        for tex in ("albedo.png", "normal.png", "roughness.png"):
            assert (bdir / "textures" / tex).is_file()

        man = json.loads((bdir / "manifest.json").read_text(encoding="utf-8"))
        assert man["skinning"]["min_tet_det"] > 0.0
        assert man["skinning"]["max_rest_skin_err_m"] < 1e-6
        assert man["mujoco4_probe"]["finite"] is True

        with np.load(bdir / "physics_proxy.npz", allow_pickle=False) as zp:
            pts = zp["rest_points"]
            tets = zp["elements"]
            tris = zp["triangles"]
            vis_pts = zp["visual_rest_points"]
            p0 = pts[tets[:, 0]]
            dm = np.stack([pts[tets[:, 1]] - p0, pts[tets[:, 2]] - p0, pts[tets[:, 3]] - p0], axis=-1)
            assert float(np.min(np.linalg.det(dm))) > 0.0
            wt_ok, bad_edges = _is_watertight_manifold(tris)
            assert wt_ok, f"{aid} surface triangles not watertight (bad_edges={bad_edges})"
            if aid == "v04_dual_cooling_hoses_01":
                assert "assembled_rest_points" in zp
                apts = zp["assembled_rest_points"]
                p0a = apts[tets[:, 0]]
                dma = np.stack([apts[tets[:, 1]] - p0a, apts[tets[:, 2]] - p0a, apts[tets[:, 3]] - p0a], axis=-1)
                assert float(np.min(np.linalg.det(dma))) > 0.0

        with np.load(bdir / "skinning.npz", allow_pickle=False) as zs:
            assert str(zs["mode"][0]) == "tet_bary"
            recon = zs["w_skin"] @ pts
            assert float(np.max(np.linalg.norm(recon - vis_pts, axis=1))) < 1e-6


def test_v04_glassware_cad_coaxiality_and_barbs() -> None:
    specs = json.loads((CAD_ROOT / "glassware_cad_specs.json").read_text(encoding="utf-8"))
    assert len(specs["components"]) == len(DISTILLATION_COMPONENT_SPECS) == 12
    for cid in DISTILLATION_COMPONENT_SPECS:
        usda = CAD_ROOT / cid / "asset.usda"
        assert usda.is_file()
        txt = usda.read_text(encoding="utf-8")
        assert "UsdPreviewSurface" in txt

    layout = compute_nominal_apparatus_layout()
    assert layout["max_coaxial_error_mm"] < 0.05
    # Verify "下进上出": lower inlet barb is strictly below upper outlet barb
    assert layout["lower_inlet_barb_root_world"][2] < layout["upper_outlet_barb_root_world"][2]
    # Verify 12-wedge sockets present on hollow female glassware
    for sock_id in ("distillation_flask", "distillation_head", "liebig_condenser", "tail_adapter"):
        assert len(specs["components"][sock_id]["colliders"]["socket_wedges"]) == 12

