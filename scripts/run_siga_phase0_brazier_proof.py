"""Phase 0/1 First Quantitative Proof & Publication Figure: Solid DER Rod vs Hollow C1-Hermite Brazier Tube."""

from __future__ import annotations

import json
import math
from pathlib import Path
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from convert_asset.hermitetwin_uni import (
    HermiteRodSpec,
    WarpBrazierRodSolver,
    analytical_brazier_critical_values,
    build_straight_rod_mesh,
    evaluate_brazier_tube_surface,
)


def run_brazier_proof(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Classic thin-walled elastomeric tube: R0 = 7.0 mm, wall h_w = 1.0 mm (R0/h_w = 7)
    spec_h = HermiteRodSpec(
        length_m=0.20,
        n_elems=8,
        r_in_m=0.0065,
        r_out_m=0.0075,
        youngs_modulus_pa=2.0e6,
        poissons_ratio=0.40,
        enable_brazier=True,
    )
    spec_s = HermiteRodSpec(
        length_m=0.20,
        n_elems=8,
        r_in_m=0.0065,
        r_out_m=0.0075,
        youngs_modulus_pa=2.0e6,
        poissons_ratio=0.40,
        enable_brazier=False,
    )
    crit = analytical_brazier_critical_values(spec_h)
    mesh_h = build_straight_rod_mesh(spec_h)
    mesh_s = build_straight_rod_mesh(spec_s)
    sol_h = WarpBrazierRodSolver(mesh_h, device="cuda:0")
    sol_s = WarpBrazierRodSolver(mesh_s, device="cuda:0")

    locked = [i * 10 + d for i in range(mesh_h.n_nodes) for d in range(7)]
    kappas = np.linspace(0.02, 1.85 * crit["kappa_crit_inv_m"], 28)

    m_solid = []
    m_brazier = []
    m_analytic = []
    oval_brazier = []
    step_ms_list = []

    q_prev = mesh_h.rest_q.copy()
    for kap in kappas:
        R_arc = 1.0 / float(kap)
        q_arc = mesh_h.rest_q.copy()
        for i in range(mesh_h.n_nodes):
            s = i * mesh_h.ds
            phi = s * float(kap)
            b = i * 10
            q_arc[b + 0] = R_arc * math.sin(phi)
            q_arc[b + 2] = R_arc * (1.0 - math.cos(phi))
            q_arc[b + 3] = math.cos(phi)
            q_arc[b + 5] = math.sin(phi)

        # Warm-start cross-section DOFs for continuation along Brazier equilibrium path
        q_init = q_arc.copy()
        for i in range(mesh_h.n_nodes):
            q_init[i * 10 + 7 : i * 10 + 10] = q_prev[i * 10 + 7 : i * 10 + 10]

        t0 = time.perf_counter()
        res_h = sol_h.solve_equilibrium(q_init, dirichlet_dofs=locked, dirichlet_vals=q_arc[locked], tol=1e-11)
        step_ms_list.append((time.perf_counter() - t0) * 1000.0)
        q_prev = res_h.q_final.copy()

        # Bending moment M(kappa) = d(Energy/L) / d(kappa) via central step around kappa
        dk = 1e-4 * crit["kappa_crit_inv_m"]
        e_list = []
        for sign in (-1.0, +1.0):
            kk = float(kap) + sign * dk
            Ra = 1.0 / kk
            qa = res_h.q_final.copy()
            for i in range(mesh_h.n_nodes):
                s = i * mesh_h.ds
                phi = s * kk
                b = i * 10
                qa[b + 0] = Ra * math.sin(phi)
                qa[b + 2] = Ra * (1.0 - math.cos(phi))
                qa[b + 3] = math.cos(phi)
                qa[b + 5] = math.sin(phi)
            # Envelope theorem: at converged alpha*(kappa), dW(kappa, alpha*(kappa))/dkappa == partial W / partial kappa!
            sol_h.update_bishop_frames(qa)
            ek, _ = sol_h.eval_energy_and_grad(qa, refresh_frames=False)
            e_list.append(ek)
        m_b = (e_list[1] - e_list[0]) / (2.0 * dk * spec_h.length_m)

        m_brazier.append(m_b)
        m_solid.append(spec_s.ei0_nm2 * float(kap))
        # Exact analytical Brazier (1927) curve M(k) = EI*k*(1 - (3*(1-nu^2)*R0^4 / (2*hw^2))*k^2) up to softening
        ratio = float(kap) / crit["kappa_crit_inv_m"]
        m_analytic.append(spec_h.ei0_nm2 * float(kap) * (1.0 - (1.0 / 3.0) * (ratio**2)))
        surf = evaluate_brazier_tube_surface(mesh_h, res_h.q_final)
        oval_brazier.append(float(surf["ovalization"].mean()))

    m_brazier_arr = np.asarray(m_brazier)
    peak_idx = int(np.argmax(m_brazier_arr))
    sim_kappa_peak = float(kappas[peak_idx])
    sim_moment_peak = float(m_brazier_arr[peak_idx])
    moment_err_pct = abs(sim_moment_peak - crit["moment_crit_nm"]) / crit["moment_crit_nm"] * 100.0

    # Benchmark pure single GPU Warp energy+grad kernel latency
    sol_h.update_bishop_frames(q_prev)
    t0 = time.perf_counter()
    n_bench = 200
    for _ in range(n_bench):
        sol_h.eval_energy_and_grad(q_prev, refresh_frames=False)
    kernel_ms = (time.perf_counter() - t0) * 1000.0 / n_bench

    # Generate crisp 3-panel publication figure
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8), dpi=160)
    fig.patch.set_facecolor("#0b1120")
    for ax in axes:
        ax.set_facecolor("#111827")
        ax.tick_params(colors="#cbd5e1", labelsize=9)
        for sp_ax in ax.spines.values():
            sp_ax.set_color("#334155")

    k_norm = kappas / crit["kappa_crit_inv_m"]
    # Panel 1: Moment-Curvature Brazier Instability
    axes[0].plot(k_norm, np.asarray(m_solid) * 1e3, "--", color="#facc15", lw=2.0, label="Solid / DER Rod (alpha=0)")
    axes[0].plot(k_norm, np.asarray(m_brazier) * 1e3, "-", color="#38bdf8", lw=2.6, label="Ours: C1-Hermite Brazier (Warp GPU)")
    mask_a = k_norm <= 1.35
    axes[0].plot(k_norm[mask_a], np.asarray(m_analytic)[mask_a] * 1e3, ":", color="#fb7185", lw=2.0, label="Brazier (1927) Classical Theory")
    axes[0].axvline(1.0, color="#475569", ls="-.", lw=1.2)
    axes[0].scatter([sim_kappa_peak / crit["kappa_crit_inv_m"]], [sim_moment_peak * 1e3], color="#22c55e", s=55, zorder=5, label=f"Sim Peak ({sim_moment_peak*1e3:.2f} mN·m)")
    axes[0].set_title("A. Brazier Moment-Curvature Instability", color="#f8fafc", fontsize=11, fontweight="bold")
    axes[0].set_xlabel(r"Normalized Curvature $\kappa / \kappa_{\mathrm{crit}}$", color="#e2e8f0")
    axes[0].set_ylabel("Bending Moment M (mN·m)", color="#e2e8f0")
    axes[0].legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0", fontsize=8)
    axes[0].grid(color="#1e293b", alpha=0.8)

    # Panel 2: Ovalization Growth & Cross-Sectional Silhouettes
    axes[1].plot(k_norm, oval_brazier, "-o", ms=3.5, color="#34d399", lw=2.2, label=r"Simulated Ovalization $\zeta = \sqrt{\alpha_2^2+\beta_2^2}$")
    axes[1].axhline(2.0 / 9.0, color="#fb7185", ls="--", lw=1.4, label=r"Brazier Critical Flattening $\zeta^* = 2/9$")
    axes[1].set_title("B. Cross-Sectional Ovalization Growth", color="#f8fafc", fontsize=11, fontweight="bold")
    axes[1].set_xlabel(r"Normalized Curvature $\kappa / \kappa_{\mathrm{crit}}$", color="#e2e8f0")
    axes[1].set_ylabel(r"Quadrupole Ovalization $\zeta$", color="#e2e8f0")
    axes[1].legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0", fontsize=8)
    axes[1].grid(color="#1e293b", alpha=0.8)

    # Panel 3: Direct 2D Cross-Section Flattening Profiles at 4 Curvatures
    phis = np.linspace(0.0, 2.0 * math.pi, 180)
    for frac, col, lbl in ((0.0, "#94a3b8", "Rest (0.0)"), (0.5, "#38bdf8", "0.5 k_crit"), (1.0, "#34d399", "1.0 k_crit"), (1.7, "#fb7185", "1.7 k_crit (Kinked)")):
        idx_k = int(np.argmin(np.abs(k_norm - frac)))
        z_v = 0.0 if frac == 0.0 else oval_brazier[idx_k]
        # Inextensional Brazier cross-section shape
        r_th = 1.0 - z_v * np.cos(2.0 * phis)
        t_th = +0.5 * z_v * np.sin(2.0 * phis)
        xc = r_th * np.cos(phis) - t_th * np.sin(phis)
        yc = r_th * np.sin(phis) + t_th * np.cos(phis)
        axes[2].plot(xc, yc, color=col, lw=2.2, label=f"{lbl} (zeta={z_v:.2f})")
    axes[2].set_aspect("equal", "box")
    axes[2].set_xlim(-1.45, 1.45)
    axes[2].set_ylim(-1.45, 1.45)
    axes[2].set_title("C. Hollow Tube Cross-Section Flattening", color="#f8fafc", fontsize=11, fontweight="bold")
    axes[2].set_xlabel("Transverse X / R0", color="#e2e8f0")
    axes[2].set_ylabel("Bending Plane Z / R0", color="#e2e8f0")
    axes[2].legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0", fontsize=8, loc="upper right")
    axes[2].grid(color="#1e293b", alpha=0.8)

    plt.tight_layout()
    fig_path = out_dir / "siga_phase0_brazier_proof.png"
    fig.savefig(fig_path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    summary = {
        "device": sol_h.device,
        "warp_kernel_ms_per_eval": round(kernel_ms, 4),
        "analytical_kappa_crit_inv_m": round(crit["kappa_crit_inv_m"], 4),
        "analytical_moment_crit_mnm": round(crit["moment_crit_nm"] * 1e3, 4),
        "simulated_kappa_peak_inv_m": round(sim_kappa_peak, 4),
        "simulated_moment_peak_mnm": round(sim_moment_peak * 1e3, 4),
        "peak_moment_rel_err_pct": round(moment_err_pct, 2),
        "max_ovalization_at_1p85_kcrit": round(float(oval_brazier[-1]), 4),
        "figure_png": str(fig_path),
    }
    (out_dir / "siga_phase0_brazier_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    out = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\2833f00c-81d5-45e3-842f-b50f4070bffb\scratch\siga_phase0")
    res = run_brazier_proof(out)
    print(json.dumps(res, indent=2))

