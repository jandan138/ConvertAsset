"""Composed world-space geometry helpers for workspace profiling.

The scene-analysis work previously lived in ad-hoc probe scripts; these
helpers are the regression-locked versions used by workspace audits, zone
profiles, and evidence renders.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def _prim_mesh_world_points(prim: Any) -> list[Any]:
    """World-space points of every Mesh below prim, in composed stage units.

    Gf matrices map row vectors as ``p @ M`` (translation in the last row).
    The historical probe once multiplied by ``M.T`` and silently landed the
    bbox at the wrong coordinates; keep the convention documented here.
    """
    from pxr import Usd, UsdGeom  # type: ignore

    chunks = []
    for child in Usd.PrimRange(prim):
        if child.GetTypeName() != "Mesh":
            continue
        points = UsdGeom.Mesh(child).GetPointsAttr().Get()
        if not points:
            continue
        xform = UsdGeom.Xformable(child).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        arr = np.asarray(points, dtype=float)
        world = (np.hstack([arr, np.ones((len(arr), 1))]) @ np.asarray(xform, dtype=float))[:, :3]
        chunks.append(world)
    return chunks


def composed_mesh_world_bbox(stage: Any, prim: Any) -> tuple[Any, Any, int]:
    """Return (min, max, mesh_count) for the prim subtree in composed units."""
    if not prim or not prim.IsValid():
        return None, None, 0
    mn = np.full(3, np.inf)
    mx = np.full(3, -np.inf)
    mesh_count = 0
    for world in _prim_mesh_world_points(prim):
        mn = np.minimum(mn, world.min(axis=0))
        mx = np.maximum(mx, world.max(axis=0))
        mesh_count += 1
    if not mesh_count:
        return None, None, 0
    return mn, mx, mesh_count


def estimate_counter_band(
    stage: Any,
    prim_paths: list[str],
    *,
    floor_z: float,
    reference_counter_m: float = 0.9,
    band_low_m: float = 0.3,
    band_high_m: float = 1.5,
    bins: int = 200,
) -> dict[str, Any] | None:
    """Estimate the densest counter-height vertex band above ``floor_z``.

    Returns the band center (``counter_z``) and the implied
    ``units_per_meter`` against the standard 0.90 m counter reference, or
    None when no vertices fall in the search band.
    """
    zs = []
    for path in prim_paths:
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsValid():
            continue
        for world in _prim_mesh_world_points(prim):
            zs.append(world[:, 2])
    if not zs:
        return None
    z = np.concatenate(zs)
    # Coarse first pass to find the working band, then a fine pass.
    upm_coarse = None
    for reference_upm in (1.0, 10.0, 100.0, 1000.0, 30000.0):
        low = floor_z + band_low_m * reference_upm
        high = floor_z + band_high_m * reference_upm
        if ((z >= low) & (z <= high)).any():
            upm_coarse = reference_upm
            break
    if upm_coarse is None:
        return None
    low = floor_z + band_low_m * upm_coarse
    high = floor_z + band_high_m * upm_coarse
    band = z[(z >= low) & (z <= high)]
    hist, edges = np.histogram(band, bins=bins)
    counter_z = float(edges[int(np.argmax(hist))])
    units_per_meter = (counter_z - floor_z) / reference_counter_m
    if units_per_meter <= 0:
        return None
    return {
        "counter_z": counter_z,
        "floor_z": float(floor_z),
        "units_per_meter": float(units_per_meter),
        "reference_counter_m": float(reference_counter_m),
        "vertex_fraction": float(len(band) / len(z)),
    }
