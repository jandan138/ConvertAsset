#!/usr/bin/env python3
"""Isaac 4.1 evidence worker for a vertical lift/hold/return liquid protocol."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Any


SOURCE = "/World/Transfer/Source"
TARGET = "/World/Transfer/Target"
PARTICLES = "/World/Transfer/ParticleSet"
PHYSICS_HZ = 120
TOTAL_STEPS = 960
LIFT_HEIGHT_M = 0.10


def trajectory_height(step: int) -> float:
    if step < 240:
        return 0.0
    if step < 360:
        return LIFT_HEIGHT_M * (step - 240) / 120
    if step < 600:
        return LIFT_HEIGHT_M
    if step < 720:
        return LIFT_HEIGHT_M * (1.0 - (step - 600) / 120)
    return 0.0


def _hard_errors(text: str) -> list[str]:
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


def _run(args: argparse.Namespace) -> dict[str, Any]:
    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    try:
        app = SimulationApp({"headless": True, "multi_gpu": False, "renderer": "RayTracedLighting"})
    finally:
        sys.argv = original
    import carb
    import numpy as np
    import omni.kit.app
    import omni.physx
    import omni.physx.bindings._physx as pb
    import omni.usd
    from omni.isaac.core import World
    from omni.isaac.core.prims import RigidPrimView
    from pxr import Gf, Vt

    fixture = json.loads(args.fixture.read_text())
    cavity = fixture["source"]["cavity"]
    initial_xy = [float(value) for value in fixture["source"]["initial_xyz_m"][:2]]
    state = json.loads(args.particle_state.read_text())
    local_seed = np.asarray(state["positions"], dtype=float)
    if len(local_seed) != 580:
        raise RuntimeError("vertical lift requires the bound 580-particle state")

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
        raise RuntimeError(f"cannot open {args.scene}")
    for _ in range(40):
        app.update()
    stage = context.get_stage()
    stage.GetPrimAtPath(TARGET).SetActive(False)
    source = stage.GetPrimAtPath(SOURCE)
    source.GetAttribute("physics:kinematicEnabled").Set(True)
    source.GetAttribute("xformOp:translate").Set(Gf.Vec3d(initial_xy[0], initial_xy[1], 0.0))
    particle_prim = stage.GetPrimAtPath(PARTICLES)
    world_seed = local_seed + np.asarray([initial_xy[0], initial_xy[1], 0.0])
    seed_values = Vt.Vec3fArray.FromNumpy(world_seed.astype("float32"))
    particle_prim.GetAttribute("physxParticle:simulationPoints").Set(seed_values)
    particle_prim.GetAttribute("points").Set(seed_values)
    particle_prim.GetAttribute("velocities").Set(
        Vt.Vec3fArray.FromNumpy(np.zeros_like(world_seed, dtype="float32"))
    )

    world = World(
        stage_units_in_meters=1.0,
        physics_prim_path="/World/PhysicsScene",
        set_defaults=False,
        backend="numpy",
        device="cpu",
        physics_dt=1 / PHYSICS_HZ,
        rendering_dt=1 / PHYSICS_HZ,
    )
    view = RigidPrimView(SOURCE, name="vertical_lift_source")
    world.scene.add(view)
    omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    world.reset()
    maximum_outside = 0
    maximum_below = 0
    maximum_tracking_error = 0.0
    started = time.monotonic()
    for step in range(TOTAL_STEPS):
        height = trajectory_height(step)
        desired = np.asarray([[initial_xy[0], initial_xy[1], height]], dtype=float)
        view.set_world_poses(
            positions=desired,
            orientations=np.asarray([[1.0, 0.0, 0.0, 0.0]], dtype=float),
        )
        world.step(render=False)
        positions, _ = view.get_world_poses()
        maximum_tracking_error = max(
            maximum_tracking_error,
            float(np.linalg.norm(np.asarray(positions[0], dtype=float) - desired[0])),
        )
        live = np.asarray(particle_prim.GetAttribute("points").Get(), dtype=float)
        local = live - desired[0]
        radial = np.linalg.norm(local[:, :2], axis=1)
        inside = (
            (radial <= float(cavity["radius_m"]))
            & (local[:, 2] >= float(cavity["floor_z_m"]))
            & (local[:, 2] <= float(cavity["rim_z_m"]))
        )
        maximum_outside = max(maximum_outside, int(len(local) - int(inside.sum())))
        maximum_below = max(
            maximum_below,
            int((local[:, 2] < float(cavity["floor_z_m"])).sum()),
        )
    elapsed = time.monotonic() - started
    errors = _hard_errors(
        log_path.read_text(encoding="utf-8", errors="replace")[log_offset:]
        if log_path.exists()
        else ""
    )
    checks = {
        "particle_count": len(particle_prim.GetAttribute("points").Get()) == 580,
        "maximum_outside_source": maximum_outside <= 2,
        "maximum_below_source_floor": maximum_below == 0,
        "root_tracking_error": maximum_tracking_error <= 0.002,
        "hard_runtime_errors": not errors,
    }
    result = {
        "schema_version": "aan.task02_vertical_lift_observation.v1",
        "run_index": args.run_index,
        "protocol": {
            "settle_seconds": 2.0,
            "lift_height_m": LIFT_HEIGHT_M,
            "lift_seconds": 1.0,
            "hold_seconds": 2.0,
            "return_seconds": 1.0,
            "final_hold_seconds": 2.0,
        },
        "particle_count": 580,
        "maximum_outside_source_count": maximum_outside,
        "maximum_below_source_floor_count": maximum_below,
        "maximum_root_tracking_error_m": maximum_tracking_error,
        "hard_runtime_errors": errors,
        "physics_steps_per_wall_second": TOTAL_STEPS / elapsed if elapsed else None,
        "checks": checks,
        "overall_status": "pass" if all(checks.values()) else "blocked",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--particle-state", required=True, type=Path)
    parser.add_argument("--run-index", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = _run(args)
    print(args.out)
    return 0 if result["overall_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
