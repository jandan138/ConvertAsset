"""Volumetric annular & sculpted deformable asset bundles (v0.4) with UV-mapped PBR & tet skinning."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
from PIL import Image

from convert_asset.deformable_v03.bundle_writer import MUJOCO4_PYTHON, _write_obj
from convert_asset.deformable_v03.pbr_textures import derive_pbr_maps_from_albedo
from convert_asset.deformable_v03.sculpted_assets import (
    _edges_from_elements,
    _orient_tets_positive,
    _surface_tris_from_tets,
)
from convert_asset.deformable_v03.skinning import build_tet_barycentric_skinning


@dataclass(frozen=True)
class V04DeformableSpec:
    asset_id: str
    category: str
    structural_family: str
    dimensions_xyz_m: tuple[float, float, float]
    mass_kg: float
    youngs_modulus_pa: float
    poissons_ratio: float
    yield_stress_pa: float
    strain_onset_a: float
    strain_failure_b: float
    damage_threshold: float
    max_normal_force_n: float
    fragility_tier: str
    fallback_rgb: tuple[int, int, int]
    roughness_range: tuple[float, float]
    default_color: tuple[float, float, float]


V04_DEFORMABLE_SPECS: dict[str, V04DeformableSpec] = {
    "v04_clamp_pad_01": V04DeformableSpec(
        asset_id="v04_clamp_pad_01",
        category="silicone_flask_clamp_cushion",
        structural_family="soft_solid",
        dimensions_xyz_m=(0.048, 0.036, 0.026),
        mass_kg=0.028,
        youngs_modulus_pa=85000.0,
        poissons_ratio=0.36,
        yield_stress_pa=42000.0,
        strain_onset_a=0.30,
        strain_failure_b=0.62,
        damage_threshold=0.25,
        max_normal_force_n=16.0,
        fragility_tier="medium",
        fallback_rgb=(88, 154, 152),
        roughness_range=(0.35, 0.58),
        default_color=(0.35, 0.60, 0.60),
    ),
    "v04_ptfe_taper_sleeve_01": V04DeformableSpec(
        asset_id="v04_ptfe_taper_sleeve_01",
        category="ptfe_ground_joint_taper_sleeve",
        structural_family="soft_solid",
        dimensions_xyz_m=(0.038, 0.038, 0.028),
        mass_kg=0.024,
        youngs_modulus_pa=110000.0,
        poissons_ratio=0.34,
        yield_stress_pa=55000.0,
        strain_onset_a=0.28,
        strain_failure_b=0.58,
        damage_threshold=0.24,
        max_normal_force_n=12.0,
        fragility_tier="high",
        fallback_rgb=(236, 240, 244),
        roughness_range=(0.18, 0.36),
        default_color=(0.93, 0.94, 0.96),
    ),
    "v04_rubber_septum_01": V04DeformableSpec(
        asset_id="v04_rubber_septum_01",
        category="hollow_rubber_thermometer_septum",
        structural_family="soft_solid",
        dimensions_xyz_m=(0.036, 0.036, 0.028),
        mass_kg=0.026,
        youngs_modulus_pa=95000.0,
        poissons_ratio=0.38,
        yield_stress_pa=48000.0,
        strain_onset_a=0.30,
        strain_failure_b=0.60,
        damage_threshold=0.24,
        max_normal_force_n=14.0,
        fragility_tier="high",
        fallback_rgb=(182, 64, 54),
        roughness_range=(0.42, 0.68),
        default_color=(0.71, 0.25, 0.21),
    ),
    "v04_dual_cooling_hoses_01": V04DeformableSpec(
        asset_id="v04_dual_cooling_hoses_01",
        category="dual_annular_silicone_cooling_hoses",
        structural_family="rod_cable",
        dimensions_xyz_m=(0.42, 0.24, 0.22),
        mass_kg=0.064,
        youngs_modulus_pa=125000.0,
        poissons_ratio=0.35,
        yield_stress_pa=62000.0,
        strain_onset_a=0.34,
        strain_failure_b=0.72,
        damage_threshold=0.28,
        max_normal_force_n=20.0,
        fragility_tier="medium",
        fallback_rgb=(78, 168, 224),
        roughness_range=(0.22, 0.44),
        default_color=(0.30, 0.66, 0.88),
    ),
}


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _bishop_frames(centers: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute torsion-free Bishop orthonormal frames (T, N, B) along 3D centerline."""
    n_pts = len(centers)
    tangents = np.zeros((n_pts, 3), dtype=np.float64)
    for i in range(n_pts):
        if i == 0:
            t = centers[1] - centers[0]
        elif i == n_pts - 1:
            t = centers[-1] - centers[-2]
        else:
            t = centers[i + 1] - centers[i - 1]
        norm_t = float(np.linalg.norm(t))
        tangents[i] = t / max(norm_t, 1e-9)

    normals = np.zeros((n_pts, 3), dtype=np.float64)
    binormals = np.zeros((n_pts, 3), dtype=np.float64)
    ref = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    if abs(float(np.dot(tangents[0], ref))) > 0.90:
        ref = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    n0 = np.cross(tangents[0], ref)
    n0 = n0 / max(float(np.linalg.norm(n0)), 1e-9)
    normals[0] = n0
    binormals[0] = np.cross(tangents[0], n0)
    binormals[0] /= max(float(np.linalg.norm(binormals[0])), 1e-9)

    for i in range(1, n_pts):
        # Project previous normal perpendicular to current tangent to avoid sudden twist
        n_prev = normals[i - 1]
        ti = tangents[i]
        n_cur = n_prev - float(np.dot(n_prev, ti)) * ti
        nn = float(np.linalg.norm(n_cur))
        if nn < 1e-7:
            alt = np.array([0.0, 0.0, 1.0], dtype=np.float64)
            if abs(float(np.dot(ti, alt))) > 0.9:
                alt = np.array([1.0, 0.0, 0.0], dtype=np.float64)
            n_cur = np.cross(ti, alt)
            nn = float(np.linalg.norm(n_cur))
        normals[i] = n_cur / max(nn, 1e-9)
        bi = np.cross(ti, normals[i])
        binormals[i] = bi / max(float(np.linalg.norm(bi)), 1e-9)
    return tangents, normals, binormals


def _sample_annular_vertices(
    centers: np.ndarray,
    r_in: np.ndarray,
    r_out: np.ndarray,
    n_theta: int,
) -> np.ndarray:
    """Place (2 * K * n_theta, 3) inner & outer annular vertices along centers."""
    _, normals, binormals = _bishop_frames(centers)
    thetas = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    pts: list[tuple[float, float, float]] = []
    for i in range(len(centers)):
        ci = centers[i]
        ni = normals[i]
        bi = binormals[i]
        for r_val in (float(r_in[i]), float(r_out[i])):
            for th in thetas:
                p = ci + r_val * (np.cos(th) * ni + np.sin(th) * bi)
                pts.append((float(p[0]), float(p[1]), float(p[2])))
    return np.asarray(pts, dtype=np.float64)


def _build_annular_tube_pair(
    centers: np.ndarray,
    r_in: np.ndarray,
    r_out: np.ndarray,
    *,
    n_theta: int = 10,
    n_vis_sub: int = 3,
    n_vis_theta: int = 24,
    u_range: tuple[float, float] = (0.0, 1.0),
) -> dict[str, np.ndarray]:
    """Build conforming 5-tet annular mesh (true hollow bore) + UV-mapped smooth visual mesh."""
    if n_theta % 2 != 0:
        raise ValueError(f"n_theta must be even for conforming 5-tet annular decomposition, got {n_theta}")
    n_rings = len(centers)
    phys_pts = _sample_annular_vertices(centers, r_in, r_out, n_theta)

    def _vid(ring: int, layer: int, theta_idx: int) -> int:
        return ring * (2 * n_theta) + layer * n_theta + (theta_idx % n_theta)

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

    tets_arr = _orient_tets_positive(phys_pts, np.asarray(tets, dtype=np.int64))
    phys_tris = _surface_tris_from_tets(phys_pts, tets_arr)
    phys_edges = _edges_from_elements(tets_arr)

    # Interpolate smooth high-poly visual surface contained inside the inscribed annular walls
    s_phys = np.linspace(0.0, 1.0, n_rings)
    n_vis_rings = max(4, (n_rings - 1) * n_vis_sub + 1)
    s_vis = np.linspace(0.0, 1.0, n_vis_rings)
    vis_centers = np.column_stack([np.interp(s_vis, s_phys, centers[:, k]) for k in range(3)])
    cos_chord = float(np.cos(np.pi / float(n_theta)))
    # Keep visual outer slightly inside chorded phys polygon and inner slightly outside for clean containment
    r_in_vis = np.interp(s_vis, s_phys, r_in) * 1.01
    r_out_vis = np.interp(s_vis, s_phys, r_out) * max(0.94, cos_chord * 0.995)
    _, v_norm, v_bin = _bishop_frames(vis_centers)
    v_th = np.linspace(0.0, 2.0 * np.pi, n_vis_theta, endpoint=False)

    vis_pts_list: list[tuple[float, float, float]] = []
    vis_uvs_list: list[tuple[float, float]] = []
    u0, u1 = u_range
    for i in range(n_vis_rings):
        ci = vis_centers[i]
        ni = v_norm[i]
        bi = v_bin[i]
        u_val = u0 + (u1 - u0) * (i / float(n_vis_rings - 1))
        for r_val in (float(r_in_vis[i]), float(r_out_vis[i])):
            for tj, th in enumerate(v_th):
                p = ci + r_val * (np.cos(th) * ni + np.sin(th) * bi)
                vis_pts_list.append((float(p[0]), float(p[1]), float(p[2])))
                vis_uvs_list.append((float(u_val), float(tj / float(n_vis_theta))))

    def _vvid(ring: int, layer: int, tj: int) -> int:
        return ring * (2 * n_vis_theta) + layer * n_vis_theta + (tj % n_vis_theta)

    vis_tris: list[tuple[int, int, int]] = []
    # Outer + inner lateral walls
    for i in range(n_vis_rings - 1):
        for j in range(n_vis_theta):
            jn = (j + 1) % n_vis_theta
            o00, o10 = _vvid(i, 1, j), _vvid(i, 1, jn)
            o01, o11 = _vvid(i + 1, 1, j), _vvid(i + 1, 1, jn)
            vis_tris.append((o00, o10, o11))
            vis_tris.append((o00, o11, o01))

            i00, i10 = _vvid(i, 0, j), _vvid(i, 0, jn)
            i01, i11 = _vvid(i + 1, 0, j), _vvid(i + 1, 0, jn)
            vis_tris.append((i00, i11, i10))
            vis_tris.append((i00, i01, i11))

    # End caps closing annular tube
    for j in range(n_vis_theta):
        jn = (j + 1) % n_vis_theta
        # Start cap (i = 0)
        vis_tris.append((_vvid(0, 0, j), _vvid(0, 1, jn), _vvid(0, 1, j)))
        vis_tris.append((_vvid(0, 0, j), _vvid(0, 0, jn), _vvid(0, 1, jn)))
        # End cap (i = n_vis_rings - 1)
        lr = n_vis_rings - 1
        vis_tris.append((_vvid(lr, 0, j), _vvid(lr, 1, j), _vvid(lr, 1, jn)))
        vis_tris.append((_vvid(lr, 0, j), _vvid(lr, 1, jn), _vvid(lr, 0, jn)))

    return {
        "phys_pts": phys_pts,
        "tets": tets_arr,
        "phys_tris": phys_tris,
        "phys_edges": phys_edges,
        "vis_pts": np.asarray(vis_pts_list, dtype=np.float64),
        "vis_tris": np.asarray(vis_tris, dtype=np.int64),
        "vis_uvs": np.asarray(vis_uvs_list, dtype=np.float64),
    }


def _build_clamp_pad_asset() -> dict[str, Any]:
    """U-profile ribbed silicone clamp cushion pad (dim=3 volumetric tets)."""
    nx, ny, nz = 4, 4, 2
    sx, sy, sz = 0.048, 0.036, 0.026
    xs = np.linspace(-0.5 * sx, 0.5 * sx, nx + 1)
    ys = np.linspace(-0.5 * sy, 0.5 * sy, ny + 1)
    zs = np.linspace(0.0, sz, nz + 1)
    verts = []
    for z in zs:
        for y in ys:
            for x in xs:
                # Carve gentle U-groove concavity on upper center while keeping solid pad envelope
                z_mod = float(z)
                if z > 0.5 * sz and abs(y) < 0.011:
                    z_mod = float(z) - 0.005 * (1.0 - abs(y) / 0.011)
                verts.append((float(x), float(y), z_mod))
    phys_pts = np.asarray(verts, dtype=np.float64)

    def _vid(ix: int, iy: int, iz: int) -> int:
        return iz * ((ny + 1) * (nx + 1)) + iy * (nx + 1) + ix

    tets: list[tuple[int, int, int, int]] = []
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                p000 = _vid(ix, iy, iz)
                p100 = _vid(ix + 1, iy, iz)
                p010 = _vid(ix, iy + 1, iz)
                p110 = _vid(ix + 1, iy + 1, iz)
                p001 = _vid(ix, iy, iz + 1)
                p101 = _vid(ix + 1, iy, iz + 1)
                p011 = _vid(ix, iy + 1, iz + 1)
                p111 = _vid(ix + 1, iy + 1, iz + 1)
                if (ix + iy + iz) % 2 == 0:
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
    tets_arr = _orient_tets_positive(phys_pts, np.asarray(tets, dtype=np.int64))
    phys_tris = _surface_tris_from_tets(phys_pts, tets_arr)
    phys_edges = _edges_from_elements(tets_arr)

    # High-poly visual hex shell inside physical volume
    vx, vy, vz = 16, 12, 8
    xvs = np.linspace(-0.48 * sx, 0.48 * sx, vx + 1)
    yvs = np.linspace(-0.48 * sy, 0.48 * sy, vy + 1)
    zvs = np.linspace(0.001, 0.98 * sz, vz + 1)
    grid_pts: list[tuple[float, float, float]] = []
    grid_uvs: list[tuple[float, float]] = []
    idx_map: dict[tuple[int, int, int], int] = {}
    for iz, zv in enumerate(zvs):
        for iy, yv in enumerate(yvs):
            for ix, xv in enumerate(xvs):
                is_bnd = ix in (0, vx) or iy in (0, vy) or iz in (0, vz)
                if not is_bnd:
                    continue
                zm = float(zv)
                if zv > 0.5 * sz and abs(yv) < 0.011:
                    zm = float(zv) - 0.005 * (1.0 - abs(yv) / 0.011)
                idx_map[(ix, iy, iz)] = len(grid_pts)
                grid_pts.append((float(xv), float(yv), zm))
                grid_uvs.append((ix / float(vx), (iy / float(vy) + iz / float(vz)) * 0.5))

    vis_tris: list[tuple[int, int, int]] = []
    # Top/bottom z faces
    for iz, flip in ((0, True), (vz, False)):
        for iy in range(vy):
            for ix in range(vx):
                a, b, c, d = idx_map[(ix, iy, iz)], idx_map[(ix + 1, iy, iz)], idx_map[(ix + 1, iy + 1, iz)], idx_map[(ix, iy + 1, iz)]
                vis_tris.extend([(a, c, b), (a, d, c)] if flip else [(a, b, c), (a, c, d)])
    # Front/back y faces
    for iy, flip in ((0, False), (vy, True)):
        for iz in range(vz):
            for ix in range(vx):
                a, b, c, d = idx_map[(ix, iy, iz)], idx_map[(ix + 1, iy, iz)], idx_map[(ix + 1, iy, iz + 1)], idx_map[(ix, iy, iz + 1)]
                vis_tris.extend([(a, c, b), (a, d, c)] if flip else [(a, b, c), (a, c, d)])
    # Left/right x faces
    for ix, flip in ((0, True), (vx, False)):
        for iz in range(vz):
            for iy in range(vy):
                a, b, c, d = idx_map[(ix, iy, iz)], idx_map[(ix, iy + 1, iz)], idx_map[(ix, iy + 1, iz + 1)], idx_map[(ix, iy, iz + 1)]
                vis_tris.extend([(a, c, b), (a, d, c)] if flip else [(a, b, c), (a, c, d)])

    return {
        "phys_pts": phys_pts,
        "tets": tets_arr,
        "phys_tris": phys_tris,
        "phys_edges": phys_edges,
        "vis_pts": np.asarray(grid_pts, dtype=np.float64),
        "vis_tris": np.asarray(vis_tris, dtype=np.int64),
        "vis_uvs": np.asarray(grid_uvs, dtype=np.float64),
    }


def _build_ptfe_taper_sleeve_asset() -> dict[str, Any]:
    """True hollow 1:10 conical PTFE/fluoroelastomer ground-joint taper sleeve."""
    centers = np.array(
        [
            [0.0, 0.0, 0.000],
            [0.0, 0.0, 0.009],
            [0.0, 0.0, 0.019],
            [0.0, 0.0, 0.028],
        ],
        dtype=np.float64,
    )
    # 1:10 ground-glass taper expands gently from bottom to top
    r_in = np.array([0.0118, 0.0124, 0.0130, 0.0136], dtype=np.float64)
    r_out = np.array([0.0156, 0.0162, 0.0168, 0.0174], dtype=np.float64)
    return _build_annular_tube_pair(centers, r_in, r_out, n_theta=10, n_vis_sub=4, n_vis_theta=28)


def _build_rubber_septum_asset() -> dict[str, Any]:
    """True hollow flanged terracotta rubber thermometer septum adapter."""
    centers = np.array(
        [
            [0.0, 0.0, 0.000],
            [0.0, 0.0, 0.009],
            [0.0, 0.0, 0.019],
            [0.0, 0.0, 0.028],
        ],
        dtype=np.float64,
    )
    r_in = np.array([0.0056, 0.0056, 0.0056, 0.0060], dtype=np.float64)
    r_out = np.array([0.0136, 0.0144, 0.0172, 0.0182], dtype=np.float64)
    return _build_annular_tube_pair(centers, r_in, r_out, n_theta=10, n_vis_sub=4, n_vis_theta=28)


def _dual_hose_centerlines(assembled: bool) -> tuple[np.ndarray, np.ndarray]:
    """Return (inlet_centers, outlet_centers) local to z_table=0.755 for staged or barb-assembled state."""
    u_inward = np.array([0.0, 0.70710678, 0.70710678], dtype=np.float64)  # points from barb tip -> root

    # Assembled state: active cuffs slipped over condenser barbs!
    # Lower inlet barb root = (0.08154, -0.014, 0.161), tip = (0.08154, -0.03946, 0.13554)
    in_cuff0 = np.array([0.08154, -0.03946, 0.13554], dtype=np.float64) + 0.008 * u_inward
    in_cuff1 = np.array([0.08154, -0.014, 0.161], dtype=np.float64)
    in_pts_asm = np.array(
        [
            [0.180, -0.175, 0.014],
            [0.165, -0.168, 0.018],
            [0.145, -0.150, 0.032],
            [0.122, -0.125, 0.058],
            [0.100, -0.092, 0.090],
            [0.086, -0.060, 0.118],
            in_cuff0,
            0.5 * (in_cuff0 + in_cuff1),
            in_cuff1,
        ],
        dtype=np.float64,
    )
    # Upper outlet barb root = (-0.04210, -0.014, 0.201), tip = (-0.04210, -0.03946, 0.17554)
    out_cuff0 = np.array([-0.04210, -0.03946, 0.17554], dtype=np.float64) + 0.008 * u_inward
    out_cuff1 = np.array([-0.04210, -0.014, 0.201], dtype=np.float64)
    out_pts_asm = np.array(
        [
            [-0.150, -0.175, 0.014],
            [-0.132, -0.168, 0.020],
            [-0.110, -0.150, 0.042],
            [-0.088, -0.122, 0.080],
            [-0.068, -0.090, 0.122],
            [-0.050, -0.058, 0.158],
            out_cuff0,
            0.5 * (out_cuff0 + out_cuff1),
            out_cuff1,
        ],
        dtype=np.float64,
    )
    if assembled:
        return in_pts_asm, out_pts_asm

    # Isometric SE(3) staged pose (-22 deg pitch about ring-0 + -42 mm Y staging offset -> exact zero rest-vs-assembled stretch!)
    th = np.deg2rad(-22.0)
    rot_x = np.array([[1.0, 0.0, 0.0], [0.0, np.cos(th), -np.sin(th)], [0.0, np.sin(th), np.cos(th)]], dtype=np.float64)
    y_shift = np.array([0.0, -0.042, 0.0], dtype=np.float64)

    p0_in = in_pts_asm[0].copy()
    in_pts = p0_in + (in_pts_asm - p0_in) @ rot_x.T + y_shift
    in_pts[:, 2] = np.maximum(in_pts[:, 2], 0.014)

    p0_out = out_pts_asm[0].copy()
    out_pts = p0_out + (out_pts_asm - p0_out) @ rot_x.T + y_shift
    out_pts[:, 2] = np.maximum(out_pts[:, 2], 0.014)
    return in_pts, out_pts


def _build_dual_cooling_hoses_asset() -> dict[str, Any]:
    """Build 2-component disjoint hollow annular silicone hoses (staged + assembled poses)."""
    in_c, out_c = _dual_hose_centerlines(assembled=False)
    in_asm_c, out_asm_c = _dual_hose_centerlines(assembled=True)

    r_in = np.full(len(in_c), 0.0062, dtype=np.float64)
    r_out = np.full(len(in_c), 0.0108, dtype=np.float64)
    # Slightly flared cuff collar at rings -3..-1
    r_out[-3:] = 0.0114

    comp_in = _build_annular_tube_pair(
        in_c, r_in, r_out, n_theta=8, n_vis_sub=3, n_vis_theta=20, u_range=(0.02, 0.46)
    )
    comp_out = _build_annular_tube_pair(
        out_c, r_in, r_out, n_theta=8, n_vis_sub=3, n_vis_theta=20, u_range=(0.54, 0.98)
    )

    n_p_in = len(comp_in["phys_pts"])
    n_v_in = len(comp_in["vis_pts"])
    phys_pts = np.vstack([comp_in["phys_pts"], comp_out["phys_pts"]])
    tets = np.vstack([comp_in["tets"], comp_out["tets"] + n_p_in])
    tets = _orient_tets_positive(phys_pts, tets)
    phys_tris = np.vstack([comp_in["phys_tris"], comp_out["phys_tris"] + n_p_in])
    phys_edges = np.vstack([comp_in["phys_edges"], comp_out["phys_edges"] + n_p_in])
    vis_pts = np.vstack([comp_in["vis_pts"], comp_out["vis_pts"]])
    vis_tris = np.vstack([comp_in["vis_tris"], comp_out["vis_tris"] + n_v_in])
    vis_uvs = np.vstack([comp_in["vis_uvs"], comp_out["vis_uvs"]])

    # Matching-topology assembled rest vertices for distill_06 reverse disassembly
    asm_in_pts = _sample_annular_vertices(in_asm_c, r_in, r_out, n_theta=8)
    asm_out_pts = _sample_annular_vertices(out_asm_c, r_in, r_out, n_theta=8)
    assembled_pts = np.vstack([asm_in_pts, asm_out_pts])

    return {
        "phys_pts": phys_pts,
        "tets": tets,
        "phys_tris": phys_tris,
        "phys_edges": phys_edges,
        "vis_pts": vis_pts,
        "vis_tris": vis_tris,
        "vis_uvs": vis_uvs,
        "assembled_rest_points": assembled_pts,
    }


def _generate_custom_pbr_maps(spec: V04DeformableSpec, tex_dir: Path, tex_size: int = 1024) -> dict[str, Path]:
    """Generate clean micro-textured PBR albedo/normal/roughness maps in pure numpy/PIL."""
    tex_dir.mkdir(parents=True, exist_ok=True)
    raw_alb = tex_dir / f"{spec.asset_id}_raw_albedo.png"
    rng = np.random.default_rng(abs(hash(spec.asset_id)) % 100000 + 42)
    u = np.linspace(0.0, 1.0, tex_size, endpoint=False, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, tex_size, endpoint=False, dtype=np.float32)[:, None]

    if spec.asset_id == "v04_dual_cooling_hoses_01":
        # Left half u < 0.5 = translucent ice-blue inlet hose; Right half u >= 0.5 = amber-coral outlet hose
        rgb = np.zeros((tex_size, tex_size, 3), dtype=np.float32)
        inlet_col = np.array([72.0, 174.0, 232.0], dtype=np.float32)
        outlet_col = np.array([230.0, 128.0, 74.0], dtype=np.float32)
        rib = 6.5 * np.sin(2.0 * np.pi * 18.0 * v) + rng.normal(0.0, 2.5, (tex_size, tex_size))
        band_in = ((u > 0.36) & (u < 0.44)).astype(np.float32) * 26.0
        band_out = ((u > 0.86) & (u < 0.94)).astype(np.float32) * 26.0
        mask_out = (u >= 0.5).astype(np.float32)
        for c in range(3):
            rgb[:, :, c] = (
                (1.0 - mask_out) * (inlet_col[c] + rib + band_in)
                + mask_out * (outlet_col[c] + rib + band_out)
            )
        albedo_u8 = np.clip(rgb, 0.0, 255.0).astype(np.uint8)
        Image.fromarray(albedo_u8, mode="RGB").save(raw_alb, format="PNG")
        lum = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]) / 255.0
        dx = (np.roll(lum, -1, axis=1) - np.roll(lum, 1, axis=1)) * 1.4
        dy = (np.roll(lum, -1, axis=0) - np.roll(lum, 1, axis=0)) * 1.4
        nz = np.ones_like(lum, dtype=np.float32)
        nl = np.sqrt(dx * dx + dy * dy + nz * nz)
        nrm_u8 = np.clip(np.stack([-dx / nl * 0.5 + 0.5, -dy / nl * 0.5 + 0.5, nz / nl * 0.5 + 0.5], axis=-1) * 255.0, 0.0, 255.0).astype(np.uint8)
        r_min, r_max = spec.roughness_range
        rgh_u8 = np.clip((r_max - lum * (r_max - r_min)) * 255.0, 0.0, 255.0).astype(np.uint8)
        p_alb, p_nrm, p_rgh = tex_dir / "albedo.png", tex_dir / "normal.png", tex_dir / "roughness.png"
        Image.fromarray(albedo_u8, mode="RGB").save(p_alb, format="PNG")
        Image.fromarray(nrm_u8, mode="RGB").save(p_nrm, format="PNG")
        Image.fromarray(rgh_u8, mode="L").save(p_rgh, format="PNG")
        return {"albedo": p_alb, "normal": p_nrm, "roughness": p_rgh}

    rgb = np.zeros((tex_size, tex_size, 3), dtype=np.float32)
    base_col = np.array(spec.fallback_rgb, dtype=np.float32)
    pattern = 7.0 * np.sin(2.0 * np.pi * 16.0 * u) + 4.0 * np.cos(2.0 * np.pi * 10.0 * v) + rng.normal(0.0, 3.0, (tex_size, tex_size))
    for c in range(3):
        rgb[:, :, c] = base_col[c] + pattern
    Image.fromarray(np.clip(rgb, 0.0, 255.0).astype(np.uint8), mode="RGB").save(raw_alb, format="PNG")
    return derive_pbr_maps_from_albedo(
        raw_alb,
        tex_dir,
        normal_strength=1.8,
        roughness_range=spec.roughness_range,
        out_size=tex_size,
        fallback_rgb=spec.fallback_rgb,
    )


def _write_v04_base_usda(path: Path, spec: V04DeformableSpec, phys_pts: np.ndarray, phys_tris: np.ndarray) -> None:
    pts_str = ", ".join(f"({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f})" for p in phys_pts)
    cnt_str = ", ".join("3" for _ in range(len(phys_tris)))
    idx_str = ", ".join(str(int(i)) for t in phys_tris for i in t)
    usda = f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Mesh "DeformableAsset"
    {{
        custom string deformable:assetId = "{spec.asset_id}"
        custom string deformable:structuralFamily = "{spec.structural_family}"
        custom double deformable:youngsModulusPa = {spec.youngs_modulus_pa}
        custom double deformable:poissonsRatio = {spec.poissons_ratio}
        custom string deformable:strainMetric = "polar_stretch_q95"
        custom double deformable:strainOnsetA = {spec.strain_onset_a}
        custom double deformable:strainFailureB = {spec.strain_failure_b}
        custom double deformable:damageThreshold = {spec.damage_threshold}
        custom double deformable:maxNormalForceN = {spec.max_normal_force_n}
        int[] faceVertexCounts = [{cnt_str}]
        int[] faceVertexIndices = [{idx_str}]
        point3f[] points = [{pts_str}]
    }}
}}
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(usda, encoding="utf-8")


def _write_v04_visual_highpoly_usda(
    path: Path,
    vis_pts: np.ndarray,
    vis_tris: np.ndarray,
    vis_uvs: np.ndarray,
) -> None:
    pts_str = ", ".join(f"({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f})" for p in vis_pts)
    cnt_str = ", ".join("3" for _ in range(len(vis_tris)))
    idx_str = ", ".join(str(int(i)) for t in vis_tris for i in t)
    uv_str = ", ".join(f"({float(u):.5f}, {float(v):.5f})" for u, v in vis_uvs)
    usda = f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Scope "Looks"
    {{
        def Material "PBRMat"
        {{
            token outputs:surface.connect = </World/Looks/PBRMat/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor.connect = </World/Looks/PBRMat/AlbedoTex.outputs:rgb>
                float inputs:roughness.connect = </World/Looks/PBRMat/RoughnessTex.outputs:r>
                normal3f inputs:normal.connect = </World/Looks/PBRMat/NormalTex.outputs:rgb>
                float inputs:metallic = 0.0
                token outputs:surface
            }}

            def Shader "PrimvarReader"
            {{
                uniform token info:id = "UsdPrimvarReader_float2"
                token inputs:varname = "st"
                float2 outputs:result
            }}

            def Shader "AlbedoTex"
            {{
                uniform token info:id = "UsdUVTexture"
                asset inputs:file = @./textures/albedo.png@
                token inputs:sourceColorSpace = "sRGB"
                token inputs:wrapS = "repeat"
                token inputs:wrapT = "repeat"
                float2 inputs:st.connect = </World/Looks/PBRMat/PrimvarReader.outputs:result>
                color3f outputs:rgb
            }}

            def Shader "RoughnessTex"
            {{
                uniform token info:id = "UsdUVTexture"
                asset inputs:file = @./textures/roughness.png@
                token inputs:sourceColorSpace = "raw"
                token inputs:wrapS = "repeat"
                token inputs:wrapT = "repeat"
                float2 inputs:st.connect = </World/Looks/PBRMat/PrimvarReader.outputs:result>
                float outputs:r
            }}

            def Shader "NormalTex"
            {{
                uniform token info:id = "UsdUVTexture"
                asset inputs:file = @./textures/normal.png@
                token inputs:sourceColorSpace = "raw"
                token inputs:wrapS = "repeat"
                token inputs:wrapT = "repeat"
                float4 inputs:scale = (2, 2, 2, 1)
                float4 inputs:bias = (-1, -1, -1, 0)
                float2 inputs:st.connect = </World/Looks/PBRMat/PrimvarReader.outputs:result>
                normal3f outputs:rgb
            }}
        }}
    }}

    def Mesh "VisualHighPoly" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {{
        rel material:binding = </World/Looks/PBRMat>
        bool doubleSided = 1
        uniform token subdivisionScheme = "none"
        int[] faceVertexCounts = [{cnt_str}]
        int[] faceVertexIndices = [{idx_str}]
        point3f[] points = [{pts_str}]
        texCoord2f[] primvars:st = [{uv_str}] (
            interpolation = "vertex"
        )
    }}
}}
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(usda, encoding="utf-8")


def verify_v04_bundle_mujoco4(bundle_dir: Path) -> dict[str, Any]:
    """Run live MuJoCo 4.0.1 CPU settle probe on a v0.4 volumetric tet deformable bundle (0% GPU)."""
    proxy = np.load(bundle_dir / "physics_proxy.npz", allow_pickle=False)
    man = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    spec = man["source"]
    pts = np.asarray(proxy["rest_points"], dtype=np.float64)
    tets = np.asarray(proxy["elements"], dtype=np.int64)

    p_str = "  ".join(f"{p[0]:.5f} {p[1]:.5f} {p[2]:.5f}" for p in pts)
    e_str = "  ".join(f"{t[0]} {t[1]} {t[2]} {t[3]}" for t in tets)
    el_tag = f'<elasticity young="{spec["youngs_modulus_pa"]}" poisson="{spec["poissons_ratio"]}" damping="0.06"/>'
    xml = f'''<mujoco>
  <option timestep="0.002" integrator="discrete" iterations="80"><flag speculative="enable"/></option>
  <worldbody>
    <geom type="plane" size="1 1 0.1" friction="0.8 0.02 0.002"/>
    <flexcomp name="obj" type="direct" dim="3" pos="0 0 0.005" point="{p_str}" element="{e_str}" mass="{spec["mass_kg"]}" radius="0.0018">
      <contact condim="3" friction="1.4 0.02 0.002" selfcollide="none" solref="0.004 1"/>
      <edge equality="false"/>
      {el_tag}
    </flexcomp>
  </worldbody>
</mujoco>'''

    script = f"""
import json, mujoco, numpy as np
m = mujoco.MjModel.from_xml_string({xml!r})
d = mujoco.MjData(m)
mujoco.mj_forward(m, d)
h0 = float(d.flexvert_xpos[:, 2].max() - d.flexvert_xpos[:, 2].min())
for _ in range(120):
    mujoco.mj_step(m, d)
pts_f = d.flexvert_xpos.copy()
fin = bool(np.all(np.isfinite(pts_f)))
h1 = float(pts_f[:, 2].max() - pts_f[:, 2].min()) if fin else -1.0
print(json.dumps({{"finite": fin, "h0_m": round(h0, 5), "h1_m": round(h1, 5), "nvert": int(len(pts_f))}}))
"""
    if not MUJOCO4_PYTHON.is_file():
        raise FileNotFoundError(f"MuJoCo4 Python not found: {MUJOCO4_PYTHON}")
    proc = subprocess.run([str(MUJOCO4_PYTHON), "-c", script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout.strip().splitlines()[-1])


def build_v04_deformable_bundle(
    asset_id: str,
    bundle_dir: str | Path,
    *,
    tex_size: int = 1024,
    run_mujoco_probe: bool = True,
) -> dict[str, Any]:
    """Build complete M1 v0.4 volumetric tet + watertight shell + PBR + skinning bundle."""
    if asset_id not in V04_DEFORMABLE_SPECS:
        raise ValueError(f"Unknown v0.4 deformable asset_id: {asset_id!r}")
    spec = V04_DEFORMABLE_SPECS[asset_id]
    builders = {
        "v04_clamp_pad_01": _build_clamp_pad_asset,
        "v04_ptfe_taper_sleeve_01": _build_ptfe_taper_sleeve_asset,
        "v04_rubber_septum_01": _build_rubber_septum_asset,
        "v04_dual_cooling_hoses_01": _build_dual_cooling_hoses_asset,
    }
    built = builders[asset_id]()
    out_dir = Path(bundle_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    phys_pts = built["phys_pts"]
    tets = built["tets"]
    phys_tris = built["phys_tris"]
    phys_edges = built["phys_edges"]
    vis_pts = built["vis_pts"]
    vis_tris = built["vis_tris"]
    vis_uvs = built["vis_uvs"]

    # Check positive Jacobian across all tetrahedra
    p0 = phys_pts[tets[:, 0]]
    dm = np.stack([phys_pts[tets[:, 1]] - p0, phys_pts[tets[:, 2]] - p0, phys_pts[tets[:, 3]] - p0], axis=-1)
    min_det = float(np.min(np.linalg.det(dm)))
    if min_det <= 0.0:
        raise RuntimeError(f"Non-positive tet determinant for {asset_id}: {min_det}")

    w_skin, skin_err = build_tet_barycentric_skinning(phys_pts, tets, vis_pts)
    if skin_err > 1e-6:
        raise RuntimeError(f"Skinning rest error too large for {asset_id}: {skin_err:.6e}")
    np.savez_compressed(out_dir / "skinning.npz", mode=np.array(["tet_bary"]), w_skin=w_skin)

    _generate_custom_pbr_maps(spec, out_dir / "textures", tex_size=tex_size)

    proxy_payload: dict[str, np.ndarray] = {
        "rest_points": phys_pts,
        "elements": tets,
        "triangles": phys_tris,
        "edges": phys_edges,
        "visual_rest_points": vis_pts,
        "visual_triangles": vis_tris,
        "visual_uvs": vis_uvs,
    }
    if "assembled_rest_points" in built:
        proxy_payload["assembled_rest_points"] = built["assembled_rest_points"]
    np.savez_compressed(out_dir / "physics_proxy.npz", **proxy_payload)

    _write_v04_base_usda(out_dir / "base.usda", spec, phys_pts, phys_tris)
    _write_v04_visual_highpoly_usda(out_dir / "visual_highpoly.usda", vis_pts, vis_tris, vis_uvs)
    _write_obj(out_dir / "engines" / "mujoco4" / "mesh.obj", phys_pts, phys_tris)
    _write_obj(out_dir / "engines" / "visual_highpoly.obj", vis_pts, vis_tris, vis_uvs)

    sha_index = {
        rel: _sha256_file(out_dir / rel)
        for rel in (
            "base.usda",
            "visual_highpoly.usda",
            "physics_proxy.npz",
            "skinning.npz",
            "textures/albedo.png",
            "textures/normal.png",
            "textures/roughness.png",
            "engines/mujoco4/mesh.obj",
        )
    }
    manifest: dict[str, Any] = {
        "schema_version": "distillation_v04_bundle/v0.1",
        "asset_id": asset_id,
        "source": {
            "asset_id": spec.asset_id,
            "category": spec.category,
            "structural_family": spec.structural_family,
            "dimensions_xyz_m": list(spec.dimensions_xyz_m),
            "mass_kg": spec.mass_kg,
            "youngs_modulus_pa": spec.youngs_modulus_pa,
            "poissons_ratio": spec.poissons_ratio,
            "yield_stress_pa": spec.yield_stress_pa,
            "default_color": list(spec.default_color),
            "roughness_range": list(spec.roughness_range),
        },
        "skinning": {
            "mode": "tet_bary",
            "n_phys_verts": int(len(phys_pts)),
            "n_phys_tets": int(len(tets)),
            "min_tet_det": min_det,
            "n_vis_verts": int(len(vis_pts)),
            "n_vis_tris": int(len(vis_tris)),
            "max_rest_skin_err_m": float(skin_err),
        },
        "integrity_budget": {
            "fragility_tier": spec.fragility_tier,
            "strain_metric": "polar_stretch_q95",
            "strain_onset_a": spec.strain_onset_a,
            "strain_failure_b": spec.strain_failure_b,
            "damage_threshold": spec.damage_threshold,
            "max_normal_force_n": spec.max_normal_force_n,
            "max_shear_force_n": round(0.75 * spec.max_normal_force_n, 2),
        },
        "sha256_index": sha_index,
        "mujoco4_probe": None,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if run_mujoco_probe:
        manifest["mujoco4_probe"] = verify_v04_bundle_mujoco4(out_dir)
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def build_all_v04_deformable_bundles(
    bundles_root: str | Path,
    *,
    tex_size: int = 1024,
    run_mujoco_probe: bool = True,
) -> dict[str, Any]:
    root = Path(bundles_root)
    root.mkdir(parents=True, exist_ok=True)
    summaries: dict[str, Any] = {}
    for aid in V04_DEFORMABLE_SPECS:
        man = build_v04_deformable_bundle(aid, root / aid, tex_size=tex_size, run_mujoco_probe=run_mujoco_probe)
        summaries[aid] = man
    (root / "m1_v04_bundles_summary.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    return summaries
