#!/usr/bin/env python3
"""Shared utilities for CVIU v3 counterfactual, optical feature, VLM, and risk-gate scripts."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


DEFAULT_SOURCE_ASSETS_ROOT = "/cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu"
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 768
STRICT_POINT_RE = re.compile(r"\s*Point:\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*")
RELAXED_XY_RE = re.compile(
    r"(?is)(?:point(?:_xy)?\s*[:=]\s*[\(\[]?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*[\)\]]?"
    r"|^\s*[\(\[]?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*[\)\]]?\s*$)"
)
MOLMO_POINT_RE = re.compile(
    r'<points?\s+[^>]*?(?:x1?|x)\s*=\s*"?(-?\d+(?:\.\d+)?)"?[^>]*?(?:y1?|y)\s*=\s*"?(-?\d+(?:\.\d+)?)"?[^>]*?/?>',
    re.IGNORECASE,
)
MOLMO2_COORDS_RE = re.compile(
    r'<(?:points?|tracks)\b[^>]*?\bcoords\s*=\s*"([^"]+)"',
    re.IGNORECASE,
)
MOLMO2_ANGLE_POINT_RE = re.compile(
    r"<\s*point\s*:\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
MOLMO2_TRIPLE_RE = re.compile(
    r"(?:^|[;\s,])\d+\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)"
)
JSON_POINT2D_RE = re.compile(
    r'"point_2d"\s*:\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]'
)
JSON_BBOX2D_RE = re.compile(
    r'"bbox_2d"\s*:\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]'
)


def repo_root_from_script(script_path: Path | None = None) -> Path:
    here = (script_path or Path(__file__)).resolve()
    for parent in here.parents:
        if (parent / ".git").exists() and (parent / "paper" / "shared" / "evidence").is_dir():
            return parent
    return here.parents[4]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_asset_path(raw_path: str | Path, assets_root: Path | None = None) -> Path:
    p = Path(raw_path)
    if p.exists():
        return p
    env_root = os.environ.get("CVIU_ASSETS_ROOT")
    override = assets_root or (Path(env_root).expanduser() if env_root else None)
    if override is not None:
        raw_str = str(raw_path).replace("\\", "/")
        prefix = DEFAULT_SOURCE_ASSETS_ROOT.rstrip("/") + "/"
        if raw_str.startswith(prefix):
            return override / raw_str[len(prefix) :]
        return override / p.name
    return p


def sanitize_pair_id(pair_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "__", pair_id).strip("_")


def parse_point_by_mode(raw: str, parser_mode: str = "strict") -> list[float] | None:
    if not isinstance(raw, str):
        return None
    if parser_mode == "strict":
        m = STRICT_POINT_RE.fullmatch(raw)
        if not m:
            return None
        vals = [float(m.group(1)), float(m.group(2))]
    elif parser_mode == "relaxed_xy":
        m = STRICT_POINT_RE.fullmatch(raw)
        if m:
            vals = [float(m.group(1)), float(m.group(2))]
        else:
            m2 = RELAXED_XY_RE.search(raw.strip())
            if not m2:
                return None
            x_s = m2.group(1) if m2.group(1) is not None else m2.group(3)
            y_s = m2.group(2) if m2.group(2) is not None else m2.group(4)
            vals = [float(x_s), float(y_s)]
    elif parser_mode == "molmo_0_100":
        mm = MOLMO_POINT_RE.search(raw)
        if mm:
            vals = [float(mm.group(1)) * 10.0, float(mm.group(2)) * 10.0]
        else:
            return parse_point_by_mode(raw, parser_mode="relaxed_xy")
    elif parser_mode == "molmo2_1000":
        m = STRICT_POINT_RE.fullmatch(raw)
        if m:
            vals = [float(m.group(1)), float(m.group(2))]
        else:
            mc = MOLMO2_COORDS_RE.search(raw)
            if mc:
                vals = None
                for seg in re.split(r"[\t:;,]+", mc.group(1).strip()):
                    nums = re.findall(r"-?\d+(?:\.\d+)?", seg)
                    if len(nums) >= 4 and (len(nums) - 1) % 3 == 0:
                        vals = [float(nums[2]), float(nums[3])]
                        break
                    if len(nums) >= 3 and len(nums) % 3 == 0:
                        vals = [float(nums[1]), float(nums[2])]
                        break
                    if len(nums) == 2:
                        vals = [float(nums[0]), float(nums[1])]
                        break
                if vals is None:
                    return parse_point_by_mode(raw, parser_mode="relaxed_xy")
            else:
                ma = MOLMO2_ANGLE_POINT_RE.search(raw)
                if ma:
                    vals = [float(ma.group(1)), float(ma.group(2))]
                else:
                    mm = MOLMO_POINT_RE.search(raw)
                    if mm:
                        vals = [float(mm.group(1)), float(mm.group(2))]
                    else:
                        return parse_point_by_mode(raw, parser_mode="relaxed_xy")
    elif parser_mode == "flex_1000":
        mj = JSON_POINT2D_RE.search(raw)
        mb = JSON_BBOX2D_RE.search(raw)
        if mj:
            vals = [float(mj.group(1)), float(mj.group(2))]
        elif mb:
            vals = [0.5 * (float(mb.group(1)) + float(mb.group(3))), 0.5 * (float(mb.group(2)) + float(mb.group(4)))]
        else:
            cleaned = re.sub(r"point_2d|bbox_2d", "", raw, flags=re.IGNORECASE)
            nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", cleaned)]
            if len(nums) == 4:
                vals = [0.5 * (nums[0] + nums[2]), 0.5 * (nums[1] + nums[3])]
            elif len(nums) == 2:
                vals = [nums[0], nums[1]]
            else:
                return parse_point_by_mode(raw, parser_mode="relaxed_xy")
    elif parser_mode == "unit_float_xy":
        nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", raw)]
        if len(nums) >= 4 and all(0.0 <= v <= 1.0 for v in nums[:4]):
            vals = [500.0 * (nums[0] + nums[2]), 500.0 * (nums[1] + nums[3])]
        elif len(nums) >= 2 and all(0.0 <= v <= 1.0 for v in nums[:2]) and not any(v > 1.0 for v in nums[:4]):
            vals = [1000.0 * nums[0], 1000.0 * nums[1]]
        else:
            return parse_point_by_mode(raw, parser_mode="relaxed_xy")
    else:
        raise ValueError(f"Unsupported parser_mode: {parser_mode}")

    if any(not math.isfinite(v) for v in vals):
        return None
    return vals


def score_normalized_point(
    point: Sequence[float] | None,
    mask: np.ndarray,
) -> tuple[bool, bool, bool]:
    """Score normalized [0, 1000) point against bool mask with exact 13_cviu_formal geometry."""
    h, w = mask.shape
    valid = point is not None and len(point) == 2 and all(0.0 <= float(v) < 1000.0 for v in point)
    if not valid:
        return False, False, False
    px_f = float(point[0]) * w / 1000.0
    py_f = float(point[1]) * h / 1000.0
    ix = min(w - 1, max(0, int(px_f)))
    iy = min(h - 1, max(0, int(py_f)))
    hit = bool(mask[iy, ix])
    ys, xs = np.where(mask)
    if len(xs):
        bbox_hit = bool(float(xs.min()) <= px_f < float(xs.max() + 1) and float(ys.min()) <= py_f < float(ys.max() + 1))
    else:
        bbox_hit = False
    return True, hit, bbox_hit


def point_displacement_px(
    pt_a: Sequence[float] | None,
    valid_a: bool,
    pt_b: Sequence[float] | None,
    valid_b: bool,
    width: int = IMAGE_WIDTH,
    height: int = IMAGE_HEIGHT,
) -> float | None:
    if not valid_a or not valid_b or pt_a is None or pt_b is None:
        return None
    dx = (float(pt_a[0]) - float(pt_b[0])) * (width / 1000.0)
    dy = (float(pt_a[1]) - float(pt_b[1])) * (height / 1000.0)
    return float(math.hypot(dx, dy))


def srgb_uint8_to_linear(rgb: np.ndarray) -> np.ndarray:
    c = rgb.astype(np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((np.maximum(c, 0.04045) + 0.055) / 1.055) ** 2.4)


def srgb_uint8_to_lab(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert uint8 sRGB (..., 3) to (Lab float64, linear_Y float64)."""
    lin = srgb_uint8_to_linear(rgb)
    r, g, b = lin[..., 0], lin[..., 1], lin[..., 2]
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b

    xn, yn, zn = 0.95047, 1.00000, 1.08883
    eps = 216.0 / 24389.0
    kappa = 24389.0 / 27.0

    def _f(t: np.ndarray) -> np.ndarray:
        return np.where(t > eps, np.cbrt(np.maximum(t, eps)), (kappa * t + 16.0) / 116.0)

    fx = _f(x / xn)
    fy = _f(y / yn)
    fz = _f(z / zn)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b_lab = 200.0 * (fy - fz)
    return np.stack([L, a, b_lab], axis=-1), y


def lab_to_srgb_uint8(lab: np.ndarray) -> np.ndarray:
    """Convert float CIE Lab (..., 3) back to clipped uint8 sRGB."""
    L = np.clip(lab[..., 0].astype(np.float64), 0.0, 100.0)
    a = lab[..., 1].astype(np.float64)
    b_lab = lab[..., 2].astype(np.float64)

    eps = 216.0 / 24389.0
    kappa = 24389.0 / 27.0
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b_lab / 200.0

    xr = np.where((fx ** 3) > eps, fx ** 3, (116.0 * fx - 16.0) / kappa)
    yr = np.where(L > (kappa * eps), ((L + 16.0) / 116.0) ** 3, L / kappa)
    zr = np.where((fz ** 3) > eps, fz ** 3, (116.0 * fz - 16.0) / kappa)

    x = xr * 0.95047
    y = yr * 1.00000
    z = zr * 1.08883

    r = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    lin = np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)
    srgb = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * (np.maximum(lin, 0.0031308) ** (1.0 / 2.4)) - 0.055)
    return np.clip(np.rint(srgb * 255.0), 0.0, 255.0).astype(np.uint8)


def scene_cluster_ratio_ci(
    scene_num_den: np.ndarray,
    draws: np.ndarray,
) -> dict[str, Any]:
    """Compute ratio estimate + 10,000-draw scene-cluster 95% CI from shape (S, 2) array."""
    num = scene_num_den[:, 0].astype(np.float64)
    den = scene_num_den[:, 1].astype(np.float64)
    tot_den = float(den.sum())
    tot_num = float(num.sum())
    totals = den[draws].sum(axis=1)
    vals = np.divide(num[draws].sum(axis=1), totals, out=np.full(len(draws), np.nan), where=totals > 0)
    finite = vals[np.isfinite(vals)]
    return {
        "estimate": (tot_num / tot_den) if tot_den > 0 else None,
        "numerator": tot_num,
        "denominator": tot_den,
        "scene_bootstrap_ci95": np.quantile(finite, [0.025, 0.975]).tolist() if len(finite) else None,
        "finite_bootstrap_draws": int(len(finite)),
        "degenerate_bootstrap": bool(len(finite) and np.ptp(finite) < 1e-12),
    }


def scene_cluster_diff_ci(
    num_den_b: np.ndarray,
    num_den_a: np.ndarray,
    draws: np.ndarray,
) -> dict[str, Any]:
    """Compute paired scene-cluster CI for (ratio_b - ratio_a)."""
    den_b_tot = float(num_den_b[:, 1].sum())
    den_a_tot = float(num_den_a[:, 1].sum())
    est_b = (float(num_den_b[:, 0].sum()) / den_b_tot) if den_b_tot > 0 else None
    est_a = (float(num_den_a[:, 0].sum()) / den_a_tot) if den_a_tot > 0 else None

    tot_b = num_den_b[:, 1][draws].sum(axis=1)
    tot_a = num_den_a[:, 1][draws].sum(axis=1)
    val_b = np.divide(num_den_b[:, 0][draws].sum(axis=1), tot_b, out=np.full(len(draws), np.nan), where=tot_b > 0)
    val_a = np.divide(num_den_a[:, 0][draws].sum(axis=1), tot_a, out=np.full(len(draws), np.nan), where=tot_a > 0)
    diff = val_b - val_a
    finite = diff[np.isfinite(diff)]
    return {
        "difference": (est_b - est_a) if (est_a is not None and est_b is not None) else None,
        "paired_scene_bootstrap_ci95": np.quantile(finite, [0.025, 0.975]).tolist() if len(finite) else None,
        "finite_bootstrap_draws": int(len(finite)),
    }


def roc_auc_score_np(y_true: Sequence[int], y_score: Sequence[float]) -> float | None:
    """Tie-aware exact ROC-AUC in pure numpy."""
    yt = np.asarray(y_true, dtype=np.int64)
    ys = np.asarray(y_score, dtype=np.float64)
    n_pos = int((yt == 1).sum())
    n_neg = int((yt == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return None
    order = np.argsort(ys, kind="mergesort")
    ys_sorted = ys[order]
    ranks = np.empty(len(ys), dtype=np.float64)
    i = 0
    n = len(ys_sorted)
    while i < n:
        j = i + 1
        while j < n and ys_sorted[j] == ys_sorted[i]:
            j += 1
        avg_rank = 0.5 * (i + 1 + j)
        ranks[order[i:j]] = avg_rank
        i = j
    pos_rank_sum = float(ranks[yt == 1].sum())
    return float((pos_rank_sum - 0.5 * n_pos * (n_pos + 1)) / (n_pos * n_neg))


def average_precision_np(y_true: Sequence[int], y_score: Sequence[float]) -> float | None:
    """Exact sklearn-compatible Average Precision (AUPRC) in pure numpy."""
    yt = np.asarray(y_true, dtype=np.int64)
    ys = np.asarray(y_score, dtype=np.float64)
    n_pos = int((yt == 1).sum())
    if n_pos == 0 or n_pos == len(yt):
        return None
    desc = np.argsort(-ys, kind="mergesort")
    y_sorted = yt[desc]
    ys_sorted = ys[desc]
    distinct = np.where(np.diff(ys_sorted) != 0)[0]
    threshold_idxs = np.r_[distinct, len(ys_sorted) - 1]
    tps = np.cumsum(y_sorted)[threshold_idxs].astype(np.float64)
    fps = (1 + threshold_idxs).astype(np.float64) - tps
    precision = np.divide(tps, tps + fps, out=np.ones_like(tps), where=(tps + fps) > 0)
    recall = tps / float(n_pos)
    prev_recall = np.r_[0.0, recall[:-1]]
    return float(np.sum((recall - prev_recall) * precision))


def fit_standardized_l2_logreg(
    X_train: np.ndarray,
    y_train: np.ndarray,
    *,
    c_reg: float = 1.0,
    max_iter: int = 80,
    tol: float = 1e-10,
) -> dict[str, Any]:
    """Fit standardized L2 logistic regression via damped Newton (sklearn penalty=l2 objective)."""
    X = np.asarray(X_train, dtype=np.float64)
    y = np.asarray(y_train, dtype=np.float64)
    n, d = X.shape
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std = np.where(std > 1e-8, std, 1.0)
    Xs = (X - mean) / std
    n_pos = float(y.sum())
    if n_pos <= 0.0 or n_pos >= float(n):
        p0 = float(np.clip(n_pos / max(n, 1), 1e-6, 1.0 - 1e-6))
        return {
            "mean": mean,
            "std": std,
            "w": np.zeros(d, dtype=np.float64),
            "b": float(math.log(p0 / (1.0 - p0))),
            "constant_prior": True,
        }

    Xa = np.hstack([Xs, np.ones((n, 1), dtype=np.float64)])
    theta = np.zeros(d + 1, dtype=np.float64)
    reg_diag = np.zeros(d + 1, dtype=np.float64)
    reg_diag[:d] = 1.0

    def _loss(th: np.ndarray) -> float:
        z = Xa @ th
        # log(1 + exp(z)) - y*z summed over n, scaled by C, plus 0.5*||w||^2
        log_term = np.logaddexp(0.0, z) - y * z
        return float(c_reg * np.sum(log_term) + 0.5 * np.dot(th[:d], th[:d]))

    cur_loss = _loss(theta)
    for _ in range(max_iter):
        z = np.clip(Xa @ theta, -35.0, 35.0)
        p = 1.0 / (1.0 + np.exp(-z))
        grad = c_reg * (Xa.T @ (p - y)) + reg_diag * theta
        if float(np.max(np.abs(grad))) < tol:
            break
        w_diag = np.maximum(p * (1.0 - p), 1e-12)
        hess = c_reg * (Xa.T * w_diag) @ Xa + np.diag(reg_diag)
        hess[d, d] += 1e-10
        step = np.linalg.solve(hess, grad)
        alpha = 1.0
        cur_dot = float(np.dot(grad, step))
        while alpha > 1e-8:
            cand = theta - alpha * step
            if _loss(cand) <= cur_loss - 1e-4 * alpha * cur_dot:
                break
            alpha *= 0.5
        new_theta = theta - alpha * step
        new_loss = _loss(new_theta)
        if abs(cur_loss - new_loss) < 1e-12 and float(np.max(np.abs(alpha * step))) < 1e-9:
            theta = new_theta
            break
        theta = new_theta
        cur_loss = new_loss

    return {
        "mean": mean,
        "std": std,
        "w": theta[:d],
        "b": float(theta[d]),
        "constant_prior": False,
    }


def predict_proba_logreg(model: Mapping[str, Any], X: np.ndarray) -> np.ndarray:
    Xf = np.asarray(X, dtype=np.float64)
    Xs = (Xf - model["mean"]) / model["std"]
    z = np.clip(Xs @ model["w"] + float(model["b"]), -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-z))

