"""True Cosserat twist-aware tubular skinning with longitudinal torsion-indicator stripes."""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from convert_asset.distillation_v04.deformable_specs_v04 import _bishop_frames


def extract_twist_angles_from_link_frames(
    link_positions: Sequence[Sequence[float]],
    link_rotations: Sequence[np.ndarray],
    *,
    local_material_axis: int = 1,
) -> np.ndarray:
    """Compute unwrapped material twist angle theta(s) (rad) relative to torsion-free Bishop frames."""
    pos = np.asarray(link_positions, dtype=np.float64)
    rots = np.asarray(link_rotations, dtype=np.float64)
    n = len(pos)
    tangents, normals, binormals = _bishop_frames(pos)
    raw = np.zeros((n,), dtype=np.float64)
    for i in range(n):
        d_mat = rots[i][:, int(local_material_axis)]
        # Project material radial vector orthogonal to centerline tangent
        d_proj = d_mat - float(np.dot(d_mat, tangents[i])) * tangents[i]
        dn = float(np.linalg.norm(d_proj))
        if dn < 1e-6:
            raw[i] = raw[i - 1] if i > 0 else 0.0
        else:
            d_proj /= dn
            c = float(np.dot(d_proj, normals[i]))
            s = float(np.dot(d_proj, binormals[i]))
            raw[i] = math.atan2(s, c)
    unwrapped = np.unwrap(raw)
    return unwrapped - unwrapped[0]


def build_cosserat_twist_stripe_tube(
    centerline_pts: np.ndarray,
    twist_angles_rad: np.ndarray | None = None,
    *,
    radius_m: float = 0.0048,
    n_circ: int = 24,
    base_rgb: tuple[float, float, float] = (0.78, 0.52, 0.14),
    stripe_rgb: tuple[float, float, float] = (0.28, 0.14, 0.03),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate Cosserat-twisted tubular mesh (verts, normals, tri_indices, vertex_colors)."""
    pts = np.asarray(centerline_pts, dtype=np.float64)
    n_rings = len(pts)
    if twist_angles_rad is None:
        tw = np.zeros((n_rings,), dtype=np.float64)
    else:
        tw_in = np.asarray(twist_angles_rad, dtype=np.float64)
        if len(tw_in) == n_rings:
            tw = tw_in
        else:
            tw = np.interp(np.linspace(0.0, 1.0, n_rings), np.linspace(0.0, 1.0, len(tw_in)), tw_in)

    _, normals, binormals = _bishop_frames(pts)
    thetas = np.linspace(0.0, 2.0 * np.pi, n_circ, endpoint=False)

    verts = np.zeros((n_rings * n_circ, 3), dtype=np.float32)
    v_nrms = np.zeros((n_rings * n_circ, 3), dtype=np.float32)
    v_cols = np.zeros((n_rings * n_circ, 3), dtype=np.float32)

    for i in range(n_rings):
        ci, ni, bi = pts[i], normals[i], binormals[i]
        th_i = float(tw[i])
        ct, st = math.cos(th_i), math.sin(th_i)
        d1 = ct * ni + st * bi
        d2 = -st * ni + ct * bi
        for j, phi in enumerate(thetas):
            idx = i * n_circ + j
            rad_dir = math.cos(phi) * d1 + math.sin(phi) * d2
            verts[idx] = ci + radius_m * rad_dir
            v_nrms[idx] = rad_dir
            # Two opposing longitudinal dark-amber stripes to make axial twist immediately visible!
            is_stripe = (j in (0, 1, n_circ // 2, n_circ // 2 + 1))
            v_cols[idx] = stripe_rgb if is_stripe else base_rgb

    tris = []
    for i in range(n_rings - 1):
        for j in range(n_circ):
            jn = (j + 1) % n_circ
            a = i * n_circ + j
            b = i * n_circ + jn
            c = (i + 1) * n_circ + jn
            d = (i + 1) * n_circ + j
            tris.append((a, b, c))
            tris.append((a, c, d))
    return verts, v_nrms, np.asarray(tris, dtype=np.int32), v_cols

