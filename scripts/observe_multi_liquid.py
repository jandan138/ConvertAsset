#!/usr/bin/env python3
"""One isolated Isaac Sim 4.1 static observation for a multi-set liquid package."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--seconds", type=float, required=True)
    parser.add_argument("--run-index", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    try:
        app = SimulationApp({"headless": True, "multi_gpu": False, "renderer": "RayTracedLighting"})
    finally:
        sys.argv = original
    import carb
    import omni.kit.app
    import omni.physx
    import omni.physx.bindings._physx as pb
    import omni.usd
    from omni.isaac.core import World
    from pxr import Sdf, Usd, UsdGeom

    manifest = json.loads(args.manifest.read_text())
    settings = carb.settings.get_settings()
    log_path = Path(str(settings.get("/log/file")))
    log_offset = log_path.stat().st_size if log_path.exists() else 0
    settings.set(pb.SETTING_UPDATE_TO_USD, True)
    settings.set(pb.SETTING_UPDATE_PARTICLES_TO_USD, True)
    settings.set(pb.SETTING_UPDATE_VELOCITIES_TO_USD, True)
    settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
    settings.set_bool("/physics/suppressReadback", False)
    fixture_path = args.out.parent / f"qualification_fixture_{args.run_index}.usda"
    fixture_layer = Sdf.Layer.CreateNew(str(fixture_path))
    fixture_layer.subLayerPaths = [str(args.scene.resolve())]
    fixture_layer.Save()
    fixture_stage = Usd.Stage.Open(str(fixture_path))
    for item in manifest["sets"]:
        fixture_stage.OverridePrim(item["container_prim"]).CreateAttribute(
            "physics:kinematicEnabled", Sdf.ValueTypeNames.Bool
        ).Set(True)
    fixture_stage.GetRootLayer().Save()
    context = omni.usd.get_context()
    if not context.open_stage(str(fixture_path.resolve())):
        raise RuntimeError(f"cannot open {fixture_path}")
    for _ in range(40):
        app.update()
    stage = context.get_stage()
    meters = float(UsdGeom.GetStageMetersPerUnit(stage))
    up_axis = str(UsdGeom.GetStageUpAxis(stage)).upper()
    vertical = 2 if up_axis == "Z" else 1
    physics = next((p.GetPath().pathString for p in stage.Traverse() if p.GetTypeName() == "PhysicsScene"), None)
    if physics is None:
        raise RuntimeError("scene has no PhysicsScene")
    world = World(
        stage_units_in_meters=meters,
        physics_prim_path=physics,
        set_defaults=False,
        backend="numpy",
        device="cpu",
        physics_dt=1 / 120,
        rendering_dt=1 / 120,
    )
    omni.physx.get_physx_interface().overwrite_gpu_setting(1)
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    bounds = {}
    for item in manifest["sets"]:
        box = cache.ComputeWorldBound(stage.GetPrimAtPath(item["container_prim"])).ComputeAlignedBox()
        bounds[item["id"]] = ([float(v) for v in box.GetMin()], [float(v) for v in box.GetMax()])
    world.reset()
    steps = round(args.seconds * 120)
    started = time.monotonic()
    for _ in range(steps):
        world.step(render=False)
    elapsed = time.monotonic() - started
    spacing = float(manifest["sampling"]["spacing_m"]) / meters
    sets = {}
    for item in manifest["sets"]:
        prim = stage.GetPrimAtPath(item["particle_prim"])
        values = prim.GetAttribute("points").Get()
        if values is None:
            raise RuntimeError(f"live points unavailable for {item['id']}")
        minimum, maximum = bounds[item["id"]]
        inside = sum(
            all(minimum[i] - spacing <= float(point[i]) <= maximum[i] + spacing for i in range(3))
            for point in values
        )
        below = sum(float(point[vertical]) < minimum[vertical] - spacing for point in values)
        sets[item["id"]] = {
            "particle_count": len(values),
            "retention_ratio": inside / int(item["particle_count"]),
            "below_floor_count": below,
            "container_world_bounds_stage": [minimum, maximum],
            "final_points_bounds_stage": [
                [min(float(point[i]) for point in values) for i in range(3)],
                [max(float(point[i]) for point in values) for i in range(3)],
            ],
        }
    text = (
        log_path.read_text(encoding="utf-8", errors="replace")[log_offset:]
        if log_path.exists() else ""
    )
    markers = (
        "failed to cook GPU-compatible mesh",
        "Non-GPU-compatible convex mesh",
        "Particles feature is only supported on GPU",
        "CUDA error",
        "illegal memory access",
    )
    result = {
        "schema_version": "aan.multi_liquid_cold_observation.v1",
        "run_index": args.run_index,
        "runtime": {
            "name": "isaac41",
            "kit_version": str(omni.kit.app.get_app().get_app_version()),
        },
        "duration_seconds": args.seconds,
        "physics_steps_per_wall_second": steps / elapsed if elapsed else None,
        "sets": sets,
        "hard_errors": [line.strip() for line in text.splitlines() if any(marker in line for marker in markers)],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if not result["hard_errors"] else 1


if __name__ == "__main__":
    try:
        code = main()
    except BaseException:
        traceback.print_exc()
        code = 2
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
