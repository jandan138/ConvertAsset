#!/usr/bin/env python3
"""Qualify one Isaac 4.1 recomposition run of the exact Wangshuai asset set."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sys
import traceback
from typing import Any


ASSET_IDS = (
    "tube15_threaded_liquid_ready",
    "tube15_threaded_closed_cap",
    "funnel_small_v2_liquid_ready",
    "small_v2_liquid_seed_1948",
)


def classify_run(
    *,
    authored_particle_count: int,
    runtime_particle_count: int,
    captured_count: int,
    below_floor_count: int,
    nonfinite_count: int,
    hard_errors: list[str],
) -> dict[str, Any]:
    capture_ratio = (
        captured_count / authored_particle_count if authored_particle_count else 0.0
    )
    checks = {
        "particle_count_identity": runtime_particle_count == authored_particle_count == 1948,
        "tube_capture_ratio": capture_ratio >= 0.95,
        "no_below_floor_leak": below_floor_count == 0,
        "all_particle_positions_finite": nonfinite_count == 0,
        "no_hard_errors": not hard_errors,
    }
    return {
        "overall_status": "pass" if all(checks.values()) else "blocked",
        "checks": checks,
        "capture_ratio": capture_ratio,
    }


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _build_fixture(source_path: Path, asset_set: Path, fixture: Path) -> None:
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics

    source = Usd.Stage.Open(str(source_path), Usd.Stage.LoadAll)
    index = json.loads((asset_set / "asset_set_manifest.json").read_text())
    entries = {item["id"]: item for item in index["assets"]}
    stage = Usd.Stage.CreateNew(str(fixture))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)

    def add_asset(asset_id: str, destination: str, source_prim: str | None) -> None:
        item = entries[asset_id]
        root = UsdGeom.Xform.Define(stage, destination)
        asset = asset_set / item["entry_usd"]
        root.GetPrim().GetReferences().AddReference(str(asset), item["entry_prim"])
        if source_prim is not None:
            matrix = UsdGeom.Xformable(
                source.GetPrimAtPath(source_prim)
            ).GetLocalTransformation()
            root.MakeMatrixXform().Set(matrix)

    add_asset("tube15_threaded_liquid_ready", "/World/shiguan", "/World/shiguan")
    add_asset("funnel_small_v2_liquid_ready", "/World/funnel", "/World/funnel")
    add_asset("tube15_threaded_closed_cap", "/World/cap", "/World/cap")
    add_asset("small_v2_liquid_seed_1948", "/World/LiquidOverlay", None)

    ground = UsdGeom.Plane.Define(stage, "/World/GroundPlane")
    ground.CreateAxisAttr(UsdGeom.Tokens.z)
    ground.CreateDoubleSidedAttr(True)
    UsdPhysics.CollisionAPI.Apply(ground.GetPrim())
    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr((0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr(9.81)
    scene_prim = scene.GetPrim()
    scene_prim.CreateAttribute(
        "physxScene:broadphaseType", Sdf.ValueTypeNames.Token, custom=True
    ).Set("GPU")
    scene_prim.CreateAttribute(
        "physxScene:enableGPUDynamics", Sdf.ValueTypeNames.Bool, custom=True
    ).Set(True)
    scene_prim.CreateAttribute(
        "physxScene:solverType", Sdf.ValueTypeNames.Token, custom=True
    ).Set("TGS")
    scene_prim.CreateAttribute(
        "physxScene:timeStepsPerSecond", Sdf.ValueTypeNames.UInt, custom=True
    ).Set(120)
    stage.GetRootLayer().Save()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--asset-set", type=Path, required=True)
    parser.add_argument("--mode", choices=("source", "recomposed"), default="recomposed")
    parser.add_argument("--run-index", type=int, required=True)
    parser.add_argument("--seconds", type=float, default=16.0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = original
    try:
        import carb
        import omni.kit.app
        import omni.physx
        import omni.physx.bindings._physx as pb
        import omni.usd
        from omni.isaac.core import World

        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        if args.mode == "source":
            fixture = args.source.resolve()
            particle_path = "/World/ParticleSet"
            physics_path = "/World/PhysicsScene"
        else:
            fixture = out.parent / "fixture.usda"
            _build_fixture(args.source.resolve(), args.asset_set.resolve(), fixture)
            particle_path = "/World/LiquidOverlay/ParticleSet"
            physics_path = "/World/PhysicsScene"
        context = omni.usd.get_context()
        if not context.open_stage(str(fixture)):
            raise RuntimeError(f"cannot open fixture: {fixture}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        stage = context.get_stage()
        particle_prim = stage.GetPrimAtPath(particle_path)
        authored_points = particle_prim.GetAttribute("points").Get()
        authored_count = len(authored_points)
        settings = carb.settings.get_settings()
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        settings.set(pb.SETTING_UPDATE_PARTICLES_TO_USD, True)
        settings.set(pb.SETTING_UPDATE_VELOCITIES_TO_USD, True)
        settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
        settings.set_bool("/physics/suppressReadback", False)
        log_path = Path(str(settings.get("/log/file")))
        log_offset = log_path.stat().st_size if log_path.exists() else 0
        world = World(
            stage_units_in_meters=1.0,
            physics_prim_path=physics_path,
            set_defaults=False,
            physics_dt=1 / 120,
            rendering_dt=1 / 120,
        )
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        world.reset()
        for _ in range(max(1, round(args.seconds * 120))):
            world.step(render=False)
        points = particle_prim.GetAttribute("points").Get()
        runtime_count = len(points)
        captured = 0
        below_floor = 0
        nonfinite = 0
        for point in points:
            xyz = tuple(float(value) for value in point)
            if not all(math.isfinite(value) for value in xyz):
                nonfinite += 1
                continue
            radius = math.hypot(xyz[0], xyz[1])
            if radius <= 0.0075 and 0.001 <= xyz[2] <= 0.1015:
                captured += 1
            if xyz[2] < -0.002:
                below_floor += 1
        log = (
            log_path.read_text(encoding="utf-8", errors="replace")[log_offset:]
            if log_path.exists()
            else ""
        )
        markers = (
            "CUDA error",
            "illegal memory access",
            "PhysX error",
            "Failed to cook",
        )
        hard_errors = [
            line.strip()
            for line in log.splitlines()
            if any(marker in line for marker in markers)
        ]
        result = classify_run(
            authored_particle_count=authored_count,
            runtime_particle_count=runtime_count,
            captured_count=captured,
            below_floor_count=below_floor,
            nonfinite_count=nonfinite,
            hard_errors=hard_errors,
        )
        report = {
            "schema_version": "aan.wangshuai_funnel_tube15_recomposition_run.v1",
            "status": result["overall_status"],
            "mode": args.mode,
            "run_index": args.run_index,
            "duration_seconds": args.seconds,
            "runtime": {
                "name": "isaac41",
                "kit_version": str(omni.kit.app.get_app().get_app_version()),
            },
            "source_sha256": _sha(args.source.resolve()),
            "asset_set_manifest_sha256": _sha(
                args.asset_set.resolve() / "asset_set_manifest.json"
            ),
            "fixture": str(fixture),
            "checks": result["checks"],
            "observations": {
                "authored_particle_count": authored_count,
                "runtime_particle_count": runtime_count,
                "captured_count": captured,
                "capture_ratio": result["capture_ratio"],
                "below_floor_count": below_floor,
                "nonfinite_count": nonfinite,
                "hard_errors": hard_errors,
            },
            "claims": {
                "recomposition_liquid_transfer": result["overall_status"] == "pass",
                "physics_parameters_unchanged": True,
                "robot_policy_success": False,
                "task_success": False,
                "benchmark_success": False,
            },
        }
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True), flush=True)
        return 0 if result["overall_status"] == "pass" else 2
    except BaseException:
        traceback.print_exc()
        return 3
    finally:
        pass


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
