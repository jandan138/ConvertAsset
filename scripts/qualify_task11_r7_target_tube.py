#!/usr/bin/env python3
"""Qualify Task11 r7 tube with kinematic parallel jaws in Isaac Sim 4.1."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import traceback


ENTRY = "/World/CentrifugeTube15mlClosed"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = original
    scene_path = Path(tempfile.gettempdir()) / f"task11_r7_grasp_{os.getpid()}.usda"
    try:
        import carb
        import omni.physx
        import omni.physx.bindings._physx as pb
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.prims import RigidPrim, XFormPrim
        from pxr import Gf, Usd, UsdGeom, UsdPhysics

        package = args.package.resolve()
        stage = Usd.Stage.CreateNew(str(scene_path))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        world_prim = UsdGeom.Xform.Define(stage, "/World").GetPrim()
        stage.SetDefaultPrim(world_prim)
        tube = UsdGeom.Xform.Define(stage, "/World/Tube")
        tube.GetPrim().GetReferences().AddReference(str(package / "asset.usd"), ENTRY)
        tube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.02))
        ground = UsdGeom.Cube.Define(stage, "/World/Ground")
        ground.CreateSizeAttr(1.0)
        ground.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.005))
        ground.AddScaleOp().Set(Gf.Vec3f(0.25, 0.25, 0.01))
        UsdPhysics.CollisionAPI.Apply(ground.GetPrim())
        for name, sign in (("left", -1.0), ("right", 1.0)):
            jaw = UsdGeom.Cube.Define(stage, f"/World/Jaws/{name}")
            jaw.CreateSizeAttr(1.0)
            jaw.AddTranslateOp().Set(Gf.Vec3d(sign * 0.031, 0.0, 0.11033))
            jaw.AddScaleOp().Set(Gf.Vec3f(0.012, 0.035, 0.024))
            UsdPhysics.CollisionAPI.Apply(jaw.GetPrim())
            body = UsdPhysics.RigidBodyAPI.Apply(jaw.GetPrim())
            body.CreateKinematicEnabledAttr(True)
        physics = UsdPhysics.Scene.Define(stage, "/World/physicsScene")
        physics.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
        physics.CreateGravityMagnitudeAttr(9.81)
        stage.GetRootLayer().Save()

        context = omni.usd.get_context()
        if not context.open_stage(str(scene_path)):
            raise RuntimeError(f"cannot open {scene_path}")
        for _ in range(40):
            app.update()
        settings = carb.settings.get_settings()
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
        world = World(
            stage_units_in_meters=1.0,
            physics_prim_path="/World/physicsScene",
            set_defaults=False,
            physics_dt=1 / 120,
            rendering_dt=1 / 120,
        )
        tube_prim = world.scene.add(RigidPrim("/World/Tube", name="tube"))
        left = world.scene.add(XFormPrim("/World/Jaws/left", name="left_jaw"))
        right = world.scene.add(XFormPrim("/World/Jaws/right", name="right_jaw"))
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        world.reset()
        for _ in range(120):
            world.step(render=False)
        initial, _ = tube_prim.get_world_pose()

        # Move only the kinematic jaws.  The tube is never teleported.
        for step in range(180):
            alpha = (step + 1) / 180
            gap = 0.031 + (0.0150 - 0.031) * alpha
            z = 0.11033
            left.set_world_pose(position=[-gap, 0.0, z])
            right.set_world_pose(position=[gap, 0.0, z])
            world.step(render=False)
        closed, _ = tube_prim.get_world_pose()
        for step in range(240):
            dz = 0.10 * (step + 1) / 240
            left.set_world_pose(position=[-0.0150, 0.0, 0.11033 + dz])
            right.set_world_pose(position=[0.0150, 0.0, 0.11033 + dz])
            world.step(render=False)
        lifted, _ = tube_prim.get_world_pose()
        tail = []
        for _ in range(240):
            left.set_world_pose(position=[-0.0150, 0.0, 0.21033])
            right.set_world_pose(position=[0.0150, 0.0, 0.21033])
            world.step(render=False)
            tail.append([float(v) for v in tube_prim.get_world_pose()[0]])
        final = tail[-1]
        initial_xyz = [float(v) for v in initial]
        closed_xyz = [float(v) for v in closed]
        lifted_xyz = [float(v) for v in lifted]
        lift_distance = final[2] - initial_xyz[2]
        hold_tail_motion = math.dist(tail[0], tail[-1])
        hold_vertical_motion = abs(tail[-1][2] - tail[0][2])
        hold_lateral_motion = math.hypot(
            tail[-1][0] - tail[0][0], tail[-1][1] - tail[0][1]
        )
        lateral_error = math.hypot(final[0], final[1])
        passed = (
            lift_distance >= 0.09
            and hold_vertical_motion <= 0.003
            and hold_lateral_motion <= 0.008
            and lateral_error <= 0.01
            and final[2] >= lifted_xyz[2] - 0.003
        )
        report = {
            "schema_version": "aan.task11_r7_tube_grasp_qualification.v1",
            "status": "pass" if passed else "blocked",
            "runtime": "isaac41",
            "method": "kinematic_parallel_jaws_physical_contact_no_tube_pose_write",
            "observations": {
                "initial_xyz_m": initial_xyz,
                "after_close_xyz_m": closed_xyz,
                "after_lift_xyz_m": lifted_xyz,
                "final_xyz_m": final,
                "lift_distance_m": lift_distance,
                "hold_tail_motion_m": hold_tail_motion,
                "hold_vertical_motion_m": hold_vertical_motion,
                "hold_lateral_motion_m": hold_lateral_motion,
                "lateral_error_m": lateral_error,
                "tube_transform_write_count": 0,
            },
            "claims": {
                "fixed_candidate_close_lift_hold": passed,
                "physical_contact": True,
                "lift2_geometry_proxy": True,
                "true_lift2_robot": False,
                "robot_policy_success": False,
            },
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        manifest_path = package / "evidence/manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["overall_status"] = "pass" if passed else "blocked"
        manifest["blocked_reasons"] = [] if passed else ["close_lift_hold_failed"]
        manifest["claims"]["fixed_candidate_close_lift_hold"] = passed
        manifest["runtime_qualification"] = "evidence/grasp_qualification/report.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
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
