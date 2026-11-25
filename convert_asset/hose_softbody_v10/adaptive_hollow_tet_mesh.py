"""Non-uniform adaptive hollow annular tetrahedral mesh builder for Route B PhysX GPU FEM hoses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from convert_asset.deformable_v03.sculpted_assets import _orient_tets_positive, _surface_tris_from_tets
from convert_asset.distillation_v04.deformable_specs_v04 import _bishop_frames


@dataclass(frozen=True)
class AdaptiveHollowTubeMesh:
    """Conforming 5-tet hollow tube mesh with high-density cuff(s) and graded mid-span."""

    rest_points: np.ndarray  # (V, 3) float64
    tets: np.ndarray  # (T, 4) int64 positively oriented
    surface_tris: np.ndarray  # (F, 3) int64
    ring_s: np.ndarray  # (K,) arc-length coordinate [0..L]
    n_rings: int
    n_theta: int
    r_in: float
    r_out: float
    cuff_ring_indices: np.ndarray  # rings within the dense barb-mating cuff
    min_tet_volume_m3: float
    total_volume_m3: float

    def ring_inner_vertex_indices(self, ring_idx: int) -> np.ndarray:
        base = int(ring_idx) * (2 * self.n_theta)
        return np.arange(base, base + self.n_theta, dtype=np.int64)

    def ring_outer_vertex_indices(self, ring_idx: int) -> np.ndarray:
        base = int(ring_idx) * (2 * self.n_theta) + self.n_theta
        return np.arange(base, base + self.n_theta, dtype=np.int64)


def _build_graded_arc_samples(
    total_length_m: float,
    *,
    cuff_length_m: float = 0.045,
    cuff_ds_m: float = 0.0045,
    body_ds_m: float = 0.015,
    dense_both_ends: bool = False,
) -> np.ndarray:
    """Build smooth monotonic 1D arc-length stations dense at the barb cuff(s) and graded in mid-span."""
    L = float(total_length_m)
    cuff_len = min(float(cuff_length_m), 0.35 * L)
    s_list = [0.0]
    s = 0.0
    while s < L - 1e-7:
        dist_start = s
        dist_end = L - s
        d_edge = min(dist_start, dist_end) if dense_both_ends else dist_start
        if d_edge <= cuff_len:
            ds = cuff_ds_m
        elif d_edge <= cuff_len + 0.045:
            u = (d_edge - cuff_len) / 0.045
            ds = (1.0 - u) * cuff_ds_m + u * body_ds_m
        else:
            ds = body_ds_m
        s_next = min(L, s + ds)
        if L - s_next < 0.45 * ds:
            s_next = L
        s_list.append(s_next)
        s = s_next
    return np.asarray(s_list, dtype=np.float64)


def _resample_polyline_by_arc(ctrl_pts: np.ndarray, s_targets: np.ndarray) -> np.ndarray:
    pts = np.asarray(ctrl_pts, dtype=np.float64)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    total = max(float(arc[-1]), 1e-9)
    s_scaled = np.clip(s_targets, 0.0, s_targets[-1]) * (total / max(float(s_targets[-1]), 1e-9))
    return np.column_stack([np.interp(s_scaled, arc, pts[:, k]) for k in range(3)])


def _signed_tet_volumes(pts: np.ndarray, tets: np.ndarray) -> np.ndarray:
    a = pts[tets[:, 0]]
    b = pts[tets[:, 1]]
    c = pts[tets[:, 2]]
    d = pts[tets[:, 3]]
    return np.einsum("ij,ij->i", b - a, np.cross(c - a, d - a)) / 6.0


def build_adaptive_hollow_tube_tet_mesh(
    centerline_ctrl: Sequence[Sequence[float]],
    *,
    r_in: float = 0.0031,
    r_out: float = 0.0049,
    n_theta: int = 10,
    cuff_length_m: float = 0.045,
    cuff_ds_m: float = 0.0045,
    body_ds_m: float = 0.015,
    dense_both_ends: bool = False,
) -> AdaptiveHollowTubeMesh:
    """Build a conforming non-uniform hollow annular tet mesh with zero inverted elements."""
    if n_theta % 2 != 0 or n_theta < 6:
        raise ValueError(f"n_theta must be even and >= 6 for conforming 5-tet parity, got {n_theta}")
    ctrl = np.asarray(centerline_ctrl, dtype=np.float64)
    total_len = float(np.sum(np.linalg.norm(np.diff(ctrl, axis=0), axis=1)))
    ring_s = _build_graded_arc_samples(
        total_len,
        cuff_length_m=cuff_length_m,
        cuff_ds_m=cuff_ds_m,
        body_ds_m=body_ds_m,
        dense_both_ends=dense_both_ends,
    )
    centers = _resample_polyline_by_arc(ctrl, ring_s)
    n_rings = len(centers)
    _, normals, binormals = _bishop_frames(centers)

    thetas = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    pts_list: list[np.ndarray] = []
    for i in range(n_rings):
        ci, ni, bi = centers[i], normals[i], binormals[i]
        for r_val in (float(r_in), float(r_out)):
            for th in thetas:
                pts_list.append(ci + r_val * (np.cos(th) * ni + np.sin(th) * bi))
    rest_points = np.asarray(pts_list, dtype=np.float64)

    def _vid(ring: int, layer: int, j: int) -> int:
        return ring * (2 * n_theta) + layer * n_theta + (j % n_theta)

    tets: list[tuple[int, int, int, int]] = []
    for i in range(n_rings - 1):
        for j in range(n_theta):
            jn = (j + 1) % n_theta
            p000 = _vid(i, 0, j)
            p100 = _vid(i, 0, jn)
            p010 = _vid(i, 1, j)
            p110 = _vid(i, 1, jn)
            p001 = _vid(i + 1, 0, j)
            p101 = _vid(i + 1, 0, jn)
            p011 = _vid(i + 1, 1, j)
            p111 = _vid(i + 1, 1, jn)
            if (i + j) % 2 == 0:
                tets.extend(
                    [
                        (p000, p100, p110, p101),
                        (p000, p110, p010, p011),
                        (p000, p001, p101, p011),
                        (p111, p110, p101, p011),
                        (p000, p110, p101, p011),
                    ]
                )
            else:
                tets.extend(
                    [
                        (p100, p110, p010, p111),
                        (p000, p100, p010, p001),
                        (p100, p101, p111, p001),
                        (p010, p111, p011, p001),
                        (p100, p010, p111, p001),
                    ]
                )

    tets_arr = _orient_tets_positive(rest_points, np.asarray(tets, dtype=np.int64))
    vols = _signed_tet_volumes(rest_points, tets_arr)
    min_vol = float(np.min(vols))
    if min_vol <= 0.0:
        raise RuntimeError(f"Adaptive hollow tube has non-positive tet volume: {min_vol:.3e}")
    surf_tris = _surface_tris_from_tets(rest_points, tets_arr)
    cuff_rings = np.nonzero(ring_s <= cuff_length_m + 1e-6)[0].astype(np.int64)
    return AdaptiveHollowTubeMesh(
        rest_points=rest_points,
        tets=tets_arr,
        surface_tris=surf_tris,
        ring_s=ring_s,
        n_rings=n_rings,
        n_theta=n_theta,
        r_in=float(r_in),
        r_out=float(r_out),
        cuff_ring_indices=cuff_rings,
        min_tet_volume_m3=min_vol,
        total_volume_m3=float(np.sum(vols)),
    )


def compute_cuff_hoop_and_pinch_strain(
    mesh: AdaptiveHollowTubeMesh,
    deformed_pts: np.ndarray,
) -> dict[str, float]:
    """Measure real radial expansion (barb insertion hoop strain) & elliptical pinch ovalization."""
    pts = np.asarray(deformed_pts, dtype=np.float64)
    max_hoop_strain = 0.0
    max_pinch_ratio = 0.0
    max_outer_r_mm = mesh.r_out * 1000.0
    min_inner_r_mm = mesh.r_in * 1000.0

    for ri in mesh.cuff_ring_indices:
        in_pts = pts[mesh.ring_inner_vertex_indices(int(ri))]
        out_pts = pts[mesh.ring_outer_vertex_indices(int(ri))]
        c_in = np.mean(in_pts, axis=0)
        r_in_vec = np.linalg.norm(in_pts - c_in[None, :], axis=1)
        r_out_vec = np.linalg.norm(out_pts - c_in[None, :], axis=1)
        mean_r_in = float(np.mean(r_in_vec))
        hoop = (mean_r_in - mesh.r_in) / max(mesh.r_in, 1e-6)
        max_hoop_strain = max(max_hoop_strain, hoop)
        oval = (float(np.max(r_out_vec)) - float(np.min(r_out_vec))) / max(float(np.mean(r_out_vec)), 1e-6)
        max_pinch_ratio = max(max_pinch_ratio, oval)
        max_outer_r_mm = max(max_outer_r_mm, float(np.max(r_out_vec)) * 1000.0)
        min_inner_r_mm = min(min_inner_r_mm, float(np.min(r_in_vec)) * 1000.0)

    return {
        "max_cuff_hoop_strain": round(max_hoop_strain, 4),
        "max_cuff_hoop_strain_pct": round(100.0 * max_hoop_strain, 2),
        "max_cuff_pinch_ovalization": round(max_pinch_ratio, 4),
        "max_cuff_outer_radius_mm": round(max_outer_r_mm, 3),
        "min_cuff_inner_radius_mm": round(min_inner_r_mm, 3),
    }

