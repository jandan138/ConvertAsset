#!/usr/bin/env python3
"""Qualify the 29.77 mm magnetic stir bar in Isaac Sim 4.1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ENTRY = "/World/MagneticStirBar"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()

    original_argv = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = original_argv
    try:
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.prims import RigidPrim
        from pxr import Gf, UsdGeom, UsdPhysics

        context = omni.usd.get_context()
        asset = package / "asset.usd"
        if not context.open_stage(str(asset)):
            raise RuntimeError(f"cannot open {asset}")
        for _ in range(40):
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        root = UsdGeom.Xformable(stage.GetPrimAtPath(ENTRY))
        translate = root.AddTranslateOp()
        translate.Set(Gf.Vec3d(0.0, 0.0, 0.04))

        floor = UsdGeom.Cube.Define(stage, "/World/__qualification/floor")
        floor.CreateSizeAttr(1.0)
        UsdGeom.Xformable(floor).AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.005))
        UsdGeom.Xformable(floor).AddScaleOp().Set(Gf.Vec3f(0.5, 0.5, 0.01))
        UsdPhysics.CollisionAPI.Apply(floor.GetPrim())
        physics = UsdPhysics.Scene.Define(stage, "/World/__qualification/physicsScene")
        physics.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
        physics.CreateGravityMagnitudeAttr(9.81)

        world = World(
            stage_units_in_meters=1.0,
            physics_prim_path=str(physics.GetPath()),
            set_defaults=False,
            physics_dt=1 / 120,
            rendering_dt=1 / 120,
        )
        bar = world.scene.add(RigidPrim(prim_path=ENTRY, name="stir_bar_29_77"))
        world.reset()
        initial = [float(value) for value in bar.get_world_pose()[0]]
        tail_positions = []
        for step in range(600):
            world.step(render=False)
            if step >= 480:
                tail_positions.append(
                    [float(value) for value in bar.get_world_pose()[0]]
                )
        final = tail_positions[-1]
        motion = abs(initial[2] - final[2])
        tail_span = max(position[2] for position in tail_positions) - min(
            position[2] for position in tail_positions
        )
        velocity = [float(value) for value in bar.get_linear_velocity()]
        stable_support = (
            -0.001 <= final[2] <= 0.01
            and tail_span <= 0.001
            and sum(value * value for value in velocity) ** 0.5 <= 0.02
        )
        root_motion = motion >= 0.01
        passed = stable_support and root_motion
        report = {
            "schema_version": "aan.magnetic_stir_bar_runtime_qualification.v1",
            "status": "pass" if passed else "blocked",
            "runtime": "isaac41",
            "method": "free_drop_to_static_support",
            "observations": {
                "initial_xyz_m": initial,
                "final_xyz_m": final,
                "root_translation_m": motion,
                "tail_vertical_span_m": tail_span,
                "final_linear_velocity_m_s": velocity,
            },
            "claims": {
                "stable_support": stable_support,
                "root_motion": root_motion,
                "robot_grasp_success": False,
                "task_success": False,
            },
        }
        report_path = package / "evidence/runtime_qualification/report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

        manifest_path = package / "evidence/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["overall_status"] = report["status"]
        manifest["blocked_reasons"] = [] if passed else [
            "isaac41_runtime_qualification_failed"
        ]
        manifest["runtime_qualification"] = {
            "runtime": "isaac41",
            "report": "evidence/runtime_qualification/report.json",
            "method": report["method"],
        }
        manifest["claims"]["isaac41_stable_support"] = stable_support
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if passed else 1
    except BaseException:
        import traceback

        traceback.print_exc()
        return 2
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
