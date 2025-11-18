# -*- coding: utf-8 -*-
"""Public interfaces for native C++ meshqem backend.

This module exposes thin, stable entrypoints:

- simplify_mesh_with_cpp: legacy path using external meshqem executable
    via temporary OBJ files (geometry only).
- simplify_mesh_with_cpp_uv: in-memory path using optional `meshqem_py`
    pybind11 bindings with face-varying UV triplets.

Low-level details (USD extraction, OBJ I/O, etc.) are implemented in
`backend_cpp_impl.py` to keep this module small and focused.
"""
from __future__ import annotations

import os
import tempfile
from typing import Any, Optional

try:
    from pxr import Usd, UsdGeom  # type: ignore
except Exception:
    Usd = None  # type: ignore[assignment]
    UsdGeom = None  # type: ignore[assignment]

try:
    # Optional: C++ native binding module built via pybind11.
    # Prefer relative import so the compiled .so living in this
    # package directory (convert_asset/mesh) is discovered reliably.
    from . import meshqem_py  # type: ignore
except Exception:  # pragma: no cover - binding may not be built in all environments
    meshqem_py = None  # type: ignore[assignment]

from .backend_cpp_impl import (
    extract_tri_mesh_from_prim,
    extract_facevarying_uv_triplets,
    write_obj_tri,
    read_obj_tri,
    run_meshqem_executable,
)


def simplify_mesh_with_cpp(
    prim: Any,
    exe_path: str,
    ratio: float | None = None,
    target_faces: int | None = None,
    max_collapses: int | None = None,
    time_limit: float | None = None,
    progress_interval: int = 20000,
        apply: bool = True,
        show_output: bool = False,
) -> tuple[int, int, int, int]:
    if Usd is None or UsdGeom is None:
        raise RuntimeError("pxr.Usd not available; run inside Isaac/pxr environment")

    mesh = UsdGeom.Mesh(prim)
    points, faces = extract_tri_mesh_from_prim(prim)
    if not points or not faces:
        return (0, 0, 0, 0)

    with tempfile.TemporaryDirectory() as td:
        inp = os.path.join(td, "in.obj")
        out = os.path.join(td, "out.obj")
        write_obj_tri(inp, points, faces)
        run_meshqem_executable(
            exe_path,
            inp,
            out,
            ratio=ratio,
            target_faces=target_faces,
            max_collapses=max_collapses,
            time_limit=time_limit,
            progress_interval=progress_interval,
            show_output=show_output,
        )

        new_pts, new_faces = read_obj_tri(out)
        if apply:
            # write back
            mesh.GetPointsAttr().Set(new_pts)
            counts2 = [3] * len(new_faces)
            idx2: list[int] = []
            for a, b, c in new_faces:
                idx2.extend([int(a), int(b), int(c)])
            mesh.GetFaceVertexCountsAttr().Set(counts2)
            mesh.GetFaceVertexIndicesAttr().Set(idx2)

        return (len(faces), len(new_faces), len(points), len(new_pts))


def simplify_mesh_with_cpp_uv(
    prim: Any,
    ratio: float | None = None,
    target_faces: int | None = None,
    max_collapses: int | None = None,
    time_limit: float | None = None,
    progress_interval: int = 20000,
    apply: bool = True,
) -> tuple[int, int, int, int]:
    """使用 C++ 原生 QEM 后端进行减面，并携带 face-varying UV。

    说明：
    - 通过可选的 pybind11 模块 `meshqem_py` 直接在内存中调用 C++，不再走临时 OBJ。
    - 若绑定模块不可用，则回退到 Python `qem_simplify_ex` 路径由调用方决定是否使用。
    """
    if Usd is None or UsdGeom is None:
        raise RuntimeError("pxr.Usd not available; run inside Isaac/pxr environment")
    if meshqem_py is None:
        raise RuntimeError("meshqem_py binding not available; build native bindings to use simplify_mesh_with_cpp_uv")

    mesh = UsdGeom.Mesh(prim)
    points, faces = extract_tri_mesh_from_prim(prim)
    if not points or not faces:
        return (0, 0, 0, 0)
    face_uv_triplets = extract_facevarying_uv_triplets(prim)

    faces_n = len(faces)
    verts_n = len(points)

    # 计算目标面数/坍塌上限，与 C++ SimplifyOptions 语义对应。
    # 若 target_faces 未给出，则使用 ratio；否则优先使用 target_faces。
    if target_faces is not None:
        tf = int(target_faces)
    elif ratio is not None:
        r = max(0.0, min(1.0, float(ratio)))
        tf = int(faces_n * r)
    else:
        tf = -1

    mc = max_collapses if max_collapses is not None else -1
    tl = float(time_limit) if time_limit is not None else -1.0
    pi = int(progress_interval) if progress_interval is not None else 20000

    new_verts, new_faces, new_face_uvs = meshqem_py.simplify_with_uv(
        points,
        faces,
        face_uv_triplets,
        ratio if ratio is not None else 0.5,
        tf,
        mc,
        tl,
        pi,
    )

    if apply:
        mesh.GetPointsAttr().Set([(float(x), float(y), float(z)) for (x, y, z) in new_verts])
        counts2 = [3] * len(new_faces)
        idx2: list[int] = []
        for a, b, c in new_faces:
            idx2.extend([int(a), int(b), int(c)])
        mesh.GetFaceVertexCountsAttr().Set(counts2)
        mesh.GetFaceVertexIndicesAttr().Set(idx2)

        # 若 C++ 返回了新的 UV triplets，则写回 primvars:st
        if new_face_uvs is not None:
            from .simplify import _write_facevarying_uv  # type: ignore
            _write_facevarying_uv(mesh, new_face_uvs, name="st")

    return (faces_n, len(new_faces), verts_n, len(new_verts))

