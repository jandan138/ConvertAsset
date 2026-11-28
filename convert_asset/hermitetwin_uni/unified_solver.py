"""Unified Coupled Dynamic Solver: 1D C1-Hermite Brazier Rod + 2D C1 Kirchhoff-Love Shell + IPC-Barrier Contact."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Sequence

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from convert_asset.hose_softbody_v10.specs_v10 import CondenserBarbGeometryV10, DEFAULT_CONDENSER_BARB_V10

from .ipc_proxy_contact_warp import (
    BarbInterferenceResult,
    conservative_ccd_max_step_1d_barb,
    evaluate_rod_on_3olive_barb_contact,
    evaluate_rod_to_shell_ipc_contact,
)
from .rod_brazier_warp import WarpBrazierRodSolver
from .shell_kl_warp import WarpKirchhoffLoveShellSolver
from .state_and_basis import DOFS_PER_ROD_NODE


@dataclass
class UnifiedStepResult:
    q_rod_next: np.ndarray
    q_shell_next: np.ndarray
    min_rod_shell_clearance_mm: float
    contact_energy_j: float
    residual_norm: float
    n_iters: int
    wall_time_ms: float


def solve_3olive_barb_interference_fit(
    rod_solver: WarpBrazierRodSolver,
    *,
    barb_geom: CondenserBarbGeometryV10 = DEFAULT_CONDENSER_BARB_V10,
    mu_friction: float = 0.85,
    hose_weight_n: float = 0.35,
    max_iters: int = 30,
    tol: float = 1e-8,
) -> BarbInterferenceResult:
    """Solve real IPC-Barrier radial interference fit of a 1D Brazier-Hermite hose seated over a 3-olive glass barb.

    Initializes inner bore strictly outside the 3 olives (zero initial penetration, IPC-valid), then relaxes
    to exact physical radial equilibrium under hoop elasticity + 3-olive barrier contact.
    """
    mesh = rod_solver.mesh
    q = mesh.rest_q.copy()
    r_in0 = float(mesh.spec.r_in_m)

    # Start strictly feasible (d > 0) by pre-expanding cuff nodes slightly above max olive radius
    for i in range(mesh.n_nodes):
        s_i = i * mesh.ds
        if barb_geom.seat_start_s_m - mesh.ds <= s_i <= barb_geom.seat_end_s_m + mesh.ds:
            r_need = barb_geom.olive_radius_m + 0.0004
            q[i * DOFS_PER_ROD_NODE + 7] = max(0.0, (r_need / r_in0) - 1.0)

    # Fix axial x-positions of root & tip to keep hose seated over barb while radial/hoop/ovalization equilibrate
    locked = [0, 3, 4, 5, 6]
    d_idx = np.asarray(locked, dtype=np.int64)
    d_val = q[d_idx].copy()
    free_mask = np.ones(mesh.n_dofs, dtype=bool)
    free_mask[d_idx] = False
    free_idx = np.nonzero(free_mask)[0]

    rod_solver.update_bishop_frames(q)
    e_el, g_el = rod_solver.eval_energy_and_grad(q, refresh_frames=False)
    e_c, g_c, H_c, diag = evaluate_rod_on_3olive_barb_contact(mesh, q, barb_geom=barb_geom, mu_friction=mu_friction)
    res = g_el + g_c
    res_norm = float(np.linalg.norm(res[free_idx]))

    for _ in range(max_iters):
        if res_norm < tol:
            break
        K_el = rod_solver.eval_hessian_fd_banded(q)
        H = K_el + H_c
        H_ff = H[np.ix_(free_idx, free_idx)]
        rhs = -res[free_idx]

        reg = 1e-8
        dq_f = None
        for _ in range(12):
            try:
                cf = cho_factor(H_ff + reg * np.eye(len(free_idx)), lower=True)
                dq_f = cho_solve(cf, rhs)
                if float(np.dot(rhs, dq_f)) > 0.0:
                    break
            except Exception:
                pass
            reg *= 10.0
        if dq_f is None:
            break

        dq_full = np.zeros(mesh.n_dofs, dtype=np.float64)
        dq_full[free_idx] = dq_f
        eta_max = conservative_ccd_max_step_1d_barb(mesh, q, dq_full, barb_geom=barb_geom)

        obj0 = e_el + e_c
        slope = float(np.dot(res[free_idx], dq_f))
        eta = eta_max
        accepted = False
        for _ in range(14):
            q_try = q + eta * dq_full
            q_try[d_idx] = d_val
            e_el_t, _ = rod_solver.eval_energy_and_grad(q_try, refresh_frames=False)
            e_c_t, _, _, _ = evaluate_rod_on_3olive_barb_contact(mesh, q_try, barb_geom=barb_geom, mu_friction=mu_friction)
            if (e_el_t + e_c_t) <= obj0 + 1e-4 * eta * slope or abs((e_el_t + e_c_t) - obj0) < 1e-14:
                q = q_try
                accepted = True
                break
            eta *= 0.5
        if not accepted:
            break
        rod_solver.update_bishop_frames(q)
        e_el, g_el = rod_solver.eval_energy_and_grad(q, refresh_frames=False)
        e_c, g_c, H_c, diag = evaluate_rod_on_3olive_barb_contact(mesh, q, barb_geom=barb_geom, mu_friction=mu_friction)
        res = g_el + g_c
        res_norm = float(np.linalg.norm(res[free_idx]))

    pull_cap = float(diag["axial_pull_off_capacity_n"])
    return BarbInterferenceResult(
        mu_friction=float(mu_friction),
        cuff_hoop_expansion_pct=float(diag["cuff_hoop_expansion_pct"]),
        peak_radial_clamping_n=float(diag["total_radial_clamping_n"]),
        axial_pull_off_capacity_n=pull_cap,
        hands_off_self_lock=bool(pull_cap > hose_weight_n),
        min_bore_clearance_mm=float(diag["min_bore_clearance_mm"]),
        q_equil=q,
    )


class UnifiedRodShellSolver:
    """Simultaneous coupled Backward-Euler solver for 1D Brazier Rod + 2D Kirchhoff-Love Shell + IPC Contact."""

    def __init__(
        self,
        rod_solver: WarpBrazierRodSolver,
        shell_solver: WarpKirchhoffLoveShellSolver,
        *,
        proxy_nu: int = 12,
        proxy_nv: int = 12,
        d_hat_m: float = 0.0040,
        kappa_b: float = 6.0e3,
    ) -> None:
        self.rod = rod_solver
        self.shell = shell_solver
        self.d_hat_m = float(d_hat_m)
        self.kappa_b = float(kappa_b)

        sm = shell_solver.mesh
        u = np.linspace(0.0, sm.length_u_m, proxy_nu)
        v = np.linspace(0.0, sm.length_v_m, proxy_nv)
        uu, vv = np.meshgrid(u, v, indexing="ij")
        self.shell_W_proxy = sm.build_sample_matrix(np.column_stack([uu.ravel(), vv.ravel()]))

    def step_coupled(
        self,
        q_rod_curr: np.ndarray,
        q_rod_prev: np.ndarray,
        q_shell_curr: np.ndarray,
        q_shell_prev: np.ndarray,
        *,
        dt: float = 1.0 / 60.0,
        gravity_z: float = -9.81,
        rod_dirichlet: Sequence[int] = (),
        rod_dirichlet_vals: Sequence[float] = (),
        shell_dirichlet_sdofs: Sequence[int] = (),
        shell_dirichlet_vals: Sequence[float] = (),
        rod_f_ext: np.ndarray | None = None,
        shell_f_ext: np.ndarray | None = None,
        max_iters: int = 12,
        tol: float = 1e-6,
    ) -> UnifiedStepResult:
        """One monolithic coupled implicit Backward-Euler step with J_W^T H_IPC J_W rod-shell contact."""
        t0 = time.perf_counter()
        n_r = self.rod.mesh.n_dofs
        n_s = self.shell.n_sdof
        n_tot = n_r + n_s
        inv_dt2 = 1.0 / (dt * dt)

        qr_c = np.asarray(q_rod_curr, dtype=np.float64).ravel()
        qr_p = np.asarray(q_rod_prev, dtype=np.float64).ravel()
        qs_c = np.asarray(q_shell_curr, dtype=np.float64).ravel()
        qs_p = np.asarray(q_shell_prev, dtype=np.float64).ravel()

        qr_tilde = 2.0 * qr_c - qr_p
        qs_tilde = 2.0 * qs_c - qs_p

        Mr = self.rod.mesh.mass_matrix
        Ms = self.shell.mass_3d
        cr = self.rod.mesh.spec.rayleigh_damping / dt
        cs = self.shell.rayleigh_damping / dt

        # Gravity generalized forces
        gr_vec = np.zeros(n_r, dtype=np.float64)
        gr_vec[2::DOFS_PER_ROD_NODE] = gravity_z
        fr_ext = Mr @ gr_vec + (0.0 if rod_f_ext is None else np.asarray(rod_f_ext, dtype=np.float64).ravel())

        gs_vec = np.zeros(n_s, dtype=np.float64)
        gs_vec[2::12] = gravity_z
        fs_ext = Ms @ gs_vec + (0.0 if shell_f_ext is None else np.asarray(shell_f_ext, dtype=np.float64).ravel())

        d_idx_list = [int(i) for i in rod_dirichlet] + [n_r + int(i) for i in shell_dirichlet_sdofs]
        d_val_list = [float(v) for v in rod_dirichlet_vals] + [float(v) for v in shell_dirichlet_vals]
        d_idx = np.asarray(d_idx_list, dtype=np.int64)
        d_val = np.asarray(d_val_list, dtype=np.float64)

        free_mask = np.ones(n_tot, dtype=bool)
        if len(d_idx) > 0:
            free_mask[d_idx] = False
        free_idx = np.nonzero(free_mask)[0]

        q_all = np.concatenate([qr_c, qs_c])
        if len(d_idx) > 0:
            q_all[d_idx] = d_val

        def _eval_all(q_vec: np.ndarray, need_H: bool):
            qr = q_vec[:n_r]
            qs = q_vec[n_r:]
            self.rod.update_bishop_frames(qr)
            er, gr = self.rod.eval_energy_and_grad(qr, refresh_frames=False)
            em, eb, gs, Ks = self.shell.eval_energy_grad_stiffness(qs.reshape(-1, 3), compute_stiffness=need_H)
            ec, gcr, gcs, Hrr, Hss, Hrs, min_cl = evaluate_rod_to_shell_ipc_contact(
                self.rod.mesh, qr, self.shell_W_proxy, qs.reshape(-1, 3), d_hat_m=self.d_hat_m, kappa_b=self.kappa_b
            )
            in_r = 0.5 * inv_dt2 * float((qr - qr_tilde) @ (Mr @ (qr - qr_tilde))) + 0.5 * cr * float((qr - qr_c) @ (Mr @ (qr - qr_c)))
            in_s = 0.5 * inv_dt2 * float((qs - qs_tilde) @ (Ms @ (qs - qs_tilde))) + 0.5 * cs * float((qs - qs_c) @ (Ms @ (qs - qs_c)))
            obj = in_r + in_s + er + em + eb + ec - float(np.dot(fr_ext, qr)) - float(np.dot(fs_ext, qs))
            res_r = (inv_dt2 * Mr @ (qr - qr_tilde)) + (cr * Mr @ (qr - qr_c)) + gr + gcr - fr_ext
            res_s = (inv_dt2 * Ms @ (qs - qs_tilde)) + (cs * Ms @ (qs - qs_c)) + gs + gcs - fs_ext
            res_all = np.concatenate([res_r, res_s])
            H_all = None
            if need_H:
                Kr = self.rod.eval_hessian_fd_banded(qr)
                assert Ks is not None
                H_all = np.zeros((n_tot, n_tot), dtype=np.float64)
                H_all[:n_r, :n_r] = (inv_dt2 + cr) * Mr + Kr + Hrr
                H_all[n_r:, n_r:] = (inv_dt2 + cs) * Ms + Ks + Hss
                H_all[:n_r, n_r:] = Hrs
                H_all[n_r:, :n_r] = Hrs.T
            return obj, res_all, H_all, ec, min_cl

        obj, res, H, ec, min_cl = _eval_all(q_all, need_H=True)
        res_norm = float(np.linalg.norm(res[free_idx]))

        it = 0
        for it in range(1, max_iters + 1):
            if res_norm < tol:
                break
            assert H is not None
            H_ff = H[np.ix_(free_idx, free_idx)]
            rhs = -res[free_idx]
            reg = 1e-7
            dq_f = None
            for _ in range(12):
                try:
                    cf = cho_factor(H_ff + reg * np.eye(len(free_idx)), lower=True)
                    dq_f = cho_solve(cf, rhs)
                    if float(np.dot(rhs, dq_f)) > 0.0:
                        break
                except Exception:
                    pass
                reg *= 10.0
            if dq_f is None:
                break

            dq_full = np.zeros(n_tot, dtype=np.float64)
            dq_full[free_idx] = dq_f
            slope = float(np.dot(res[free_idx], dq_f))
            # Conservative line search guaranteeing strict non-penetration (min_cl > 0) AND descent
            eta = 1.0
            accepted = False
            for _ in range(14):
                q_try = q_all + eta * dq_full
                if len(d_idx) > 0:
                    q_try[d_idx] = d_val
                obj_t, _, _, _, min_cl_t = _eval_all(q_try, need_H=False)
                if min_cl_t > 1e-6 and (obj_t <= obj + 1e-4 * eta * slope or abs(obj_t - obj) < 1e-14):
                    q_all = q_try
                    accepted = True
                    break
                eta *= 0.5
            if not accepted:
                break
            obj, res, H, ec, min_cl = _eval_all(q_all, need_H=True)
            res_norm = float(np.linalg.norm(res[free_idx]))

        return UnifiedStepResult(
            q_rod_next=q_all[:n_r].copy(),
            q_shell_next=q_all[n_r:].reshape(self.shell.n_vec_dofs, 3).copy(),
            min_rod_shell_clearance_mm=round(1000.0 * min_cl, 4),
            contact_energy_j=float(ec),
            residual_norm=res_norm,
            n_iters=it,
            wall_time_ms=round((time.perf_counter() - t0) * 1000.0, 3),
        )

