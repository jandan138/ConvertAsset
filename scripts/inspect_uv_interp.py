#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspect UV primvars and their interpolation on all Mesh prims in a USD stage.
Usage:
  /isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/scripts/inspect_uv_interp.py /abs/path/to/file.usd

Outputs lines like:
  /World/Geom/Mesh primvar=st interpolation=faceVarying count=12345 expected=12345 ok
and a short summary at the end.
"""
from __future__ import annotations
import sys
from typing import Iterable

try:
    from pxr import Usd, UsdGeom
except Exception as e:
    print("[ERROR] pxr not available:", e)
    sys.exit(2)

if len(sys.argv) < 2:
    print("Usage: inspect_uv_interp.py </abs/path/to/file.usd>")
    sys.exit(1)

path = sys.argv[1]
stage = Usd.Stage.Open(path)
if stage is None:
    print(f"[ERROR] Failed to open stage: {path}")
    sys.exit(3)

mesh_count = 0
have_uv_count = 0
summary = {('vertex', 'ok'): 0, ('vertex', 'mismatch'): 0, ('faceVarying', 'ok'): 0, ('faceVarying', 'mismatch'): 0}

# Helper to compute expected counts

def _expected_count(mesh: UsdGeom.Mesh, interp: str) -> int:
    if interp == 'vertex':
        pts = mesh.GetPointsAttr().Get() or []
        return len(pts)
    if interp == 'faceVarying':
        counts = mesh.GetFaceVertexCountsAttr().Get() or []
        return sum(int(c) for c in counts)
    return -1

for prim in stage.Traverse():
    if prim.GetTypeName() != 'Mesh':
        continue
    mesh_count += 1
    mesh = UsdGeom.Mesh(prim)
    pvapi = UsdGeom.PrimvarsAPI(mesh)
    primvars = pvapi.GetPrimvars()
    # Heuristic: consider UV primvars: names containing 'st' or 'uv' (case-insensitive) with float2/texcoord-like role
    uv_found_here = False
    for pv in primvars:
        name = pv.GetPrimvarName()  # e.g., 'st'
        base_name = pv.GetBaseName()
        low = name.lower()
        if ('st' in low) or ('uv' in low) or ('texcoord' in low):
            interp = pv.GetInterpolation()
            vals = pv.Get() or []
            exp = _expected_count(mesh, interp)
            status = 'ok' if (exp < 0 or len(vals) == exp) else 'mismatch'
            print(f"{prim.GetPath()} primvar={name} interpolation={interp} count={len(vals)} expected={exp} {status}")
            uv_found_here = True
            if (interp, status) in summary:
                summary[(interp, status)] += 1
    if not uv_found_here:
        # Also print a hint for common canonical names
        for cand in ['st', 'st0', 'uv', 'UVMap', 'st1', 'TexCoord']:
            pv = mesh.GetPrimvar(cand)
            if pv and pv.HasValue():
                interp = pv.GetInterpolation()
                vals = pv.Get() or []
                exp = _expected_count(mesh, interp)
                status = 'ok' if (exp < 0 or len(vals) == exp) else 'mismatch'
                print(f"{prim.GetPath()} primvar={cand} interpolation={interp} count={len(vals)} expected={exp} {status}")
                uv_found_here = True
                if (interp, status) in summary:
                    summary[(interp, status)] += 1
                break
        if not uv_found_here:
            print(f"{prim.GetPath()} (Mesh) has NO UV-like primvars (st/uv/TexCoord)")
    have_uv_count += 1 if uv_found_here else 0

print("----- Summary -----")
print(f"Meshes total: {mesh_count}")
print(f"Meshes with any UV-like primvar: {have_uv_count}")
for k in [('vertex','ok'), ('vertex','mismatch'), ('faceVarying','ok'), ('faceVarying','mismatch')]:
    print(f"{k[0]} {k[1]}: {summary[k]}")

sys.exit(0)
