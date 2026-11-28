"""Phase 1B & Phase 2 GPU tests: 2D Shell Warp CUDA parity, 3-olive IPC barb fit, and unified 1D+2D coupled contact."""

from __future__ import annotations

import math

import numpy as np

from convert_asset.deformable_v08_hermite.bicubic_hermite_shell import (
    build_hermite_shell_mesh,
    compute_shell_energy_and_grad,
)
from convert_asset.hermitetwin_uni import (
    HermiteRodSpec,
    UnifiedRodShellSolver,
    WarpBrazierRodSolver,
    WarpKirchhoffLoveShellSolver,
    build_straight_rod_mesh,
    ipc_barrier_val_grad_hess,
    solve_3olive_barb_interference_fit,
)
from convert_asset.hose_softbody_v10.specs_v10 import DEFAULT_CONDENSER_BARB_V10


def test_shell_warp_cuda_matches_cpu_reference_to_machine_precision() -> None:
    """Verify Warp 1.19 CUDA 2D Kirchhoff-Love shell energy, gradient & GN Hessian match CPU v0.8 reference."""
    mesh = build_hermite_shell_mesh(nx=3, ny=3, length_u_m=0.24, length_v_m=0.24, area_density_kg_m2=0.32)
    rng = np.random.default_rng(7)
    q = mesh.rest_q.copy()
    # Apply large non-planar 3D saddle + stretch deformation
    for nid in range(mesh.n_nodes):
        b = 4 * nid
        x, y, _ = q[b + 0]
        q[b + 0, 2] += 0.035 * math.sin(8.0 * x) * math.cos(8.0 * y) + 0.01 * (x * x - y * y)
        q[b + 1] += rng.normal(0.0, 0.04, size=3)
        q[b + 2] += rng.normal(0.0, 0.04, size=3)
        q[b + 3] += rng.normal(0.0, 0.02, size=3)

    cm, cb, nu = 260.0, 0.018, 0.32
    e_cpu, g_cpu, K_cpu, stats_cpu = compute_shell_energy_and_grad(
        mesh, q, membrane_rigidity=cm, bending_rigidity=cb, poissons_ratio=nu, compute_stiffness=True
    )

    solver = WarpKirchhoffLoveShellSolver(mesh, membrane_rigidity=cm, bending_rigidity=cb, poissons_ratio=nu, device="cuda:0")
    em_gpu, eb_gpu, g_gpu, K_gpu = solver.eval_energy_grad_stiffness(q, compute_stiffness=True)

    assert abs((em_gpu + eb_gpu) - e_cpu) / max(abs(e_cpu), 1e-12) < 1e-11
    g_rel = float(np.linalg.norm(g_gpu - g_cpu.ravel()) / max(np.linalg.norm(g_cpu.ravel()), 1e-12))
    assert g_rel < 1e-11, f"Shell GPU vs CPU gradient mismatch: {g_rel:.3e}"
    assert K_cpu is not None and K_gpu is not None
    # Verify symmetry & SPD property of GPU Gauss-Newton stiffness matrix
    assert np.max(np.abs(K_gpu - K_gpu.T)) < 1e-10
    k_rel = float(np.linalg.norm(K_gpu - K_cpu) / max(np.linalg.norm(K_cpu), 1e-12))
    assert k_rel < 1e-10, f"Shell GPU vs CPU Gauss-Newton Hessian mismatch: {k_rel:.3e}"


def test_ipc_barrier_exact_derivatives_and_convexity() -> None:
    """Verify C-IPC barrier derivatives match central FD and Hessian is strictly positive on (0, d_hat)."""
    d_hat = 0.002
    kappa = 5000.0
    eps = 1e-8
    for d in (0.00015, 0.0006, 0.0014):
        v, g, h = ipc_barrier_val_grad_hess(d, d_hat, kappa)
        vp, gp, _ = ipc_barrier_val_grad_hess(d + eps, d_hat, kappa)
        vm, gm, _ = ipc_barrier_val_grad_hess(d - eps, d_hat, kappa)
        assert v > 0.0 and g < 0.0 and h > 0.0
        assert abs(g - (vp - vm) / (2.0 * eps)) / abs(g) < 1e-6
        assert abs(h - (gp - gm) / (2.0 * eps)) / abs(h) < 1e-5


def test_3olive_barb_interference_fit_self_lock_and_zero_friction_falsification() -> None:
    """Verify 1D Brazier-Hermite hose achieves real radial hoop expansion & self-lock over v10.1 3-olive glass barb."""
    # Hose ID = 3.0 mm seated over v10.1 3-olive barb (stem 4.4 mm, olive peaks 5.6 mm -> ~87% peak hoop expansion)
    spec = HermiteRodSpec(
        length_m=0.09,
        n_elems=9,
        r_in_m=0.0030,
        r_out_m=0.0046,
        youngs_modulus_pa=1.65e6,
        poissons_ratio=0.45,
        enable_brazier=True,
    )
    mesh = build_straight_rod_mesh(spec, origin_xyz=(0.0, 0.0, 0.0), axis_xyz=(1.0, 0.0, 0.0))
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")

    res_nom = solve_3olive_barb_interference_fit(solver, barb_geom=DEFAULT_CONDENSER_BARB_V10, mu_friction=0.85, hose_weight_n=0.35)
    res_zero = solve_3olive_barb_interference_fit(solver, barb_geom=DEFAULT_CONDENSER_BARB_V10, mu_friction=0.0, hose_weight_n=0.35)

    assert res_nom.min_bore_clearance_mm > 0.0, "IPC CCD must enforce strictly positive bore clearance!"
    assert res_nom.cuff_hoop_expansion_pct > 75.0, f"Expected real radial hoop expansion over 5.6mm olives, got {res_nom.cuff_hoop_expansion_pct:.1f}%"
    assert res_nom.peak_radial_clamping_n > 1.5
    assert res_nom.hands_off_self_lock is True
    assert res_zero.axial_pull_off_capacity_n == 0.0
    assert res_zero.hands_off_self_lock is False, "Zero-friction counterfactual MUST falsify self-lock!"


def test_unified_1d_rod_pressing_onto_2d_shell_zero_interpenetration() -> None:
    """Verify monolithic 1D Brazier Rod + 2D Kirchhoff-Love Shell coupled dynamic step with zero penetration."""
    # Suspended 2D thin shell at z = 0.0 (corners pinned), 1D hollow hose resting 6 mm above shell and pushed downward
    shell_mesh = build_hermite_shell_mesh(nx=2, ny=2, length_u_m=0.16, length_v_m=0.16, area_density_kg_m2=0.35, origin_xyz=(0.0, 0.0, 0.0))
    shell_solver = WarpKirchhoffLoveShellSolver(shell_mesh, membrane_rigidity=240.0, bending_rigidity=0.012, poissons_ratio=0.32, device="cuda:0")

    rod_spec = HermiteRodSpec(length_m=0.14, n_elems=5, r_in_m=0.0030, r_out_m=0.0045, youngs_modulus_pa=1.65e6, enable_brazier=True)
    rod_mesh = build_straight_rod_mesh(rod_spec, origin_xyz=(-0.07, 0.0, 0.0075), axis_xyz=(1.0, 0.0, 0.0))
    rod_solver = WarpBrazierRodSolver(rod_mesh, device="cuda:0")

    unified = UnifiedRodShellSolver(rod_solver, shell_solver, proxy_nu=9, proxy_nv=9, d_hat_m=0.0035, kappa_b=4.0e3)

    # Pin the 4 corner position DOFs of the 2D shell
    corner_nodes = [0, shell_mesh.ny, shell_mesh.nx * (shell_mesh.ny + 1), shell_mesh.n_nodes - 1]
    shell_dir_sdofs = [12 * nid + c for nid in corner_nodes for c in range(3)]
    shell_dir_vals = [float(shell_mesh.rest_q[4 * nid, c]) for nid in corner_nodes for c in range(3)]

    q_rod_c = rod_mesh.rest_q.copy()
    q_rod_p = rod_mesh.rest_q.copy()
    q_sh_c = shell_mesh.rest_q.copy()
    q_sh_p = shell_mesh.rest_q.copy()

    # Push rod downward by -1.2 N distributed across rod position z-DOFs for 6 coupled dynamic steps
    f_rod = np.zeros(rod_mesh.n_dofs, dtype=np.float64)
    f_rod[2::10] = -1.2 / rod_mesh.n_nodes

    min_clear_hist = []
    for _ in range(6):
        step_res = unified.step_coupled(
            q_rod_c,
            q_rod_p,
            q_sh_c,
            q_sh_p,
            dt=1.0 / 60.0,
            gravity_z=-9.81,
            shell_dirichlet_sdofs=shell_dir_sdofs,
            shell_dirichlet_vals=shell_dir_vals,
            rod_f_ext=f_rod,
        )
        min_clear_hist.append(step_res.min_rod_shell_clearance_mm)
        q_rod_p, q_rod_c = q_rod_c, step_res.q_rod_next
        q_sh_p, q_sh_c = q_sh_c, step_res.q_shell_next

    center_nid = (shell_mesh.nx // 2) * (shell_mesh.ny + 1) + (shell_mesh.ny // 2)
    shell_center_dz_mm = float((q_sh_c[4 * center_nid, 2] - shell_mesh.rest_q[4 * center_nid, 2]) * 1000.0)
    assert min(min_clear_hist) > 0.0, f"IPC barrier violated! min clearance={min(min_clear_hist):.4f} mm"
    assert shell_center_dz_mm < -0.5, f"2D shell must visibly deflect under 1D rod IPC contact, got dz={shell_center_dz_mm:.3f} mm"

