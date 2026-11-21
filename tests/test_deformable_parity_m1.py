"""Unit and live-bundle integration tests for M1 4-engine deformable parity."""

from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.deformable_parity import (
    BUNDLE_SCHEMA_VERSION,
    CALIBRATION_LOSS_MAX,
    VERIFICATION_LOSS_MAX,
    ProbeResponseSummary,
    build_arched_cloth_points,
    build_grid_cloth_mesh,
    build_voxel_tet_mesh,
    compute_probe_discrepancy_loss,
    compute_tet_deformation_gradients,
    edge_stretch_strain,
    evaluate_integrity_readout,
    load_rfws_asset_record,
    naive_rfws_strain_from_F,
    polar_stretch_strain_from_F,
)


def _rot_y(deg: float) -> np.ndarray:
    th = math.radians(deg)
    c, s = math.cos(th), math.sin(th)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def test_lazy_imports_clean() -> None:
    code = (
        "import sys; import convert_asset.deformable_parity; "
        "heavy = [m for m in ('pxr','genesis','mujoco','newton','warp') if m in sys.modules]; "
        "assert not heavy, f'Unexpected heavy top-level imports: {heavy}'"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_polar_stretch_and_edge_rotation_invariance() -> None:
    r35 = _rot_y(35.0)
    r90 = _rot_y(90.0)
    f_batch = np.stack([r35, r90] * 10, axis=0)

    polar = polar_stretch_strain_from_F(f_batch)
    naive = naive_rfws_strain_from_F(f_batch)

    assert polar < 1e-12
    assert naive > 0.80

    # Cloth edges under pure rigid rotation + translation
    flat, _, edges = build_grid_cloth_mesh(0.18, 0.18, grid_xy=(6, 6))
    arched = build_arched_cloth_points(flat, 0.18, arch_height_m=0.032)
    rotated = arched @ r35.T + np.array([0.05, -0.02, 0.10])
    assert edge_stretch_strain(arched, rotated, edges) < 1e-12


def test_voxel_tet_mesh_and_deformation_gradient() -> None:
    verts, tets, edges = build_voxel_tet_mesh((0.07, 0.07, 0.028), grid_xyz=(4, 4, 2))
    assert len(tets) == 4 * 4 * 2 * 5
    assert len(edges) > 0

    p0 = verts[tets[:, 0]]
    dm = np.stack(
        (verts[tets[:, 1]] - p0, verts[tets[:, 2]] - p0, verts[tets[:, 3]] - p0),
        axis=-1,
    )
    dets = np.linalg.det(dm)
    assert np.all(dets > 0.0)

    squeezed = verts.copy()
    squeezed[:, 0] *= 0.90
    rotated_squeezed = squeezed @ _rot_y(35.0).T
    f_rot = compute_tet_deformation_gradients(verts, rotated_squeezed, tets)
    polar = polar_stretch_strain_from_F(f_rot)
    naive = naive_rfws_strain_from_F(f_rot)
    assert abs(polar - 0.10) < 1e-6
    assert naive > 0.80


def test_integrity_readout_and_loss() -> None:
    ok = evaluate_integrity_readout(
        strain=0.10,
        strain_onset_a=0.15,
        strain_failure_b=0.45,
        peak_normal_force_n=12.0,
        max_normal_force_n=40.0,
    )
    assert ok["intact"] is True
    assert ok["damage_score"] == 0.0

    bad = evaluate_integrity_readout(
        strain=0.50,
        strain_onset_a=0.15,
        strain_failure_b=0.45,
        peak_normal_force_n=60.0,
        max_normal_force_n=40.0,
    )
    assert bad["intact"] is False
    assert bad["damage_score"] == 1.0

    ref = ProbeResponseSummary(
        probe_name="drop",
        finite_fraction=1.0,
        contact_fraction=0.5,
        penetration_absent=True,
        settling_ratio=0.01,
        steps_executed=180,
        dt_s=0.002,
        drop_deformation=0.20,
        recovery_ratio=0.95,
    )
    cand = ProbeResponseSummary(
        probe_name="drop",
        finite_fraction=1.0,
        contact_fraction=0.5,
        penetration_absent=True,
        settling_ratio=0.01,
        steps_executed=180,
        dt_s=0.002,
        drop_deformation=0.202,
        recovery_ratio=0.96,
    )
    loss = compute_probe_discrepancy_loss(cand, ref, probe_kind="drop")
    assert 0.0 <= loss < 0.01


def test_rfws_intake_loader(tmp_path: Path) -> None:
    asset_dir = tmp_path / "rfws_tofu_01"
    asset_dir.mkdir()
    (asset_dir / "visual.obj").write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n", encoding="utf-8")
    (asset_dir / "asset.json").write_text(
        json.dumps(
            {
                "asset_id": "rfws_tofu_01",
                "category": "tofu",
                "structural_family": "soft_solid",
                "dimensions_xyz_m": [0.06, 0.06, 0.03],
                "mass_kg": 0.11,
                "density_kg_m3": 1000.0,
                "youngs_modulus_pa": 30000.0,
                "poissons_ratio": 0.35,
                "yield_stress_pa": 4500.0,
                "plastic_strain_band": [0.15, 0.45],
                "visual_mesh_relpath": "visual.obj",
            }
        ),
        encoding="utf-8",
    )
    spec = load_rfws_asset_record(asset_dir)
    assert spec.asset_id == "rfws_tofu_01"
    assert spec.source_dataset == "RFW-S"
    assert len(spec.source_asset_sha256) == 64


@pytest.mark.parametrize(
    "asset_id",
    ["pilot_fragile_chocopie_tofu_01", "pilot_flexible_wiping_cloth_01"],
)
def test_live_four_engine_pilot_manifests(asset_id: str) -> None:
    from pxr import Usd

    bundle_dir = REPO_ROOT / "tmp" / "deformable_pilot_m1" / asset_id
    manifest_path = bundle_dir / "manifest.json"
    assert manifest_path.is_file(), f"Missing live pilot manifest at {manifest_path}"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == BUNDLE_SCHEMA_VERSION
    assert set(manifest["engines"].keys()) == {"genesis", "mujoco4", "newton18", "isaac_physx"}

    # Validate base.usda opens cleanly in OpenUSD
    base_stage = Usd.Stage.Open(str(bundle_dir / "base.usda"))
    assert base_stage is not None
    assert base_stage.GetPrimAtPath("/World/DeformableAsset").IsValid()

    # Validate every SHA-256 entry
    for rel, expected_sha in manifest["sha256_index"].items():
        fp = bundle_dir / rel
        assert fp.is_file(), f"Missing hashed file {fp}"
        actual_sha = sha256(fp.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, f"SHA mismatch for {rel}"
        if fp.suffix == ".usda":
            st = Usd.Stage.Open(str(fp))
            assert st is not None

    is_solid = asset_id == "pilot_fragile_chocopie_tofu_01"
    for eid, entry in manifest["engines"].items():
        assert entry["fit_loss_drop"] <= CALIBRATION_LOSS_MAX, f"{eid} drop loss too high: {entry['fit_loss_drop']}"
        assert entry["verify_loss_compression"] <= VERIFICATION_LOSS_MAX, (
            f"{eid} compression loss too high: {entry['verify_loss_compression']}"
        )
        assert entry["cal_passed"] is True
        assert entry["independent_passed"] is True
        assert entry["gentle_grasp"]["intact"] is True, f"{eid} false crush on rotated gentle grasp"
        assert entry["gentle_grasp"]["damage_score"] < 0.25
        assert entry["crush_counterfactual"]["intact"] is False, f"{eid} missed crush counterfactual"
        assert entry["crush_counterfactual"]["damage_score"] >= 0.25
        assert entry["parity_verified"] is True, f"{eid} parity_verified False"

        if is_solid:
            assert entry["gentle_grasp"]["polar_stretch_strain"] < 0.20
            assert entry["gentle_grasp"]["naive_f_minus_i"] > 0.50

