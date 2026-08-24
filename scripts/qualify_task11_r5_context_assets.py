#!/usr/bin/env python3
"""One Isaac 4.1 qualification run for Task 11 r5 context assets."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import traceback


TARGET_FRAME = (
    "/TubeRack15ml50ml_OriginalMesh/__frames/"
    "slot_15ml_r00_c02_inserted_bottom"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--tube", type=Path, required=True)
    parser.add_argument("--run-index", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = original
    scene_path = Path(tempfile.gettempdir()) / (
        f"task11_r5_rack_qualification_{os.getpid()}_{args.run_index}.usda"
    )
    try:
        import carb
        import omni.physx
        import omni.physx.bindings._physx as pb
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.prims import RigidPrim
        from pxr import Gf, Usd, UsdGeom, UsdPhysics

        root = args.root.resolve()
        context_results = {}
        for label in ("context_15ml_closed", "context_50ml_closed"):
            package = root / f"{label}/package"
            stage = Usd.Stage.Open(str(package / "asset.usd"))
            entry = stage.GetDefaultPrim()
            physics_prims = []
            for prim in stage.Traverse():
                if prim.HasAPI(UsdPhysics.RigidBodyAPI) or prim.HasAPI(
                    UsdPhysics.CollisionAPI
                ):
                    physics_prims.append(str(prim.GetPath()))
            context_results[label] = {
                "stage_open": bool(stage),
                "default_prim": str(entry.GetPath()),
                "physics_prims": physics_prims,
                "visual_static_no_physics": not physics_prims,
            }

        rack_asset = root / "mixed_rack_r2/package/asset.usd"
        rack_stage = Usd.Stage.Open(str(rack_asset))
        target = UsdGeom.XformCache().GetLocalToWorldTransform(
            rack_stage.GetPrimAtPath(TARGET_FRAME)
        ).ExtractTranslation()
        scene = Usd.Stage.CreateNew(str(scene_path))
        UsdGeom.SetStageMetersPerUnit(scene, 1.0)
        UsdGeom.SetStageUpAxis(scene, UsdGeom.Tokens.z)
        world_prim = UsdGeom.Xform.Define(scene, "/World").GetPrim()
        scene.SetDefaultPrim(world_prim)
        rack = UsdGeom.Xform.Define(scene, "/World/Rack")
        rack.GetPrim().GetReferences().AddReference(
            str(rack_asset), "/TubeRack15ml50ml_OriginalMesh"
        )
        tube = UsdGeom.Xform.Define(scene, "/World/Tube")
        tube.GetPrim().GetReferences().AddReference(
            str((args.tube.resolve() / "asset.usd")),
            "/World/CentrifugeTube15mlClosed",
        )
        initial_z = float(target[2]) + 0.08
        tube.AddTranslateOp().Set(Gf.Vec3d(target[0], target[1], initial_z))
        physics = UsdPhysics.Scene.Define(scene, "/World/physicsScene")
        physics.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
        physics.CreateGravityMagnitudeAttr(9.81)
        scene.GetRootLayer().Save()

        context = omni.usd.get_context()
        if not context.open_stage(str(scene_path)):
            raise RuntimeError(f"cannot open {scene_path}")
        for _ in range(40):
            app.update()
        settings = carb.settings.get_settings()
        log_path = Path(str(settings.get("/log/file")))
        log_offset = log_path.stat().st_size if log_path.exists() else 0
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
        world = World(
            stage_units_in_meters=1.0,
            physics_prim_path="/World/physicsScene",
            set_defaults=False,
            physics_dt=1 / 120,
            rendering_dt=1 / 120,
        )
        tube_prim = world.scene.add(RigidPrim(prim_path="/World/Tube", name="target_tube"))
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        world.reset()
        release_z = float(target[2]) + 0.005
        for step in range(120):
            alpha = (step + 1) / 120
            z = initial_z + (release_z - initial_z) * alpha
            tube_prim.set_world_pose(
                position=[float(target[0]), float(target[1]), z],
                orientation=[1.0, 0.0, 0.0, 0.0],
            )
            tube_prim.set_linear_velocity([0.0, 0.0, 0.0])
            tube_prim.set_angular_velocity([0.0, 0.0, 0.0])
            world.step(render=False)
        for _ in range(480):
            world.step(render=False)
        final_position, final_orientation = tube_prim.get_world_pose()
        final = [float(value) for value in final_position]
        quat = [float(value) for value in final_orientation]
        radial = math.hypot(final[0] - float(target[0]), final[1] - float(target[1]))
        angle_deg = math.degrees(2.0 * math.acos(min(1.0, abs(quat[0]))))
        target_slot_insertion = (
            radial <= 0.003
            and float(target[2]) - 0.002 <= final[2] <= float(target[2]) + 0.004
            and angle_deg <= 15.0
        )
        text = (
            log_path.read_text(encoding="utf-8", errors="replace")[log_offset:]
            if log_path.exists()
            else ""
        )
        markers = (
            "CUDA error",
            "illegal memory access",
            "Non-GPU-compatible convex mesh",
            "Failed to cook",
        )
        hard_errors = [
            line.strip()
            for line in text.splitlines()
            if any(marker in line for marker in markers)
        ]
        visual_static_ok = all(
            item["visual_static_no_physics"] for item in context_results.values()
        )
        passed = visual_static_ok and target_slot_insertion and not hard_errors
        report = {
            "schema_version": "aan.task11_r5_context_qualification.v1",
            "status": "pass" if passed else "blocked",
            "run_index": args.run_index,
            "runtime": "isaac41",
            "context_packages": context_results,
            "observations": {
                "target_frame_xyz_m": [float(value) for value in target],
                "initial_tube_z_m": initial_z,
                "prescribed_release_z_m": release_z,
                "final_tube_xyz_m": final,
                "final_tube_wxyz": quat,
                "radial_offset_m": radial,
                "upright_angle_deg": angle_deg,
                "hard_errors": hard_errors,
            },
            "claims": {
                "visual_static_no_physics": visual_static_ok,
                "target_slot_insertion": target_slot_insertion,
                "robot_policy_success": False,
            },
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if passed else 1
    except BaseException:
        traceback.print_exc()
        return 2
    finally:
        if scene_path.exists():
            scene_path.unlink()
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
