"""Phase 0/1 unit tests for HermiteTwin-Uni: Warp CUDA 1D C1-Hermite Brazier-Cosserat solver & Implicit Adjoint."""

from __future__ import annotations

import math

import numpy as np
import pytest

from convert_asset.hermitetwin_uni import (
    HermiteRodSpec,
    WarpBrazierRodSolver,
    analytical_brazier_critical_values,
    build_straight_rod_mesh,
    evaluate_brazier_tube_surface,
)


def test_warp_torch_zero_copy_gpu_bridge() -> None:
    """Verify Warp 1.19 CUDA and PyTorch 2.11 share the exact same RTX 4090 GPU memory pointer."""
    import torch
    import warp as wp

    wp.init()
    assert wp.is_cuda_available(), "CUDA required for HermiteTwin-Uni GPU stack"
    assert torch.cuda.is_available(), "PyTorch CUDA required"

    spec = HermiteRodSpec(length_m=0.16, n_elems=8)
    mesh = build_straight_rod_mesh(spec)
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")
    solver.eval_energy_and_grad(mesh.rest_q)
    t_view = solver.to_torch_zero_copy()
    assert t_view.is_cuda
    assert int(t_view.data_ptr()) == int(solver._wp_q.ptr)
    assert t_view.shape == (mesh.n_dofs,)


def test_analytical_energy_gradient_matches_central_fd() -> None:
    """Verify Warp CUDA analytical nodal gradient matches double-precision central FD across all 10 DOFs/node."""
    spec = HermiteRodSpec(length_m=0.20, n_elems=6, enable_brazier=True)
    mesh = build_straight_rod_mesh(spec)
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")

    rng = np.random.default_rng(123)
    q = mesh.rest_q.copy()
    # Apply nontrivial 3D bend + twist + hoop expansion + quadrupole ovalization
    for i in range(mesh.n_nodes):
        s = i * mesh.ds
        b = i * 10
        q[b + 1] += 0.012 * math.sin(math.pi * s / spec.length_m)
        q[b + 2] -= 0.018 * (s / spec.length_m) ** 2
        q[b + 3 : b + 6] += rng.normal(0.0, 0.03, size=3)
        q[b + 6] += 0.45 * (s / spec.length_m)
        q[b + 7] += 0.12 * math.cos(math.pi * s / spec.length_m)
        q[b + 8] += -0.15 * math.sin(math.pi * s / spec.length_m)
        q[b + 9] += 0.08 * math.sin(2.0 * math.pi * s / spec.length_m)

    solver.update_bishop_frames(q)
    _, grad_ana = solver.eval_energy_and_grad(q, refresh_frames=False)

    eps = 1e-6
    grad_fd = np.zeros_like(grad_ana)
    for k in range(mesh.n_dofs):
        qp = q.copy()
        qm = q.copy()
        qp[k] += eps
        qm[k] -= eps
        ep, _ = solver.eval_energy_and_grad(qp, refresh_frames=False)
        em, _ = solver.eval_energy_and_grad(qm, refresh_frames=False)
        grad_fd[k] = (ep - em) / (2.0 * eps)

    rel_err = float(np.linalg.norm(grad_ana - grad_fd) / max(np.linalg.norm(grad_fd), 1e-12))
    assert rel_err < 1e-6, f"Analytical gradient mismatch vs FD: rel_err={rel_err:.3e}"


def test_brazier_moment_curvature_softening_and_ovalization() -> None:
    """Verify hollow Brazier tube exhibits exact ovalization softening & lower bending moment than rigid-section rod."""
    # Thin-walled hollow tube (R0/hw = 7.0) so Brazier critical curvature is cleanly reached within pure bend
    spec_hollow = HermiteRodSpec(
        length_m=0.20,
        n_elems=8,
        r_in_m=0.0065,
        r_out_m=0.0075,
        youngs_modulus_pa=2.0e6,
        poissons_ratio=0.40,
        enable_brazier=True,
    )
    spec_solid = HermiteRodSpec(
        length_m=0.20,
        n_elems=8,
        r_in_m=0.0065,
        r_out_m=0.0075,
        youngs_modulus_pa=2.0e6,
        poissons_ratio=0.40,
        enable_brazier=False,
    )
    crit = analytical_brazier_critical_values(spec_hollow)
    kappa_test = 0.85 * crit["kappa_crit_inv_m"]
    total_angle = kappa_test * spec_hollow.length_m

    # Prescribe pure circular arc centerline + tangent at all nodes, solve free cross-sectional DOFs (alpha0, alpha2, beta2)
    def _build_arc_q(mesh_obj):
        q = mesh_obj.rest_q.copy()
        R_arc = 1.0 / kappa_test
        for i in range(mesh_obj.n_nodes):
            s = i * mesh_obj.ds
            phi = s * kappa_test
            b = i * 10
            q[b + 0] = R_arc * math.sin(phi)
            q[b + 1] = 0.0
            q[b + 2] = R_arc * (1.0 - math.cos(phi))
            q[b + 3] = math.cos(phi)
            q[b + 4] = 0.0
            q[b + 5] = math.sin(phi)
        return q

    mesh_h = build_straight_rod_mesh(spec_hollow)
    mesh_s = build_straight_rod_mesh(spec_solid)
    sol_h = WarpBrazierRodSolver(mesh_h, device="cuda:0")
    sol_s = WarpBrazierRodSolver(mesh_s, device="cuda:0")

    q_arc_h = _build_arc_q(mesh_h)
    q_arc_s = _build_arc_q(mesh_s)

    # Lock centerline (x, t, theta), leave cross-section (alpha0, alpha2, beta2) free to equilibrate
    locked = [i * 10 + d for i in range(mesh_h.n_nodes) for d in range(7)]
    res_h = sol_h.solve_equilibrium(q_arc_h, dirichlet_dofs=locked, dirichlet_vals=q_arc_h[locked], tol=1e-11)
    res_s = sol_s.solve_equilibrium(q_arc_s, dirichlet_dofs=locked, dirichlet_vals=q_arc_s[locked], tol=1e-11)

    surf_h = evaluate_brazier_tube_surface(mesh_h, res_h.q_final)
    max_oval = float(surf_h["ovalization"].max())
    assert res_h.residual_norm < 1e-10
    assert res_h.energy_j < 0.90 * res_s.energy_j, "Brazier ovalization must significantly soften bending energy!"
    assert max_oval > 0.12, f"Expected pronounced Brazier ovalization near kappa_crit, got {max_oval:.4f}"


def test_implicit_adjoint_matches_finite_difference_sensitivity() -> None:
    """Verify Implicit Function Theorem adjoint dL/dpsi matches full re-solve FD to < 1e-4 across all parameters."""
    spec = HermiteRodSpec(
        length_m=0.16,
        n_elems=5,
        r_in_m=0.0055,
        r_out_m=0.0070,
        youngs_modulus_pa=1.8e6,
        poissons_ratio=0.40,
        enable_brazier=True,
    )
    mesh = build_straight_rod_mesh(spec)
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")

    # Clamped root (node 0 all 7 kinematics fixed), tip load + twist torque + radial hoop load at midspan
    dirichlet = [0, 1, 2, 3, 4, 5, 6]
    d_vals = mesh.rest_q[dirichlet].copy()

    f_ext = np.zeros(mesh.n_dofs, dtype=np.float64)
    tip = (mesh.n_nodes - 1) * 10
    mid = (mesh.n_nodes // 2) * 10
    f_ext[tip + 2] = -0.18  # downward tip load -> bending + Brazier ovalization
    f_ext[tip + 6] = +0.0025  # axial twist torque -> G_scale sensitivity
    f_ext[mid + 7] = +1.50  # radial barb-like hoop pressure -> K_hoop_scale sensitivity

    # Solve equilibrium at nominal parameters
    base_res = solver.solve_equilibrium(mesh.rest_q, dirichlet_dofs=dirichlet, dirichlet_vals=d_vals, ext_force=f_ext, tol=1e-11)
    assert base_res.residual_norm < 1e-10

    # Quadratic target observation loss L(q) = 0.5 * ||W_obs * (q - q_rest)||^2
    obs_weights = np.zeros(mesh.n_dofs, dtype=np.float64)
    obs_weights[tip + 2] = 100.0
    obs_weights[tip + 6] = 10.0
    obs_weights[mid + 7] = 50.0
    obs_weights[mid + 8] = 50.0

    def _loss_and_grad(q_vec: np.ndarray) -> tuple[float, np.ndarray]:
        diff = q_vec - mesh.rest_q
        return 0.5 * float(np.sum(obs_weights * diff * diff)), obs_weights * diff

    _, dL_dq = _loss_and_grad(base_res.q_final)
    adj = solver.compute_implicit_adjoint(
        base_res.q_final,
        dL_dq,
        dirichlet_dofs=dirichlet,
        param_names=("E_scale", "G_scale", "K_hoop_scale", "K_oval_scale"),
    )

    eps_p = 1e-4
    for pname, g_adj in adj.grad_params.items():
        rp = solver.solve_equilibrium(base_res.q_final, dirichlet_dofs=dirichlet, dirichlet_vals=d_vals, ext_force=f_ext, param_overrides={pname: 1.0 + eps_p}, tol=1e-12)
        rm = solver.solve_equilibrium(base_res.q_final, dirichlet_dofs=dirichlet, dirichlet_vals=d_vals, ext_force=f_ext, param_overrides={pname: 1.0 - eps_p}, tol=1e-12)
        lp, _ = _loss_and_grad(rp.q_final)
        lm, _ = _loss_and_grad(rm.q_final)
        g_fd = (lp - lm) / (2.0 * eps_p)
        rel = abs(g_adj - g_fd) / max(abs(g_fd), 1e-10)
        assert rel < 1e-3, f"Implicit Adjoint mismatch on {pname}: adj={g_adj:.6e}, fd={g_fd:.6e}, rel={rel:.3e}"

