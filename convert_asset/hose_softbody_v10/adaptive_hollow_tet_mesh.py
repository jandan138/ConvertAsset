"""Non-uniform adaptive hollow annular tetrahedral mesh builder for Route B PhysX GPU FEM hoses."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Sequence

import numpy as np

from convert_asset.deformable_v03.sculpted_assets import _orient_tets_positive, _surface_tris_from_tets
from convert_asset.distillation_v04.deformable_specs_v04 import _bishop_frames


@dataclass(frozen=True)
class AdaptiveHollowTubeMesh:
    """Conforming 5-tet hollow tube mesh with high-density cuff(s), graded wall, and optional barb pre-stretch."""

    rest_points: np.ndarray  # (V, 3) float64 stress-free rest shape (for omniphysics:restShapePoints)
    init_points: np.ndarray  # (V, 3) float64 initial vertex coordinates (coaxially expanded over barb if pre-stretched)
    tets: np.ndarray  # (T, 4) int64 positively oriented
    surface_tris: np.ndarray  # (F, 3) int64
    ring_s: np.ndarray  # (K,) arc-length coordinate [0..L]
    ring_r_out: np.ndarray  # (K,) stress-free outer radius per ring
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


def build_coaxial_barb_hose_centerline(
    barb_origin_w: Sequence[float],
    barb_axis_w: Sequence[float],
    end_anchor_w: Sequence[float],
    *,
    seat_start_s_m: float = 0.005,
    seat_length_m: float = 0.031,
    exit_tangent_m: float = 0.020,
    bench_z_min: float = 0.7615,
    slack_y_m: float = 0.285,
    n_seat_pts: int = 10,
    n_body_pts: int = 28,
) -> np.ndarray:
    """Build a C1-smooth hose centerline strictly coaxial along the glass barb then filleting smoothly onto the bench."""
    p_orig = np.asarray(barb_origin_w, dtype=np.float64)
    u_ax = np.asarray(barb_axis_w, dtype=np.float64)
    u_ax = u_ax / max(float(np.linalg.norm(u_ax)), 1e-12)
    p_end = np.asarray(end_anchor_w, dtype=np.float64)

    # 1. Strictly straight coaxial cuff segment covering all 3 glass olives (seat_start .. seat_start + seat_length)
    s_seat = np.linspace(seat_start_s_m, seat_start_s_m + seat_length_m, max(4, int(n_seat_pts)))
    seat_pts = p_orig[None, :] + s_seat[:, None] * u_ax[None, :]
    p_tip = seat_pts[-1]

    # 2. Smooth C1 circular-arc fillet from barb exit tangent u_ax onto horizontal bench tangent u_horiz
    u_xy = np.array([u_ax[0], u_ax[1], 0.0], dtype=np.float64)
    n_xy = float(np.linalg.norm(u_xy))
    if n_xy < 1e-6:
        u_xy = np.array([0.0, -1.0, 0.0], dtype=np.float64)
    else:
        u_xy /= n_xy
    # Angle between u_ax and horizontal plane
    cos_a = float(np.clip(np.dot(u_ax, u_xy), -1.0, 1.0))
    alpha = math.acos(cos_a)  # e.g. ~1.082 rad (62 deg)
    # Choose fillet radius so the lowest point of the fillet stays >= bench_z_min - 0.003 (outer bottom > 0.750m!)
    if alpha > 1e-3 and u_ax[2] < -1e-3:
        avail_dz = max(0.006, float(p_tip[2]) - (bench_z_min))
        r_fillet = min(0.022, max(0.014, avail_dz / max(1.0 - math.cos(alpha), 1e-3)))
        # Unit normal pointing up-and-forward in the (u_xy, +Z) plane perpendicular to u_ax
        n_up = u_xy * math.sin(alpha) + np.array([0.0, 0.0, 1.0]) * math.cos(alpha)
        n_up /= max(float(np.linalg.norm(n_up)), 1e-12)
        c_arc = p_tip + r_fillet * n_up
        n_arc = 7
        arc_pts = []
        for k in range(1, n_arc + 1):
            phi = alpha * (k / float(n_arc))
            pt_a = c_arc - r_fillet * (math.cos(phi) * n_up - math.sin(phi) * u_ax)
            pt_a[2] = max(bench_z_min, float(pt_a[2]))
            arc_pts.append(pt_a)
        arc_arr = np.asarray(arc_pts, dtype=np.float64)
        p_join = arc_arr[-1]
        u_join = u_xy
    else:
        arc_arr = np.empty((0, 3), dtype=np.float64)
        p_join = p_tip
        u_join = u_ax

    # 3. C1 cubic Hermite drape from p_join (horizontal tangent u_join) to p_end with sin^2(pi*t) slack (0 derivative at ends!)
    n_rem = max(14, int(n_body_pts) - len(arc_arr))
    t_vals = np.linspace(0.0, 1.0, n_rem + 1)[1:]
    span_xy = float(np.linalg.norm(p_end[:2] - p_join[:2]))
    tan0 = u_join * max(0.10, min(0.22, 0.35 * span_xy))
    tan1 = np.array([0.0, 0.04, 0.10], dtype=np.float64)
    body_pts = []
    for t in t_vals:
        h00 = 2 * t**3 - 3 * t**2 + 1
        h10 = t**3 - 2 * t**2 + t
        h01 = -2 * t**3 + 3 * t**2
        h11 = t**3 - t**2
        pt = h00 * p_join + h10 * tan0 + h01 * p_end + h11 * tan1
        s2 = math.sin(math.pi * t) ** 2
        # Smooth C1 single-wave bench drape staying strictly inside LabBenchTop (y >= -0.328 m > -0.360 m edge!)
        # Gently sweeps outward toward the anchor's X side to pack ample bench-resting slack (~690 mm) with high min tet volume!
        sgn_x = 1.0 if float(p_end[0] - p_join[0]) >= 0.0 else -1.0
        # Wide gentle bench-resting loop sweeping outward in ±X (LabBenchTop spans x in [-0.78, +0.78], y in [-0.36, +0.40])
        pt[1] -= 0.150 * s2
        pt[1] = max(-0.328, float(pt[1]))
        pt[0] += sgn_x * 0.275 * s2
        # Smooth bench-resting profile (zero kinks, strictly >= bench_z_min)
        z_bench_blend = (1.0 - s2) * float(pt[2]) + s2 * bench_z_min
        pt[2] = max(bench_z_min, z_bench_blend)
        body_pts.append(pt)
    if len(arc_arr) > 0:
        return np.vstack([seat_pts, arc_arr, np.asarray(body_pts, dtype=np.float64)])
    return np.vstack([seat_pts, np.asarray(body_pts, dtype=np.float64)])

def build_adaptive_hollow_tube_tet_mesh(
    centerline_ctrl: Sequence[Sequence[float]],
    *,
    r_in: float = 0.0031,
    r_out: float = 0.0049,
    r_out_body: float | None = None,
    n_theta: int = 10,
    cuff_length_m: float = 0.045,
    cuff_ds_m: float = 0.0045,
    body_ds_m: float = 0.015,
    dense_both_ends: bool = False,
    barb_prestretch_fn: Callable[[float], float] | None = None,
    prestretch_length_m: float = 0.0,
    prestretch_s_offset_m: float = 0.0,
    prestretch_clearance_m: float = 0.00025,
) -> AdaptiveHollowTubeMesh:
    """Build a conforming non-uniform hollow annular tet mesh with zero inverted elements.

    Supports:
    - Graded outer wall thickness (`r_out` at cuff -> smooth cosine transition to `r_out_body` in mid-span).
    - Coaxial barb radial pre-stretch (`init_points` expanded outside barb olives while `rest_points` remains stress-free).
    """
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

    r_out_mid = float(r_out_body) if r_out_body is not None else float(r_out)
    ring_r_out = np.empty(n_rings, dtype=np.float64)
    for i in range(n_rings):
        si = float(ring_s[i])
        if si <= cuff_length_m:
            ring_r_out[i] = float(r_out)
        elif si <= cuff_length_m + 0.045:
            u = (si - cuff_length_m) / 0.045
            blend = 0.5 * (1.0 - math.cos(math.pi * u))
            ring_r_out[i] = (1.0 - blend) * float(r_out) + blend * r_out_mid
        else:
            ring_r_out[i] = r_out_mid

    thetas = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    rest_list: list[np.ndarray] = []
    init_list: list[np.ndarray] = []
    for i in range(n_rings):
        ci, ni, bi = centers[i], normals[i], binormals[i]
        r_in_rest = float(r_in)
        r_out_rest = float(ring_r_out[i])
        r_in_init = r_in_rest
        r_out_init = r_out_rest
        if barb_prestretch_fn is not None and float(ring_s[i]) <= float(prestretch_length_m) + 1e-6:
            r_barb = float(barb_prestretch_fn(float(prestretch_s_offset_m) + float(ring_s[i])))
            if r_barb > 0.0:
                r_in_init = max(r_in_rest, r_barb + float(prestretch_clearance_m))
                # Preserve wall cross-sectional area (nearly incompressible elastomer)
                wall_area_factor = max(1e-8, r_out_rest**2 - r_in_rest**2)
                r_out_init = math.sqrt(r_in_init**2 + wall_area_factor)
        for r_rest, r_init in ((r_in_rest, r_in_init), (r_out_rest, r_out_init)):
            for th in thetas:
                rad_dir = np.cos(th) * ni + np.sin(th) * bi
                rest_list.append(ci + r_rest * rad_dir)
                init_list.append(ci + r_init * rad_dir)
    rest_points = np.asarray(rest_list, dtype=np.float64)
    init_points = np.asarray(init_list, dtype=np.float64)

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
    vols_rest = _signed_tet_volumes(rest_points, tets_arr)
    vols_init = _signed_tet_volumes(init_points, tets_arr)
    min_vol = float(min(np.min(vols_rest), np.min(vols_init)))
    if min_vol <= 0.0:
        raise RuntimeError(
            f"Adaptive hollow tube has non-positive tet volume (rest={float(np.min(vols_rest)):.3e}, init={float(np.min(vols_init)):.3e})"
        )
    surf_tris = _surface_tris_from_tets(rest_points, tets_arr)
    cuff_rings = np.nonzero(ring_s <= cuff_length_m + 1e-6)[0].astype(np.int64)
    return AdaptiveHollowTubeMesh(
        rest_points=rest_points,
        init_points=init_points,
        tets=tets_arr,
        surface_tris=surf_tris,
        ring_s=ring_s,
        ring_r_out=ring_r_out,
        n_rings=n_rings,
        n_theta=n_theta,
        r_in=float(r_in),
        r_out=float(r_out),
        cuff_ring_indices=cuff_rings,
        min_tet_volume_m3=min_vol,
        total_volume_m3=float(np.sum(vols_rest)),
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
