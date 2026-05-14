# -*- coding: utf-8 -*-
"""World-space bounds helpers shared by camera and capture workflows."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class Bounds3D:
    min: tuple[float, float, float]
    max: tuple[float, float, float]
    center: tuple[float, float, float]
    size: tuple[float, float, float]

    @property
    def diagonal(self) -> float:
        return math.sqrt(sum(float(v) * float(v) for v in self.size))

    def to_dict(self) -> dict:
        return asdict(self)


def _vec3_tuple(vec) -> tuple[float, float, float]:
    return (float(vec[0]), float(vec[1]), float(vec[2]))


def _finite_values(values: Iterable[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def _should_ignore_for_bbox(prim) -> bool:
    path = prim.GetPath().pathString.lower()
    if "__default_setting" in path:
        return True
    if "hdr" in path and "sphere" in path:
        return True
    if "skydome" in path or "environment" in path:
        return True
    if "/lights" in path or path.endswith("/lights"):
        return True
    type_name = prim.GetTypeName()
    return type_name.endswith("Light")


def _range_to_bounds(rng) -> Bounds3D | None:
    if rng.IsEmpty():
        return None
    mn = rng.GetMin()
    mx = rng.GetMax()
    values = [mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]]
    if not _finite_values(values):
        return None
    size = mx - mn
    size_values = [size[0], size[1], size[2]]
    diag = math.sqrt(sum(float(v) * float(v) for v in size_values))
    if not math.isfinite(diag) or diag <= 0.0 or diag > 1.0e9:
        return None
    center = (mn + mx) * 0.5
    return Bounds3D(
        min=_vec3_tuple(mn),
        max=_vec3_tuple(mx),
        center=_vec3_tuple(center),
        size=_vec3_tuple(size),
    )


def compute_world_bounds(stage, prim_path: str) -> Bounds3D:
    """Compute a finite world-space bbox for a prim path.

    `pxr` is imported lazily so regular CLI help and unit tests do not require
    Isaac Sim's Python environment.
    """
    from pxr import Sdf, Usd, UsdGeom  # type: ignore

    prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
    if not prim or not prim.IsValid():
        raise RuntimeError(f"Target prim not found: {prim_path}")

    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
        useExtentsHint=True,
    )

    child_ranges = []
    stack = [prim]
    while stack:
        node = stack.pop()
        if not node or not node.IsValid():
            continue
        if _should_ignore_for_bbox(node):
            continue
        stack.extend(list(node.GetChildren()))
        if not node.IsA(UsdGeom.Boundable):
            continue
        bounds = _range_to_bounds(cache.ComputeWorldBound(node).ComputeAlignedRange())
        if bounds is not None:
            child_ranges.append(bounds)

    if not child_ranges:
        raise RuntimeError(f"Failed to compute finite bbox for prim: {prim_path}")

    mins = [math.inf, math.inf, math.inf]
    maxs = [-math.inf, -math.inf, -math.inf]
    for bounds in child_ranges:
        for idx in range(3):
            mins[idx] = min(mins[idx], bounds.min[idx])
            maxs[idx] = max(maxs[idx], bounds.max[idx])

    if not _finite_values([*mins, *maxs]):
        raise RuntimeError(f"Non-finite bbox extrema for prim: {prim_path}")

    size = tuple(float(maxs[idx] - mins[idx]) for idx in range(3))
    center = tuple(float((mins[idx] + maxs[idx]) * 0.5) for idx in range(3))
    merged = Bounds3D(
        min=(float(mins[0]), float(mins[1]), float(mins[2])),
        max=(float(maxs[0]), float(maxs[1]), float(maxs[2])),
        center=center,
        size=size,
    )
    return merged
