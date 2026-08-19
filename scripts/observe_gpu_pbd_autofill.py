#!/usr/bin/env python3
"""Run one Isaac Sim 4.1 cold observation for a liquid-autofill candidate."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
import traceback
from typing import Any


STEPS = 960
PHYSICS_HZ = 120
TAIL_SAMPLES = 12


def _hard_runtime_errors(text: str) -> list[str]:
    markers = (
        "failed to cook GPU-compatible mesh",
        "Non-GPU-compatible convex mesh",
        "Particles feature is only supported on GPU",
        "CUDA error",
        "illegal memory access",
    )
    return [
        line.strip()
        for line in text.splitlines()
        if any(marker in line for marker in markers)
    ]


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def _analysis_point(point: Any, *, up_axis: str, meters_per_unit: float) -> list[float]:
    values = [float(value) * meters_per_unit for value in point]
    if up_axis == "Z":
        return values
    return [values[0], values[2], values[1]]


def _target_local_points(
    stage: Any,
    *,
    target_path: str,
    world_points: Any,
    up_axis: str,
    meters_per_unit: float,
    UsdGeom: Any,
) -> list[list[float]]:
    cache = UsdGeom.XformCache()
    target = stage.GetPrimAtPath(target_path)
    inverse = cache.GetLocalToWorldTransform(target).GetInverse()
    return [
        _analysis_point(
            inverse.Transform(point),
            up_axis=up_axis,
            meters_per_unit=meters_per_unit,
        )
        for point in world_points
    ]


def _read_live_points(stage: Any, particle_path: str) -> Any:
    prim = stage.GetPrimAtPath(particle_path)
    values = prim.GetAttribute("points").Get()
    if values is None:
        raise RuntimeError(
            "live points unavailable; simulationPoints is authored rest state and is not accepted"
        )
    return values


def _matrix_pose(stage: Any, target_path: str, UsdGeom: Any) -> tuple[Any, Any]:
    matrix = UsdGeom.XformCache().GetLocalToWorldTransform(
        stage.GetPrimAtPath(target_path)
    )
    return matrix.ExtractTranslation(), matrix


def _up_direction(matrix: Any, up_axis: str) -> Any:
    direction = matrix.TransformDir((0, 0, 1) if up_axis == "Z" else (0, 1, 0))
    length = direction.GetLength()
    return direction / length if length else direction


def _run(args: argparse.Namespace) -> dict[str, Any]:
    from isaacsim import SimulationApp

    parsed = sys.argv
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
        sys.argv = parsed
    import carb
    import omni.kit.app
    import omni.physx
    import omni.physx.bindings._physx as pb
    import omni.usd
    from omni.isaac.core import World
    from pxr import UsdGeom

    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    particle_path = manifest["entrypoints"]["particle_set_prim"]
    target_path = analysis["container_prim"]
    cavity = analysis["cavity"]
    fill_target = float(manifest["fill_profile"]["target_settled_fill_ratio"])
    meters_per_unit = float(analysis["meters_per_unit"])
    up_axis = str(analysis["up_axis"])

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
    if stage is None:
        raise RuntimeError(f"could not open {args.scene}")
    physics_path = analysis.get("physics_scene_path")
    if not physics_path:
        physics_path = next(
            (
                prim.GetPath().pathString
                for prim in stage.Traverse()
                if prim.GetTypeName() == "PhysicsScene"
            ),
            None,
        )
        if physics_path is None:
            raise RuntimeError("qualification scene has no PhysicsScene")
    world = World(
        stage_units_in_meters=meters_per_unit,
        physics_prim_path=physics_path,
        set_defaults=False,
        backend="numpy",
        device="cpu",
        physics_dt=1 / PHYSICS_HZ,
        rendering_dt=1 / PHYSICS_HZ,
    )
    omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    world.reset()
    initial_translation, initial_matrix = _matrix_pose(stage, target_path, UsdGeom)
    initial_up = _up_direction(initial_matrix, up_axis)
    observations: list[dict[str, float | int]] = []
    started = time.monotonic()
    for step in range(STEPS):
        world.step(render=False)
        if step % 10 != 0 and step != STEPS - 1:
            continue
        live = _read_live_points(stage, particle_path)
        local = _target_local_points(
            stage,
            target_path=target_path,
            world_points=live,
            up_axis=up_axis,
            meters_per_unit=meters_per_unit,
            UsdGeom=UsdGeom,
        )
        inside = [
            point
            for point in local
            if (
                ((point[0] - float(cavity["center_xy_m"][0])) / float(cavity["radius_x_m"])) ** 2
                + ((point[1] - float(cavity["center_xy_m"][1])) / float(cavity["radius_y_m"])) ** 2
                <= 1.0
                and float(cavity["floor_m"]) <= point[2] <= float(cavity["rim_m"])
            )
        ]
        observations.append(
            {
                "retention_ratio": len(inside) / len(local),
                "below_floor_count": sum(
                    point[2] < float(cavity["floor_m"]) for point in local
                ),
                "fill_ratio": (
                    _quantile([point[2] for point in local], 0.95)
                    - float(cavity["floor_m"])
                )
                / (float(cavity["rim_m"]) - float(cavity["floor_m"])),
                "particle_count": len(local),
            }
        )
    elapsed = time.monotonic() - started
    final_translation, final_matrix = _matrix_pose(stage, target_path, UsdGeom)
    final_up = _up_direction(final_matrix, up_axis)
    translation_drift = (
        final_translation - initial_translation
    ).GetLength() * meters_per_unit
    cosine = max(-1.0, min(1.0, float(initial_up * final_up)))
    tilt_drift = math.degrees(math.acos(cosine))
    tail = observations[-TAIL_SAMPLES:]
    hard_errors = _hard_runtime_errors(
        log_path.read_text(encoding="utf-8", errors="replace")[log_offset:]
        if log_path.exists()
        else ""
    )
    retention = min(float(item["retention_ratio"]) for item in tail)
    below = max(int(item["below_floor_count"]) for item in tail)
    settled_fill = statistics.median(float(item["fill_ratio"]) for item in tail)
    particle_count = int(tail[-1]["particle_count"])
    checks = {
        "runtime_is_isaac41": str(omni.kit.app.get_app().get_app_version()).startswith("4.1"),
        "live_points_particle_count": particle_count
        == int(manifest["fill_profile"]["particle_count"]),
        "retention_ratio": retention >= 0.99,
        "below_floor": below == 0,
        "settled_fill_ratio": abs(settled_fill - fill_target) <= 0.05,
        "translation_drift": translation_drift <= 0.002,
        "tilt_drift": tilt_drift <= 2.0,
        "hard_runtime_errors": not hard_errors,
    }
    result = {
        "schema_version": "aan.gpu_pbd_autofill_cold_observation.v1",
        "run_index": args.run_index,
        "runtime": {
            "name": "isaac41",
            "kit_version": str(omni.kit.app.get_app().get_app_version()),
        },
        "measurement": "live_points_target_local_up_q95",
        "particle_readback_attribute": "points",
        "particle_count": particle_count,
        "minimum_tail_retention_ratio": retention,
        "maximum_tail_below_floor_count": below,
        "settled_fill_ratio": settled_fill,
        "target_translation_drift_m": translation_drift,
        "target_tilt_drift_deg": tilt_drift,
        "physics_steps_per_wall_second": STEPS / elapsed if elapsed else None,
        "hard_runtime_errors": hard_errors,
        "checks": checks,
        "overall_status": "pass" if all(checks.values()) else "blocked",
        "shutdown": {
            "policy": "eos_isaac41_controlled_worker_exit_after_evidence",
            "simulation_app_close_attempted": False,
            "reason": (
                "The process-isolated worker flushes and fsyncs its evidence, then "
                "uses a controlled process exit. Isaac Sim 4.1 plugin unloading is "
                "not part of the physics claim and can intermittently segfault."
            ),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    with args.out.open("w", encoding="utf-8") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-index", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = _run(args)
        print(args.out)
        exit_code = 0 if result["overall_status"] == "pass" else 1
    except BaseException:  # worker boundary must not enter Kit plugin teardown
        traceback.print_exc()
        exit_code = 2
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
