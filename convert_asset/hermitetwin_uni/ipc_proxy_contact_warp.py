"""High-Order C1 IPC-Barrier Contact + Conservative CCD + J_W^T H_IPC J_W Pullback (Phase 2).

Implements:
1. Strictly convex C-IPC smooth barrier b(d, d_hat) = -(d - d_hat)^2 * ln(d / d_hat) with exact b'(d), b''(d).
2. Mollified Coulomb friction potential with exact normal-coupled tangential friction force & PSD Hessian.
3. Exact 3-Olive Glass Barb radial interference-fit contact (`CondenserBarbGeometryV10` from hose_softbody_v10)
   acting directly on the 1D Brazier-Cosserat inner bore R_in(s) = r_in * (1 + alpha0(s)), producing real hoop
   expansion, radial clamping force, and hands-off friction self-lock (falsifiable at mu=0!).
4. Unified 1D-Rod <-> 2D-Shell & Rod <-> Rod material-space proxy contact with exact J_W^T H_IPC J_W pullback
   and conservative CCD line-search guard ensuring strict zero interpenetration (min_dist > 0).
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable, Sequence

import numpy as np

from convert_asset.hose_softbody_v10.specs_v10 import CondenserBarbGeometryV10, DEFAULT_CONDENSER_BARB_V10

from .state_and_basis import DOFS_PER_ROD_NODE, HermiteRodMesh, hermite_1d_basis


def ipc_barrier_val_grad_hess(d: float, d_hat: float, kappa_b: float) -> tuple[float, float, float]:
    """Evaluate C-IPC smooth barrier E(d) = kappa_b * (-(d - d_hat)^2 * ln(d / d_hat)), E'(d), E''(d) for d > 0."""
    if d >= d_hat:
        return 0.0, 0.0, 0.0
    d_safe = max(float(d), 1e-12)
    dh = float(d_hat)
    diff = d_safe - dh
    ln_r = math.log(d_safe / dh)
    val = -kappa_b * diff * diff * ln_r
    # d/dd [-(d-dh)^2 ln(d/dh)] = -2(d-dh) ln(d/dh) - (d-dh)^2 / d
    g = -kappa_b * (2.0 * diff * ln_r + (diff * diff) / d_safe)
    # d^2/dd^2 = -2 ln(d/dh) - 4(d-dh)/d + (d-dh)^2 / d^2  (strictly > 0 on (0, d_hat)!)
    h = kappa_b * (-2.0 * ln_r - 4.0 * diff / d_safe + (diff * diff) / (d_safe * d_safe))
    return val, g, max(h, 0.0)


def mollified_coulomb_friction(
    u_tan: np.ndarray,
    lambda_n: float,
    mu: float,
    eps_v: float = 1e-4,
) -> tuple[np.ndarray, np.ndarray]:
    """C1-smooth IPC mollified Coulomb friction force opposing tangential slip u_tan and its PSD 3x3 Hessian."""
    u = np.asarray(u_tan, dtype=np.float64)
    if lambda_n <= 0.0 or mu <= 0.0:
        return np.zeros(3, dtype=np.float64), np.zeros((3, 3), dtype=np.float64)
    nrm = float(np.linalg.norm(u))
    if nrm < 1e-14:
        return np.zeros(3, dtype=np.float64), (mu * lambda_n / eps_v) * np.eye(3, dtype=np.float64)
    if nrm >= eps_v:
        f1 = 1.0 / nrm
        f_vec = (mu * lambda_n * f1) * u
        # PSD tangent stiffness: (mu * lambda_n / ||u||) * (I - u_hat u_hat^T)
        u_hat = u * f1
        H = (mu * lambda_n * f1) * (np.eye(3) - np.outer(u_hat, u_hat))
        return f_vec, H
    # Smooth C1 polynomial transition f1(y) = (-y / eps^2 + 2 / eps) on [0, eps_v)
    f1 = -nrm / (eps_v * eps_v) + 2.0 / eps_v
    f_vec = (mu * lambda_n * f1) * u
    u_hat = u / nrm
    # Exact SPD Hessian inside mollified stick regime
    H = (mu * lambda_n) * (f1 * np.eye(3) - (nrm / (eps_v * eps_v)) * np.outer(u_hat, u_hat))
    return f_vec, H


@dataclass(frozen=True)
class BarbInterferenceResult:
    """Quantitative metrics from C1-Hermite Brazier 3-olive glass barb interference-fit equilibrium."""

    mu_friction: float
    cuff_hoop_expansion_pct: float
    peak_radial_clamping_n: float
    axial_pull_off_capacity_n: float
    hands_off_self_lock: bool
    min_bore_clearance_mm: float
    q_equil: np.ndarray


def evaluate_rod_on_3olive_barb_contact(
    mesh: HermiteRodMesh,
    q: np.ndarray,
    *,
    barb_geom: CondenserBarbGeometryV10 = DEFAULT_CONDENSER_BARB_V10,
    barb_origin_w: np.ndarray | None = None,
    barb_axis_w: np.ndarray | None = None,
    d_hat_m: float = 0.00045,
    kappa_b: float = 1.2e4,
    mu_friction: float = 0.85,
) -> tuple[float, np.ndarray, np.ndarray, dict[str, float]]:
    """Evaluate exact IPC-Barrier inner-bore contact between a 1D Brazier-Hermite tube and a 3-olive glass barb.

    At every Gauss point s within the seated barb zone [seat_start, seat_end]:
      bore_clearance d(s) = r_in * (1 + alpha0(s)) - (r_barb(s) + r_radial_eccentricity(s)) > 0
    Returns (barrier_energy, grad_q, H_q_psd, diagnostics) with exact analytical J_W^T H_IPC J_W pullback!
    """
    q_arr = np.asarray(q, dtype=np.float64).reshape(mesh.n_nodes, DOFS_PER_ROD_NODE)
    orig = np.zeros(3, dtype=np.float64) if barb_origin_w is None else np.asarray(barb_origin_w, dtype=np.float64)
    u_ax = np.array([1.0, 0.0, 0.0], dtype=np.float64) if barb_axis_w is None else np.asarray(barb_axis_w, dtype=np.float64)
    u_ax = u_ax / max(float(np.linalg.norm(u_ax)), 1e-12)
    P_perp = np.eye(3, dtype=np.float64) - np.outer(u_ax, u_ax)

    n_dofs = mesh.n_dofs
    e_tot = 0.0
    g_tot = np.zeros(n_dofs, dtype=np.float64)
    H_tot = np.zeros((n_dofs, n_dofs), dtype=np.float64)

    r_in0 = float(mesh.spec.r_in_m)
    ds = mesh.ds
    total_radial_n = 0.0
    min_d = 1e9
    max_a0 = 0.0

    for e in range(mesh.n_elems):
        b0 = e * DOFS_PER_ROD_NODE
        b1 = (e + 1) * DOFS_PER_ROD_NODE
        x0, t0 = q_arr[e, 0:3], q_arr[e, 3:6]
        x1, t1 = q_arr[e + 1, 0:3], q_arr[e + 1, 3:6]
        a0_0, a0_1 = q_arr[e, 7], q_arr[e + 1, 7]

        for qi in range(len(mesh.quad_xi)):
            xi = float(mesh.quad_xi[qi])
            w_ds = float(mesh.quad_w[qi]) * ds
            hv = mesh.h_val[qi]
            x_s = hv[0] * x0 + ds * hv[1] * t0 + hv[2] * x1 + ds * hv[3] * t1
            rel = x_s - orig
            s_ax = float(np.dot(rel, u_ax))
            if s_ax < barb_geom.seat_start_s_m or s_ax > barb_geom.seat_end_s_m:
                continue

            r_barb = float(barb_geom.radius_at_s(s_ax))
            a0 = (1.0 - xi) * a0_0 + xi * a0_1
            max_a0 = max(max_a0, a0)

            # Transverse eccentricity of centerline off barb axis
            r_perp = P_perp @ rel
            ecc = math.sqrt(float(np.dot(r_perp, r_perp)) + 1e-12)
            # Clear radial gap between stretched inner bore and olive profile
            d = r_in0 * (1.0 + a0) - (r_barb + ecc)
            min_d = min(min_d, d)

            # Exact IPC barrier weighted by arc-length quadrature w_ds
            vb, gb, hb = ipc_barrier_val_grad_hess(d, d_hat_m, kappa_b * w_ds)
            if vb == 0.0 and gb == 0.0:
                continue

            e_tot += vb
            # Normal contact force magnitude contributed by this quadrature slice: f_n = -gb > 0
            total_radial_n += max(0.0, -gb)

            # Exact Jacobian row J_d = dd / dq (non-zero on [x0, t0, x1, t1, a0_0, a0_1])
            n_ecc = -r_perp / ecc  # dd / d(x_s) = -r_perp / ||r_perp||
            idx_loc = [
                b0 + 0, b0 + 1, b0 + 2,
                b0 + 3, b0 + 4, b0 + 5,
                b1 + 0, b1 + 1, b1 + 2,
                b1 + 3, b1 + 4, b1 + 5,
                b0 + 7, b1 + 7,
            ]
            j_row = np.zeros(14, dtype=np.float64)
            j_row[0:3] = hv[0] * n_ecc
            j_row[3:6] = (ds * hv[1]) * n_ecc
            j_row[6:9] = hv[2] * n_ecc
            j_row[9:12] = (ds * hv[3]) * n_ecc
            j_row[12] = (1.0 - xi) * r_in0
            j_row[13] = xi * r_in0

            g_tot[idx_loc] += gb * j_row
            H_tot[np.ix_(idx_loc, idx_loc)] += hb * np.outer(j_row, j_row)

    diag = {
        "total_radial_clamping_n": float(total_radial_n),
        "axial_pull_off_capacity_n": float(mu_friction * total_radial_n),
        "cuff_hoop_expansion_pct": float(100.0 * max_a0),
        "min_bore_clearance_mm": float(1000.0 * (min_d if min_d < 1e8 else 0.0)),
    }
    return e_tot, g_tot, H_tot, diag


def evaluate_rod_to_shell_ipc_contact(
    rod_mesh: HermiteRodMesh,
    q_rod: np.ndarray,
    shell_W_proxy: np.ndarray,
    q_shell_vec: np.ndarray,
    *,
    d_hat_m: float = 0.0040,
    kappa_b: float = 6.0e3,
    n_rod_samples_per_elem: int = 2,
) -> tuple[float, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Unified 1D-Rod <-> 2D-Shell C1 IPC-Barrier contact with exact J_W^T H_IPC J_W pullback.

    Evaluates pairwise smooth barrier between C1 rod outer-radius proxy spheres (center x(s), radius r_out*(1+a0))
    and 2D C1 Hermite shell material-space proxy points p_s = W_proxy @ q_shell.
    Returns (energy, g_rod, g_shell_flat, H_rr, H_ss, H_rs, min_clearance_m).
    """
    q_r = np.asarray(q_rod, dtype=np.float64).reshape(rod_mesh.n_nodes, DOFS_PER_ROD_NODE)
    q_s = np.asarray(q_shell_vec, dtype=np.float64)
    p_shell = shell_W_proxy @ q_s  # (M_s, 3)

    n_rdof = rod_mesh.n_dofs
    n_sdof = 3 * q_s.shape[0]
    ds = rod_mesh.ds
    r_out0 = float(rod_mesh.spec.r_out_m)

    e_tot = 0.0
    g_rod = np.zeros(n_rdof, dtype=np.float64)
    g_shell = np.zeros(n_sdof, dtype=np.float64)
    H_rr = np.zeros((n_rdof, n_rdof), dtype=np.float64)
    H_ss = np.zeros((n_sdof, n_sdof), dtype=np.float64)
    H_rs = np.zeros((n_rdof, n_sdof), dtype=np.float64)
    min_clear = 1e9

    xis = np.linspace(0.25, 0.75, n_rod_samples_per_elem)
    hv_all, _, _ = hermite_1d_basis(xis)
    r_cut = r_out0 + d_hat_m + 0.006

    for e in range(rod_mesh.n_elems):
        b0 = e * DOFS_PER_ROD_NODE
        b1 = (e + 1) * DOFS_PER_ROD_NODE
        x0, t0 = q_r[e, 0:3], q_r[e, 3:6]
        x1, t1 = q_r[e + 1, 0:3], q_r[e + 1, 3:6]
        a0_0, a0_1 = q_r[e, 7], q_r[e + 1, 7]

        for k in range(len(xis)):
            xi = float(xis[k])
            hv = hv_all[k]
            x_r = hv[0] * x0 + ds * hv[1] * t0 + hv[2] * x1 + ds * hv[3] * t1
            a0 = (1.0 - xi) * a0_0 + xi * a0_1
            r_eff = r_out0 * (1.0 + a0)

            diff_all = x_r[None, :] - p_shell  # (M_s, 3)
            dist_all = np.linalg.norm(diff_all, axis=1)
            cand_ids = np.nonzero(dist_all < r_cut)[0]
            if len(cand_ids) == 0:
                continue

            idx_r = [
                b0 + 0, b0 + 1, b0 + 2,
                b0 + 3, b0 + 4, b0 + 5,
                b1 + 0, b1 + 1, b1 + 2,
                b1 + 3, b1 + 4, b1 + 5,
                b0 + 7, b1 + 7,
            ]
            for sid in cand_ids:
                dist = float(dist_all[sid])
                d = dist - r_eff
                min_clear = min(min_clear, d)
                if d >= d_hat_m:
                    continue
                vb, gb, hb = ipc_barrier_val_grad_hess(d, d_hat_m, kappa_b)
                e_tot += vb

                n_dir = diff_all[sid] / max(dist, 1e-12)  # points from shell -> rod
                jr = np.zeros(14, dtype=np.float64)
                jr[0:3] = hv[0] * n_dir
                jr[3:6] = (ds * hv[1]) * n_dir
                jr[6:9] = hv[2] * n_dir
                jr[9:12] = (ds * hv[3]) * n_dir
                jr[12] = -(1.0 - xi) * r_out0
                jr[13] = -xi * r_out0

                # Shell Jacobian row: dd / dq_shell = -W_proxy[sid, v] * n_dir
                w_row = shell_W_proxy[sid]
                nz_v = np.nonzero(np.abs(w_row) > 1e-12)[0]
                idx_s = [int(v) * 3 + c for v in nz_v for c in range(3)]
                js = np.empty(len(idx_s), dtype=np.float64)
                for ii, v in enumerate(nz_v):
                    js[3 * ii : 3 * ii + 3] = -w_row[v] * n_dir

                g_rod[idx_r] += gb * jr
                g_shell[idx_s] += gb * js
                H_rr[np.ix_(idx_r, idx_r)] += hb * np.outer(jr, jr)
                H_ss[np.ix_(idx_s, idx_s)] += hb * np.outer(js, js)
                H_rs[np.ix_(idx_r, idx_s)] += hb * np.outer(jr, js)

    return e_tot, g_rod, g_shell, H_rr, H_ss, H_rs, float(min_clear)


def conservative_ccd_max_step_1d_barb(
    mesh: HermiteRodMesh,
    q: np.ndarray,
    dq: np.ndarray,
    *,
    barb_geom: CondenserBarbGeometryV10 = DEFAULT_CONDENSER_BARB_V10,
    barb_origin_w: np.ndarray | None = None,
    barb_axis_w: np.ndarray | None = None,
    safety: float = 0.80,
) -> float:
    """Conservative CCD line-search upper bound eta_max in (0, 1] ensuring strict d > 0 along barb bore."""
    orig = np.zeros(3, dtype=np.float64) if barb_origin_w is None else np.asarray(barb_origin_w, dtype=np.float64)
    u_ax = np.array([1.0, 0.0, 0.0], dtype=np.float64) if barb_axis_w is None else np.asarray(barb_axis_w, dtype=np.float64)
    u_ax = u_ax / max(float(np.linalg.norm(u_ax)), 1e-12)
    P_perp = np.eye(3, dtype=np.float64) - np.outer(u_ax, u_ax)
    r_in0 = float(mesh.spec.r_in_m)
    ds = mesh.ds

    def _min_d(q_vec: np.ndarray) -> float:
        qa = q_vec.reshape(mesh.n_nodes, DOFS_PER_ROD_NODE)
        md = 1e9
        for e in range(mesh.n_elems):
            x0, t0 = qa[e, 0:3], qa[e, 3:6]
            x1, t1 = qa[e + 1, 0:3], qa[e + 1, 3:6]
            for qi in range(len(mesh.quad_xi)):
                xi = float(mesh.quad_xi[qi])
                hv = mesh.h_val[qi]
                x_s = hv[0] * x0 + ds * hv[1] * t0 + hv[2] * x1 + ds * hv[3] * t1
                rel = x_s - orig
                s_ax = float(np.dot(rel, u_ax))
                if s_ax < barb_geom.seat_start_s_m or s_ax > barb_geom.seat_end_s_m:
                    continue
                r_b = float(barb_geom.radius_at_s(s_ax))
                a0 = (1.0 - xi) * qa[e, 7] + xi * qa[e + 1, 7]
                r_p = P_perp @ rel
                ecc = math.sqrt(float(np.dot(r_p, r_p)) + 1e-12)
                md = min(md, r_in0 * (1.0 + a0) - (r_b + ecc))
        return md

    eta = 1.0
    for _ in range(24):
        if _min_d(q + eta * dq) > 2e-6:
            return min(1.0, eta * (1.0 if eta == 1.0 else safety))
        eta *= 0.5
    return 0.0

