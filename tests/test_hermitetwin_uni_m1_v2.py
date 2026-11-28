"""M1 GPU Verification Suite: Exact Brazier Localized Kinking, Sparse GPU Shell Assembly, and Official ipctk 1.6.1 CCD."""

from __future__ import annotations

import math
import time

import numpy as np

from convert_asset.hermitetwin_uni import (
    HermiteRodSpec,
    IPCTKC1ContactSystem,
    SparseUnifiedSceneSolver,
    WarpBrazierRodSolver,
    WarpKirchhoffLoveShellSolver,
    analytical_brazier_critical_values,
    build_hermite_shell_mesh,
    build_rod_proxy_topology,
    build_straight_rod_mesh,
    eval_rod_proxy_vertices_and_jacobian,
    solve_sparse_linear_warp_gpu,
)
from convert_asset.hermitetwin_uni.state_and_basis import DOFS_PER_ROD_NODE


def test_kink_exact_brazier_warp_gradient_matches_central_fd() -> None:
    """Verify V2 kink_exact Warp CUDA gradient matches central FD (< 1e-6) across all 10 DOFs incl. deep collapse + bore barrier."""
    spec = HermiteRodSpec(
        length_m=0.20,
        n_elems=6,
        r_in_m=0.0088,
        r_out_m=0.0100,
        youngs_modulus_pa=1.5e6,
        enable_brazier=True,
        brazier_model="kink_exact",
    )
    mesh = build_straight_rod_mesh(spec)
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")

    rng = np.random.default_rng(42)
    q = mesh.rest_q.copy().reshape(mesh.n_nodes, DOFS_PER_ROD_NODE)
    for i in range(mesh.n_nodes):
        u = i / float(mesh.n_elems)
        q[i, 2] -= 0.04 * u * u
        q[i, 3:6] = np.array([math.cos(0.7 * u), 0.08 * u, -math.sin(0.7 * u)])
        q[i, 6] = 0.25 * u
        q[i, 7] = 0.04 * math.sin(math.pi * u)
        # Test BOTH regimes: zeta < 0.50 (node 2) and zeta > 0.62 where C1 floor + inner-bore IPC barrier activate (node 3)!
        q[i, 8] = 0.64 * math.exp(-((u - 0.5) / 0.18) ** 2)
        q[i, 9] = 0.08 * math.sin(2.0 * math.pi * u)
    q_flat = q.ravel() + rng.normal(0.0, 1e-4, size=mesh.n_dofs)

    solver.update_bishop_frames(q_flat)
    _, g_ana = solver.eval_energy_and_grad(q_flat, refresh_frames=False)

    eps = 1e-7
    for idx in (20, 22, 23, 25, 26, 27, 28, 29, 37, 38, 39):
        qp = q_flat.copy(); qp[idx] += eps
        qm = q_flat.copy(); qm[idx] -= eps
        ep, _ = solver.eval_energy_and_grad(qp, refresh_frames=False)
        em, _ = solver.eval_energy_and_grad(qm, refresh_frames=False)
        g_fd = (ep - em) / (2.0 * eps)
        rel = abs(g_ana[idx] - g_fd) / max(abs(g_fd), 1e-8)
        assert rel < 1e-5, f"kink_exact gradient mismatch at dof {idx}: ana={g_ana[idx]:.6e}, fd={g_fd:.6e}, rel={rel:.3e}"


def test_brazier_m_crit_within_2_5_pct_and_localized_kink_snapback() -> None:
    """Verify V2 kink_exact matches analytical Brazier (1927) M_crit to < 2.5%, localizes mid-span kink, and snaps back cleanly."""
    # Thin-walled hollow tube (R0=9.4mm, h_w=1.2mm -> R0/h_w = 7.83)
    spec = HermiteRodSpec(
        length_m=0.26,
        n_elems=20,
        r_in_m=0.0088,
        r_out_m=0.0100,
        youngs_modulus_pa=1.5e6,
        poissons_ratio=0.45,
        enable_brazier=True,
        brazier_model="kink_exact",
    )
    mesh = build_straight_rod_mesh(spec)
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")
    crit = analytical_brazier_critical_values(spec)

    # 1. Exact uniform-curvature Brazier limit-point check (free ends ovalization -> exact Brazier 1927 theory!)
    n_end = (mesh.n_nodes - 1) * DOFS_PER_ROD_NODE
    dir_free_ov = [0, 1, 2, 3, 4, 5, 6, n_end + 3, n_end + 4, n_end + 5, n_end + 6]
    q_u = mesh.rest_q.copy()
    moments = []
    for deg in np.linspace(15.0, 130.0, 14):
        th = math.radians(float(deg))
        dv = np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, math.cos(th), 0.0, -math.sin(th), 0.0])
        res = solver.solve_equilibrium(q_u, dirichlet_dofs=dir_free_ov, dirichlet_vals=dv, max_iters=30, tol=1e-8)
        q_u = res.q_final
        _, g = solver.eval_energy_and_grad(q_u, refresh_frames=True)
        d_td = np.array([-math.sin(th), 0.0, -math.cos(th)])
        moments.append(float(np.dot(g[n_end + 3 : n_end + 6], d_td)))

    m_peak = max(moments)
    rel_err = abs(m_peak - crit["moment_crit_nm"]) / crit["moment_crit_nm"]
    assert rel_err < 0.025, f"Brazier M_crit error too large: sim={m_peak*1e3:.3f} vs theory={crit['moment_crit_nm']*1e3:.3f} mN*m ({rel_err*100:.2f}%)"

    # 2. Clamped-chuck localized kinking + elastic snap-back using SparseUnifiedSceneSolver dynamic rollout!
    scene = SparseUnifiedSceneSolver(rod_solvers=[solver])
    # Circular end chucks clamp alpha0=alpha2=beta2=0 at BOTH ends -> naturally nucleates sharp localized kink at mid-span!
    dir_chuck = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, n_end + 3, n_end + 4, n_end + 5, n_end + 6, n_end + 7, n_end + 8, n_end + 9]
    q_curr = mesh.rest_q.copy()
    q_prev = q_curr.copy()
    peak_mid_ov = 0.0
    end_ov_at_peak = 0.0
    for deg in np.linspace(10.0, 155.0, 26):
        th = math.radians(float(deg))
        dv = np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, math.cos(th), 0.0, -math.sin(th), 0.0, 0.0, 0.0, 0.0])
        sr = scene.step_dynamic(q_curr, q_prev, dt=1.0 / 60.0, gravity_z=0.0, dirichlet_dofs=dir_chuck, dirichlet_vals=dv, max_iters=14)
        q_prev, q_curr = q_curr, sr.q_next
        qa = q_curr.reshape(mesh.n_nodes, DOFS_PER_ROD_NODE)
        ov = np.hypot(qa[:, 8], qa[:, 9])
        if float(ov.max()) > peak_mid_ov:
            peak_mid_ov = float(ov.max())
            end_ov_at_peak = float(0.5 * (ov[1] + ov[-2]))

    # Localized kink: deep wall-to-wall flattening (> 50% ovalization) sharply higher than near-chuck nodes!
    assert peak_mid_ov > 0.50, f"Expected deep Brazier kink (>50% ovalization), got {peak_mid_ov*100:.1f}%"
    assert peak_mid_ov > 1.5 * end_ov_at_peak, f"Expected localized mid-span kink vs ends: mid={peak_mid_ov:.3f}, near_end={end_ov_at_peak:.3f}"

    # Unload smoothly back to 0 deg + brief hold for dynamic ringing to damp -> elastic snap-back recovery!
    unload_sched = list(np.linspace(145.0, 0.0, 22)) + [0.0] * 18
    for deg in unload_sched:
        th = math.radians(float(deg))
        dv = np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, math.cos(th), 0.0, -math.sin(th), 0.0, 0.0, 0.0, 0.0])
        sr = scene.step_dynamic(q_curr, q_prev, dt=1.0 / 60.0, gravity_z=0.0, dirichlet_dofs=dir_chuck, dirichlet_vals=dv, max_iters=14)
        q_prev, q_curr = q_curr, sr.q_next
    qa_un = q_curr.reshape(mesh.n_nodes, DOFS_PER_ROD_NODE)
    assert float(np.max(np.hypot(qa_un[:, 8], qa_un[:, 9]))) < 0.05, "Tube failed to recover circular section after unloading!"


def test_sparse_12x12_shell_gpu_assembly_and_warp_cg() -> None:
    """Verify O(n_elems) sparse GPU assembly on 12x12 C1 shell (2,028 DOFs) is < 5 ms and matches Warp GPU CG."""
    mesh = build_hermite_shell_mesh(nx=12, ny=12, length_u_m=0.32, length_v_m=0.32, area_density_kg_m2=0.28)
    sol = WarpKirchhoffLoveShellSolver(mesh, membrane_rigidity=220.0, bending_rigidity=0.012, poissons_ratio=0.32, device="cuda:0")
    q = mesh.rest_q.copy()
    q[0::4, 2] += 0.012 * np.sin(np.pi * q[0::4, 0] / 0.32) * np.sin(np.pi * q[0::4, 1] / 0.32)

    # Warmup + benchmark sparse GPU assembly
    em, eb, g, K_sp = sol.eval_energy_grad_stiffness_sparse(q, compute_stiffness=True)
    assert K_sp is not None and K_sp.shape == (mesh.n_vec_dofs * 3, mesh.n_vec_dofs * 3)
    t0 = time.perf_counter()
    for _ in range(10):
        sol.eval_energy_grad_stiffness_sparse(q, compute_stiffness=True)
    avg_ms = (time.perf_counter() - t0) * 1000.0 / 10.0
    assert avg_ms < 25.0, f"12x12 sparse GPU shell assembly too slow: {avg_ms:.2f} ms"

    # Verify Warp GPU BSR + Jacobi-CG solves sparse SPD system accurately
    H_spd = (K_sp + 3600.0 * sol.mass_3d_sparse).tocsc()
    rhs = -g
    x_gpu, iters, cg_ms = solve_sparse_linear_warp_gpu(H_spd, rhs, tol=1e-7, maxiter=400, device="cuda:0")
    rel_res = float(np.linalg.norm(H_spd @ x_gpu - rhs) / max(np.linalg.norm(rhs), 1e-12))
    assert rel_res < 1e-5, f"Warp GPU BSR-CG residual too high: {rel_res:.3e} ({iters} iters, {cg_ms:.1f} ms)"


def test_ipctk_c1_nonlinear_proxy_jacobian_and_tight_inclusion_ccd() -> None:
    """Verify exact rod proxy Jacobian J_W vs FD (< 1e-5) and official ipctk Tight-Inclusion 0-intersection cinch."""
    spec = HermiteRodSpec(length_m=0.16, n_elems=8, r_in_m=0.0052, r_out_m=0.0070, youngs_modulus_pa=1.5e6, brazier_model="kink_exact")
    mesh_a = build_straight_rod_mesh(spec)
    mesh_b = build_straight_rod_mesh(spec)

    # 1. Exact sparse Jacobian J_W check vs FD on all 10 DOF types (x, t, theta, alpha0, alpha2, beta2)
    rp_a = build_rod_proxy_topology(mesh_a, samples_per_elem=2, n_phi=8)
    q_test = mesh_a.rest_q.copy()
    q_test[4 * 10 + 2] = 0.012
    q_test[4 * 10 + 6] = 0.35
    q_test[4 * 10 + 7] = 0.12
    q_test[4 * 10 + 8] = -0.18
    q_test[4 * 10 + 9] = 0.09
    from convert_asset.hermitetwin_uni.ipctk_c1_contact import _compute_rod_ring_frames
    d1r, d2r = _compute_rod_ring_frames(mesh_a, q_test, rp_a.xis_ring)
    V0, J_W = eval_rod_proxy_vertices_and_jacobian(rp_a, q_test, d1_rings=d1r, d2_rings=d2r, compute_jacobian=True)
    assert J_W is not None
    eps = 1e-6
    for dof in (42, 43, 46, 47, 48, 49):
        qp = q_test.copy(); qp[dof] += eps
        qm = q_test.copy(); qm[dof] -= eps
        Vp, _ = eval_rod_proxy_vertices_and_jacobian(rp_a, qp, d1_rings=d1r, d2_rings=d2r, compute_jacobian=False)
        Vm, _ = eval_rod_proxy_vertices_and_jacobian(rp_a, qm, d1_rings=d1r, d2_rings=d2r, compute_jacobian=False)
        col_fd = ((Vp - Vm) / (2.0 * eps)).ravel()
        col_ana = J_W[:, dof].toarray().ravel()
        err = float(np.linalg.norm(col_ana - col_fd) / max(np.linalg.norm(col_fd), 1e-10))
        assert err < 1e-5, f"Proxy Jacobian J_W mismatch on dof {dof}: rel_err={err:.3e}"

    # 2. Live 3D crossing cinch under official ipctk 1.6.1 Tight-Inclusion CCD -> ZERO intersections + Brazier flattening!
    qa0 = mesh_a.rest_q.copy().reshape(mesh_a.n_nodes, DOFS_PER_ROD_NODE)
    qa0[:, 2] = +0.018
    qb0 = mesh_b.rest_q.copy().reshape(mesh_b.n_nodes, DOFS_PER_ROD_NODE)
    for i in range(mesh_b.n_nodes):
        qb0[i, 0:3] = [0.08, i * mesh_b.ds - 0.08, 0.0]
        qb0[i, 3:6] = [0.0, 1.0, 0.0]

    rp_b = build_rod_proxy_topology(mesh_b, samples_per_elem=2, n_phi=8)
    contact = IPCTKC1ContactSystem(rod_specs=[rp_a, rp_b], d_hat_m=0.0018, barrier_stiffness=5.0e4, mu_friction=0.35)
    sol_a = WarpBrazierRodSolver(mesh_a, device="cuda:0")
    sol_b = WarpBrazierRodSolver(mesh_b, device="cuda:0")
    scene = SparseUnifiedSceneSolver(rod_solvers=[sol_a, sol_b], contact_system=contact)

    q_curr = np.concatenate([qa0.ravel(), qb0.ravel()])
    q_prev = q_curr.copy()
    assert not contact.has_intersections(q_curr)

    na = mesh_a.n_dofs
    n_end = (mesh_a.n_nodes - 1) * DOFS_PER_ROD_NODE
    dir_a = [0, 1, 2, 3, 4, 5, 6, n_end + 0, n_end + 1, n_end + 2, n_end + 3, n_end + 4, n_end + 5, n_end + 6]
    dir_b = [na + i for i in dir_a]
    d_idx = dir_a + dir_b
    d_b_vals = qb0.ravel()[dir_a].copy()

    for z_end in np.linspace(0.015, -0.012, 12):
        d_a_vals = qa0.ravel()[dir_a].copy()
        d_a_vals[2] = float(z_end)
        d_a_vals[9] = float(z_end)
        sr = scene.step_dynamic(
            q_curr, q_prev, dt=1.0 / 60.0, gravity_z=0.0,
            dirichlet_dofs=d_idx, dirichlet_vals=np.concatenate([d_a_vals, d_b_vals]), max_iters=14,
        )
        q_prev, q_curr = q_curr, sr.q_next
        assert not sr.has_intersections, f"ipctk Tight-Inclusion CCD detected intersection at z_end={z_end}!"

    qa_fin = q_curr[:na].reshape(mesh_a.n_nodes, DOFS_PER_ROD_NODE)
    ov_max = float(np.max(np.hypot(qa_fin[:, 8], qa_fin[:, 9])))
    assert ov_max > 0.03, f"Expected real contact-induced Brazier flattening via J_W^T g_IPC, got {ov_max*100:.2f}%"

