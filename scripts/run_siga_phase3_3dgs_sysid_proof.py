"""Phase 3 Publication Proof: Anisotropic C1-3DGS + Two-Stage CMA-ES & Implicit Adjoint Multi-View Video SysID."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from convert_asset.hermitetwin_uni import (
    CameraSpec,
    HermiteRodGaussianRenderer,
    HermiteRodSpec,
    MultiViewTargetFrame,
    WarpBrazierRodSolver,
    build_straight_rod_mesh,
    run_two_stage_3dgs_adjoint_sysid,
)


def run_phase3_proof(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = HermiteRodSpec(length_m=0.16, n_elems=5, r_in_m=0.0055, r_out_m=0.0070, youngs_modulus_pa=1.6e6, enable_brazier=True)
    mesh = build_straight_rod_mesh(spec)
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")
    renderer_opt = HermiteRodGaussianRenderer(mesh, samples_per_elem=3, n_phi=12, device="cuda:0")
    renderer_hd = HermiteRodGaussianRenderer(mesh, samples_per_elem=5, n_phi=16, device="cuda:0")

    dirichlet = [0, 1, 2, 3, 4, 5, 6]
    d_vals = mesh.rest_q[dirichlet].copy()
    f_ext = np.zeros(mesh.n_dofs, dtype=np.float64)
    tip = (mesh.n_nodes - 1) * 10
    f_ext[tip + 2] = -0.25
    f_ext[tip + 6] = +0.0060

    true_params = {"E_scale": 1.72, "G_scale": 0.58}
    res_gt = solver.solve_equilibrium(mesh.rest_q, dirichlet_dofs=dirichlet, dirichlet_vals=d_vals, ext_force=f_ext, param_overrides=true_params, tol=1e-12)
    res_init = solver.solve_equilibrium(mesh.rest_q, dirichlet_dofs=dirichlet, dirichlet_vals=d_vals, ext_force=f_ext, param_overrides={"E_scale": 1.0, "G_scale": 1.0}, tol=1e-12)

    cams_opt = [
        CameraSpec(height=64, width=84, eye_xyz=(0.08, -0.25, 0.02), target_xyz=(0.08, 0.0, -0.025)),
        CameraSpec(height=64, width=84, eye_xyz=(0.24, -0.17, 0.07), target_xyz=(0.08, 0.0, -0.025)),
    ]
    targets = []
    with torch.no_grad():
        q_gt_t = torch.tensor(res_gt.q_final, device=renderer_opt.device, dtype=renderer_opt.dtype)
        for cam in cams_opt:
            o = renderer_opt.render(q_gt_t, cam)
            targets.append(MultiViewTargetFrame(cam=cam, target_rgb=o["rgb"], target_mask=o["silhouette"]))

    sysid = run_two_stage_3dgs_adjoint_sysid(
        solver,
        renderer_opt,
        targets,
        dirichlet_dofs=dirichlet,
        dirichlet_vals=d_vals,
        ext_force=f_ext,
        param_names=("E_scale", "G_scale"),
        init_log_params=(0.0, 0.0),
        cmaes_generations=5,
        cmaes_pop_size=6,
        adjoint_maxiter=14,
        seed=11,
    )

    # Render crisp HD 3DGS images (240x320) for visual comparison
    cam_hd = CameraSpec(height=240, width=320, eye_xyz=(0.08, -0.24, 0.02), target_xyz=(0.08, 0.0, -0.025))
    with torch.no_grad():
        img_gt = renderer_hd.render(torch.tensor(res_gt.q_final, device=renderer_hd.device, dtype=renderer_hd.dtype), cam_hd)["rgb"].cpu().numpy()
        img_init = renderer_hd.render(torch.tensor(res_init.q_final, device=renderer_hd.device, dtype=renderer_hd.dtype), cam_hd)["rgb"].cpu().numpy()
        img_rec = renderer_hd.render(torch.tensor(sysid.q_recovered, device=renderer_hd.device, dtype=renderer_hd.dtype), cam_hd)["rgb"].cpu().numpy()

    psnr_init = float(-10.0 * np.log10(max(float(np.mean((img_init - img_gt) ** 2)), 1e-12)))
    psnr_rec = float(-10.0 * np.log10(max(float(np.mean((img_rec - img_gt) ** 2)), 1e-12)))

    fig, axes = plt.subplots(1, 4, figsize=(19.2, 4.6), dpi=160)
    fig.patch.set_facecolor("#0b1120")
    for ax in axes:
        ax.set_facecolor("#111827")
        for sp_ax in ax.spines.values():
            sp_ax.set_color("#334155")

    axes[0].imshow(np.clip(img_gt, 0, 1))
    axes[0].set_title(f"A. Ground-Truth 3DGS Target\n(E={true_params['E_scale']:.2f}x, G={true_params['G_scale']:.2f}x)", color="#f8fafc", fontsize=10, fontweight="bold")
    axes[0].axis("off")

    axes[1].imshow(np.clip(img_init, 0, 1))
    axes[1].set_title(f"B. Initial Guess (1.0x, 1.0x)\nPSNR = {psnr_init:.1f} dB", color="#facc15", fontsize=10, fontweight="bold")
    axes[1].axis("off")

    axes[2].imshow(np.clip(img_rec, 0, 1))
    axes[2].set_title(
        f"C. Recovered C1-3DGS Twin\n(E={sysid.final_params['E_scale']:.3f}x, G={sysid.final_params['G_scale']:.3f}x | {psnr_rec:.1f} dB)",
        color="#4ade80",
        fontsize=10,
        fontweight="bold",
    )
    axes[2].axis("off")

    # Panel D: Two-Stage Log-Loss Convergence
    n1 = len(sysid.cmaes_loss_history)
    x1 = np.arange(n1)
    x2 = np.arange(n1 - 1, n1 - 1 + len(sysid.adjoint_loss_history))
    axes[3].semilogy(x1, np.maximum(sysid.cmaes_loss_history, 1e-12), "-o", color="#facc15", lw=2.0, ms=4, label="Stage 1: CMA-ES Global")
    axes[3].semilogy(x2, np.maximum(sysid.adjoint_loss_history, 1e-12), "-s", color="#38bdf8", lw=2.4, ms=4, label="Stage 2: 3DGS x Warp Implicit Adjoint")
    axes[3].axvline(n1 - 1, color="#475569", ls="--", lw=1.2)
    axes[3].set_title("D. Pixel-Space Real-to-Sim Convergence", color="#f8fafc", fontsize=10, fontweight="bold")
    axes[3].set_xlabel("Optimization Step", color="#e2e8f0")
    axes[3].set_ylabel("Multi-View RGB + Mask Loss (log)", color="#e2e8f0")
    axes[3].tick_params(colors="#cbd5e1", labelsize=8)
    axes[3].legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0", fontsize=8)
    axes[3].grid(color="#1e293b", alpha=0.8)

    plt.tight_layout()
    fig_path = out_dir / "siga_phase3_3dgs_sysid_proof.png"
    fig.savefig(fig_path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    summary = {
        "true_params": true_params,
        "cmaes_params": {k: round(v, 5) for k, v in sysid.cmaes_params.items()},
        "final_params": {k: round(v, 5) for k, v in sysid.final_params.items()},
        "rel_err_pct": {k: round(abs(sysid.final_params[k] - true_params[k]) / true_params[k] * 100.0, 4) for k in true_params},
        "init_loss": sysid.init_loss,
        "cmaes_loss": sysid.cmaes_loss,
        "final_loss": sysid.final_loss,
        "psnr_init_db": round(psnr_init, 2),
        "psnr_recovered_db": round(psnr_rec, 2),
        "wall_time_s": sysid.wall_time_s,
        "figure_png": str(fig_path),
    }
    (out_dir / "siga_phase3_sysid_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    out = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\2833f00c-81d5-45e3-842f-b50f4070bffb\scratch\siga_phase3")
    print(json.dumps(run_phase3_proof(out), indent=2))

