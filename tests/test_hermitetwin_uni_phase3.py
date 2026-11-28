"""Phase 3 GPU tests: C1-frame Anisotropic 3DGS EWA autograd, chained pixel-level Implicit Adjoint, and Two-Stage SysID."""

from __future__ import annotations

import math

import numpy as np
import torch

from convert_asset.deformable_v08_hermite.bicubic_hermite_shell import build_hermite_shell_mesh
from convert_asset.hermitetwin_uni import (
    CameraSpec,
    HermiteRodGaussianRenderer,
    HermiteRodSpec,
    HermiteShellGaussianRenderer,
    MultiViewTargetFrame,
    WarpBrazierRodSolver,
    build_straight_rod_mesh,
    evaluate_multiview_pixel_loss_and_grad_q,
    run_two_stage_3dgs_adjoint_sysid,
)


def test_anisotropic_3dgs_rod_and_shell_render_and_autograd() -> None:
    """Verify deformation-gradient anisotropic 3DGS renders cleanly on CUDA and yields exact dL/dq autograd."""
    # 1. Bent + twisted + ovalized 1D Brazier tube
    rod_spec = HermiteRodSpec(length_m=0.18, n_elems=5, r_in_m=0.0055, r_out_m=0.0072, enable_brazier=True)
    rod_mesh = build_straight_rod_mesh(rod_spec)
    rod_rend = HermiteRodGaussianRenderer(rod_mesh, samples_per_elem=3, n_phi=10, device="cuda:0")
    cam = CameraSpec(height=64, width=80, eye_xyz=(0.09, -0.28, 0.05), target_xyz=(0.09, 0.0, -0.02))

    q_rod = rod_mesh.rest_q.copy()
    for i in range(rod_mesh.n_nodes):
        u = i / float(rod_mesh.n_elems)
        q_rod[i * 10 + 2] -= 0.03 * u * u
        q_rod[i * 10 + 6] += 0.8 * u
        q_rod[i * 10 + 8] -= 0.18 * math.sin(math.pi * u)

    q_t = torch.tensor(q_rod, device=rod_rend.device, dtype=rod_rend.dtype, requires_grad=True)
    out = rod_rend.render(q_t, cam)
    assert out["rgb"].shape == (64, 80, 3)
    assert float(out["silhouette"].max().item()) > 0.80

    # Check exact autograd vs central FD on a sample pixel-space scalar objective
    loss = torch.mean(out["rgb"] ** 2) + torch.mean(out["silhouette"] ** 2)
    (g_auto,) = torch.autograd.grad(loss, q_t)
    g_auto_np = g_auto.detach().cpu().numpy()

    eps = 1e-6
    for idx in (22, 36, 38):  # z-pos, twist theta, Brazier ovalization alpha2
        qp = q_rod.copy()
        qm = q_rod.copy()
        qp[idx] += eps
        qm[idx] -= eps
        with torch.no_grad():
            op = rod_rend.render(torch.tensor(qp, device=rod_rend.device, dtype=rod_rend.dtype), cam)
            om = rod_rend.render(torch.tensor(qm, device=rod_rend.device, dtype=rod_rend.dtype), cam)
            lp = float((torch.mean(op["rgb"] ** 2) + torch.mean(op["silhouette"] ** 2)).item())
            lm = float((torch.mean(om["rgb"] ** 2) + torch.mean(om["silhouette"] ** 2)).item())
        g_fd = (lp - lm) / (2.0 * eps)
        assert abs(g_auto_np[idx] - g_fd) / max(abs(g_fd), 1e-8) < 1e-4

    # 2. Curved 2D Kirchhoff-Love thin shell
    sh_mesh = build_hermite_shell_mesh(nx=2, ny=2, length_u_m=0.18, length_v_m=0.18, area_density_kg_m2=0.30, origin_xyz=(0.0, 0.0, 0.0))
    sh_rend = HermiteShellGaussianRenderer(sh_mesh, gs_nu=10, gs_nv=10, device="cuda:0")
    cam_sh = CameraSpec(height=64, width=80, eye_xyz=(0.0, -0.32, 0.20), target_xyz=(0.0, 0.0, 0.0))
    qs_t = torch.tensor(sh_mesh.rest_q, device=sh_rend.device, dtype=sh_rend.dtype, requires_grad=True)
    out_sh = sh_rend.render(qs_t, cam_sh)
    assert float(out_sh["silhouette"].max().item()) > 0.80
    (g_sh,) = torch.autograd.grad(torch.mean(out_sh["rgb"] ** 2), qs_t)
    assert float(torch.linalg.norm(g_sh).item()) > 1e-5


def test_end_to_end_pixel_loss_implicit_adjoint_gradient() -> None:
    """Verify full chained gradient dL_pixel/dpsi = (PyTorch 3DGS autograd) x (Warp Implicit Adjoint) vs FD."""
    spec = HermiteRodSpec(length_m=0.16, n_elems=5, r_in_m=0.0055, r_out_m=0.0070, youngs_modulus_pa=1.6e6, enable_brazier=True)
    mesh = build_straight_rod_mesh(spec)
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")
    renderer = HermiteRodGaussianRenderer(mesh, samples_per_elem=3, n_phi=10, device="cuda:0")

    dirichlet = [0, 1, 2, 3, 4, 5, 6]
    d_vals = mesh.rest_q[dirichlet].copy()
    f_ext = np.zeros(mesh.n_dofs, dtype=np.float64)
    tip = (mesh.n_nodes - 1) * 10
    f_ext[tip + 2] = -0.22  # bending + Brazier ovalization
    f_ext[tip + 6] = +0.0045  # axial torsion -> shifts longitudinal stripe pixels!

    # Ground-truth rendered image at true parameters
    cam = CameraSpec(height=64, width=80, eye_xyz=(0.08, -0.26, 0.03), target_xyz=(0.08, 0.0, -0.02))
    res_gt = solver.solve_equilibrium(
        mesh.rest_q,
        dirichlet_dofs=dirichlet,
        dirichlet_vals=d_vals,
        ext_force=f_ext,
        param_overrides={"E_scale": 1.35, "G_scale": 0.75},
        tol=1e-12,
    )
    with torch.no_grad():
        out_gt = renderer.render(torch.tensor(res_gt.q_final, device=renderer.device, dtype=renderer.dtype), cam)
    targets = [MultiViewTargetFrame(cam=cam, target_rgb=out_gt["rgb"], target_mask=out_gt["silhouette"])]

    # Evaluate chained Implicit Adjoint at nominal (1.0, 1.0)
    res_nom = solver.solve_equilibrium(mesh.rest_q, dirichlet_dofs=dirichlet, dirichlet_vals=d_vals, ext_force=f_ext, tol=1e-12)
    _, dL_dq = evaluate_multiview_pixel_loss_and_grad_q(renderer, res_nom.q_final, targets)
    adj = solver.compute_implicit_adjoint(res_nom.q_final, dL_dq, dirichlet_dofs=dirichlet, param_names=("E_scale", "G_scale"))

    eps_p = 1e-4
    # E_scale gradient is < 1e-3 exact; G_scale couples weakly to Bishop-frame
    # refresh across FD equilibrium re-solves (~0.32% frozen-frame residual).
    tols = {"E_scale": 1e-3, "G_scale": 5e-3}
    for pname in ("E_scale", "G_scale"):
        rp = solver.solve_equilibrium(res_nom.q_final, dirichlet_dofs=dirichlet, dirichlet_vals=d_vals, ext_force=f_ext, param_overrides={pname: 1.0 + eps_p}, tol=1e-12)
        rm = solver.solve_equilibrium(res_nom.q_final, dirichlet_dofs=dirichlet, dirichlet_vals=d_vals, ext_force=f_ext, param_overrides={pname: 1.0 - eps_p}, tol=1e-12)
        lp, _ = evaluate_multiview_pixel_loss_and_grad_q(renderer, rp.q_final, targets)
        lm, _ = evaluate_multiview_pixel_loss_and_grad_q(renderer, rm.q_final, targets)
        g_fd = (lp - lm) / (2.0 * eps_p)
        rel = abs(adj.grad_params[pname] - g_fd) / max(abs(g_fd), 1e-10)
        assert rel < tols[pname], (
            f"Chained pixel->adjoint gradient mismatch on {pname}: "
            f"adj={adj.grad_params[pname]:.6e}, fd={g_fd:.6e}, rel={rel:.3e}"
        )


def test_two_stage_cmaes_adjoint_sysid_recovers_hidden_material_from_images() -> None:
    """Verify Two-Stage CMA-ES + Implicit Adjoint recovers hidden (E_scale, G_scale) to < 2% from pure 3DGS images."""
    spec = HermiteRodSpec(length_m=0.16, n_elems=5, r_in_m=0.0055, r_out_m=0.0070, youngs_modulus_pa=1.6e6, enable_brazier=True)
    mesh = build_straight_rod_mesh(spec)
    solver = WarpBrazierRodSolver(mesh, device="cuda:0")
    renderer = HermiteRodGaussianRenderer(mesh, samples_per_elem=3, n_phi=10, device="cuda:0")

    dirichlet = [0, 1, 2, 3, 4, 5, 6]
    d_vals = mesh.rest_q[dirichlet].copy()
    f_ext = np.zeros(mesh.n_dofs, dtype=np.float64)
    tip = (mesh.n_nodes - 1) * 10
    f_ext[tip + 2] = -0.24
    f_ext[tip + 6] = +0.0055

    true_params = {"E_scale": 1.65, "G_scale": 0.62}
    res_gt = solver.solve_equilibrium(mesh.rest_q, dirichlet_dofs=dirichlet, dirichlet_vals=d_vals, ext_force=f_ext, param_overrides=true_params, tol=1e-12)

    cams = [
        CameraSpec(height=56, width=72, eye_xyz=(0.08, -0.26, 0.02), target_xyz=(0.08, 0.0, -0.02)),
        CameraSpec(height=56, width=72, eye_xyz=(0.24, -0.18, 0.08), target_xyz=(0.08, 0.0, -0.02)),
    ]
    targets = []
    with torch.no_grad():
        q_gt_t = torch.tensor(res_gt.q_final, device=renderer.device, dtype=renderer.dtype)
        for cam in cams:
            o = renderer.render(q_gt_t, cam)
            targets.append(MultiViewTargetFrame(cam=cam, target_rgb=o["rgb"], target_mask=o["silhouette"]))

    sysid = run_two_stage_3dgs_adjoint_sysid(
        solver,
        renderer,
        targets,
        dirichlet_dofs=dirichlet,
        dirichlet_vals=d_vals,
        ext_force=f_ext,
        param_names=("E_scale", "G_scale"),
        init_log_params=(0.0, 0.0),
        cmaes_generations=4,
        cmaes_pop_size=6,
        adjoint_maxiter=12,
        seed=7,
    )

    err_e = abs(sysid.final_params["E_scale"] - true_params["E_scale"]) / true_params["E_scale"]
    err_g = abs(sysid.final_params["G_scale"] - true_params["G_scale"]) / true_params["G_scale"]
    assert sysid.final_loss < 0.1 * sysid.cmaes_loss, "Stage-2 Implicit Adjoint must sharply polish Stage-1 CMA-ES!"
    assert err_e < 0.02, f"E_scale recovery error too high: {err_e*100:.2f}% (got {sysid.final_params['E_scale']:.4f})"
    assert err_g < 0.02, f"G_scale recovery error too high: {err_g*100:.2f}% (got {sysid.final_params['G_scale']:.4f})"

