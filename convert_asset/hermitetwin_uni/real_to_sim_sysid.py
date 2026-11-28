"""Two-Stage Differentiable Multi-View Video SysID: CMA-ES + (PyTorch 3DGS Autograd x Warp Implicit Adjoint)."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Sequence

import numpy as np
from scipy.optimize import minimize
import torch

from convert_asset.deformable_v08_hermite.sysid_cmaes_adjoint import run_cmaes_pure_numpy

from .gsplat_c1_renderer import CameraSpec, HermiteRodGaussianRenderer
from .rod_brazier_warp import WarpBrazierRodSolver


@dataclass(frozen=True)
class MultiViewTargetFrame:
    """Observed target camera view (RGB + Silhouette mask) for Real-to-Sim SysID."""

    cam: CameraSpec
    target_rgb: torch.Tensor  # (H, W, 3) on CUDA
    target_mask: torch.Tensor  # (H, W) on CUDA


@dataclass
class PixelSysIDResult:
    """Full audit record of Two-Stage CMA-ES + Implicit Adjoint pixel-level parameter identification."""

    param_names: tuple[str, ...]
    init_params: dict[str, float]
    cmaes_params: dict[str, float]
    final_params: dict[str, float]
    init_loss: float
    cmaes_loss: float
    final_loss: float
    cmaes_loss_history: list[float]
    adjoint_loss_history: list[float]
    cmaes_evals: int
    adjoint_evals: int
    wall_time_s: float
    q_recovered: np.ndarray


def evaluate_multiview_pixel_loss_and_grad_q(
    renderer: HermiteRodGaussianRenderer,
    q_rod_np: np.ndarray,
    targets: Sequence[MultiViewTargetFrame],
    *,
    w_rgb: float = 1.0,
    w_mask: float = 1.5,
) -> tuple[float, np.ndarray]:
    """Compute exact multi-view RGB + Silhouette loss and exact dL/dq via PyTorch 3DGS autograd on CUDA."""
    q_t = torch.tensor(q_rod_np, device=renderer.device, dtype=renderer.dtype, requires_grad=True)
    loss_tot = torch.zeros((), device=renderer.device, dtype=renderer.dtype)
    for tgt in targets:
        out = renderer.render(q_t, tgt.cam)
        l_rgb = torch.mean((out["rgb"] - tgt.target_rgb) ** 2)
        l_msk = torch.mean((out["silhouette"] - tgt.target_mask) ** 2)
        loss_tot = loss_tot + w_rgb * l_rgb + w_mask * l_msk
    loss_tot = loss_tot / float(max(len(targets), 1))
    (g_q,) = torch.autograd.grad(loss_tot, q_t)
    return float(loss_tot.detach().cpu().item()), g_q.detach().cpu().numpy().astype(np.float64)


def run_two_stage_3dgs_adjoint_sysid(
    solver: WarpBrazierRodSolver,
    renderer: HermiteRodGaussianRenderer,
    targets: Sequence[MultiViewTargetFrame],
    *,
    dirichlet_dofs: Sequence[int],
    dirichlet_vals: Sequence[float],
    ext_force: np.ndarray,
    param_names: Sequence[str] = ("E_scale", "G_scale", "K_oval_scale"),
    init_log_params: Sequence[float] | None = None,
    log_bounds: tuple[float, float] = (-1.4, 1.4),
    cmaes_generations: int = 5,
    cmaes_pop_size: int = 8,
    adjoint_maxiter: int = 12,
    seed: int = 42,
) -> PixelSysIDResult:
    """Two-stage pixel-space Real-to-Sim SysID: Stage-1 CMA-ES + Stage-2 Implicit Adjoint L-BFGS-B."""
    t0 = time.perf_counter()
    pnames = tuple(param_names)
    dim = len(pnames)
    x0 = np.zeros(dim, dtype=np.float64) if init_log_params is None else np.asarray(init_log_params, dtype=np.float64)
    lo = np.full(dim, float(log_bounds[0]), dtype=np.float64)
    hi = np.full(dim, float(log_bounds[1]), dtype=np.float64)

    q_cache = solver.mesh.rest_q.copy()

    def _log_to_dict(x_log: np.ndarray) -> dict[str, float]:
        return {k: float(np.exp(v)) for k, v in zip(pnames, x_log)}

    def _forward_only(x_log: np.ndarray) -> float:
        nonlocal q_cache
        pdict = _log_to_dict(x_log)
        res = solver.solve_equilibrium(
            q_cache,
            dirichlet_dofs=dirichlet_dofs,
            dirichlet_vals=dirichlet_vals,
            ext_force=ext_force,
            param_overrides=pdict,
            tol=1e-10,
        )
        q_cache = res.q_final.copy()
        with torch.no_grad():
            q_t = torch.tensor(res.q_final, device=renderer.device, dtype=renderer.dtype)
            l_tot = 0.0
            for tgt in targets:
                out = renderer.render(q_t, tgt.cam)
                l_tot += float(torch.mean((out["rgb"] - tgt.target_rgb) ** 2).item()) + 1.5 * float(
                    torch.mean((out["silhouette"] - tgt.target_mask) ** 2).item()
                )
            return l_tot / float(max(len(targets), 1))

    init_loss = _forward_only(x0)

    # Stage 1: Global CMA-ES exploration
    x_cma, f_cma, cma_hist, cma_evals = run_cmaes_pure_numpy(
        _forward_only,
        x0=x0,
        bounds_low=lo,
        bounds_high=hi,
        sigma0=0.40,
        max_generations=cmaes_generations,
        pop_size=cmaes_pop_size,
        seed=seed,
    )

    # Stage 2: Exact Implicit Adjoint (PyTorch 3DGS autograd x Warp Implicit Adjoint) L-BFGS-B polish!
    adj_hist: list[float] = [float(f_cma)]
    adj_evals = 0
    best_x = x_cma.copy()
    best_f = float(f_cma)
    best_q = q_cache.copy()

    def _val_and_grad_log(x_log: np.ndarray) -> tuple[float, np.ndarray]:
        nonlocal q_cache, adj_evals, best_x, best_f, best_q
        adj_evals += 1
        pdict = _log_to_dict(x_log)
        res = solver.solve_equilibrium(
            q_cache,
            dirichlet_dofs=dirichlet_dofs,
            dirichlet_vals=dirichlet_vals,
            ext_force=ext_force,
            param_overrides=pdict,
            tol=1e-11,
        )
        q_cache = res.q_final.copy()
        loss_val, dL_dq = evaluate_multiview_pixel_loss_and_grad_q(renderer, res.q_final, targets)
        adj = solver.compute_implicit_adjoint(
            res.q_final,
            dL_dq,
            dirichlet_dofs=dirichlet_dofs,
            param_names=pnames,
            param_overrides=pdict,
        )
        # Chain rule for log-parameterization: dL/d(log psi) = psi * (dL/dpsi)
        g_log = np.array([pdict[k] * adj.grad_params[k] for k in pnames], dtype=np.float64)
        adj_hist.append(loss_val)
        if loss_val < best_f:
            best_f = loss_val
            best_x = x_log.copy()
            best_q = res.q_final.copy()
        return loss_val, g_log

    bounds = list(zip(lo.tolist(), hi.tolist()))
    minimize(
        _val_and_grad_log,
        x0=x_cma,
        method="L-BFGS-B",
        jac=True,
        bounds=bounds,
        options={"maxiter": int(adjoint_maxiter), "ftol": 1e-12, "gtol": 1e-8},
    )

    return PixelSysIDResult(
        param_names=pnames,
        init_params=_log_to_dict(x0),
        cmaes_params=_log_to_dict(x_cma),
        final_params=_log_to_dict(best_x),
        init_loss=float(init_loss),
        cmaes_loss=float(f_cma),
        final_loss=float(best_f),
        cmaes_loss_history=cma_hist,
        adjoint_loss_history=adj_hist,
        cmaes_evals=cma_evals,
        adjoint_evals=adj_evals,
        wall_time_s=round(time.perf_counter() - t0, 3),
        q_recovered=best_q,
    )

