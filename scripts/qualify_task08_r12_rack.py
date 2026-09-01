#!/usr/bin/env python3
"""One Isaac Sim 4.1 cold-start qualification for the Task 08 r12 rack."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import traceback


SLOTS = ("slot_15ml_r00_c01", "slot_15ml_r00_c02", "slot_15ml_r00_c03")
RACK_ENTRY = "/TubeRack15ml50ml_OriginalMesh"
BODY_ENTRY = "/World/Tube15LongNeckThreadedBody"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-set", type=Path, required=True)
    parser.add_argument("--run-index", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = original
    fixture = Path(tempfile.gettempdir()) / (
        f"task08_r12_rack_{os.getpid()}_{args.run_index}.usda"
    )
    try:
        import carb
        import omni.physx
        import omni.physx.bindings._physx as pb
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.prims import RigidPrim
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

        root = args.asset_set.resolve()
        rack_asset = root / "packages/mixed_rack_18plus4_scaled_sdf_r3/asset.usd"
        body_asset = (
            root / "packages/tube15_long_neck_threaded_body_glass_v1_2/asset.usd"
        )
        rack_stage = Usd.Stage.Open(str(rack_asset))
        cache = UsdGeom.XformCache()
        targets = {}
        for slot in SLOTS:
            frame = rack_stage.GetPrimAtPath(
                f"{RACK_ENTRY}/__frames/{slot}_inserted_bottom"
            )
            targets[slot] = tuple(
                float(value)
                for value in cache.GetLocalToWorldTransform(frame).ExtractTranslation()
            )
        stage = Usd.Stage.CreateNew(str(fixture))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        world_prim = UsdGeom.Xform.Define(stage, "/World").GetPrim()
        stage.SetDefaultPrim(world_prim)
        rack = UsdGeom.Xform.Define(stage, "/World/Rack")
        rack.GetPrim().GetReferences().AddReference(str(rack_asset), RACK_ENTRY)
        for index, slot in enumerate(SLOTS):
            tube = UsdGeom.Xform.Define(stage, f"/World/Tube{index}")
            tube.GetPrim().GetReferences().AddReference(str(body_asset), BODY_ENTRY)
            tube.AddTranslateOp().Set(Gf.Vec3d(*targets[slot]))
        physics = UsdPhysics.Scene.Define(stage, "/World/physicsScene")
        physics.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
        physics.CreateGravityMagnitudeAttr(9.81)
        physics.GetPrim().CreateAttribute(
            "physxScene:broadphaseType", Sdf.ValueTypeNames.Token, custom=True
        ).Set("GPU")
        physics.GetPrim().CreateAttribute(
            "physxScene:enableGPUDynamics", Sdf.ValueTypeNames.Bool, custom=True
        ).Set(True)
        physics.GetPrim().CreateAttribute(
            "physxScene:solverType", Sdf.ValueTypeNames.Token, custom=True
        ).Set("TGS")
        physics.GetPrim().CreateAttribute(
            "physxScene:timeStepsPerSecond", Sdf.ValueTypeNames.UInt, custom=True
        ).Set(120)
        stage.GetRootLayer().Save()
        context = omni.usd.get_context()
        if not context.open_stage(str(fixture)):
            raise RuntimeError(f"cannot open {fixture}")
        for _ in range(50):
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
        tubes = [
            world.scene.add(RigidPrim(prim_path=f"/World/Tube{index}", name=f"tube{index}"))
            for index in range(3)
        ]
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        world.reset()
        for _ in range(960):
            world.step(render=False)
        observations = []
        stable = True
        for index, (slot, target) in enumerate(zip(SLOTS, targets.values(), strict=True)):
            position, orientation = tubes[index].get_world_pose()
            xyz = [float(value) for value in position]
            quat = [float(value) for value in orientation]
            radial = math.hypot(xyz[0] - target[0], xyz[1] - target[1])
            tilt = math.degrees(2.0 * math.acos(min(1.0, abs(quat[0]))))
            passed = (
                radial <= 0.003
                and target[2] - 0.002 <= xyz[2] <= target[2] + 0.004
                and tilt <= 15.0
            )
            stable = stable and passed
            observations.append(
                {
                    "slot": slot,
                    "target_xyz_m": list(target),
                    "final_xyz_m": xyz,
                    "final_wxyz": quat,
                    "radial_offset_m": radial,
                    "upright_angle_deg": tilt,
                    "stable": passed,
                }
            )
        text = (
            log_path.read_text(encoding="utf-8", errors="replace")[log_offset:]
            if log_path.exists()
            else ""
        )
        markers = (
            "CUDA error",
            "illegal memory access",
            "Failed to cook",
            "Non-GPU-compatible",
        )
        hard_errors = [
            line.strip()
            for line in text.splitlines()
            if any(marker in line for marker in markers)
        ]
        passed = stable and not hard_errors
        report = {
            "schema_version": "aan.task08_r12_rack_qualification.v1",
            "overall_status": "pass" if passed else "blocked",
            "runtime": "isaac41",
            "run_index": args.run_index,
            "physics_steps": 960,
            "observations": observations,
            "hard_errors": hard_errors,
            "claims": {
                "selected_slot_stability": stable,
                "robot_policy_success": False,
                "thread_interaction_ready": False,
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
        if fixture.exists():
            fixture.unlink()
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
