#!/usr/bin/env python3
"""Qualify one Task 02 r8.1 fluid component in an Isaac Sim 4.1 worker."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys
import time
from typing import Any


SOURCE = "/World/FluidWorkcell/SourceContainer"
TARGET = "/World/FluidWorkcell/TargetContainer"
PARTICLES = "/World/FluidWorkcell/ParticleSet"
PARTICLE_COUNT = 548
PHYSICS_HZ = 30


def _progress(message: str) -> None:
    print(f"[task02-r81] {message}", flush=True)


def _write_observation(path: Path, result: dict[str, Any]) -> None:
    """Persist evidence before Kit teardown, which may abort in Isaac 4.1."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def _hard_runtime_errors(log_text: str) -> list[str]:
    markers = (
        "failed to cook GPU-compatible mesh",
        "Non-GPU-compatible convex mesh",
        "Particles feature is only supported on GPU",
        "CUDA error",
        "illegal memory access",
    )
    return [
        line.strip()
        for line in log_text.splitlines()
        if any(marker in line for marker in markers)
    ]


def _classify(positions: Any, source_matrix: Any, np: Any) -> dict[str, Any]:
    local = np.c_[positions, np.ones((len(positions), 1))] @ np.linalg.inv(
        source_matrix
    )
    source = (
        (np.linalg.norm(local[:, :2], axis=1) <= 0.018)
        & (local[:, 2] >= 0.004)
        & (local[:, 2] <= 0.282)
    )
    target_center = np.asarray([-0.16, -0.17], dtype=float)
    target = (
        (np.linalg.norm(positions[:, :2] - target_center, axis=1) <= 0.035)
        & (positions[:, 2] >= 0.0)
        & (positions[:, 2] <= 0.12)
    )
    below = positions[:, 2] < -0.002
    tabletop = (
        ~source
        & ~target
        & ~below
        & (positions[:, 2] <= 0.08)
        & (np.abs(positions[:, 0]) <= 0.6)
        & (np.abs(positions[:, 1]) <= 0.35)
    )
    return {
        "source": int(source.sum()),
        "target": int(target.sum()),
        "below_support": int(below.sum()),
        "tabletop_spill": int(tabletop.sum()),
        "particle_count": int(len(positions)),
    }


def _source_matrix(position: Any, orientation_wxyz: Any, np: Any) -> Any:
    w, x, y, z = [float(value) for value in orientation_wxyz]
    rotation = np.asarray(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)],
            [2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)],
            [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=float,
    )
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[3, :3] = position
    return matrix


def _read_positions(stage: Any, np: Any) -> Any:
    prim = stage.GetPrimAtPath(PARTICLES)
    for name in ("physxParticle:simulationPoints", "points"):
        values = prim.GetAttribute(name).Get()
        if values is not None:
            return np.asarray(values, dtype=float)
    raise RuntimeError("particle positions unavailable")


def _run(args: argparse.Namespace) -> dict[str, Any]:
    from isaacsim import SimulationApp

    scene_path = args.scene.resolve()
    # Match the proven LabUtopia Isaac 4.1 launch boundary: start Kit without
    # forwarding this script's CLI and open the USD only after the application
    # is ready.  Passing open_usd to SimulationApp makes stage loading part of
    # Kit construction and leaves no observable boundary for qualification.
    parsed_argv = sys.argv
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
        sys.argv = parsed_argv
    try:
        import carb
        import numpy as np
        import omni.kit.app
        import omni.physx
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.prims import RigidPrimView

        _progress("runtime modules imported")
        import omni.physx.bindings._physx as pb

        _progress("application ready")
        settings = carb.settings.get_settings()
        log_path = Path(str(settings.get("/log/file")))
        try:
            settings.set(pb.SETTING_UPDATE_TO_USD, True)
            settings.set(pb.SETTING_UPDATE_PARTICLES_TO_USD, True)
            settings.set(pb.SETTING_UPDATE_VELOCITIES_TO_USD, True)
            settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
            settings.set_bool("/physics/suppressReadback", False)
            _progress("particle readback enabled")
            context = omni.usd.get_context()
            _progress("opening qualification stage")
            if not context.open_stage(str(scene_path)):
                raise RuntimeError(f"could not open {args.scene}")
            for _ in range(40):
                app.update()
            stage = context.get_stage()
            if stage is None or Path(stage.GetRootLayer().realPath) != scene_path:
                raise RuntimeError(f"could not open {args.scene}")
            _progress("stage loaded")
            stage.SetEditTarget(stage.GetSessionLayer())
            source_prim = stage.GetPrimAtPath(SOURCE)
            source_prim.GetAttribute("physics:kinematicEnabled").Set(True)
            world = World(
                stage_units_in_meters=1.0,
                physics_prim_path="/World/PhysicsScene",
                set_defaults=False,
                backend="numpy",
                device="cpu",
                physics_dt=1 / PHYSICS_HZ,
                rendering_dt=1 / PHYSICS_HZ,
            )
            omni.physx.get_physx_interface().overwrite_gpu_setting(1)
            source_view = RigidPrimView(SOURCE, name="task02_r81_source")
            world.scene.add(source_view)
            world.reset()
            for _ in range(30):
                world.step(render=False)
            _progress("physics initialized")
            source_positions, source_orientations = source_view.get_world_poses()
            initial_position = np.asarray(source_positions[0], dtype=float)
            initial_orientation = np.asarray(source_orientations[0], dtype=float)
            source_matrix = _source_matrix(initial_position, initial_orientation, np)
            scores: list[dict[str, Any]] = []
            for _ in range(8 * PHYSICS_HZ):
                world.step(render=False)
                scores.append(_classify(_read_positions(stage, np), source_matrix, np))
            _progress("static hold complete")
            static_min = min(score["source"] for score in scores)
            static_below = max(score["below_support"] for score in scores)

            target_position = np.asarray([-0.16, -0.17, 0.0], dtype=float)
            pivot = target_position + np.asarray([0.025, 0.0, 0.17349], dtype=float)
            local_rim = np.asarray([0.0, 0.0, 0.27659], dtype=float)
            upright_position = pivot - local_rim
            for index in range(1, 2 * PHYSICS_HZ + 1):
                alpha = index / (2 * PHYSICS_HZ)
                position = initial_position * (1.0 - alpha) + upright_position * alpha
                source_view.set_world_poses(
                    positions=np.asarray([position], dtype=np.float32),
                    orientations=np.asarray([initial_orientation], dtype=np.float32),
                )
                world.step(render=False)
            _progress("upright transport complete")
            steps = 3 * PHYSICS_HZ
            for index in range(1, steps + 1):
                angle = math.radians(-110.0 * index / steps)
                orientation = np.asarray(
                    [math.cos(angle / 2), 0.0, math.sin(angle / 2), 0.0],
                    dtype=np.float32,
                )
                matrix = _source_matrix(np.zeros(3), orientation, np)
                position = pivot - local_rim @ matrix[:3, :3]
                source_view.set_world_poses(
                    positions=np.asarray([position], dtype=np.float32),
                    orientations=np.asarray([orientation], dtype=np.float32),
                )
                world.step(render=False)
            _progress("tilt complete")
            for _ in range(5 * PHYSICS_HZ):
                world.step(render=False)
            _progress("hold and settle complete")
            final_positions = _read_positions(stage, np)
            final_source_positions, final_source_orientations = (
                source_view.get_world_poses()
            )
            final_matrix = _source_matrix(
                np.asarray(final_source_positions[0], dtype=float),
                np.asarray(final_source_orientations[0], dtype=float),
                np,
            )
            final = _classify(final_positions, final_matrix, np)
            render_timings: list[float] = []
            for _ in range(90):
                started = time.perf_counter()
                world.step(render=True)
                render_timings.append((time.perf_counter() - started) * 1000.0)
            _progress("RTX measurement complete")
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            errors = _hard_runtime_errors(log_text)
            result = {
                "schema_version": "aan.task02_r81_fluid_runtime_observation.v1",
                "partition_count": args.partition_count,
                "run_index": args.run_index,
                "runtime": {
                    "kit_version": str(omni.kit.app.get_app().get_app_version()),
                    "gpu": "NVIDIA GeForce RTX 4090",
                    "resolution": [960, 540],
                },
                "static_hold": {
                    "minimum_source_count": static_min,
                    "minimum_source_ratio": static_min / PARTICLE_COUNT,
                    "maximum_below_support_count": static_below,
                },
                "pour": {
                    **final,
                    "target_ratio": final["target"] / PARTICLE_COUNT,
                    "tabletop_spill_ratio": final["tabletop_spill"] / PARTICLE_COUNT,
                },
                "performance": {
                    "mean_rtx_fps": 1000.0 / statistics.fmean(render_timings[30:]),
                    "sample_count": len(render_timings[30:]),
                },
                "hard_runtime_errors": errors,
            }
        finally:
            pass
        checks = {
            "gpu_cooking": not errors,
            "particle_count": final["particle_count"] == PARTICLE_COUNT,
            "static_retention": static_min / PARTICLE_COUNT >= 0.95,
            "below_support": static_below == 0 and final["below_support"] == 0,
            "target_reception": final["target"] / PARTICLE_COUNT >= 0.8,
            "tabletop_spill": final["tabletop_spill"] / PARTICLE_COUNT <= 0.05,
            "performance": result["performance"]["mean_rtx_fps"] >= 40.0,
        }
        result["checks"] = checks
        result["overall_status"] = "pass" if all(checks.values()) else "blocked"
        _write_observation(args.out, result)
        return result
    finally:
        app.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--partition-count", required=True, type=int)
    parser.add_argument("--run-index", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = _run(args)
    _write_observation(args.out, result)
    print(args.out)
    return 0 if result["overall_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
