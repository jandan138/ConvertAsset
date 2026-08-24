#!/usr/bin/env python3
"""Qualify LABSPIN X8 r5 preview assembly and first-step continuity."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import traceback


ROOT = "/World/Centrifuge"
MAXIMUM_FIRST_STEP_JUMP_M = 0.001
LINK_JOINTS = {
    "lid_link": "lid_hinge_joint",
    "rotor_link": "rotor_spin_joint",
    "encoder_link": "encoder_joint",
    "start_button_link": "start_button_joint",
    "stop_button_link": "stop_button_joint",
    "lid_open_button_link": "lid_open_button_joint",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = original
    try:
        import carb
        import omni.physx.bindings._physx as pb
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from pxr import UsdGeom, UsdPhysics

        context = omni.usd.get_context()
        if not context.open_stage(str(args.asset.resolve())):
            raise RuntimeError(f"cannot open {args.asset}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        stage = context.get_stage()
        settings = carb.settings.get_settings()
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)

        def xyz(path: str) -> list[float]:
            point = UsdGeom.XformCache().GetLocalToWorldTransform(
                stage.GetPrimAtPath(path)
            ).ExtractTranslation()
            return [float(value) for value in point]

        expected = {}
        before = {}
        residuals = {}
        for link_name, joint_name in LINK_JOINTS.items():
            link_path = f"{ROOT}/{link_name}"
            joint = UsdPhysics.Joint.Get(stage, f"{ROOT}/{joint_name}")
            target = joint.GetLocalPos0Attr().Get()
            expected[link_name] = [float(value) for value in target]
            before[link_name] = xyz(link_path)
            residuals[link_name] = sum(
                (before[link_name][index] - expected[link_name][index]) ** 2
                for index in range(3)
            ) ** 0.5
        static_rest_pose_assembled = max(residuals.values()) <= 0.0001

        world = World(stage_units_in_meters=1.0, physics_dt=1 / 120, rendering_dt=1 / 120)
        world.scene.add(Articulation(ROOT, name="labspin_r5_rest_pose"))
        world.reset()
        after_reset = {
            name: xyz(f"{ROOT}/{name}") for name in LINK_JOINTS
        }
        for _ in range(10):
            world.step(render=False)
        after = {name: xyz(f"{ROOT}/{name}") for name in LINK_JOINTS}
        reset_jump = {
            name: sum(
                (after_reset[name][index] - before[name][index]) ** 2
                for index in range(3)
            ) ** 0.5
            for name in LINK_JOINTS
        }
        ten_step_jump = {
            name: sum(
                (after[name][index] - before[name][index]) ** 2
                for index in range(3)
            ) ** 0.5
            for name in LINK_JOINTS
        }
        maximum_first_step_jump_m = max(
            max(reset_jump.values()), max(ten_step_jump.values())
        )
        first_step_pose_continuity = (
            maximum_first_step_jump_m <= MAXIMUM_FIRST_STEP_JUMP_M
        )
        passed = static_rest_pose_assembled and first_step_pose_continuity
        report = {
            "schema_version": "aan.labspin_x8_r5_rest_pose_qualification.v1",
            "status": "pass" if passed else "blocked",
            "runtime": "isaac41",
            "observations": {
                "expected_link_xyz_m": expected,
                "authored_link_xyz_m": before,
                "constraint_residual_m": residuals,
                "reset_jump_m": reset_jump,
                "ten_step_jump_m": ten_step_jump,
                "maximum_first_step_jump_m": maximum_first_step_jump_m,
            },
            "claims": {
                "static_rest_pose_assembled": static_rest_pose_assembled,
                "first_step_pose_continuity": first_step_pose_continuity,
                "robot_policy_success": False,
                "task11_success": False,
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
        app.close()


if __name__ == "__main__":
    try:
        code = main()
    except BaseException:
        traceback.print_exc()
        code = 2
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
