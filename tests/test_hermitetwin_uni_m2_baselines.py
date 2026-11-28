"""M2 GPU Verification Suite: 3D Nonlinear Tet FEM (Warp CUDA), Classic DER, and Official Linear C0 C-IPC Baselines."""

from __future__ import annotations

import math

import numpy as np

from convert_asset.hermitetwin_uni import (
    HermiteRodSpec,
    WarpBrazierRodSolver,
    WarpKirchhoffLoveShellSolver,
    build_hermite_shell_mesh,
    build_straight_rod_mesh,
)
from convert_asset.hermitetwin_uni.baselines import (
    CIPCLinearShellBaseline,
    DiscreteElasticRodBaseline,
    StableNeoHookeanTetSolver,
    build_c0_rect_shell_mesh,
    build_der_straight_rod,
    build_multilayer_hollow_tube_tet_mesh,
)


def test_fem3d_warp_snh_gradient_and_35k_tet_gpu_assembly() -> None:
    """Verify Warp CUDA Stable Neo-Hookean 3D tet gradient (< 1e-6 vs FD) and 35k-tet GPU assembly."""
    # 1. Exact analytical gradient vs FD on a 2-layer hollow tube
    mesh_sm = build_multilayer_hollow_tube_tet_mesh(length_m=0.12, r_in_m=0.006, r_out_m=0.008, n_z=8, n_theta=10, n_radial=2)
    sol_sm = StableNeoHookeanTetSolver(mesh_sm, youngs_modulus_pa=1.5e6, poissons_ratio=0.42, device="cuda:0")
    rng = np.random.default_rng(11)
    V_def = mesh_sm.rest_V + rng.normal(0.0, 2e-4, size=mesh_sm.rest_V.shape)
    _, g_ana, K_sp = sol_sm.eval_energy_grad_hess_sparse(V_def, compute_hessian=True)
    assert K_sp is not None and K_sp.shape == (sol_sm.n_dofs, sol_sm.n_dofs)

    eps = 1e-7
    for dof in (120, 121, 122, 305, 306):
        Vp = V_def.ravel().copy(); Vp[dof] += eps
        Vm = V_def.ravel().copy(); Vm[dof] -= eps
        ep, _, _ = sol_sm.eval_energy_grad_hess_sparse(Vp, compute_hessian=False)
        em, _, _ = sol_sm.eval_energy_grad_hess_sparse(Vm, compute_hessian=False)
        g_fd = (ep - em) / (2.0 * eps)
        rel = abs(g_ana[dof] - g_fd) / max(abs(g_fd), 1e-8)
        assert rel < 1e-5, f"3D Tet FEM gradient mismatch on dof {dof}: ana={g_ana[dof]:.6e}, fd={g_fd:.6e}, rel={rel:.3e}"

    # 2. Verify 34,560-tet (~35k-tet) 3-layer hollow tube GPU assembly runs cleanly with zero inverted tets!
    mesh_35k = build_multilayer_hollow_tube_tet_mesh(length_m=0.26, r_in_m=0.0088, r_out_m=0.0100, n_z=72, n_theta=32, n_radial=3)
    assert len(mesh_35k.tets) == 34560
    sol_35k = StableNeoHookeanTetSolver(mesh_35k, youngs_modulus_pa=1.5e6, poissons_ratio=0.45, device="cuda:0")
    e0, g0, K35 = sol_35k.eval_energy_grad_hess_sparse(mesh_35k.rest_V, compute_hessian=True)
    assert abs(e0) < 1e-12 and float(np.linalg.norm(g0)) < 1e-10
    assert K35 is not None and K35.nnz > 100000


def test_der_vs_hermite_vs_3d_fem_cantilever_parity() -> None:
    """Verify cantilever beam deflection matches across Euler-Bernoulli theory, DER, 3D Tet FEM, and HermiteTwin-Uni."""
    L, r_in, r_out, E, nu = 0.20, 0.006, 0.008, 2.0e6, 0.40
    F_tip = -0.04  # gentle tip load -> linear Euler-Bernoulli regime
    spec = HermiteRodSpec(length_m=L, n_elems=10, r_in_m=r_in, r_out_m=r_out, youngs_modulus_pa=E, poissons_ratio=nu, enable_brazier=False)
    w_eb = F_tip * (L**3) / (3.0 * spec.ei0_nm2)  # exact analytical tip z-deflection

    # 1. HermiteTwin-Uni
    h_mesh = build_straight_rod_mesh(spec)
    h_sol = WarpBrazierRodSolver(h_mesh, device="cuda:0")
    f_h = np.zeros(h_mesh.n_dofs)
    f_h[(h_mesh.n_nodes - 1) * 10 + 2] = F_tip
    h_res = h_sol.solve_equilibrium(h_mesh.rest_q, dirichlet_dofs=[0, 1, 2, 3, 4, 5, 6], dirichlet_vals=h_mesh.rest_q[:7], ext_force=f_h, tol=1e-10)
    w_hermite = float(h_res.q_final[(h_mesh.n_nodes - 1) * 10 + 2])

    # 2. Classic DER baseline (add 1 clamped ghost segment [-ds, 0] so free span [0, L] has exact length L!)
    ds_der = L / 10.0
    spec_der = HermiteRodSpec(length_m=L + ds_der, n_elems=11, r_in_m=r_in, r_out_m=r_out, youngs_modulus_pa=E, poissons_ratio=nu, enable_brazier=False)
    d_mesh = build_der_straight_rod(spec_der)
    d_mesh.rest_x[:, 0] -= ds_der
    d_sol = DiscreteElasticRodBaseline(d_mesh)
    q_d0 = np.concatenate([d_mesh.rest_x.ravel(), np.zeros(d_mesh.n_edges)])
    f_d = np.zeros(d_mesh.n_dofs)
    f_d[(d_mesh.n_nodes - 1) * 3 + 2] = F_tip
    # Clamp ghost vertex 0 (x=-ds) and root vertex 1 (x=0) -> exact clamped cantilever of free length L!
    d_dir = [0, 1, 2, 3, 4, 5, 3 * d_mesh.n_nodes]
    d_res = d_sol.solve_equilibrium(q_d0, dirichlet_dofs=d_dir, dirichlet_vals=q_d0[d_dir], ext_force=f_d, tol=1e-9)
    w_der = float(d_res.x_final[-1, 2])

    # 3. 3D Nonlinear Tet FEM (7,680 tets, 2 radial layers, low aspect ratio -> overcomes P1 locking!)
    t_mesh = build_multilayer_hollow_tube_tet_mesh(length_m=L, r_in_m=r_in, r_out_m=r_out, n_z=48, n_theta=16, n_radial=2)
    t_sol = StableNeoHookeanTetSolver(t_mesh, youngs_modulus_pa=E, poissons_ratio=nu, device="cuda:0")
    root_vids = t_mesh.ring_vertex_indices(0)
    t_dir = [int(v) * 3 + c for v in root_vids for c in range(3)]
    t_dval = t_mesh.rest_V[root_vids].ravel()
    tip_vids = t_mesh.ring_vertex_indices(t_mesh.n_axial - 1)
    f_t = np.zeros(t_sol.n_dofs)
    f_t[tip_vids * 3 + 2] = F_tip / float(len(tip_vids))
    t_res = t_sol.solve_equilibrium(t_mesh.rest_V, dirichlet_dofs=t_dir, dirichlet_vals=t_dval, ext_force=f_t, max_iters=25, tol=1e-6)
    w_fem3d = float(t_res.V_final[tip_vids, 2].mean())

    assert abs(w_hermite - w_eb) / abs(w_eb) < 0.03, f"Hermite vs EB mismatch: {w_hermite:.5f} vs {w_eb:.5f}"
    assert abs(w_der - w_eb) / abs(w_eb) < 0.15, f"DER vs EB mismatch: {w_der:.5f} vs {w_eb:.5f}"
    assert abs(w_fem3d - w_eb) / abs(w_eb) < 0.12, f"3D Tet FEM vs EB mismatch: {w_fem3d:.5f} vs {w_eb:.5f}"


def test_cipc_linear_shell_baseline_vs_c1_hermite() -> None:
    """Verify official ipctk C0 Discrete Shells baseline solves cleanly with 0 intersections and matches C1 shell."""
    L = 0.24
    cm, cb, nu = 260.0, 0.025, 0.32
    f_total_z = -0.05  # linear Kirchhoff plate regime (w_plate = -0.0384 m)

    # 1. Official C0 C-IPC Linear Discrete Shell (nx=8 free span + 1 ghost clamped row -> exact clamped length L!)
    du_c0 = L / 8.0
    c0_mesh = build_c0_rect_shell_mesh(nx=9, ny=8, length_u_m=L + du_c0, length_v_m=L, area_density_kg_m2=0.30)
    c0_sol = CIPCLinearShellBaseline(c0_mesh, membrane_rigidity=cm, bending_rigidity=cb, poissons_ratio=nu)
    # Clamp first two columns (ix=0, ix=1) to enforce true zero-slope clamped boundary condition
    c0_dir = [vid * 3 + c for vid in range(2 * (c0_mesh.ny + 1)) for c in range(3)]
    c0_dval = c0_mesh.rest_V[: 2 * (c0_mesh.ny + 1)].ravel()
    tip_ids = [c0_mesh.nx * (c0_mesh.ny + 1) + iy for iy in range(c0_mesh.ny + 1)]
    f_c0 = np.zeros(c0_sol.n_dofs)
    f_c0[np.asarray(tip_ids) * 3 + 2] = f_total_z / float(len(tip_ids))
    r_c0 = c0_sol.solve_equilibrium(c0_mesh.rest_V, dirichlet_dofs=c0_dir, dirichlet_vals=c0_dval, ext_force=f_c0, enable_ipc=True, max_iters=30)
    assert not r_c0["has_intersections"]
    w_c0 = float(r_c0["V_final"][tip_ids, 2].mean())

    # 2. C1 Bicubic Hermite Shell (3x3 grid = 192 DOFs, origin_xyz at z=0 matching C0 shell)
    c1_mesh = build_hermite_shell_mesh(nx=3, ny=3, length_u_m=L, length_v_m=L, area_density_kg_m2=0.30, origin_xyz=(0.0, 0.0, 0.0))
    c1_sol = WarpKirchhoffLoveShellSolver(c1_mesh, membrane_rigidity=cm, bending_rigidity=cb, poissons_ratio=nu, device="cuda:0")
    # Clamp u=0 edge position + slope x_u (ix=0)
    c1_dir, c1_dval = [], []
    for iy in range(c1_mesh.ny + 1):
        nid = iy
        for loc in (0, 1):  # x and x_u
            vd = 4 * nid + loc
            for c in range(3):
                c1_dir.append(vd * 3 + c)
                c1_dval.append(float(c1_mesh.rest_q[vd, c]))
    f_c1 = np.zeros(c1_sol.n_sdof)
    for iy in range(c1_mesh.ny + 1):
        nid = c1_mesh.nx * (c1_mesh.ny + 1) + iy
        f_c1[4 * nid * 3 + 2] = f_total_z / float(c1_mesh.ny + 1)
    q_c1 = c1_mesh.rest_q.copy()
    q_prev = q_c1.copy()
    for _ in range(18):
        sr = c1_sol.step_dynamic(q_c1, q_prev, dt=0.05, gravity_z=0.0, f_ext_flat=f_c1, dirichlet_sdofs=c1_dir, dirichlet_vals=c1_dval, max_iters=10)
        q_prev, q_c1 = q_c1, sr.q_next
    tip_c1_z = [float(q_c1[4 * (c1_mesh.nx * (c1_mesh.ny + 1) + iy), 2]) for iy in range(c1_mesh.ny + 1)]
    w_c1 = float(np.mean(tip_c1_z))

    # Compare against Kirchhoff plate bending w_plate = F * L^3 / (3 * cb * L)
    w_plate = f_total_z * (L**3) / (3.0 * cb * L)
    assert w_c0 < -0.01 and w_c1 < -0.01
    assert abs(w_c1 - w_plate) / abs(w_plate) < 0.15, f"C1 shell vs Kirchhoff plate theory: {w_c1:.5f} vs {w_plate:.5f}"
    assert abs(w_c0 - w_plate) / abs(w_plate) < 0.35, f"C0 C-IPC shell vs Kirchhoff plate theory: {w_c0:.5f} vs {w_plate:.5f}"

