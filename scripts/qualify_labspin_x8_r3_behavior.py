#!/usr/bin/env python3
"""Contact-press qualification for the LABSPIN X8 r3 embedded graph."""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--asset", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--root", default="/World/Centrifuge")
    a = p.parse_args()
    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True})
    sys.argv = original
    try:
        import numpy as np
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from omni.isaac.core.utils.types import ArticulationAction
        from pxr import Gf, UsdGeom, UsdPhysics

        context = omni.usd.get_context()
        context.open_stage(str(a.asset.resolve()))
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        cube = UsdGeom.Cube.Define(stage, "/World/__task11_probe/button_pusher")
        cube.CreateSizeAttr(1.0)
        UsdGeom.Xformable(cube).AddTranslateOp().Set(Gf.Vec3d(0.194, -0.305, 0.198))
        UsdGeom.Xformable(cube).AddScaleOp().Set(Gf.Vec3f(0.04, 0.02, 0.04))
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        rb = UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
        rb.CreateKinematicEnabledAttr(True)
        world = World(
            stage_units_in_meters=1.0, physics_dt=1 / 120, rendering_dt=1 / 120
        )
        art = world.scene.add(Articulation(a.root, name="labspin_r3"))
        world.reset()
        for _ in range(60):
            world.step(render=False)
        names = list(art.dof_names)
        idx = {n: i for i, n in enumerate(names)}
        if not all(
            n in idx
            for n in ("lid_open_button_joint", "lid_hinge_joint", "rotor_spin_joint")
        ):
            raise RuntimeError(names)
        art.apply_action(
            ArticulationAction(
                joint_positions=np.asarray([0.0025]),
                joint_indices=np.asarray([idx["lid_open_button_joint"]]),
            )
        )
        for _ in range(120):
            world.step(render=False)
        pressed = float(art.get_joint_positions()[idx["lid_open_button_joint"]])
        art.apply_action(
            ArticulationAction(
                joint_positions=np.asarray([0.0]),
                joint_indices=np.asarray([idx["lid_open_button_joint"]]),
            )
        )
        for _ in range(360):
            world.step(render=False)
        opened = float(art.get_joint_positions()[idx["lid_hinge_joint"]])
        for _ in range(240):
            world.step(render=False)
        held = float(art.get_joint_positions()[idx["lid_hinge_joint"]])
        passed = pressed >= 0.0021 and opened <= -1.30 and held <= -1.25
        report = {
            "schema_version": "aan.labspin_x8_lid_behavior_qualification.v1",
            "status": "pass" if passed else "blocked",
            "method": "button_drive_target_no_direct_button_or_lid_joint_state_write",
            "runtime": "isaac41",
            "runtime_dof_names": names,
            "observations": {
                "button_pressed_m": pressed,
                "lid_opened_rad": opened,
                "lid_held_after_release_rad": held,
            },
            "claims": {
                "button_causes_lid_open": passed,
                "contact_press_qualified": False,
                "lid_remains_open_after_release": passed,
                "manual_close_and_latch": False,
                "rotor_open_interlock": False,
                "robot_policy_success": False,
                "task11_success": False,
            },
        }
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0 if passed else 1
    except BaseException:
        import traceback

        traceback.print_exc()
        return 2
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
