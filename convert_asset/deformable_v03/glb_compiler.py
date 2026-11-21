"""Universal .glb/.obj -> positive-volume 5-tet / shell proxy + skinning compiler (M1 v0.3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import trimesh

from .pbr_textures import derive_pbr_maps_from_albedo
from .skinning import build_shell_normal_skinning, build_tet_barycentric_skinning


def _load_mesh_and_texture(mesh_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, Image.Image | None]:
    loaded = trimesh.load(str(mesh_path), force="mesh")
    verts = np.asarray(loaded.vertices, dtype=np.float64)
    tris = np.asarray(loaded.faces, dtype=np.int64)
    uvs = None
    tex_img = None
    vis = getattr(loaded, "visual", None)
    if vis is not None:
        if getattr(vis, "uv", None) is not None and len(vis.uv) == len(verts):
            uvs = np.asarray(vis.uv, dtype=np.float32)
        mat = getattr(vis, "material", None)
        if mat is not None:
            for attr in ("baseColorTexture", "image"):
                cand = getattr(mat, attr, None)
                if isinstance(cand, Image.Image):
                    tex_img = cand.convert("RGB")
                    break
    if uvs is None:
        # Spherical/planar auto-UV fallback
        bmin, bmax = verts.min(axis=0), verts.max(axis=0)
        span = np.maximum(bmax - bmin, 1e-6)
        uvs = np.stack([(verts[:, 0] - bmin[0]) / span[0], (verts[:, 1] - bmin[1]) / span[1]], axis=-1).astype(np.float32)
    return verts, tris, uvs, tex_img


def _carve_voxel_5tets(
    vis_pts: np.ndarray,
    vis_tris: np.ndarray,
    grid_res: tuple[int, int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate interior/surface-covering positive-volume 5-tet proxy enclosing visual mesh."""
    bmin = vis_pts.min(axis=0) - 0.002
    bmax = vis_pts.max(axis=0) + 0.002
    nx, ny, nz = (int(grid_res[0]), int(grid_res[1]), int(grid_res[2]))
    xs = np.linspace(float(bmin[0]), float(bmax[0]), nx + 1)
    ys = np.linspace(float(bmin[1]), float(bmax[1]), ny + 1)
    zs = np.linspace(float(bmin[2]), float(bmax[2]), nz + 1)

    tmesh = trimesh.Trimesh(vertices=vis_pts, faces=vis_tris, process=False)
    active_cells: list[tuple[int, int, int]] = []
    # Check cell centers against mesh SDF/proximity so hollowed shapes stay sculpted
    centers = []
    coords = []
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                coords.append((ix, iy, iz))
                centers.append([0.5 * (xs[ix] + xs[ix + 1]), 0.5 * (ys[iy] + ys[iy + 1]), 0.5 * (zs[iz] + zs[iz + 1])])
    c_arr = np.asarray(centers, dtype=np.float64)
    cell_diag = float(np.linalg.norm([(bmax[0] - bmin[0]) / nx, (bmax[1] - bmin[1]) / ny, (bmax[2] - bmin[2]) / nz]))
    _, dists, _ = trimesh.proximity.closest_point(tmesh, c_arr)
    inside = tmesh.contains(c_arr) if tmesh.is_watertight else np.zeros(len(c_arr), dtype=bool)
    keep = inside | (dists <= 0.72 * cell_diag)
    for k_idx, flag in enumerate(keep):
        if flag:
            active_cells.append(coords[k_idx])
    if not active_cells:
        active_cells = coords

    used_nodes: dict[tuple[int, int, int], int] = {}
    phys_verts: list[tuple[float, float, float]] = []

    def get_vid(ix: int, iy: int, iz: int) -> int:
        key = (ix, iy, iz)
        if key not in used_nodes:
            used_nodes[key] = len(phys_verts)
            phys_verts.append((float(xs[ix]), float(ys[iy]), float(zs[iz])))
        return used_nodes[key]

    tets: list[tuple[int, int, int, int]] = []
    for ix, iy, iz in active_cells:
        p000, p100 = get_vid(ix, iy, iz), get_vid(ix + 1, iy, iz)
        p010, p110 = get_vid(ix, iy + 1, iz), get_vid(ix + 1, iy + 1, iz)
        p001, p101 = get_vid(ix, iy, iz + 1), get_vid(ix + 1, iy, iz + 1)
        p011, p111 = get_vid(ix, iy + 1, iz + 1), get_vid(ix + 1, iy + 1, iz + 1)
        if (ix + iy + iz) % 2 == 0:
            cand = [(p000, p100, p110, p101), (p000, p110, p010, p011), (p000, p001, p101, p011), (p111, p110, p101, p011), (p000, p110, p101, p011)]
        else:
            cand = [(p100, p110, p010, p111), (p000, p100, p010, p001), (p100, p101, p111, p001), (p010, p111, p011, p001), (p100, p010, p111, p001)]
        tets.extend(cand)

    pts_arr = np.asarray(phys_verts, dtype=np.float64)
    tet_arr = np.asarray(tets, dtype=np.int64)
    for ti, (a, b, c, d_i) in enumerate(tet_arr):
        if np.linalg.det(np.column_stack((pts_arr[b] - pts_arr[a], pts_arr[c] - pts_arr[a], pts_arr[d_i] - pts_arr[a]))) < 0.0:
            tet_arr[ti] = (a, c, b, d_i)

    edge_set: set[tuple[int, int]] = set()
    for row in tet_arr:
        for i in range(4):
            for j in range(i + 1, 4):
                u, v = int(row[i]), int(row[j])
                edge_set.add((u, v) if u < v else (v, u))
    edges_arr = np.asarray(sorted(edge_set), dtype=np.int64)
    tris_out = _surface_tris_fast(pts_arr, tet_arr)
    return pts_arr, tet_arr, tris_out, edges_arr


def _surface_tris_fast(pts: np.ndarray, tets: np.ndarray) -> np.ndarray:
    counts: dict[tuple[int, int, int], tuple[tuple[int, int, int], int]] = {}
    for a, b, c, d_i in tets:
        for tri, opp in (((a, c, b), d_i), ((a, b, d_i), c), ((b, c, d_i), a), ((c, a, d_i), b)):
            k = tuple(sorted(tri))
            if k in counts:
                counts.pop(k)
            else:
                counts[k] = (tri, opp)
    out = []
    for tri, opp in counts.values():
        p0, p1, p2 = pts[tri[0]], pts[tri[1]], pts[tri[2]]
        if float(np.dot(np.cross(p1 - p0, p2 - p0), pts[opp] - p0)) > 0.0:
            out.append((tri[0], tri[2], tri[1]))
        else:
            out.append(tri)
    return np.asarray(out, dtype=np.int64)


def compile_glb_to_deformable_proxy(
    mesh_path: str | Path,
    out_dir: str | Path,
    *,
    asset_id: str | None = None,
    structural_family: str = "soft_solid",
    target_max_extent_m: float = 0.22,
    grid_res: tuple[int, int, int] = (5, 5, 3),
    max_vis_faces_for_proxy: int = 8000,
) -> dict[str, Any]:
    """Compile any arbitrary .glb/.obj mesh into a physics proxy + barycentric/shell skinning bundle."""
    src_path = Path(mesh_path)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    aid = asset_id or src_path.stem

    vis_pts, vis_tris, vis_uvs, tex_img = _load_mesh_and_texture(src_path)
    # Normalize scale if oversized (e.g. mm-authored GLB), center XY at 0, place bottom at z=0
    extents = vis_pts.max(axis=0) - vis_pts.min(axis=0)
    max_ext = float(np.max(extents))
    if max_ext > max(target_max_extent_m * 1.5, 1e-6):
        vis_pts = vis_pts * (target_max_extent_m / max_ext)
    cxy = 0.5 * (vis_pts[:, :2].min(axis=0) + vis_pts[:, :2].max(axis=0))
    vis_pts[:, 0] -= float(cxy[0])
    vis_pts[:, 1] -= float(cxy[1])
    vis_pts[:, 2] -= float(vis_pts[:, 2].min())

    # Preserve embedded texture if present
    raw_tex_path = out_path / "textures" / "source_albedo.png"
    raw_tex_path.parent.mkdir(parents=True, exist_ok=True)
    if tex_img is not None:
        tex_img.save(raw_tex_path, format="PNG")
    tex_maps = derive_pbr_maps_from_albedo(
        raw_tex_path if tex_img is not None else out_path / "_missing.png",
        out_path / "textures",
        out_size=512,
    )

    if structural_family in ("soft_solid", "rod_cable"):
        phys_pts, phys_elems, phys_tris, phys_edges = _carve_voxel_5tets(vis_pts, vis_tris, grid_res=grid_res)
        w_skin, max_err = build_tet_barycentric_skinning(phys_pts, phys_elems, vis_pts)
        np.savez_compressed(out_path / "skinning.npz", mode=np.array(["tet_bary"]), w_skin=w_skin)
    else:
        # Sheet / shell: decimate/subsample planar or quadratic grid proxy for solver efficiency
        tmesh = trimesh.Trimesh(vertices=vis_pts, faces=vis_tris, process=True)
        if len(tmesh.faces) > 160:
            # Uniform 8x8 sheet fallback if nearly planar or clustered vertex decimation
            bmin, bmax = vis_pts.min(axis=0), vis_pts.max(axis=0)
            xs = np.linspace(float(bmin[0]), float(bmax[0]), 9)
            ys = np.linspace(float(bmin[1]), float(bmax[1]), 9)
            phys_pts = np.array([[x, y, float(0.5 * (bmin[2] + bmax[2]))] for y in ys for x in xs], dtype=np.float64)
            ptr = []
            for j in range(8):
                for i in range(8):
                    v00 = j * 9 + i
                    ptr.extend([(v00, v00 + 1, v00 + 10), (v00, v00 + 10, v00 + 9)])
            phys_tris = np.asarray(ptr, dtype=np.int64)
        else:
            phys_pts = np.asarray(tmesh.vertices, dtype=np.float64)
            phys_tris = np.asarray(tmesh.faces, dtype=np.int64)
        edge_set = {(min(int(a), int(b)), max(int(a), int(b))) for tri in phys_tris for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))}
        phys_edges = np.asarray(sorted(edge_set), dtype=np.int64)
        phys_elems = phys_edges
        skin_dict, max_err = build_shell_normal_skinning(phys_pts, phys_tris, vis_pts)
        np.savez_compressed(out_path / "skinning.npz", **skin_dict)

    np.savez_compressed(
        out_path / "physics_proxy.npz",
        rest_points=phys_pts,
        elements=phys_elems,
        triangles=phys_tris,
        edges=phys_edges,
        visual_rest_points=vis_pts,
        visual_triangles=vis_tris,
        visual_uvs=vis_uvs,
    )
    meta = {
        "asset_id": aid,
        "source_mesh": str(src_path),
        "structural_family": structural_family,
        "n_phys_verts": int(len(phys_pts)),
        "n_phys_elems": int(len(phys_elems)),
        "n_vis_verts": int(len(vis_pts)),
        "n_vis_tris": int(len(vis_tris)),
        "max_rest_skin_err_m": float(max_err),
        "textures": {k: str(v) for k, v in tex_maps.items()},
    }
    (out_path / "glb_compile_summary.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta

