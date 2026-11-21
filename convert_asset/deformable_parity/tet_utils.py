"""Pure-NumPy tetrahedral/cloth mesh builders and kinematic strain utilities (M1)."""

from __future__ import annotations

import numpy as np


_CUBE_TET_BASE: tuple[tuple[tuple[int, int, int], ...], ...] = (
    ((0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 0, 1)),
    ((0, 0, 0), (1, 0, 1), (1, 1, 0), (0, 1, 1)),
    ((0, 0, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1)),
    ((1, 0, 1), (1, 1, 1), (1, 1, 0), (0, 1, 1)),
    ((0, 0, 0), (1, 1, 0), (0, 1, 0), (0, 1, 1)),
)


def build_voxel_tet_mesh(
    size_xyz_m: tuple[float, float, float],
    grid_xyz: tuple[int, int, int] = (4, 4, 2),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a watertight centered tetrahedral voxel mesh (vertices, tets, edges).

    All returned tetrahedra are oriented with strictly positive signed volume
    ``det([p1 - p0, p2 - p0, p3 - p0]) > 0``.
    """
    sx, sy, sz = (float(size_xyz_m[0]), float(size_xyz_m[1]), float(size_xyz_m[2]))
    nx, ny, nz = (int(grid_xyz[0]), int(grid_xyz[1]), int(grid_xyz[2]))
    if nx <= 0 or ny <= 0 or nz <= 0:
        raise ValueError(f"grid_xyz must be positive, got {grid_xyz!r}")

    verts = np.zeros(((nx + 1) * (ny + 1) * (nz + 1), 3), dtype=np.float64)

    def vid(ix: int, iy: int, iz: int) -> int:
        return (iz * (ny + 1) + iy) * (nx + 1) + ix

    for iz in range(nz + 1):
        z = -0.5 * sz + (sz * iz) / nz
        for iy in range(ny + 1):
            y = -0.5 * sy + (sy * iy) / ny
            for ix in range(nx + 1):
                x = -0.5 * sx + (sx * ix) / nx
                verts[vid(ix, iy, iz)] = (x, y, z)

    tets_list: list[list[int]] = []
    edges_set: set[tuple[int, int]] = set()
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                mx, my, mz = ix % 2, iy % 2, iz % 2
                flip = (mx + my + mz) % 2
                for src_tet in _CUBE_TET_BASE:
                    ordered = (
                        (src_tet[1], src_tet[0], src_tet[2], src_tet[3])
                        if flip
                        else src_tet
                    )
                    tet_idx: list[int] = []
                    for cx, cy, cz in ordered:
                        wx = mx + (1 - 2 * mx) * cx
                        wy = my + (1 - 2 * my) * cy
                        wz = mz + (1 - 2 * mz) * cz
                        tet_idx.append(vid(ix + wx, iy + wy, iz + wz))
                    p0, p1, p2, p3 = verts[tet_idx]
                    det = float(np.linalg.det(np.column_stack((p1 - p0, p2 - p0, p3 - p0))))
                    if det < 0.0:
                        tet_idx[0], tet_idx[1] = tet_idx[1], tet_idx[0]
                    tets_list.append(tet_idx)
                    for i in range(4):
                        for j in range(i + 1, 4):
                            u, v = tet_idx[i], tet_idx[j]
                            edges_set.add((u, v) if u < v else (v, u))

    tets = np.asarray(tets_list, dtype=np.int32)
    edges = np.asarray(sorted(edges_set), dtype=np.int32)
    return verts, tets, edges


def compute_tet_deformation_gradients(
    rest_points: np.ndarray,
    cur_points: np.ndarray,
    tets: np.ndarray,
) -> np.ndarray:
    """Compute per-tetrahedron 3x3 deformation gradients F = Ds @ Dm^-1.

    Supports ``cur_points`` of shape ``(V, 3)`` or ``(T, V, 3)``.
    """
    rest = np.asarray(rest_points, dtype=np.float64)
    cur = np.asarray(cur_points, dtype=np.float64)
    idx = np.asarray(tets, dtype=np.int64)
    if rest.ndim != 2 or rest.shape[1] != 3:
        raise ValueError(f"Expected rest_points (V, 3), got {rest.shape}")
    if idx.ndim != 2 or idx.shape[1] != 4:
        raise ValueError(f"Expected tets (M, 4), got {idx.shape}")

    single = cur.ndim == 2
    if single:
        cur = cur[None, ...]
    if cur.ndim != 3 or cur.shape[1:] != rest.shape:
        raise ValueError(f"Expected cur_points shape {(rest.shape)} or (T, V, 3), got {cur.shape}")

    p0 = rest[idx[:, 0]]
    dm = np.stack(
        (rest[idx[:, 1]] - p0, rest[idx[:, 2]] - p0, rest[idx[:, 3]] - p0),
        axis=-1,
    )
    dm_inv = np.linalg.inv(dm)  # (M, 3, 3)

    c0 = cur[:, idx[:, 0], :]
    ds = np.stack(
        (
            cur[:, idx[:, 1], :] - c0,
            cur[:, idx[:, 2], :] - c0,
            cur[:, idx[:, 3], :] - c0,
        ),
        axis=-1,
    )  # (T, M, 3, 3)
    f = np.einsum("tmij,mjk->tmik", ds, dm_inv)
    return f[0] if single else f


def build_arched_cloth_points(
    flat_points: np.ndarray,
    width_m: float,
    arch_height_m: float = 0.032,
) -> np.ndarray:
    """Apply a smooth arch ``z(x) = A0 * cos(pi * x / W)`` shifted so min z == 0."""
    pts = np.asarray(flat_points, dtype=np.float64).copy()
    w = max(float(width_m), 1e-6)
    z = float(arch_height_m) * np.cos(np.pi * pts[:, 0] / w)
    z = z - float(np.min(z))
    pts[:, 2] = pts[:, 2] + z
    return pts


def vertical_span_m(points: np.ndarray) -> float:
    """Compute robust Q98 - Q02 vertical span (height) in meters."""
    pts = np.asarray(points, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[0] == 0:
        raise ValueError(f"Expected non-empty (N, 3) points, got {pts.shape}")
    return float(np.percentile(pts[:, 2], 98) - np.percentile(pts[:, 2], 2))

