# -*- coding: utf-8 -*-
"""Pure-Python orbit camera pose planning."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from .bounds import Bounds3D


@dataclass(frozen=True)
class CameraPoseSpec:
    view_index: int
    azimuth_deg: float
    elevation_deg: float
    distance: float
    position: tuple[float, float, float]
    target: tuple[float, float, float]

    def to_dict(self) -> dict:
        return asdict(self)


def _even_view_count(views: int) -> int:
    count = max(2, int(views))
    if count % 2 != 0:
        count += 1
    return count


def plan_orbit_poses(
    bounds: Bounds3D,
    *,
    views: int = 6,
    distance_scale: float = 1.0,
    fov_h_deg: float = 55.0,
    aspect: float = 4.0 / 3.0,
    padding: float = 1.15,
    start_azimuth_deg: float = 30.0,
    top_elevation_deg: float = 35.0,
    bottom_elevation_deg: float = -35.0,
) -> list[CameraPoseSpec]:
    """Plan two-elevation orbit views around a target bbox."""
    count = _even_view_count(views)
    half = max(1, count // 2)
    cx, cy, cz = bounds.center
    fov_h = math.radians(max(1.0e-3, float(fov_h_deg)))
    safe_aspect = max(1.0e-6, float(aspect))
    fov_v = 2.0 * math.atan(math.tan(fov_h * 0.5) / safe_aspect)
    half_diag = max(float(bounds.diagonal) * 0.5, 0.5)
    fit_h = half_diag / max(math.tan(fov_h * 0.5), 1.0e-6)
    fit_v = half_diag / max(math.tan(fov_v * 0.5), 1.0e-6)
    distance = max(fit_h, fit_v, 1.0) * float(distance_scale) * float(padding)
    poses: list[CameraPoseSpec] = []

    for view_index in range(count):
        azimuth = float(start_azimuth_deg) + float(view_index % half) * 360.0 / float(half)
        elevation = float(top_elevation_deg) if view_index < half else float(bottom_elevation_deg)
        azim_rad = math.radians(azimuth)
        elev_rad = math.radians(elevation)
        off_x = distance * math.cos(elev_rad) * math.cos(azim_rad)
        off_y = distance * math.cos(elev_rad) * math.sin(azim_rad)
        off_z = distance * math.sin(elev_rad)
        poses.append(
            CameraPoseSpec(
                view_index=view_index,
                azimuth_deg=azimuth,
                elevation_deg=elevation,
                distance=distance,
                position=(float(cx + off_x), float(cy + off_y), float(cz + off_z)),
                target=(float(cx), float(cy), float(cz)),
            )
        )
    return poses
