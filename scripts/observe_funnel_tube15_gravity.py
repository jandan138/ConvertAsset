#!/usr/bin/env python3
"""Observe one funnel-to-tube gravity feed in Isaac Sim 4.1."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    from isaacsim import SimulationApp

    saved = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = saved
    import carb
    import omni.kit.app
    import omni.physx
    import omni.physx.bindings._physx as pb
    import omni.usd
    from omni.isaac.core import World

    fixture = json.loads(args.fixture.read_text())
    settings = carb.settings.get_settings()
    log_path = Path(str(settings.get("/log/file")))
    log_offset = log_path.stat().st_size if log_path.exists() else 0
    settings.set(pb.SETTING_UPDATE_TO_USD, True)
    settings.set(pb.SETTING_UPDATE_PARTICLES_TO_USD, True)
    settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
    context = omni.usd.get_context()
    if not context.open_stage(str(args.scene.resolve())):
        raise RuntimeError("could not open integration scene")
    for _ in range(40):
        app.update()
    stage = context.get_stage()
    world = World(
        stage_units_in_meters=1.0,
        physics_prim_path=fixture["physics_scene_path"],
        set_defaults=False,
        backend="numpy",
        device="cpu",
        physics_dt=1 / 120,
        rendering_dt=1 / 120,
    )
    omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    world.reset()
    particle = stage.GetPrimAtPath(fixture["particle_set_prim"])
    previous = particle.GetAttribute("points").Get()
    initial = int(fixture["particle_count"])
    legal: set[int] = set()
    leaks: set[int] = set()
    recipe = fixture["liquid_recipe"]["payload"]
    outlet_z = float(fixture["funnel_outlet_z_m"])
    tolerance = (
        float(fixture["funnel_outer_outlet_radius_m"])
        + 0.5 * float(recipe["particle_set"]["width_m"])
        + float(recipe["particle_system"]["max_velocity_m_s"]) / 120.0
    )
    for _ in range(1440):
        world.step(render=False)
        live = particle.GetAttribute("points").Get()
        for index, point in enumerate(live):
            before = previous[index]
            if before[2] > outlet_z >= point[2]:
                alpha = (before[2] - outlet_z) / max(before[2] - point[2], 1e-9)
                radius = math.hypot(
                    before[0] + alpha * (point[0] - before[0]),
                    before[1] + alpha * (point[1] - before[1]),
                )
                (legal if radius <= tolerance else leaks).add(index)
        previous = live
    tube = fixture["tube"]
    captured = sum(
        math.hypot(point[0], point[1]) <= float(tube["inner_radius_m"])
        and float(tube["floor_z_m"]) <= point[2] <= float(tube["rim_z_m"])
        for point in previous
    )
    below_floor = sum(point[2] < float(tube["floor_z_m"]) - 0.001 for point in previous)
    log = log_path.read_text(errors="replace")[log_offset:] if log_path.exists() else ""
    markers = ("CUDA error", "illegal memory access", "Particles feature is only supported on GPU")
    hard = [line for line in log.splitlines() if any(marker in line for marker in markers)]
    result = {
        "schema_version": "aan.funnel_tube15_gravity_observation.v1",
        "status": "observed",
        "particle_count": initial,
        "legal_outlet_ratio": len(legal) / initial,
        "tube_capture_ratio": captured / initial,
        "structural_leak_count": len(leaks),
        "below_tube_floor_count": below_floor,
        "hard_errors": hard,
        "liquid_recipe": {k: fixture["liquid_recipe"][k] for k in ("id", "sha256")},
        "runtime": {"name": "isaac41", "kit_version": str(omni.kit.app.get_app().get_app_version())},
    }
    acceptance = fixture["acceptance"]
    result["overall_status"] = "pass" if (
        result["legal_outlet_ratio"] >= acceptance["minimum_legal_outlet_ratio"]
        and result["tube_capture_ratio"] >= acceptance["minimum_tube_capture_ratio"]
        and result["structural_leak_count"] <= acceptance["maximum_structural_leak_count"]
        and not hard
    ) else "blocked"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
