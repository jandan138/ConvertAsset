#!/usr/bin/env python3
"""Observe one prescribed GPU-PBD source-to-target transfer in Isaac Sim 4.1."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys
import time
from typing import Any


SOURCE = "/World/Transfer/Source"
TARGET = "/World/Transfer/Target"
PARTICLES = "/World/Transfer/ParticleSet"
PHYSICS_HZ = 120


def hard_runtime_errors(text: str) -> list[str]:
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


def source_matrix(position: Any, orientation_wxyz: Any, np: Any) -> Any:
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


def pose_for_pivot(
    *, pivot_xyz: Any, rim_z_m: float, angle_deg: float, np: Any
) -> tuple[Any, Any]:
    angle = math.radians(angle_deg)
    orientation = np.asarray(
        [math.cos(angle / 2), 0.0, math.sin(angle / 2), 0.0], dtype=float
    )
    rotation = source_matrix(np.zeros(3), orientation, np)[:3, :3]
    local_rim = np.asarray([0.0, 0.0, rim_z_m], dtype=float)
    position = np.asarray(pivot_xyz, dtype=float) - local_rim @ rotation
    return position, orientation


def classify_particles(
    positions: Any,
    *,
    source_matrix: Any,
    source_cavity: dict[str, float],
    target_cavity: dict[str, float],
    np: Any,
) -> dict[str, int]:
    local = np.c_[positions, np.ones((len(positions), 1))] @ np.linalg.inv(
        source_matrix
    )
    source = (
        (np.linalg.norm(local[:, :2], axis=1) <= float(source_cavity["radius_m"]))
        & (local[:, 2] >= float(source_cavity["floor_z_m"]))
        & (local[:, 2] <= float(source_cavity["rim_z_m"]))
    )
    target = (
        (np.linalg.norm(positions[:, :2], axis=1) <= float(target_cavity["radius_m"]))
        & (positions[:, 2] >= float(target_cavity["floor_z_m"]))
        & (positions[:, 2] <= float(target_cavity["rim_z_m"]))
    )
    below = positions[:, 2] < -0.002
    spill = ~source & ~target & ~below
    return {
        "source": int(source.sum()),
        "target": int(target.sum()),
        "below_support": int(below.sum()),
        "spill": int(spill.sum()),
        "particle_count": int(len(positions)),
    }


def qualification_checks(
    *,
    static_source_ratio: float,
    maximum_below_support: int,
    final: dict[str, int],
    hard_runtime_errors: list[str],
    mean_rtx_fps: float,
) -> dict[str, bool]:
    count = int(final["particle_count"])
    return {
        "gpu_cooking": not hard_runtime_errors,
        "particle_count": count == 548,
        "static_retention": static_source_ratio >= 0.95,
        "below_support_observed": maximum_below_support > 0
        or int(final["below_support"]) > 0,
        "target_reception": count > 0 and int(final["target"]) / count >= 0.5,
        "performance": mean_rtx_fps >= 40.0,
    }


def blocking_checks_pass(checks: dict[str, bool]) -> bool:
    return all(
        value for name, value in checks.items() if name != "below_support_observed"
    )


def _read_positions(stage: Any, np: Any) -> Any:
    prim = stage.GetPrimAtPath(PARTICLES)
    # Isaac 4.1 leaves ``simulationPoints`` at the authored rest state;
    # live particle readback is written to ``points``.
    for name in ("points", "physxParticle:simulationPoints"):
        values = prim.GetAttribute(name).Get()
        if values is not None:
            return np.asarray(values, dtype=float)
    raise RuntimeError("particle positions unavailable")


def _checkpoint(stage: Any, source_view: Any, *, name: str, np: Any) -> dict[str, Any]:
    prim = stage.GetPrimAtPath(PARTICLES)
    attributes: dict[str, Any] = {}
    for attribute_name in ("physxParticle:simulationPoints", "points", "velocities"):
        values = prim.GetAttribute(attribute_name).Get()
        if values is None:
            attributes[attribute_name] = None
            continue
        array = np.asarray(values, dtype=float)
        attributes[attribute_name] = {
            "count": int(len(array)),
            "minimum": array.min(axis=0).tolist(),
            "maximum": array.max(axis=0).tolist(),
            "mean": array.mean(axis=0).tolist(),
        }
    positions, orientations = source_view.get_world_poses()
    return {
        "name": name,
        "source_position": np.asarray(positions[0], dtype=float).tolist(),
        "source_orientation_wxyz": np.asarray(orientations[0], dtype=float).tolist(),
        "particle_attributes": attributes,
    }


def _lerp(a: Any, b: Any, alpha: float, np: Any) -> Any:
    return (
        np.asarray(a, dtype=float) * (1.0 - alpha) + np.asarray(b, dtype=float) * alpha
    )


def _run(args: argparse.Namespace) -> dict[str, Any]:
    from isaacsim import SimulationApp

    scene = args.scene.resolve()
    fixture = json.loads(args.fixture_profile.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate_json)
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
    try:
        import carb
        import numpy as np
        import omni.kit.app
        import omni.physx
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.prims import RigidPrimView
        import omni.physx.bindings._physx as pb

        settings = carb.settings.get_settings()
        log_path = Path(str(settings.get("/log/file")))
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        settings.set(pb.SETTING_UPDATE_PARTICLES_TO_USD, True)
        settings.set(pb.SETTING_UPDATE_VELOCITIES_TO_USD, True)
        settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
        settings.set_bool("/physics/suppressReadback", False)
        context = omni.usd.get_context()
        if not context.open_stage(str(scene)):
            raise RuntimeError(f"could not open {scene}")
        for _ in range(40):
            app.update()
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError(f"could not open {scene}")
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
        source_view = RigidPrimView(SOURCE, name="transfer_source")
        target_view = RigidPrimView(TARGET, name="transfer_target")
        world.scene.add(source_view)
        world.scene.add(target_view)
        world.reset()
        for _ in range(30):
            world.step(render=False)

        source_cavity = fixture["source"]["cavity"]
        target_cavity = fixture["target"]["cavity"]
        protocol = fixture["trajectory_protocol"]
        initial_position = np.asarray(fixture["source"]["initial_xyz_m"], dtype=float)
        upright = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=float)

        static_scores = []
        initial_matrix = source_matrix(initial_position, upright, np)
        for _ in range(round(float(protocol["settle_seconds"]) * PHYSICS_HZ)):
            world.step(render=False)
            static_scores.append(
                classify_particles(
                    _read_positions(stage, np),
                    source_matrix=initial_matrix,
                    source_cavity=source_cavity,
                    target_cavity=target_cavity,
                    np=np,
                )
            )
        static_min = min(score["source"] for score in static_scores)
        maximum_below = max(score["below_support"] for score in static_scores)
        checkpoints = [_checkpoint(stage, source_view, name="after_static_hold", np=np)]

        high_root = np.asarray(
            [initial_position[0], initial_position[1], float(protocol["high_root_z_m"])]
        )
        for index in range(1, round(float(protocol["lift_seconds"]) * PHYSICS_HZ) + 1):
            alpha = index / round(float(protocol["lift_seconds"]) * PHYSICS_HZ)
            position = _lerp(initial_position, high_root, alpha, np)
            source_view.set_world_poses(
                positions=np.asarray([position], dtype=np.float32),
                orientations=np.asarray([upright], dtype=np.float32),
            )
            world.step(render=False)

        rim_z = float(source_cavity["rim_z_m"])
        lateral_root = np.asarray(
            [float(candidate["rim_offset_x_m"]), 0.0, high_root[2]],
            dtype=float,
        )
        lateral_steps = round(
            float(protocol.get("lateral_approach_seconds", 0.0)) * PHYSICS_HZ
        )
        for index in range(1, lateral_steps + 1):
            alpha = index / lateral_steps
            position = _lerp(high_root, lateral_root, alpha, np)
            source_view.set_world_poses(
                positions=np.asarray([position], dtype=np.float32),
                orientations=np.asarray([upright], dtype=np.float32),
            )
            world.step(render=False)

        high_root = lateral_root
        high_pivot = high_root + np.asarray([0.0, 0.0, rim_z])
        pretilt = float(protocol["pretilt_degrees"])
        for index in range(
            1, round(float(protocol["pretilt_seconds"]) * PHYSICS_HZ) + 1
        ):
            alpha = index / round(float(protocol["pretilt_seconds"]) * PHYSICS_HZ)
            position, orientation = pose_for_pivot(
                pivot_xyz=high_pivot, rim_z_m=rim_z, angle_deg=pretilt * alpha, np=np
            )
            source_view.set_world_poses(
                positions=np.asarray([position], dtype=np.float32),
                orientations=np.asarray([orientation], dtype=np.float32),
            )
            world.step(render=False)

        low_pivot = np.asarray(
            [
                float(candidate["rim_offset_x_m"]),
                0.0,
                float(target_cavity["rim_z_m"]) + float(candidate["rim_gap_m"]),
            ]
        )
        approach_steps = round(
            float(protocol["tilt_and_approach_seconds"]) * PHYSICS_HZ
        )
        for index in range(1, approach_steps + 1):
            alpha = index / approach_steps
            pivot = _lerp(high_pivot, low_pivot, alpha, np)
            angle = pretilt * (1.0 - alpha) + float(candidate["tilt_deg"]) * alpha
            position, orientation = pose_for_pivot(
                pivot_xyz=pivot, rim_z_m=rim_z, angle_deg=angle, np=np
            )
            source_view.set_world_poses(
                positions=np.asarray([position], dtype=np.float32),
                orientations=np.asarray([orientation], dtype=np.float32),
            )
            world.step(render=False)

        checkpoints.append(
            _checkpoint(stage, source_view, name="after_tilt_and_approach", np=np)
        )

        for _ in range(round(float(candidate["dwell_seconds"]) * PHYSICS_HZ)):
            world.step(render=False)

        checkpoints.append(_checkpoint(stage, source_view, name="after_dwell", np=np))

        retreat_steps = round(float(protocol["retreat_seconds"]) * PHYSICS_HZ)
        for index in range(1, retreat_steps + 1):
            alpha = index / retreat_steps
            pivot = _lerp(low_pivot, high_pivot, alpha, np)
            angle = float(candidate["tilt_deg"]) * (1.0 - alpha) + pretilt * alpha
            position, orientation = pose_for_pivot(
                pivot_xyz=pivot, rim_z_m=rim_z, angle_deg=angle, np=np
            )
            source_view.set_world_poses(
                positions=np.asarray([position], dtype=np.float32),
                orientations=np.asarray([orientation], dtype=np.float32),
            )
            world.step(render=False)

        upright_steps = round(float(protocol["upright_seconds"]) * PHYSICS_HZ)
        for index in range(1, upright_steps + 1):
            alpha = index / upright_steps
            position, orientation = pose_for_pivot(
                pivot_xyz=high_pivot,
                rim_z_m=rim_z,
                angle_deg=pretilt * (1.0 - alpha),
                np=np,
            )
            source_view.set_world_poses(
                positions=np.asarray([position], dtype=np.float32),
                orientations=np.asarray([orientation], dtype=np.float32),
            )
            world.step(render=False)

        return_steps = round(float(protocol["return_seconds"]) * PHYSICS_HZ)
        for index in range(1, return_steps + 1):
            alpha = index / return_steps
            position = _lerp(high_root, initial_position, alpha, np)
            source_view.set_world_poses(
                positions=np.asarray([position], dtype=np.float32),
                orientations=np.asarray([upright], dtype=np.float32),
            )
            world.step(render=False)

        settle_scores = []
        for _ in range(round(float(protocol["final_settle_seconds"]) * PHYSICS_HZ)):
            world.step(render=False)
            settle_scores.append(
                classify_particles(
                    _read_positions(stage, np),
                    source_matrix=initial_matrix,
                    source_cavity=source_cavity,
                    target_cavity=target_cavity,
                    np=np,
                )
            )
        final = settle_scores[-1]
        maximum_below = max(
            maximum_below, max(score["below_support"] for score in settle_scores)
        )
        final_positions = _read_positions(stage, np).tolist()
        args.out.with_name("final_particle_positions.json").write_text(
            json.dumps(final_positions, indent=2) + "\n", encoding="utf-8"
        )
        checkpoints.append(
            _checkpoint(stage, source_view, name="after_return_and_settle", np=np)
        )
        args.out.with_name("trajectory_checkpoints.json").write_text(
            json.dumps(checkpoints, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        timings = []
        for _ in range(90):
            started = time.perf_counter()
            world.step(render=True)
            timings.append((time.perf_counter() - started) * 1000.0)
        fps = 1000.0 / statistics.fmean(timings[30:])
        errors = hard_runtime_errors(
            log_path.read_text(encoding="utf-8", errors="replace")
        )
        static_ratio = static_min / int(final["particle_count"])
        checks = qualification_checks(
            static_source_ratio=static_ratio,
            maximum_below_support=maximum_below,
            final=final,
            hard_runtime_errors=errors,
            mean_rtx_fps=fps,
        )
        result = {
            "schema_version": "aan.gpu_pbd_transfer_observation.v1",
            "candidate_id": candidate["candidate_id"],
            "particle_readback_attribute": "points",
            "trajectory": candidate,
            "run_index": args.run_index,
            "runtime": {
                "kit_version": str(omni.kit.app.get_app().get_app_version()),
                "gpu": "NVIDIA GeForce RTX 4090",
                "resolution": [960, 540],
            },
            "static_hold": {
                "minimum_source_count": static_min,
                "minimum_source_ratio": static_ratio,
                "maximum_below_support_count": maximum_below,
            },
            "pour": {
                **final,
                "target_ratio": final["target"] / final["particle_count"],
                "spill_ratio": final["spill"] / final["particle_count"],
            },
            "target_actor_mode": "fixed_kinematic_rigid_body",
            "source_actor_mode": "prescribed_kinematic_trajectory",
            "performance": {"mean_rtx_fps": fps, "sample_count": 60},
            "trajectory_checkpoints": "trajectory_checkpoints.json",
            "hard_runtime_errors": errors,
            "checks": checks,
            "overall_status": "pass" if blocking_checks_pass(checks) else "blocked",
            "claim_boundary": "Prescribed kinematic transfer feasibility only; spill is recorded but non-blocking; no robot or benchmark claim.",
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return result
    finally:
        app.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--fixture-profile", required=True, type=Path)
    parser.add_argument("--candidate-json", required=True)
    parser.add_argument("--run-index", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = _run(args)
    print(args.out)
    return 0 if result["overall_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
