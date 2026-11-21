"""High-poly sculpted UV-mapped deformable assets and matched physics proxies (v0.3)."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np


@dataclass(frozen=True)
class V03AssetSpec:
    asset_id: str
    category: str
    structural_family: str
    dimensions_xyz_m: tuple[float, float, float]
    mass_kg: float
    youngs_modulus_pa: float
    poissons_ratio: float
    yield_stress_pa: float | None
    strain_onset_a: float
    strain_failure_b: float
    damage_threshold: float
    max_normal_force_n: float
    fragility_tier: str
    skin_mode: str  # "tet_bary" or "shell_frame"
    fallback_rgb: tuple[int, int, int]
    roughness_range: tuple[float, float]
    raw_texture_name: str
    default_color: tuple[float, float, float]


V03_ASSET_SPECS: dict[str, V03AssetSpec] = {
    "v03_croissant_butter_01": V03AssetSpec(
        asset_id="v03_croissant_butter_01",
        category="flaky_croissant_pastry",
        structural_family="soft_solid",
        dimensions_xyz_m=(0.118, 0.068, 0.032),
        mass_kg=0.068,
        youngs_modulus_pa=38000.0,
        poissons_ratio=0.28,
        yield_stress_pa=18000.0,
        strain_onset_a=0.16,
        strain_failure_b=0.46,
        damage_threshold=0.25,
        max_normal_force_n=14.0,
        fragility_tier="high",
        skin_mode="tet_bary",
        fallback_rgb=(210, 140, 62),
        roughness_range=(0.30, 0.58),
        raw_texture_name="croissant_crust_raw.png",
        default_color=(0.82, 0.55, 0.24),
    ),
    "v03_strawberry_fresh_01": V03AssetSpec(
        asset_id="v03_strawberry_fresh_01",
        category="fresh_strawberry_fruit",
        structural_family="soft_solid",
        dimensions_xyz_m=(0.056, 0.056, 0.044),
        mass_kg=0.042,
        youngs_modulus_pa=22000.0,
        poissons_ratio=0.32,
        yield_stress_pa=11000.0,
        strain_onset_a=0.13,
        strain_failure_b=0.36,
        damage_threshold=0.25,
        max_normal_force_n=7.5,
        fragility_tier="ultra_high",
        skin_mode="tet_bary",
        fallback_rgb=(196, 36, 48),
        roughness_range=(0.24, 0.48),
        raw_texture_name="strawberry_skin_raw.png",
        default_color=(0.78, 0.14, 0.19),
    ),
    "v03_waffle_towel_01": V03AssetSpec(
        asset_id="v03_waffle_towel_01",
        category="waffle_weave_cotton_towel",
        structural_family="cloth_sheet",
        dimensions_xyz_m=(0.20, 0.20, 0.038),
        mass_kg=0.048,
        youngs_modulus_pa=28000.0,
        poissons_ratio=0.30,
        yield_stress_pa=None,
        strain_onset_a=0.18,
        strain_failure_b=0.50,
        damage_threshold=0.25,
        max_normal_force_n=35.0,
        fragility_tier="medium",
        skin_mode="shell_frame",
        fallback_rgb=(88, 158, 152),
        roughness_range=(0.72, 0.94),
        raw_texture_name="waffle_cotton_raw.png",
        default_color=(0.35, 0.62, 0.60),
    ),
    "v03_linen_dust_cover_01": V03AssetSpec(
        asset_id="v03_linen_dust_cover_01",
        category="protective_linen_dust_cover",
        structural_family="cloth_sheet",
        dimensions_xyz_m=(0.20, 0.20, 0.006),
        mass_kg=0.052,
        youngs_modulus_pa=22000.0,
        poissons_ratio=0.30,
        yield_stress_pa=None,
        strain_onset_a=0.18,
        strain_failure_b=0.50,
        damage_threshold=0.25,
        max_normal_force_n=38.0,
        fragility_tier="medium",
        skin_mode="shell_frame",
        fallback_rgb=(74, 102, 134),
        roughness_range=(0.68, 0.90),
        raw_texture_name="charcoal_linen_raw.png",
        default_color=(0.29, 0.40, 0.53),
    ),
    "v03_idc_ribbon_cable_01": V03AssetSpec(
        asset_id="v03_idc_ribbon_cable_01",
        category="flexible_idc_ribbon_cable",
        structural_family="rod_cable",
        dimensions_xyz_m=(0.18, 0.024, 0.009),
        mass_kg=0.045,
        youngs_modulus_pa=95000.0,
        poissons_ratio=0.32,
        yield_stress_pa=42000.0,
        strain_onset_a=0.22,
        strain_failure_b=0.58,
        damage_threshold=0.25,
        max_normal_force_n=28.0,
        fragility_tier="medium",
        skin_mode="tet_bary",
        fallback_rgb=(142, 150, 162),
        roughness_range=(0.35, 0.60),
        raw_texture_name="idc_ribbon_raw.png",
        default_color=(0.56, 0.59, 0.64),
    ),
    "v03_esd_silicone_boot_01": V03AssetSpec(
        asset_id="v03_esd_silicone_boot_01",
        category="esd_silicone_protective_boot",
        structural_family="shell",
        dimensions_xyz_m=(0.064, 0.064, 0.032),
        mass_kg=0.048,
        youngs_modulus_pa=160000.0,
        poissons_ratio=0.36,
        yield_stress_pa=None,
        strain_onset_a=0.20,
        strain_failure_b=0.55,
        damage_threshold=0.25,
        max_normal_force_n=42.0,
        fragility_tier="medium",
        skin_mode="shell_frame",
        fallback_rgb=(64, 176, 178),
        roughness_range=(0.45, 0.72),
        raw_texture_name="esd_silicone_raw.png",
        default_color=(0.25, 0.69, 0.70),
    ),
    "v03_lab_silicone_tube_01": V03AssetSpec(
        asset_id="v03_lab_silicone_tube_01",
        category="medical_silicone_tubing",
        structural_family="rod_cable",
        dimensions_xyz_m=(0.19, 0.022, 0.022),
        mass_kg=0.052,
        youngs_modulus_pa=85000.0,
        poissons_ratio=0.38,
        yield_stress_pa=45000.0,
        strain_onset_a=0.22,
        strain_failure_b=0.58,
        damage_threshold=0.25,
        max_normal_force_n=26.0,
        fragility_tier="medium",
        skin_mode="tet_bary",
        fallback_rgb=(224, 172, 102),
        roughness_range=(0.18, 0.38),
        raw_texture_name="lab_silicone_raw.png",
        default_color=(0.88, 0.67, 0.40),
    ),
    "v03_pipette_rubber_bulb_01": V03AssetSpec(
        asset_id="v03_pipette_rubber_bulb_01",
        category="laboratory_pipette_rubber_bulb",
        structural_family="shell",
        dimensions_xyz_m=(0.054, 0.054, 0.064),
        mass_kg=0.045,
        youngs_modulus_pa=180000.0,
        poissons_ratio=0.35,
        yield_stress_pa=None,
        strain_onset_a=0.22,
        strain_failure_b=0.60,
        damage_threshold=0.25,
        max_normal_force_n=45.0,
        fragility_tier="medium",
        skin_mode="shell_frame",
        fallback_rgb=(188, 86, 62),
        roughness_range=(0.52, 0.78),
        raw_texture_name="rubber_bulb_raw.png",
        default_color=(0.74, 0.34, 0.24),
    ),
}


def _hex_5tet_grid(nx: int, ny: int, nz: int) -> tuple[np.ndarray, np.ndarray]:
    """Return normalized grid coords in [-1, 1]^3 and strictly positive-orientation 5-tet decomposition."""
    us = np.linspace(-1.0, 1.0, nx + 1)
    vs = np.linspace(-1.0, 1.0, ny + 1)
    ws = np.linspace(-1.0, 1.0, nz + 1)
    pts = np.array([(u, v, w) for w in ws for v in vs for u in us], dtype=np.float64)

    def vid(ix: int, iy: int, iz: int) -> int:
        return iz * ((ny + 1) * (nx + 1)) + iy * (nx + 1) + ix

    tets: list[tuple[int, int, int, int]] = []
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                p000, p100 = vid(ix, iy, iz), vid(ix + 1, iy, iz)
                p010, p110 = vid(ix, iy + 1, iz), vid(ix + 1, iy + 1, iz)
                p001, p101 = vid(ix, iy, iz + 1), vid(ix + 1, iy, iz + 1)
                p011, p111 = vid(ix, iy + 1, iz + 1), vid(ix + 1, iy + 1, iz + 1)
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
    return pts, np.asarray(tets, dtype=np.int64)


def _orient_tets_positive(pts: np.ndarray, tets: np.ndarray) -> np.ndarray:
    out = np.asarray(tets, dtype=np.int64).copy()
    for idx, (a, b, c, d_i) in enumerate(out):
        det = float(np.linalg.det(np.column_stack((pts[b] - pts[a], pts[c] - pts[a], pts[d_i] - pts[a]))))
        if det < 0.0:
            out[idx] = (a, c, b, d_i)
    return out


def _edges_from_elements(elems: np.ndarray) -> np.ndarray:
    edge_set: set[tuple[int, int]] = set()
    w = elems.shape[1]
    for row in elems:
        for i in range(w):
            for j in range(i + 1, w):
                u, v = int(row[i]), int(row[j])
                edge_set.add((u, v) if u < v else (v, u))
    return np.asarray(sorted(edge_set), dtype=np.int64)


def _surface_tris_from_tets(pts: np.ndarray, tets: np.ndarray) -> np.ndarray:
    face_counts: dict[tuple[int, int, int], tuple[tuple[int, int, int], int]] = {}
    for a, b, c, d_i in tets:
        for tri, opp in (
            ((a, c, b), d_i),
            ((a, b, d_i), c),
            ((b, c, d_i), a),
            ((c, a, d_i), b),
        ):
            key = tuple(sorted(tri))
            if key in face_counts:
                face_counts.pop(key)
            else:
                face_counts[key] = (tri, opp)
    out: list[tuple[int, int, int]] = []
    for tri, opp in face_counts.values():
        p0, p1, p2 = pts[tri[0]], pts[tri[1]], pts[tri[2]]
        n = np.cross(p1 - p0, p2 - p0)
        if float(np.dot(n, pts[opp] - p0)) > 0.0:
            out.append((tri[0], tri[2], tri[1]))
        else:
            out.append(tri)
    return np.asarray(out, dtype=np.int64)


def _loft_closed_tube(
    n_u: int,
    n_v: int,
    eval_ring_fn: Any,
    uv_scale: tuple[float, float] = (1.0, 1.0),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Loft a closed double-pole parametric surface u in [-1, 1], v in [0, 2*pi) -> (verts, tris, uvs)."""
    us = np.linspace(-1.0, 1.0, n_u)
    vs = np.linspace(0.0, 2.0 * math.pi, n_v, endpoint=False)
    verts: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []

    p_start = eval_ring_fn(-1.0, 0.0, is_pole=True)
    p_end = eval_ring_fn(1.0, 0.0, is_pole=True)
    verts.append(tuple(float(x) for x in p_start))
    uvs.append((0.0, 0.5))

    ring_start = len(verts)
    for ui in range(1, n_u - 1):
        u = float(us[ui])
        u_tex = 0.5 * (u + 1.0) * uv_scale[0]
        for vi, v in enumerate(vs):
            p = eval_ring_fn(u, float(v), is_pole=False)
            verts.append((float(p[0]), float(p[1]), float(p[2])))
            uvs.append((u_tex, (vi / float(n_v)) * uv_scale[1]))

    end_pole_idx = len(verts)
    verts.append(tuple(float(x) for x in p_end))
    uvs.append((uv_scale[0], 0.5))

    tris: list[tuple[int, int, int]] = []
    # Start pole fan (u=-1)
    for vi in range(n_v):
        vn = (vi + 1) % n_v
        tris.append((0, ring_start + vn, ring_start + vi))
    # Interior rings
    for ui in range(n_u - 3):
        r0 = ring_start + ui * n_v
        r1 = ring_start + (ui + 1) * n_v
        for vi in range(n_v):
            vn = (vi + 1) % n_v
            tris.append((r0 + vi, r0 + vn, r1 + vn))
            tris.append((r0 + vi, r1 + vn, r1 + vi))
    # End pole fan (u=+1)
    last_ring = ring_start + (n_u - 3) * n_v
    for vi in range(n_v):
        vn = (vi + 1) % n_v
        tris.append((end_pole_idx, last_ring + vi, last_ring + vn))

    v_arr = np.asarray(verts, dtype=np.float64)
    t_arr = np.asarray(tris, dtype=np.int64)
    uv_arr = np.asarray(uvs, dtype=np.float32)

    # Ensure positive outward signed volume orientation
    vol = 0.0
    for a, b, c in t_arr:
        vol += float(np.dot(v_arr[a], np.cross(v_arr[b], v_arr[c]))) / 6.0
    if vol < 0.0:
        t_arr = t_arr[:, [0, 2, 1]]
    return v_arr, t_arr, uv_arr


def _normalize_xy_center_z_floor(pts: np.ndarray, extra_pts: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None]:
    cxy = pts[:, :2].mean(axis=0)
    z0 = float(pts[:, 2].min())
    out = pts.copy()
    out[:, 0] -= float(cxy[0])
    out[:, 1] -= float(cxy[1])
    out[:, 2] -= z0
    if extra_pts is None:
        return out, None
    ext = extra_pts.copy()
    ext[:, 0] -= float(cxy[0])
    ext[:, 1] -= float(cxy[1])
    ext[:, 2] -= z0
    return out, ext


def _build_croissant_pair() -> dict[str, Any]:
    g, tets = _hex_5tet_grid(6, 2, 2)
    u, v, w = g[:, 0], g[:, 1], g[:, 2]
    th = 0.88 * u
    taper = 1.0 - 0.50 * (u ** 2)
    rx = 0.062 + 0.024 * taper * v
    phys_pts = np.column_stack([rx * np.sin(th), rx * np.cos(th) - 0.062, 0.0155 * taper * (w + 1.0)])
    tets = _orient_tets_positive(phys_pts, tets)

    def eval_croissant(uu: float, phi: float, is_pole: bool) -> np.ndarray:
        th_u = 0.88 * uu
        tap = max(0.14, 1.0 - 0.52 * (uu ** 2))
        if is_pole:
            r_mid = 0.062
            return np.array([r_mid * math.sin(th_u), r_mid * math.cos(th_u) - 0.062, 0.008], dtype=np.float64)
        # 5 laminated roll segments + gentle rounded belly
        seg_rib = 1.0 + 0.14 * abs(math.sin(2.5 * math.pi * uu))
        r_y = 0.0255 * tap * seg_rib
        r_z = 0.0175 * tap * seg_rib
        ly = r_y * math.cos(phi)
        lz = r_z * math.sin(phi)
        # Slightly flatten resting underside
        if lz < -0.55 * r_z:
            lz = -0.55 * r_z + 0.25 * (lz + 0.55 * r_z)
        z_mid = 0.0155 * tap
        r_arc = 0.062 + ly
        return np.array([r_arc * math.sin(th_u), r_arc * math.cos(th_u) - 0.062, max(0.0, z_mid + lz)], dtype=np.float64)

    vis_pts, vis_tris, vis_uvs = _loft_closed_tube(50, 32, eval_croissant, uv_scale=(2.2, 1.0))
    phys_pts, vis_pts = _normalize_xy_center_z_floor(phys_pts, vis_pts)
    return {
        "phys_pts": phys_pts,
        "phys_elems": tets,
        "phys_tris": _surface_tris_from_tets(phys_pts, tets),
        "phys_edges": _edges_from_elements(tets),
        "vis_pts": vis_pts,
        "vis_tris": vis_tris,
        "vis_uvs": vis_uvs,
    }


def _build_strawberry_pair() -> dict[str, Any]:
    g, tets = _hex_5tet_grid(4, 4, 2)
    u, v, w = g[:, 0], g[:, 1], g[:, 2]
    z_norm = 0.5 * (w + 1.0)
    # Upright berry: flat base z=0, plump waist z~0.35, tapered conical dome z=1.0
    xy_profile = 0.0265 * (0.78 + 0.34 * np.sin(math.pi * (z_norm ** 0.72)) - 0.36 * (z_norm ** 1.7))
    # Smooth corner rounding on square hex grid
    r_sq = np.maximum(np.abs(u), np.abs(v))
    r_eu = np.sqrt(u * u + v * v + 1e-12)
    blend = 1.0 - 0.22 * np.maximum(0.0, (u * u * v * v))
    phys_pts = np.column_stack([xy_profile * blend * u, xy_profile * blend * v, 0.044 * z_norm])
    tets = _orient_tets_positive(phys_pts, tets)

    def eval_berry(uu: float, phi: float, is_pole: bool) -> np.ndarray:
        zn = 0.5 * (uu + 1.0)
        z_val = 0.045 * zn
        if is_pole:
            return np.array([0.0, 0.0, z_val], dtype=np.float64)
        rad = 0.0275 * (0.76 + 0.36 * math.sin(math.pi * (zn ** 0.72)) - 0.44 * (zn ** 1.8))
        # Subtle achene dimple ripple + gentle 5-lobe strawberry silhouette
        lobe = 1.0 + 0.025 * math.cos(5.0 * phi) + 0.015 * math.sin(14.0 * zn * math.pi + 7.0 * phi)
        rad = max(0.002, rad * lobe)
        return np.array([rad * math.cos(phi), rad * math.sin(phi), z_val], dtype=np.float64)

    vis_pts, vis_tris, vis_uvs = _loft_closed_tube(42, 32, eval_berry, uv_scale=(1.5, 1.5))
    phys_pts, vis_pts = _normalize_xy_center_z_floor(phys_pts, vis_pts)
    return {
        "phys_pts": phys_pts,
        "phys_elems": tets,
        "phys_tris": _surface_tris_from_tets(phys_pts, tets),
        "phys_edges": _edges_from_elements(tets),
        "vis_pts": vis_pts,
        "vis_tris": vis_tris,
        "vis_uvs": vis_uvs,
    }


def _build_cloth_pair(
    size_xy: float = 0.20,
    thick: float = 0.0046,
    n_phys: int = 8,
    n_vis: int = 28,
    pleat_amp: float = 0.0,
) -> dict[str, Any]:
    xs = np.linspace(-0.5 * size_xy, 0.5 * size_xy, n_phys + 1)
    ys = np.linspace(-0.5 * size_xy, 0.5 * size_xy, n_phys + 1)
    phys_pts = np.array(
        [
            [
                x,
                y,
                pleat_amp * math.exp(-(((x + 0.055) / 0.022) ** 2)) if pleat_amp > 0.0 else 0.0,
            ]
            for y in ys
            for x in xs
        ],
        dtype=np.float64,
    )
    phys_tris_l: list[tuple[int, int, int]] = []
    for j in range(n_phys):
        for i in range(n_phys):
            v00 = j * (n_phys + 1) + i
            v10 = v00 + 1
            v01 = (j + 1) * (n_phys + 1) + i
            v11 = v01 + 1
            phys_tris_l.extend([(v00, v10, v11), (v00, v11, v01)])
    phys_tris = np.asarray(phys_tris_l, dtype=np.int64)

    # Thickened pillowed high-poly cloth slab (top + bottom + hem perimeter -> ~3,200+ tris)
    hx = np.linspace(-0.5 * size_xy, 0.5 * size_xy, n_vis + 1)
    hy = np.linspace(-0.5 * size_xy, 0.5 * size_xy, n_vis + 1)
    nv1 = n_vis + 1
    vis_verts: list[tuple[float, float, float]] = []
    vis_uvs: list[tuple[float, float]] = []
    ht = 0.5 * thick
    for is_top, sgn in ((True, 1.0), (False, -1.0)):
        for j, y in enumerate(hy):
            for i, x in enumerate(hx):
                u_n = i / float(n_vis)
                v_n = j / float(n_vis)
                edge_dist = min(u_n, 1.0 - u_n, v_n, 1.0 - v_n)
                taper = min(1.0, edge_dist / 0.04)
                waffle = 0.0007 * math.sin(18.0 * math.pi * u_n) * math.sin(18.0 * math.pi * v_n) * taper
                z_pleat = pleat_amp * math.exp(-(((float(x) + 0.055) / 0.022) ** 2)) if pleat_amp > 0.0 else 0.0
                vis_verts.append((float(x), float(y), sgn * (ht * (0.55 + 0.45 * taper) + max(-0.4 * ht, waffle)) + z_pleat))
                vis_uvs.append((u_n * 2.0, v_n * 2.0))

    vis_tris_l: list[tuple[int, int, int]] = []
    top_off = 0
    bot_off = nv1 * nv1
    for j in range(n_vis):
        for i in range(n_vis):
            a = top_off + j * nv1 + i
            b, c, d = a + 1, a + nv1, a + nv1 + 1
            vis_tris_l.extend([(a, b, d), (a, d, c)])
            ab = bot_off + j * nv1 + i
            bb, cb, db = ab + 1, ab + nv1, ab + nv1 + 1
            vis_tris_l.extend([(ab, db, bb), (ab, cb, db)])
    # Stitch perimeter edges
    for i in range(n_vis):
        # y=0 border
        t0, t1 = top_off + i, top_off + i + 1
        b0, b1 = bot_off + i, bot_off + i + 1
        vis_tris_l.extend([(t0, b0, b1), (t0, b1, t1)])
        # y=max border
        rt0, rt1 = top_off + n_vis * nv1 + i, top_off + n_vis * nv1 + i + 1
        rb0, rb1 = bot_off + n_vis * nv1 + i, bot_off + n_vis * nv1 + i + 1
        vis_tris_l.extend([(rt0, rb1, rb0), (rt0, rt1, rb1)])
    for j in range(n_vis):
        # x=0 border
        t0, t1 = top_off + j * nv1, top_off + (j + 1) * nv1
        b0, b1 = bot_off + j * nv1, bot_off + (j + 1) * nv1
        vis_tris_l.extend([(t0, t1, b1), (t0, b1, b0)])
        # x=max border
        ct0, ct1 = top_off + j * nv1 + n_vis, top_off + (j + 1) * nv1 + n_vis
        cb0, cb1 = bot_off + j * nv1 + n_vis, bot_off + (j + 1) * nv1 + n_vis
        vis_tris_l.extend([(ct0, cb1, ct1), (ct0, cb0, cb1)])

    vis_pts = np.asarray(vis_verts, dtype=np.float64)
    return {
        "phys_pts": phys_pts,
        "phys_elems": _edges_from_elements(phys_tris),
        "phys_tris": phys_tris,
        "phys_edges": _edges_from_elements(phys_tris),
        "vis_pts": vis_pts,
        "vis_tris": np.asarray(vis_tris_l, dtype=np.int64),
        "vis_uvs": np.asarray(vis_uvs, dtype=np.float32),
    }


def _build_ribbon_cable_pair() -> dict[str, Any]:
    g, tets = _hex_5tet_grid(10, 2, 1)
    u, v, w = g[:, 0], g[:, 1], g[:, 2]
    phys_pts = np.column_stack([0.090 * u, 0.012 * v, 0.0045 * (w + 1.0)])
    tets = _orient_tets_positive(phys_pts, tets)

    def eval_ribbon(uu: float, phi: float, is_pole: bool) -> np.ndarray:
        x_val = 0.092 * uu
        if is_pole:
            return np.array([x_val, 0.0, 0.0045], dtype=np.float64)
        is_header = abs(uu) > 0.84
        hy = 0.0135 if is_header else 0.0115
        hz = 0.0068 if is_header else 0.0042
        # Rounded superellipse cross-section + micro conductor ribs on middle span
        cy = math.cos(phi)
        sz = math.sin(phi)
        rib = 0.0 if is_header else 0.0006 * math.cos(16.0 * math.pi * (cy * 0.5 + 0.5))
        yy = math.copysign(abs(cy) ** 0.55, cy) * hy
        zz = 0.0045 + math.copysign(abs(sz) ** 0.55, sz) * hz + (rib if sz > 0 else -rib) * 0.5
        return np.array([x_val, yy, max(0.0, zz)], dtype=np.float64)

    vis_pts, vis_tris, vis_uvs = _loft_closed_tube(48, 30, eval_ribbon, uv_scale=(1.0, 1.0))
    phys_pts, vis_pts = _normalize_xy_center_z_floor(phys_pts, vis_pts)
    return {
        "phys_pts": phys_pts,
        "phys_elems": tets,
        "phys_tris": _surface_tris_from_tets(phys_pts, tets),
        "phys_edges": _edges_from_elements(tets),
        "vis_pts": vis_pts,
        "vis_tris": vis_tris,
        "vis_uvs": vis_uvs,
    }


def _build_silicone_tube_pair() -> dict[str, Any]:
    g, tets = _hex_5tet_grid(12, 2, 2)
    u, v, w = g[:, 0], g[:, 1], g[:, 2]
    # Round square hex cross section smoothly into octagon/cylinder keeping positive Jacobians
    s_fac = 1.0 / np.maximum(1.0, np.sqrt(1.0 + 0.28 * (v * v * w * w)))
    phys_pts = np.column_stack([0.095 * u, 0.011 * v * s_fac, 0.011 * (w * s_fac + 1.0)])
    tets = _orient_tets_positive(phys_pts, tets)

    def eval_tube(uu: float, phi: float, is_pole: bool) -> np.ndarray:
        x_val = 0.096 * uu
        if is_pole:
            return np.array([x_val, 0.0, 0.011], dtype=np.float64)
        # Beveled medical tubing tips at |u| > 0.96
        r_tip = 0.0108 * min(1.0, max(0.35, (1.0 - abs(uu)) / 0.04))
        collar = 1.0 + (0.08 if 0.80 < abs(uu) < 0.90 else 0.0)
        rad = r_tip * collar
        return np.array([x_val, rad * math.cos(phi), 0.011 + rad * math.sin(phi)], dtype=np.float64)

    vis_pts, vis_tris, vis_uvs = _loft_closed_tube(50, 28, eval_tube, uv_scale=(2.0, 1.0))
    phys_pts, vis_pts = _normalize_xy_center_z_floor(phys_pts, vis_pts)
    return {
        "phys_pts": phys_pts,
        "phys_elems": tets,
        "phys_tris": _surface_tris_from_tets(phys_pts, tets),
        "phys_edges": _edges_from_elements(tets),
        "vis_pts": vis_pts,
        "vis_tris": vis_tris,
        "vis_uvs": vis_uvs,
    }


def _build_esd_boot_pair() -> dict[str, Any]:
    # Closed dim=2 rounded protective boot cap: 6 rings * 12 = 72 + 2 poles -> clean triangle shell
    def eval_boot_phys(uu: float, phi: float, is_pole: bool) -> np.ndarray:
        zn = 0.5 * (uu + 1.0)
        if is_pole:
            return np.array([0.0, 0.0, 0.032 * zn], dtype=np.float64)
        profile = 1.0 - 0.18 * (zn ** 2.2)
        c, s = math.cos(phi), math.sin(phi)
        rx = 0.032 * profile * (abs(c) ** 0.72) * (1.0 if c >= 0 else -1.0)
        ry = 0.032 * profile * (abs(s) ** 0.72) * (1.0 if s >= 0 else -1.0)
        return np.array([rx, ry, 0.032 * zn], dtype=np.float64)

    phys_pts, phys_tris, _ = _loft_closed_tube(7, 12, eval_boot_phys, uv_scale=(1.0, 1.0))

    def eval_boot_vis(uu: float, phi: float, is_pole: bool) -> np.ndarray:
        zn = 0.5 * (uu + 1.0)
        if is_pole:
            return np.array([0.0, 0.0, 0.033 * zn], dtype=np.float64)
        rib = 1.0 + 0.04 * math.sin(10.0 * math.pi * zn)
        flange = 1.08 if zn < 0.14 else (1.0 - 0.22 * (zn ** 2.2))
        c, s = math.cos(phi), math.sin(phi)
        rx = 0.032 * flange * rib * (abs(c) ** 0.68) * (1.0 if c >= 0 else -1.0)
        ry = 0.032 * flange * rib * (abs(s) ** 0.68) * (1.0 if s >= 0 else -1.0)
        return np.array([rx, ry, 0.033 * zn], dtype=np.float64)

    vis_pts, vis_tris, vis_uvs = _loft_closed_tube(44, 36, eval_boot_vis, uv_scale=(1.5, 1.5))
    phys_pts, vis_pts = _normalize_xy_center_z_floor(phys_pts, vis_pts)
    return {
        "phys_pts": phys_pts,
        "phys_elems": _edges_from_elements(phys_tris),
        "phys_tris": phys_tris,
        "phys_edges": _edges_from_elements(phys_tris),
        "vis_pts": vis_pts,
        "vis_tris": vis_tris,
        "vis_uvs": vis_uvs,
    }


def _build_rubber_bulb_pair() -> dict[str, Any]:
    def _pear_radius(zn: float, amp: float = 0.027) -> float:
        # Wide lower collar base tapering gently -> swollen bulb belly -> rounded top tip
        r = amp * (0.48 + 0.52 * math.sin(math.pi * (zn ** 0.85)) * (1.1 - 0.15 * zn))
        if zn < 0.14:
            r = amp * 0.52
        return max(0.002, r)

    def eval_bulb_phys(uu: float, phi: float, is_pole: bool) -> np.ndarray:
        zn = 0.5 * (uu + 1.0)
        if is_pole:
            return np.array([0.0, 0.0, 0.064 * zn], dtype=np.float64)
        rad = _pear_radius(zn, 0.027)
        return np.array([rad * math.cos(phi), rad * math.sin(phi), 0.064 * zn], dtype=np.float64)

    phys_pts, phys_tris, _ = _loft_closed_tube(8, 10, eval_bulb_phys, uv_scale=(1.0, 1.0))

    def eval_bulb_vis(uu: float, phi: float, is_pole: bool) -> np.ndarray:
        zn = 0.5 * (uu + 1.0)
        if is_pole:
            return np.array([0.0, 0.0, 0.065 * zn], dtype=np.float64)
        rib = 1.0 + (0.045 * math.sin(14.0 * math.pi * zn) if 0.15 < zn < 0.85 else 0.0)
        collar_ring = 1.09 if 0.05 < zn < 0.13 else 1.0
        rad = _pear_radius(zn, 0.0275) * rib * collar_ring
        return np.array([rad * math.cos(phi), rad * math.sin(phi), 0.065 * zn], dtype=np.float64)

    vis_pts, vis_tris, vis_uvs = _loft_closed_tube(48, 36, eval_bulb_vis, uv_scale=(1.5, 1.5))
    phys_pts, vis_pts = _normalize_xy_center_z_floor(phys_pts, vis_pts)
    return {
        "phys_pts": phys_pts,
        "phys_elems": _edges_from_elements(phys_tris),
        "phys_tris": phys_tris,
        "phys_edges": _edges_from_elements(phys_tris),
        "vis_pts": vis_pts,
        "vis_tris": vis_tris,
        "vis_uvs": vis_uvs,
    }


def build_sculpted_v03_asset(asset_id: str) -> dict[str, Any]:
    """Build matched physics proxy and UV-mapped high-poly sculpted visual mesh for one v0.3 asset."""
    builders = {
        "v03_croissant_butter_01": _build_croissant_pair,
        "v03_strawberry_fresh_01": _build_strawberry_pair,
        "v03_waffle_towel_01": lambda: _build_cloth_pair(size_xy=0.20, thick=0.0052, n_phys=8, n_vis=28, pleat_amp=0.036),
        "v03_linen_dust_cover_01": lambda: _build_cloth_pair(size_xy=0.20, thick=0.0044, n_phys=8, n_vis=28, pleat_amp=0.0),
        "v03_idc_ribbon_cable_01": _build_ribbon_cable_pair,
        "v03_esd_silicone_boot_01": _build_esd_boot_pair,
        "v03_lab_silicone_tube_01": _build_silicone_tube_pair,
        "v03_pipette_rubber_bulb_01": _build_rubber_bulb_pair,
    }
    if asset_id not in builders:
        raise ValueError(f"Unknown v0.3 sculpted asset_id: {asset_id!r}")
    data = builders[asset_id]()
    data["spec"] = V03_ASSET_SPECS[asset_id]
    return data
