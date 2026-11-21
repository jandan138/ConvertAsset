"""M1 + M2 verification tests for v0.5 MorphTwin absorption in ConvertAsset."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from convert_asset.deformable_parity.contracts import DeformableSourceSpec
from convert_asset.deformable_v05 import (
    BUNDLE_SCHEMA_VERSION_V02,
    MultiEngineDeformableBundleV02,
    apply_material_morph,
    build_relaxable_carrier_graph,
    bulk_shear_from_young_poisson,
    calibrate_carrier_graph,
    compile_deformable_bundle_v02,
    evaluate_reduced_bulk_shear_energy,
    simulate_explicit_with_fracture,
    transfer_material_response,
    young_poisson_from_bulk_shear,
)
from convert_asset.deformable_v05.response_carriers import build_box_tet_grid
from convert_asset.video_deformable_intake import (
    RemoteVideoIntakeConfig,
    build_colab_worker_command,
)
from convert_asset.video_deformable_intake.synthetic_proxy import (
    run_pilot1_synthetic_intake_to_bundle,
)


def test_relaxable_carriers_decouple_bulk_and_shear_and_fracture() -> None:
    pts, tets = build_box_tet_grid((0.06, 0.06, 0.06), subdiv_xyz=(2, 2, 1))
    g_base = build_relaxable_carrier_graph(
        pts, tets, youngs_modulus_pa=20000.0, total_mass_kg=0.1, enable_carriers=False
    )
    g_mt = build_relaxable_carrier_graph(
        pts, tets, youngs_modulus_pa=20000.0, total_mass_kg=0.1, enable_carriers=True
    )
    k0, m0, _ = evaluate_reduced_bulk_shear_energy(g_mt, (0.0, 0.0))
    assert k0 > 0.0 and m0 > 0.0

    # Carrier graph must have full-rank, well-conditioned 2x2 sensitivity Jacobian A
    cal = calibrate_carrier_graph(g_mt)
    assert cal.is_well_conditioned(max_cond=25.0), f"Bad cond: {cal.condition_number}"

    # Adjusting u_bulk vs u_shear independently changes kappa/mu ratio (breaks central-force lock)
    k_b, m_b, _ = evaluate_reduced_bulk_shear_energy(g_mt, (0.8, -0.4))
    k_s, m_s, _ = evaluate_reduced_bulk_shear_energy(g_mt, (-0.4, 0.8))
    ratio_b = k_b / m_b
    ratio_s = k_s / m_s
    assert ratio_b > ratio_s * 1.05, f"Expected decoupled bulk/shear ratio shift: {ratio_b} vs {ratio_s}"

    # Central-force baseline without carriers has zero sensitivity to u_bs
    cal_base = calibrate_carrier_graph(g_base)
    assert not cal_base.is_well_conditioned()

    # Explicit simulation with excessive pull triggers irreversible spring fracture
    def _pull_force(step: int, pos: np.ndarray, vel: np.ndarray) -> np.ndarray:
        f = np.zeros_like(pos)
        top = pos[:, 2] > 0.045
        bot = pos[:, 2] < 0.015
        f[top, 2] = 180.0
        f[bot, 2] = -180.0
        return f

    sim = simulate_explicit_with_fracture(
        g_mt,
        steps=35,
        dt_s=5e-4,
        fracture_strain_threshold=0.15,
        external_force_fn=_pull_force,
    )
    assert sim["finite_ok"] is True
    assert sim["fractured_edge_count"] > 0
    assert sim["fractured_edge_ratio"] > 0.0


def test_m1_bundle_v02_compile_morph_and_cross_object_transfer(tmp_path: Path) -> None:
    croissant = DeformableSourceSpec(
        asset_id="coffee_croissant_v05",
        category="croissant",
        structural_family="soft_solid",
        dimensions_xyz_m=(0.09, 0.055, 0.045),
        mass_kg=0.065,
        density_kg_m3=292.0,
        youngs_modulus_pa=14000.0,
        poissons_ratio=0.28,
        fragility_tier="high",
    )
    silicone_boot = DeformableSourceSpec(
        asset_id="smt_esd_silicone_boot_v05",
        category="silicone_boot",
        structural_family="soft_solid",
        dimensions_xyz_m=(0.05, 0.05, 0.04),
        mass_kg=0.055,
        density_kg_m3=550.0,
        youngs_modulus_pa=42000.0,
        poissons_ratio=0.41,
        fragility_tier="low",
    )

    b_crois, m_crois = compile_deformable_bundle_v02(croissant, tmp_path / "croissant")
    b_boot, _ = compile_deformable_bundle_v02(silicone_boot, tmp_path / "boot")

    assert b_crois.schema_version == BUNDLE_SCHEMA_VERSION_V02
    assert len(b_crois.engines) == 4
    assert all(e.parity_verified for e in b_crois.engines.values())
    assert all(e.morph_calibration.is_well_conditioned() for e in b_crois.engines.values())
    assert b_crois.optional_sidecars["morphtwin_spring_3dgs"]["enabled"] is True

    # Round-trip JSON deserialization
    reloaded = MultiEngineDeformableBundleV02.from_dict(json.loads(m_crois.read_text(encoding="utf-8")))
    assert reloaded.asset_id == croissant.asset_id

    # Zero-retrain delta_q morph (soften bulk & shear by 2x, plus Poisson shift)
    morphed = apply_material_morph(
        b_crois,
        delta_q=(-math.log(2.0), -0.4),
        out_overlay_dir=tmp_path / "morphed_overlays",
    )
    for eng_id, em in morphed["engines"].items():
        assert em["roundtrip_rel_err"] <= 0.10, f"{eng_id} roundtrip err too high: {em}"
        assert Path(em["overlay_path"]).exists()

    # Cross-object material transfer: silicone_boot -> croissant
    transferred = transfer_material_response(
        donor_bundle=b_boot,
        target_bundle=b_crois,
        out_overlay_dir=tmp_path / "transferred_overlays",
    )
    assert transferred["transfer_from_asset_id"] == silicone_boot.asset_id
    for eng_id, em in transferred["engines"].items():
        assert em["effective_params"]["youngs_modulus_pa"] > croissant.youngs_modulus_pa
        assert em["achieved_poisson"] > croissant.poissons_ratio

    # Sanity check inverse continuum math
    k, m = bulk_shear_from_young_poisson(32000.0, 0.36)
    e2, nu2 = young_poisson_from_bulk_shear(k, m)
    assert abs(e2 - 32000.0) < 1e-3 and abs(nu2 - 0.36) < 1e-6


def test_m2_pilot1_synthetic_video_intake_beats_central_force_baseline(tmp_path: Path) -> None:
    res = run_pilot1_synthetic_intake_to_bundle(
        tmp_path / "pilot1",
        asset_id="real2sim_sponge_block_0001",
        true_youngs_pa=18500.0,
        true_poisson=0.39,
    )
    mt = res["morphtwin_receipt"]
    base = res["central_force_baseline_receipt"]

    # Decoupled MorphTwin inversion must recover nu far more accurately than central-force nu=0.25 lock
    assert mt["poisson_abs_error"] < 0.03
    assert base["poisson_abs_error"] > 0.10
    assert mt["poisson_abs_error"] < base["poisson_abs_error"] * 0.25
    assert mt["youngs_relative_error"] < 0.05
    assert mt["holdout_track_error_m"] < base["holdout_track_error_m"]
    assert Path(res["bundle_manifest_path"]).exists()

    cmd = build_colab_worker_command(
        RemoteVideoIntakeConfig(
            video_dir="/content/data/sponge",
            output_dir="/content/out/sponge",
            asset_id="real2sim_sponge_block_0001",
            category="sponge",
        )
    )
    assert "--asset-id real2sim_sponge_block_0001" in cmd

