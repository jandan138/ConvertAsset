"""Phase 4 GPU tests: 1D-1D Crossing Pinch C-IPC + Brazier Flattening, Composite 3DGS, and Real-Video BV17t4y1V7XH SysID."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from convert_asset.hermitetwin_uni import (
    CameraSpec,
    HermiteRodGaussianRenderer,
    HermiteRodSpec,
    HermiteShellGaussianRenderer,
    WarpBrazierRodSolver,
    build_hermite_shell_mesh,
    build_straight_rod_mesh,
    evaluate_two_rod_ipc_contact,
    render_composite_3dgs_torch,
    run_bv17_real_video_sysid_and_zeroshot,
    solve_two_rod_crossing_pinch,
)
from convert_asset.hermitetwin_uni.real_video_bv_sysid import DEFAULT_BV_VIDEO
from convert_asset.hermitetwin_uni.state_and_basis import DOFS_PER_ROD_NODE


def test_two_rod_crossing_pinch_ipc_zero_penetration_and_brazier_flattening() -> None:
    """Verify 1D-1D C-IPC exact gradient vs FD, strictly zero penetration, and Brazier pinch flattening."""
    spec = HermiteRodSpec(length_m=0.16, n_elems=6, r_in_m=0.0052, r_out_m=0.0070, youngs_modulus_pa=1.5e6, enable_brazier=True)
    mesh_a = build_straight_rod_mesh(spec)
    mesh_b = build_straight_rod_mesh(spec)

    # Tube A runs along X at z = +0.0155; Tube B runs along Y at z = 0.0 (centered at x=0.08, y=0)
    qa0 = mesh_a.rest_q.copy().reshape(mesh_a.n_nodes, DOFS_PER_ROD_NODE)
    qa0[:, 2] = +0.0155

    qb0 = mesh_b.rest_q.copy().reshape(mesh_b.n_nodes, DOFS_PER_ROD_NODE)
    for i in range(mesh_b.n_nodes):
        s_i = i * mesh_b.ds - 0.5 * spec.length_m
        qb0[i, 0:3] = [0.08, s_i, 0.0]
        qb0[i, 3:6] = [0.0, 1.0, 0.0]

    # 1. Exact gradient verification vs central FD at close approach
    _, ga, gb, _, _, _, min_cl0 = evaluate_two_rod_ipc_contact(mesh_a, qa0.ravel(), mesh_b, qb0.ravel(), d_hat_m=0.0040, kappa_b=5.0e3)
    assert min_cl0 > 0.0
    eps = 1e-6
    for idx in (3 * 10 + 2, 3 * 10 + 8):  # midpoint z and Brazier ovalization alpha2
        qp = qa0.ravel().copy()
        qm = qa0.ravel().copy()
        qp[idx] += eps
        qm[idx] -= eps
        ep, *_ = evaluate_two_rod_ipc_contact(mesh_a, qp, mesh_b, qb0.ravel(), d_hat_m=0.0040, kappa_b=5.0e3)
        em, *_ = evaluate_two_rod_ipc_contact(mesh_a, qm, mesh_b, qb0.ravel(), d_hat_m=0.0040, kappa_b=5.0e3)
        g_fd = (ep - em) / (2.0 * eps)
        assert abs(ga[idx] - g_fd) / max(abs(g_fd), 1e-8) < 1e-4

    # 2. Cinch Tube A ends downward by -18 mm across Tube B in 4 continuation steps -> strict zero penetration!
    solver_a = WarpBrazierRodSolver(mesh_a, device="cuda:0")
    solver_b = WarpBrazierRodSolver(mesh_b, device="cuda:0")
    n_end = (mesh_a.n_nodes - 1) * DOFS_PER_ROD_NODE
    dir_a = [0, 1, 2, 3, 4, 5, 6, n_end + 0, n_end + 1, n_end + 2, n_end + 3, n_end + 4, n_end + 5, n_end + 6]
    dir_b = list(dir_a)

    qa_cur, qb_cur = qa0.ravel().copy(), qb0.ravel().copy()
    d_b_vals = qb_cur[dir_b].copy()
    res = None
    for z_end in (+0.012, +0.006, 0.000, -0.006):
        d_a_vals = qa0.ravel()[dir_a].copy()
        d_a_vals[2] = z_end
        d_a_vals[9] = z_end
        res = solve_two_rod_crossing_pinch(
            solver_a,
            solver_b,
            qa_cur,
            qb_cur,
            dirichlet_a=dir_a,
            dirichlet_a_vals=d_a_vals,
            dirichlet_b=dir_b,
            dirichlet_b_vals=d_b_vals,
            d_hat_m=0.0032,
            kappa_b=8.0e3,
        )
        qa_cur, qb_cur = res.q_a, res.q_b
        assert res.min_clearance_mm > 0.0, f"1D-1D C-IPC violated zero penetration: {res.min_clearance_mm} mm"

    assert res is not None
    assert res.max_ovalization_a_pct > 2.0, f"Expected Brazier flattening at crossing pinch, got {res.max_ovalization_a_pct}%"
    assert res.max_ovalization_b_pct > 2.0, f"Expected Brazier flattening on lower tube, got {res.max_ovalization_b_pct}%"


def test_composite_1d_rod_and_2d_shell_3dgs_render() -> None:
    """Verify unified depth-sorted composite 3DGS renders 1D rod + 2D shell cleanly in one EWA pass."""
    rod_mesh = build_straight_rod_mesh(HermiteRodSpec(length_m=0.16, n_elems=4))
    sh_mesh = build_hermite_shell_mesh(nx=2, ny=2, length_u_m=0.16, length_v_m=0.16, area_density_kg_m2=0.3, origin_xyz=(0.08, 0.0, -0.03))
    r_rend = HermiteRodGaussianRenderer(rod_mesh, samples_per_elem=3, n_phi=10, device="cuda:0")
    s_rend = HermiteShellGaussianRenderer(sh_mesh, gs_nu=10, gs_nv=10, device="cuda:0")
    cam = CameraSpec(height=64, width=80, eye_xyz=(0.08, -0.32, 0.14), target_xyz=(0.08, 0.0, -0.01))
    with torch.no_grad():
        gr = r_rend.build_gaussians(torch.tensor(rod_mesh.rest_q, device=r_rend.device, dtype=r_rend.dtype))
        gs = s_rend.build_gaussians(torch.tensor(sh_mesh.rest_q, device=s_rend.device, dtype=s_rend.dtype))
        out = render_composite_3dgs_torch([gr, gs], cam)
    assert out["rgb"].shape == (64, 80, 3)
    assert float(out["silhouette"].max().item()) > 0.85


@pytest.mark.skipif(not DEFAULT_BV_VIDEO.is_file(), reason="Local Bilibili BV17t4y1V7XH clip not present")
def test_real_video_bv17_sysid_and_zeroshot_generalization() -> None:
    """Verify Real-to-Sim SysID on real Bilibili BV17t4y1V7XH video + Zero-Shot generalization to unseen hose."""
    rep = run_bv17_real_video_sysid_and_zeroshot(DEFAULT_BV_VIDEO, timestamp_s=145.0)
    assert 0.70 <= rep.mm_per_px <= 1.25, f"Unexpected condenser calibration scale: {rep.mm_per_px} mm/px"
    assert rep.train_iou_two_stage >= 0.78, f"Real video train IoU too low: {rep.train_iou_two_stage}"
    assert rep.train_iou_two_stage > rep.train_iou_init + 0.10, "Two-stage SysID must sharply improve over naive init!"
    assert rep.train_rmse_two_stage_mm <= 1.0, f"Real video train centerline RMSE too high: {rep.train_rmse_two_stage_mm} mm"
    assert rep.test_zeroshot_iou_two_stage >= 0.60, f"Zero-shot unseen hose IoU too low: {rep.test_zeroshot_iou_two_stage}"
    assert rep.test_zeroshot_rmse_two_stage_mm <= 2.5, f"Zero-shot unseen hose RMSE too high: {rep.test_zeroshot_rmse_two_stage_mm} mm"

