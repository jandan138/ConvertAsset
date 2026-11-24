"""Unit & mathematical invariant tests for HermiteTwin v0.8 in ConvertAsset."""

from __future__ import annotations

import json
import math
from pathlib import Path
import time

import numpy as np

from convert_asset.deformable_v08_hermite import (
    BUNDLE_SCHEMA_VERSION_V03,
    HermiteShellSimulator,
    HermiteShellSpec,
    MaterialSpaceContactModel,
    RigidObstacleBox,
    SpringMassShellBaseline,
    SpringMassShellConfig,
    ThinShellBundleManifestV03,
    build_hermite_shell_mesh,
    compile_thin_shell_bundle_v03,
    evaluate_dense_surface,
    render_hermite_3dgs_frame,
    run_two_stage_sysid,
)
from convert_asset.deformable_v08_hermite.bicubic_hermite_shell import (
    _local_bf_element_matrices,
    compute_shell_energy_and_grad,
)


def _rotation_matrix(axis: np.ndarray, angle_rad: float) -> np.ndarray:
    a = np.asarray(axis, dtype=np.float64)
    a = a / np.linalg.norm(a)
    K = np.array(
        [
            [0.0, -a[2], a[1]],
            [a[2], 0.0, -a[0]],
            [-a[1], a[0], 0.0],
        ],
        dtype=np.float64,
    )
    return np.eye(3) + math.sin(angle_rad) * K + (1.0 - math.cos(angle_rad)) * (K @ K)


def test_hermite_partition_of_unity_and_analytical_gradient() -> None:
    xi = np.array([0.0, 0.23, 0.5, 0.77, 1.0])
    eta = np.array([0.1, 0.4, 0.5, 0.85, 0.95])
    N, _, _, _, _, _ = _local_bf_element_matrices(xi, eta, du=0.075, dv=0.065)
    # Sum of positional basis functions (cols 0, 4, 8, 12) must equal 1 everywhere
    pos_sum = N[:, 0] + N[:, 4] + N[:, 8] + N[:, 12]
    assert np.allclose(pos_sum, 1.0, atol=1e-12)

    mesh = build_hermite_shell_mesh(
        nx=2, ny=2, length_u_m=0.20, length_v_m=0.20, area_density_kg_m2=0.3
    )
    e_rest, g_rest, _, bd_rest = compute_shell_energy_and_grad(
        mesh, mesh.rest_q, membrane_rigidity=250.0, bending_rigidity=0.05, poissons_ratio=0.30
    )
    assert e_rest < 1e-12 and bd_rest["energy_membrane"] < 1e-12 and bd_rest["energy_bending"] < 1e-12
    assert float(np.max(np.abs(g_rest))) < 1e-12
    surf_rest = evaluate_dense_surface(mesh, mesh.rest_q, eval_nu=7, eval_nv=7)
    assert np.allclose(surf_rest["vertices"][..., 2], 0.755, atol=1e-12)

    rng = np.random.default_rng(123)
    q = mesh.rest_q.copy()
    q[0::4] += rng.normal(0.0, 0.008, size=q[0::4].shape)
    q[1::4] += rng.normal(0.0, 0.03, size=q[1::4].shape)
    q[2::4] += rng.normal(0.0, 0.03, size=q[2::4].shape)

    e0, grad, K_gn, _ = compute_shell_energy_and_grad(
        mesh, q, membrane_rigidity=250.0, bending_rigidity=0.05, poissons_ratio=0.30
    )
    assert e0 > 0.0
    assert np.allclose(K_gn, K_gn.T, atol=1e-9)

    eps = 1e-6
    for idx in [(0, 2), (4, 0), (5, 2), (7, 1), (12, 2)]:
        qp = q.copy()
        qm = q.copy()
        qp[idx] += eps
        qm[idx] -= eps
        ep, _, _, _ = compute_shell_energy_and_grad(
            mesh, qp, membrane_rigidity=250.0, bending_rigidity=0.05, poissons_ratio=0.30
        )
        em, _, _, _ = compute_shell_energy_and_grad(
            mesh, qm, membrane_rigidity=250.0, bending_rigidity=0.05, poissons_ratio=0.30
        )
        fd = (ep - em) / (2.0 * eps)
        assert abs(fd - grad[idx]) < 1e-5, f"Mismatch at {idx}: fd={fd}, ana={grad[idx]}"


def test_kirchhoff_love_energy_is_so3_rotation_invariant() -> None:
    mesh = build_hermite_shell_mesh(
        nx=3, ny=3, length_u_m=0.24, length_v_m=0.24, area_density_kg_m2=0.28
    )
    rng = np.random.default_rng(7)
    q_def = mesh.rest_q.copy()
    q_def[0::4, 2] += 0.02 * np.sin(8.0 * q_def[0::4, 0])
    q_def[0::4, :2] += rng.normal(0.0, 0.004, size=(mesh.n_nodes, 2))
    q_def[1::4] += rng.normal(0.0, 0.02, size=(mesh.n_nodes, 3))

    e1, _, _, bd1 = compute_shell_energy_and_grad(
        mesh, q_def, membrane_rigidity=300.0, bending_rigidity=0.08, poissons_ratio=0.32
    )
    R = _rotation_matrix(np.array([0.4, -0.7, 0.5]), 1.13)
    q_rot = q_def @ R.T
    q_rot[0::4] += np.array([0.35, -0.22, 0.51])  # rigid translation on position DOFs only

    e2, _, _, bd2 = compute_shell_energy_and_grad(
        mesh, q_rot, membrane_rigidity=300.0, bending_rigidity=0.08, poissons_ratio=0.32
    )
    assert abs(e1 - e2) < 1e-10
    assert abs(bd1["energy_membrane"] - bd2["energy_membrane"]) < 1e-10
    assert abs(bd1["energy_bending"] - bd2["energy_bending"]) < 1e-10


def test_material_space_grasp_force_conservation_and_zero_friction_slip() -> None:
    spec = HermiteShellSpec(
        asset_id="test_cloth_01",
        structural_family="cloth_sheet",
        nx=4,
        ny=4,
        length_u_m=0.28,
        length_v_m=0.28,
        thickness_m=0.0018,
        area_density_kg_m2=0.26,
        youngs_modulus_pa=85000.0,
        poissons_ratio=0.30,
        coulomb_friction_mu=0.85,
    )
    sim_stick = HermiteShellSimulator(spec, origin_xyz=(0.0, 0.0, 0.755))
    contact_stick = MaterialSpaceContactModel(
        sim_stick.mesh,
        contact_nu=20,
        contact_nv=20,
        coulomb_friction_mu=0.85,
        table_z_m=0.755,
    )

    spec_zf = HermiteShellSpec(
        asset_id="test_cloth_01_zf",
        structural_family="cloth_sheet",
        nx=4,
        ny=4,
        length_u_m=0.28,
        length_v_m=0.28,
        thickness_m=0.0018,
        area_density_kg_m2=0.26,
        youngs_modulus_pa=85000.0,
        poissons_ratio=0.30,
        coulomb_friction_mu=0.0,
    )
    sim_zf = HermiteShellSimulator(spec_zf, origin_xyz=(0.0, 0.0, 0.755))
    contact_zf = MaterialSpaceContactModel(
        sim_zf.mesh,
        contact_nu=20,
        contact_nv=20,
        coulomb_friction_mu=0.0,
        table_z_m=0.755,
    )

    # Verify force conservation: sum of positional nodal forces equals sum of sample forces
    g_pos = np.array([-0.10, -0.10, 0.758])
    g_rot = np.eye(3)
    contact_stick.update_gripper(
        q_cur=sim_stick.q, gripper_pos_xyz=g_pos, gripper_rot_3x3=g_rot, gripper_gap_m=0.004
    )
    assert np.sum(contact_stick.sample_states == 2) > 0
    f_node, _, meta = contact_stick.evaluate_forces_and_stiffness(
        sim_stick.q, sim_stick.v, dt_s=1.0 / 60.0
    )
    # Move gripper upward slightly so non-zero force appears and verify W^T partition of unity
    contact_stick.gripper_pos = np.array([-0.10, -0.10, 0.775])
    f_node2, _, _ = contact_stick.evaluate_forces_and_stiffness(
        sim_stick.q, sim_stick.v, dt_s=1.0 / 60.0
    )
    assert np.linalg.norm(np.sum(f_node2[0::4], axis=0)) > 0.1

    # Rollout lift for sticky vs zero-friction counterfactual
    t0 = time.perf_counter()
    for step in range(36):
        alpha = max(0.0, (step - 5) / 30.0)
        gp = np.array([-0.10, -0.10, 0.758 + 0.14 * alpha])
        contact_stick.update_gripper(
            q_cur=sim_stick.q, gripper_pos_xyz=gp, gripper_rot_3x3=g_rot, gripper_gap_m=0.004
        )
        sim_stick.step(
            1.0 / 60.0,
            contact_force_and_stiffness_fn=contact_stick.evaluate_forces_and_stiffness,
            post_step_projection_fn=contact_stick.project_unilateral_contacts,
        )

        contact_zf.update_gripper(
            q_cur=sim_zf.q, gripper_pos_xyz=gp, gripper_rot_3x3=g_rot, gripper_gap_m=0.004
        )
        sim_zf.step(
            1.0 / 60.0,
            contact_force_and_stiffness_fn=contact_zf.evaluate_forces_and_stiffness,
            post_step_projection_fn=contact_zf.project_unilateral_contacts,
        )
    elapsed = time.perf_counter() - t0
    assert elapsed < 4.0, f"CPU step timing exceeded budget: {elapsed:.2f}s for 2x36 steps"

    z_stick_corner = float(sim_stick.q[0, 2])
    z_zf_corner = float(sim_zf.q[0, 2])
    assert z_stick_corner > 0.83, f"Sticky lift failed: z={z_stick_corner}"
    assert z_zf_corner < z_stick_corner - 0.05, (
        f"Zero-friction should slip instead of lifting: z_zf={z_zf_corner}, z_stick={z_stick_corner}"
    )


def test_cmaes_adjoint_sysid_and_bundle_v03_with_3dgs(tmp_path: Path) -> None:
    # Fast analytical recovery test for two-stage CMA-ES + L-BFGS-B
    true_p = np.array([0.42, -0.31, 0.15])
    res = run_two_stage_sysid(
        method_name="hermitetwin_shell",
        loss_fn=lambda x: float(np.sum((x - true_p) ** 2) + 0.1 * np.sum(np.abs(x - true_p))),
        x0=np.array([0.0, 0.0, 0.0]),
        bounds_low=np.array([-1.5, -1.5, -1.5]),
        bounds_high=np.array([1.5, 1.5, 1.5]),
        cmaes_generations=6,
        cmaes_pop_size=8,
        adjoint_maxiter=12,
        seed=9,
    )
    assert res.best_loss < 0.02
    assert len(res.loss_history) >= 7

    # Compile bundle v0.3 + render 3DGS frame + test rigid obstacle & spring-mass baseline
    spec = HermiteShellSpec(
        asset_id="v08_waffle_towel_01",
        structural_family="cloth_sheet",
        nx=4,
        ny=4,
        length_u_m=0.30,
        length_v_m=0.30,
        thickness_m=0.0016,
        area_density_kg_m2=0.25,
        youngs_modulus_pa=80000.0,
        poissons_ratio=0.30,
    )
    manifest, m_path = compile_thin_shell_bundle_v03(spec, tmp_path / "bundle_v03")
    assert manifest.schema_version == BUNDLE_SCHEMA_VERSION_V03
    assert manifest.calibration_record.is_well_conditioned()
    assert len(manifest.engine_overlays) == 4
    reloaded = ThinShellBundleManifestV03.from_dict(json.loads(m_path.read_text(encoding="utf-8")))
    assert reloaded.asset_id == spec.asset_id

    mesh = build_hermite_shell_mesh(
        nx=spec.nx,
        ny=spec.ny,
        length_u_m=spec.length_u_m,
        length_v_m=spec.length_v_m,
        area_density_kg_m2=spec.area_density_kg_m2,
    )
    gs_out = render_hermite_3dgs_frame(
        tmp_path / "bundle_v03" / manifest.gs_binding_relpath,
        mesh.rest_q,
        image_hw=(96, 128),
    )
    assert gs_out["rgb"].shape == (96, 128, 3)
    assert np.any(gs_out["foreground_mask"])

    # Baseline spring-mass smoke + dense evaluation
    base = SpringMassShellBaseline(
        SpringMassShellConfig(),
        obstacles=[RigidObstacleBox("book", (0.0, 0.0, 0.77), (0.05, 0.04, 0.015))],
    )
    b_step = base.step(
        1.0 / 60.0,
        gripper_pos_xyz=np.array([-0.10, -0.10, 0.758]),
        gripper_rot_3x3=np.eye(3),
        gripper_gap_m=0.004,
    )
    assert b_step["finite_ok"] is True
    grid_b = base.evaluate_grid(eval_nu=15, eval_nv=15)
    grid_h = evaluate_dense_surface(mesh, mesh.rest_q, eval_nu=15, eval_nv=15)
    assert grid_b["vertices"].shape == (15, 15, 3)
    assert grid_h["mean_curvature"].shape == (15, 15)
