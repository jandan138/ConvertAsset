"""Dual-mesh barycentric volumetric and local-frame shell skinning operators (v0.3)."""

from __future__ import annotations

import numpy as np


def _closest_point_on_tri_bary(p: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (closest_point, bary_weights[3]) for point p onto triangle (a, b, c) (Ericson)."""
    ab = b - a
    ac = c - a
    ap = p - a

    d1 = float(np.dot(ab, ap))
    d2 = float(np.dot(ac, ap))
    if d1 <= 0.0 and d2 <= 0.0:
        return a.copy(), np.array([1.0, 0.0, 0.0], dtype=np.float64)

    bp = p - b
    d3 = float(np.dot(ab, bp))
    d4 = float(np.dot(ac, bp))
    if d3 >= 0.0 and d4 <= d3:
        return b.copy(), np.array([0.0, 1.0, 0.0], dtype=np.float64)

    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        return a + v * ab, np.array([1.0 - v, v, 0.0], dtype=np.float64)

    cp = p - c
    d5 = float(np.dot(ab, cp))
    d6 = float(np.dot(ac, cp))
    if d6 >= 0.0 and d5 <= d6:
        return c.copy(), np.array([0.0, 0.0, 1.0], dtype=np.float64)

    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        return a + w * ac, np.array([1.0 - w, 0.0, w], dtype=np.float64)

    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return b + w * (c - b), np.array([0.0, 1.0 - w, w], dtype=np.float64)

    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    u = 1.0 - v - w
    return a + ab * v + ac * w, np.array([u, v, w], dtype=np.float64)


def _tri_local_frame(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    """Build covariant orthonormal (3, 3) column frame [t1, t2, n] for triangle (p0, p1, p2)."""
    e1 = p1 - p0
    n1 = float(np.linalg.norm(e1))
    t1 = e1 / max(n1, 1e-9)
    n_vec = np.cross(e1, p2 - p0)
    nn = float(np.linalg.norm(n_vec))
    n_ax = n_vec / max(nn, 1e-9)
    t2 = np.cross(n_ax, t1)
    t2_n = float(np.linalg.norm(t2))
    t2 = t2 / max(t2_n, 1e-9)
    return np.column_stack((t1, t2, n_ax))


def build_tet_barycentric_skinning(
    rest_phys_pts: np.ndarray,
    tets: np.ndarray,
    vis_pts: np.ndarray,
) -> tuple[np.ndarray, float]:
    """Bind high-poly visual vertices to positive-volume tetrahedra with exact partition-of-unity weights."""
    phys = np.asarray(rest_phys_pts, dtype=np.float64)
    elem = np.asarray(tets, dtype=np.int64)
    vis = np.asarray(vis_pts, dtype=np.float64)

    p0 = phys[elem[:, 0]]
    dm = np.stack((phys[elem[:, 1]] - p0, phys[elem[:, 2]] - p0, phys[elem[:, 3]] - p0), axis=-1)
    dets = np.linalg.det(dm)
    valid_mask = np.abs(dets) > 1e-11
    if not np.any(valid_mask):
        raise ValueError("No valid non-degenerate tetrahedra found for skinning.")
    elem_v = elem[valid_mask]
    dm_v = dm[valid_mask]
    dm_inv = np.linalg.inv(dm_v)
    centroids = phys[elem_v].mean(axis=1)  # (M, 3)

    w_skin = np.zeros((len(vis), len(phys)), dtype=np.float64)
    k_top = min(20, len(elem_v))
    for vi, vp in enumerate(vis):
        d2 = np.sum((centroids - vp[None, :]) ** 2, axis=1)
        cand_ids = np.argpartition(d2, k_top - 1)[:k_top] if k_top < len(elem_v) else np.arange(len(elem_v))
        best_score = -1e18
        best_tet = int(cand_ids[0])
        best_w4 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        for tid in cand_ids:
            a, b, c, d_i = elem_v[tid]
            bary3 = dm_inv[tid] @ (vp - phys[a])
            w4 = np.array([1.0 - float(np.sum(bary3)), float(bary3[0]), float(bary3[1]), float(bary3[2])], dtype=np.float64)
            # Prefer containing tet first, then minimum overshoot outside [0, 1]
            min_w = float(np.min(w4))
            l2_pen = float(np.sum(np.maximum(0.0, -w4) ** 2))
            score = min_w - 0.15 * l2_pen
            if score > best_score:
                best_score = score
                best_tet = int(tid)
                best_w4 = w4
        w_skin[vi, elem_v[best_tet]] = best_w4

    max_err = float(np.linalg.norm(w_skin @ phys - vis, axis=1).max()) if len(vis) else 0.0
    return w_skin, max_err


def deform_tet_skinned_points(w_skin: np.ndarray, cur_phys_pts: np.ndarray) -> np.ndarray:
    """Evaluate deformed high-poly visual vertices under tetrahedral barycentric skinning."""
    return np.asarray(w_skin, dtype=np.float64) @ np.asarray(cur_phys_pts, dtype=np.float64)


def build_shell_normal_skinning(
    rest_phys_pts: np.ndarray,
    tris: np.ndarray,
    vis_pts: np.ndarray,
) -> tuple[dict[str, np.ndarray], float]:
    """Bind high-poly visual vertices to nearest physics triangle covariant local frame."""
    phys = np.asarray(rest_phys_pts, dtype=np.float64)
    tr = np.asarray(tris, dtype=np.int64)
    vis = np.asarray(vis_pts, dtype=np.float64)

    tri_centers = phys[tr].mean(axis=1)
    k_top = min(16, len(tr))
    tri_ids = np.zeros((len(vis),), dtype=np.int32)
    bary_w = np.zeros((len(vis), 3), dtype=np.float64)
    local_offsets = np.zeros((len(vis), 3), dtype=np.float64)

    frames = np.stack([_tri_local_frame(phys[t[0]], phys[t[1]], phys[t[2]]) for t in tr], axis=0)

    for vi, vp in enumerate(vis):
        d2 = np.sum((tri_centers - vp[None, :]) ** 2, axis=1)
        cand = np.argpartition(d2, k_top - 1)[:k_top] if k_top < len(tr) else np.arange(len(tr))
        best_dist = 1e18
        best_ti = 0
        best_b = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        best_cp = phys[0]
        for ti in cand:
            a, b, c = tr[ti]
            cp, bw = _closest_point_on_tri_bary(vp, phys[a], phys[b], phys[c])
            dist = float(np.linalg.norm(vp - cp))
            if dist < best_dist:
                best_dist = dist
                best_ti = int(ti)
                best_b = bw
                best_cp = cp
        tri_ids[vi] = best_ti
        bary_w[vi] = best_b
        local_offsets[vi] = frames[best_ti].T @ (vp - best_cp)

    skin = {
        "mode": np.array(["shell_frame"]),
        "tri_ids": tri_ids,
        "bary_weights": bary_w,
        "local_offsets": local_offsets,
        "tris": tr.astype(np.int32),
    }
    recon = deform_shell_skinned_points(phys, skin)
    max_err = float(np.linalg.norm(recon - vis, axis=1).max()) if len(vis) else 0.0
    return skin, max_err


def deform_shell_skinned_points(cur_phys_pts: np.ndarray, skin: dict[str, np.ndarray]) -> np.ndarray:
    """Reconstruct deformed high-poly visual vertices via covariant triangle frames."""
    phys = np.asarray(cur_phys_pts, dtype=np.float64)
    tr = np.asarray(skin["tris"], dtype=np.int64)
    tri_ids = np.asarray(skin["tri_ids"], dtype=np.int64)
    bw = np.asarray(skin["bary_weights"], dtype=np.float64)
    offsets = np.asarray(skin["local_offsets"], dtype=np.float64)

    frames = np.stack([_tri_local_frame(phys[t[0]], phys[t[1]], phys[t[2]]) for t in tr], axis=0)
    bound_tris = tr[tri_ids]
    base_pts = (
        bw[:, 0:1] * phys[bound_tris[:, 0]]
        + bw[:, 1:2] * phys[bound_tris[:, 1]]
        + bw[:, 2:3] * phys[bound_tris[:, 2]]
    )
    world_off = np.einsum("vij,vj->vi", frames[tri_ids], offsets)
    return base_pts + world_off

