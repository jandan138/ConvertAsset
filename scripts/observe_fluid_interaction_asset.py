#!/usr/bin/env python3
"""Run one process-isolated fluid-interaction asset observation in Isaac 4.1."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import traceback
from typing import Any


PHYSICS_HZ = 120


def _hard_errors(text: str) -> list[str]:
    markers = (
        "failed to cook GPU-compatible mesh",
        "Non-GPU-compatible convex mesh",
        "Particles feature is only supported on GPU",
        "CUDA error",
        "illegal memory access",
    )
    return [line.strip() for line in text.splitlines() if any(item in line for item in markers)]


def _live_points(stage: Any, path: str) -> Any:
    points = stage.GetPrimAtPath(path).GetAttribute("points").Get()
    if points is None:
        raise RuntimeError("live particle points are unavailable")
    return points


def _local_points(stage: Any, target_path: str, points: Any, UsdGeom: Any) -> list[list[float]]:
    inverse = UsdGeom.XformCache().GetLocalToWorldTransform(
        stage.GetPrimAtPath(target_path)
    ).GetInverse()
    return [[float(value) for value in inverse.Transform(point)] for point in points]


def _inside_cavity(
    point: list[float],
    cavity: dict[str, Any],
    profile: list[dict[str, Any]] | None = None,
    tolerance_m: float = 0.0,
) -> bool:
    cx, cy = cavity["center_xy_m"]
    inside = (
        ((point[0] - float(cx)) / (float(cavity["radius_x_m"]) + tolerance_m)) ** 2
        + ((point[1] - float(cy)) / (float(cavity["radius_y_m"]) + tolerance_m)) ** 2
        <= 1.0
        and float(cavity["floor_m"]) - tolerance_m
        <= point[2]
        <= float(cavity["rim_m"]) + tolerance_m
    )
    if not inside or not profile:
        return inside
    allowed = _profile_inner_radius(point[2], profile)
    return (
        math.hypot(point[0] - float(cx), point[1] - float(cy))
        <= allowed + tolerance_m
    )


def _profile_inner_radius(z: float, stations: list[dict[str, Any]]) -> float:
    if z <= float(stations[0]["z_m"]):
        return float(stations[0]["inner_radius_m"])
    for lower, upper in zip(stations, stations[1:]):
        z0, z1 = float(lower["z_m"]), float(upper["z_m"])
        if z0 <= z <= z1:
            alpha = (z - z0) / max(z1 - z0, 1e-9)
            return (1.0 - alpha) * float(lower["inner_radius_m"]) + alpha * float(
                upper["inner_radius_m"]
            )
    return float(stations[-1]["inner_radius_m"])


def _profile_outer_radius(z: float, fixture: dict[str, Any]) -> float:
    stations = fixture.get("wall_profile") or []
    if not stations:
        return float(fixture["outer_radius_m"])
    if z <= float(stations[0]["z_m"]):
        return float(stations[0]["outer_radius_m"])
    for lower, upper in zip(stations, stations[1:]):
        z0, z1 = float(lower["z_m"]), float(upper["z_m"])
        if z0 <= z <= z1:
            alpha = (z - z0) / max(z1 - z0, 1e-9)
            return (1.0 - alpha) * float(lower["outer_radius_m"]) + alpha * float(
                upper["outer_radius_m"]
            )
    return float(stations[-1]["outer_radius_m"])


def _run(args: argparse.Namespace) -> dict[str, Any]:
    from isaacsim import SimulationApp

    saved = sys.argv
    sys.argv = [sys.argv[0]]
    try:
        app = SimulationApp(
            {
                "headless": True,
                "multi_gpu": False,
                "renderer": "RayTracedLighting",
                "width": 960,
                "height": 540,
            }
        )
    finally:
        sys.argv = saved
    import carb
    import omni.kit.app
    import omni.physx
    import omni.physx.bindings._physx as pb
    import omni.usd
    from omni.isaac.core import World
    from pxr import Gf, UsdGeom

    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    settings = carb.settings.get_settings()
    log_path = Path(str(settings.get("/log/file")))
    log_offset = log_path.stat().st_size if log_path.exists() else 0
    settings.set(pb.SETTING_UPDATE_TO_USD, True)
    settings.set(pb.SETTING_UPDATE_PARTICLES_TO_USD, True)
    settings.set(pb.SETTING_UPDATE_VELOCITIES_TO_USD, True)
    settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
    settings.set_bool("/physics/suppressReadback", False)
    context = omni.usd.get_context()
    if not context.open_stage(str(args.scene.resolve())):
        raise RuntimeError(f"could not open {args.scene}")
    for _ in range(40):
        app.update()
    stage = context.get_stage()
    world = World(
        stage_units_in_meters=1.0,
        physics_prim_path=fixture["physics_scene_path"],
        set_defaults=False,
        backend="numpy",
        device="cpu",
        physics_dt=1 / PHYSICS_HZ,
        rendering_dt=1 / PHYSICS_HZ,
    )
    omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    world.reset()
    target_path = fixture["target_prim"]
    particle_path = fixture["particle_set_prim"]
    behavior = fixture["behavior"]
    initial_count = int(fixture["particle_count"])
    report: dict[str, Any] = {
        "schema_version": "aan.fluid_interaction_cold_observation.v1",
        "run_index": args.run_index,
        "behavior": behavior,
        "liquid_recipe": {
            key: fixture["liquid_recipe"][key] for key in ("id", "sha256")
        },
    }
    if behavior == "reservoir":
        cavity = fixture["cavity"]
        retention_profile = fixture.get("retention_profile") or []
        structural_bounds = fixture["structural_bounds"]
        contact_tolerance = float(
            fixture["liquid_recipe"]["particle_contact_offset_m"]
        )
        for _ in range(480):
            world.step(render=False)
        static_local = _local_points(stage, target_path, _live_points(stage, particle_path), UsdGeom)
        static_inside = sum(
            _inside_cavity(
                point, cavity, retention_profile, tolerance_m=contact_tolerance
            )
            for point in static_local
        )
        static_below_floor = sum(
            point[2] < float(structural_bounds["floor_m"]) - 0.001
            for point in static_local
        )
        structural = sum(
            point[2] < float(structural_bounds["floor_m"]) - 0.001
            or (
                point[2] <= float(cavity["rim_m"])
                and math.hypot(point[0], point[1])
                > float(structural_bounds["outer_radius_m"]) + 0.001
            )
            for point in static_local
        )
        translate = stage.GetPrimAtPath(target_path).GetAttribute("xformOp:translate:motion")
        for step in range(360):
            alpha = (step + 1) / 360.0
            translate.Set(Gf.Vec3d(0.05 * alpha, 0.0, 0.05 * alpha))
            world.step(render=False)
        motion_local = _local_points(stage, target_path, _live_points(stage, particle_path), UsdGeom)
        motion_inside = sum(
            _inside_cavity(
                point, cavity, retention_profile, tolerance_m=contact_tolerance
            )
            for point in motion_local
        )
        rotate = stage.GetPrimAtPath(target_path).GetAttribute("xformOp:rotateX:pour")
        for step in range(180):
            rotate.Set(110.0 * (step + 1) / 180.0)
            world.step(render=False)
        for _ in range(480):
            world.step(render=False)
        pour_local = _local_points(stage, target_path, _live_points(stage, particle_path), UsdGeom)
        pour_inside = sum(
            _inside_cavity(
                point, cavity, retention_profile, tolerance_m=contact_tolerance
            )
            for point in pour_local
        )
        report.update(
            {
                "static_retention_ratio": static_inside / initial_count,
                "static_below_floor_count": static_below_floor,
                "static_outside_wall_count": structural - static_below_floor,
                "motion_retention_ratio": motion_inside / initial_count,
                "pour_outflow_ratio": 1.0 - pour_inside / initial_count,
                "structural_leak_count": structural,
            }
        )
    else:
        legal_crossings: set[int] = set()
        structural_leaks: set[int] = set()
        previous = _local_points(
            stage, target_path, _live_points(stage, particle_path), UsdGeom
        )
        for _ in range(960):
            world.step(render=False)
            if behavior == "conduit":
                live = _local_points(
                    stage, target_path, _live_points(stage, particle_path), UsdGeom
                )
                outlet_z = float(fixture["outlet_z_m"])
                inlet_z = float(fixture["inlet_z_m"])
                outlet_radius = float(fixture["outlet_radius_m"])
                for index, point in enumerate(live):
                    radius = math.hypot(point[0], point[1])
                    before = previous[index]
                    if before[2] > outlet_z >= point[2]:
                        alpha = (before[2] - outlet_z) / max(
                            before[2] - point[2], 1e-9
                        )
                        crossing_radius = math.hypot(
                            before[0] + alpha * (point[0] - before[0]),
                            before[1] + alpha * (point[1] - before[1]),
                        )
                        if crossing_radius <= outlet_radius:
                            legal_crossings.add(index)
                        else:
                            structural_leaks.add(index)
                    elif point[2] < inlet_z and radius > 1.05 * _profile_outer_radius(
                        point[2], fixture
                    ):
                        structural_leaks.add(index)
                previous = live
        points = _local_points(stage, target_path, _live_points(stage, particle_path), UsdGeom)
        receiver = fixture["receiver"]
        cx, cy, cz = receiver["center_m"]
        radius = float(receiver["radius_m"])
        captured = sum(
            math.hypot(point[0] - cx, point[1] - cy) <= radius
            and point[2] <= cz + float(receiver["height_m"])
            for point in points
        )
        if behavior == "conduit":
            outlet_z = float(fixture["outlet_z_m"])
            inlet_z = float(fixture["inlet_z_m"])
            report.update(
                {
                    "legal_outlet_ratio": len(legal_crossings) / initial_count,
                    "structural_leak_count": len(structural_leaks),
                    "particles_below_inlet": sum(
                        point[2] < inlet_z for point in points
                    ),
                    "particles_below_outlet": sum(
                        point[2] < outlet_z for point in points
                    ),
                }
            )
        else:
            report.update(
                {
                    "capture_ratio": captured / initial_count,
                    "structural_leak_count": 0,
                }
            )
    hard = _hard_errors(
        log_path.read_text(encoding="utf-8", errors="replace")[log_offset:]
        if log_path.exists()
        else ""
    )
    kit_version = str(omni.kit.app.get_app().get_app_version())
    if not kit_version.startswith("4.1"):
        hard.append(f"unsupported_runtime_version:{kit_version};required:4.1.x")
    final_points = _local_points(
        stage, target_path, _live_points(stage, particle_path), UsdGeom
    )
    report["final_point_bounds_m"] = {
        "minimum": [min(point[index] for point in final_points) for index in range(3)],
        "maximum": [max(point[index] for point in final_points) for index in range(3)],
    }
    report["hard_errors"] = hard
    report["particle_count"] = len(_live_points(stage, particle_path))
    report["runtime"] = {
        "name": "isaac41",
        "kit_version": kit_version,
    }
    report["overall_status"] = "observed" if not hard else "blocked"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--run-index", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        _run(args)
        exit_code = 0
    except BaseException:
        traceback.print_exc()
        exit_code = 2
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)


if __name__ == "__main__":
    main()
