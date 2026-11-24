"""Two-stage CMA-ES + sensitivity/adjoint L-BFGS-B SysID for thin-shell digital twins."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable

import numpy as np
from scipy.optimize import minimize


@dataclass(frozen=True)
class SysIDResult:
    """Recorded result from two-stage CMA-ES + L-BFGS-B parameter identification."""

    method_name: str
    best_params: np.ndarray
    best_loss: float
    loss_history: list[float]
    cmaes_evals: int
    adjoint_evals: int
    wall_time_s: float


def run_cmaes_pure_numpy(
    loss_fn: Callable[[np.ndarray], float],
    x0: np.ndarray,
    bounds_low: np.ndarray,
    bounds_high: np.ndarray,
    *,
    sigma0: float = 0.45,
    max_generations: int = 8,
    pop_size: int = 8,
    seed: int = 42,
) -> tuple[np.ndarray, float, list[float], int]:
    """Pure-NumPy (mu, lambda)-CMA-ES over bounded continuous parameter space."""
    rng = np.random.default_rng(seed)
    dim = len(x0)
    mean = np.clip(np.asarray(x0, dtype=np.float64), bounds_low, bounds_high)
    sigma = float(sigma0)

    lam = int(max(pop_size, 4 + int(3 * np.log(max(dim, 2)))))
    mu = lam // 2
    weights = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
    weights /= np.sum(weights)
    mueff = 1.0 / np.sum(weights ** 2)

    cc = (4.0 + mueff / dim) / (dim + 4.0 + 2.0 * mueff / dim)
    cs = (mueff + 2.0) / (dim + mueff + 5.0)
    c1 = 2.0 / ((dim + 1.3) ** 2 + mueff)
    cmu = min(1.0 - c1, 2.0 * (mueff - 2.0 + 1.0 / mueff) / ((dim + 2.0) ** 2 + mueff))
    damps = 1.0 + 2.0 * max(0.0, np.sqrt((mueff - 1.0) / (dim + 1.0)) - 1.0) + cs
    chi_n = np.sqrt(dim) * (1.0 - 1.0 / (4.0 * dim) + 1.0 / (21.0 * dim * dim))

    pc = np.zeros(dim, dtype=np.float64)
    ps = np.zeros(dim, dtype=np.float64)
    C = np.eye(dim, dtype=np.float64)

    best_x = mean.copy()
    best_f = float(loss_fn(best_x))
    history = [best_f]
    eval_count = 1

    for _gen in range(max_generations):
        eigvals, eigvecs = np.linalg.eigh(0.5 * (C + C.T))
        eigvals = np.maximum(eigvals, 1e-12)
        B = eigvecs
        D = np.sqrt(eigvals)
        invsqrtC = B @ np.diag(1.0 / D) @ B.T

        arz = rng.standard_normal((lam, dim))
        arx = np.clip(mean[None, :] + sigma * (arz @ (B * D[None, :]).T), bounds_low, bounds_high)
        fits = np.empty(lam, dtype=np.float64)
        for k in range(lam):
            fits[k] = float(loss_fn(arx[k]))
            eval_count += 1
            if fits[k] < best_f:
                best_f = float(fits[k])
                best_x = arx[k].copy()

        order = np.argsort(fits)
        x_sel = arx[order[:mu]]
        mean_old = mean.copy()
        mean = np.sum(weights[:, None] * x_sel, axis=0)

        y_w = (mean - mean_old) / max(sigma, 1e-12)
        ps = (1.0 - cs) * ps + np.sqrt(cs * (2.0 - cs) * mueff) * (invsqrtC @ y_w)
        hsig = float(
            np.linalg.norm(ps) / np.sqrt(max(1.0 - (1.0 - cs) ** (2 * (_gen + 1)), 1e-9)) / chi_n
            < (1.4 + 2.0 / (dim + 1.0))
        )
        pc = (1.0 - cc) * pc + hsig * np.sqrt(cc * (2.0 - cc) * mueff) * y_w

        y_sel = (x_sel - mean_old[None, :]) / max(sigma, 1e-12)
        C = (
            (1.0 - c1 - cmu) * C
            + c1 * (np.outer(pc, pc) + (1.0 - hsig) * cc * (2.0 - cc) * C)
            + cmu * (y_sel.T @ (weights[:, None] * y_sel))
        )
        sigma *= np.exp((cs / damps) * (np.linalg.norm(ps) / chi_n - 1.0))
        sigma = float(np.clip(sigma, 1e-3, 1.5))
        history.append(best_f)

    return best_x, best_f, history, eval_count


def run_two_stage_sysid(
    *,
    method_name: str,
    loss_fn: Callable[[np.ndarray], float],
    x0: np.ndarray,
    bounds_low: np.ndarray,
    bounds_high: np.ndarray,
    cmaes_generations: int = 6,
    cmaes_pop_size: int = 8,
    adjoint_maxiter: int = 8,
    seed: int = 42,
) -> SysIDResult:
    """Run Stage-1 CMA-ES global search followed by Stage-2 sensitivity L-BFGS-B polish."""
    t0 = time.perf_counter()
    x_cma, f_cma, hist, cma_evals = run_cmaes_pure_numpy(
        loss_fn,
        x0=x0,
        bounds_low=bounds_low,
        bounds_high=bounds_high,
        max_generations=cmaes_generations,
        pop_size=cmaes_pop_size,
        seed=seed,
    )

    adj_evals = 0

    def _wrapped_loss(x: np.ndarray) -> float:
        nonlocal adj_evals
        adj_evals += 1
        return float(loss_fn(x))

    bounds = list(zip(bounds_low.tolist(), bounds_high.tolist()))
    res = minimize(
        _wrapped_loss,
        x0=x_cma,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": int(adjoint_maxiter), "maxfun": max(8, int(adjoint_maxiter) * 3), "eps": 2e-2, "ftol": 1e-5},
    )
    best_x = np.asarray(res.x if res.fun <= f_cma else x_cma, dtype=np.float64)
    best_f = float(min(float(res.fun), f_cma))
    hist.append(best_f)

    return SysIDResult(
        method_name=method_name,
        best_params=best_x,
        best_loss=best_f,
        loss_history=hist,
        cmaes_evals=cma_evals,
        adjoint_evals=adj_evals,
        wall_time_s=round(time.perf_counter() - t0, 4),
    )
