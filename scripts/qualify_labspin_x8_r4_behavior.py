#!/usr/bin/env python3
"""Qualify LABSPIN X8 r4 through physical contact probes in Isaac Sim 4.1."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import sys
from pathlib import Path


OPEN_CENTER = (0.194, -0.263, 0.198)
STOP_CENTER = (0.205, -0.2675, 0.145)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", default="/World/Centrifuge")
    args = parser.parse_args()

    original_argv = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True})
    sys.argv = original_argv
    try:
        import numpy as np
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from omni.isaac.core.utils.types import ArticulationAction
        from pxr import Gf, UsdGeom, UsdPhysics

        context = omni.usd.get_context()
        context.open_stage(str(args.asset.resolve()))
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())

        def make_pusher(name: str, center: tuple[float, float, float]):
            path = f"/World/__task11_probe/{name}"
            cube = UsdGeom.Cube.Define(stage, path)
            cube.CreateSizeAttr(1.0)
            translate = UsdGeom.Xformable(cube).AddTranslateOp()
            translate.Set(Gf.Vec3d(center[0], center[1] - 0.035, center[2]))
            UsdGeom.Xformable(cube).AddScaleOp().Set(Gf.Vec3f(0.045, 0.018, 0.014))
            UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
            body = UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
            body.CreateKinematicEnabledAttr(True)
            return translate

        open_pusher = make_pusher("open_pusher", OPEN_CENTER)
        stop_pusher = make_pusher("stop_pusher", STOP_CENTER)

        world = World(
            stage_units_in_meters=1.0,
            physics_dt=1 / 120,
            rendering_dt=1 / 120,
        )
        articulation = world.scene.add(Articulation(args.root, name="labspin_r4"))
        world.reset()
        for _ in range(90):
            world.step(render=False)

        names = list(articulation.dof_names)
        index = {name: i for i, name in enumerate(names)}
        required = {
            "lid_open_button_joint",
            "stop_button_joint",
            "lid_hinge_joint",
            "rotor_spin_joint",
        }
        if not required.issubset(index):
            raise RuntimeError(f"missing dofs: {required - set(index)}; got {names}")

        def positions() -> np.ndarray:
            return articulation.get_joint_positions().copy()

        def velocities() -> np.ndarray:
            return articulation.get_joint_velocities().copy()

        def move_pusher(op, center, pressed: bool, steps: int = 90) -> float:
            start_y = center[1] - 0.035
            end_y = center[1] + 0.003 if pressed else start_y
            initial_y = float(op.Get()[1])
            maximum = -1.0
            button_name = (
                "lid_open_button_joint" if center == OPEN_CENTER else "stop_button_joint"
            )
            for step in range(steps):
                alpha = (step + 1) / steps
                y = initial_y + (end_y - initial_y) * alpha
                op.Set(Gf.Vec3d(center[0], y, center[2]))
                world.step(render=False)
                maximum = max(maximum, float(positions()[index[button_name]]))
            return maximum

        # Interlock phase: spin the rotor, contact-press OPEN, and require the
        # button itself to travel while the lid remains closed.
        articulation.apply_action(
            ArticulationAction(
                joint_velocities=np.asarray([8.0]),
                joint_indices=np.asarray([index["rotor_spin_joint"]]),
            )
        )
        for _ in range(180):
            world.step(render=False)
        rotor_during_press = abs(float(velocities()[index["rotor_spin_joint"]]))
        interlock_button_max = move_pusher(open_pusher, OPEN_CENTER, True)
        interlock_lid = float(positions()[index["lid_hinge_joint"]])
        move_pusher(open_pusher, OPEN_CENTER, False, steps=60)

        articulation.apply_action(
            ArticulationAction(
                joint_velocities=np.asarray([0.0]),
                joint_indices=np.asarray([index["rotor_spin_joint"]]),
            )
        )
        for _ in range(360):
            world.step(render=False)
            if abs(float(velocities()[index["rotor_spin_joint"]])) <= 0.05:
                break
        rotor_before_open = abs(float(velocities()[index["rotor_spin_joint"]]))

        # Functional phase: the same physical pusher presses OPEN at rest.
        contact_button_max = move_pusher(open_pusher, OPEN_CENTER, True)
        for _ in range(420):
            world.step(render=False)
        opened = float(positions()[index["lid_hinge_joint"]])
        move_pusher(open_pusher, OPEN_CENTER, False, steps=60)
        for _ in range(180):
            world.step(render=False)
        held = float(positions()[index["lid_hinge_joint"]])
        lid_state = stage.GetPrimAtPath(args.root).GetAttribute(
            "device:lidState"
        ).Get()

        # Shutdown phase: contact-press the existing red STOP control and read
        # the USD-authored observable state, without writing its joint state.
        stop_button_max = move_pusher(stop_pusher, STOP_CENTER, True)
        for _ in range(30):
            world.step(render=False)
        power_state = stage.GetPrimAtPath(args.root).GetAttribute(
            "device:powerState"
        ).Get()

        contact_ok = contact_button_max >= 0.0021
        open_ok = opened <= -1.30 and held <= -1.25 and lid_state == "open_hold"
        interlock_ok = (
            rotor_during_press > 0.1
            and interlock_button_max >= 0.0021
            and interlock_lid >= -0.05
            and rotor_before_open <= 0.1
        )
        shutdown_ok = stop_button_max >= 0.0021 and power_state == "off"
        passed = contact_ok and open_ok and interlock_ok and shutdown_ok
        report = {
            "schema_version": "aan.labspin_x8_r4_behavior_qualification.v1",
            "status": "pass" if passed else "blocked",
            "method": "kinematic_rigid_contact_pushers_no_direct_button_or_lid_joint_state_write",
            "runtime": "isaac41",
            "runtime_dof_names": names,
            "observations": {
                "rotor_during_interlock_press_rad_s": rotor_during_press,
                "interlock_open_button_max_m": interlock_button_max,
                "lid_during_interlock_press_rad": interlock_lid,
                "rotor_before_successful_open_rad_s": rotor_before_open,
                "contact_open_button_max_m": contact_button_max,
                "lid_opened_rad": opened,
                "lid_held_after_release_rad": held,
                "lid_state": lid_state,
                "contact_stop_button_max_m": stop_button_max,
                "power_state": power_state,
            },
            "claims": {
                "contact_press_qualified": contact_ok,
                "button_causes_lid_open": contact_ok and open_ok,
                "lid_remains_open_after_release": open_ok,
                "rotor_open_interlock": interlock_ok,
                "shutdown_causes_power_off": shutdown_ok,
                "manual_close_and_latch": False,
                "robot_policy_success": False,
                "task11_success": False,
            },
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

        package_root = args.asset.resolve().parent
        manifest_path = package_root / "evidence/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["package_id"] = "labspin_x8_centrifuge_task11_r4_isaac41"
        manifest["overall_status"] = "pass" if passed else "blocked"
        manifest["blocked_reasons"] = [] if passed else [
            "task11_r4_behavior_qualification_failed"
        ]
        manifest.setdefault("claims", {}).update(report["claims"])
        manifest["runtime_qualification"] = {
            "runtime": "isaac41",
            "report": "evidence/lid_behavior/report.json",
            "method": report["method"],
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )

        static_manifest_path = package_root / "evidence/task11_static_manifest.json"
        static_manifest = json.loads(static_manifest_path.read_text())
        static_manifest["status"] = "pass" if passed else "blocked"
        static_manifest["asset_usd_sha256"] = sha256(args.asset.read_bytes()).hexdigest()
        static_manifest["claims"] = report["claims"]
        static_manifest["runtime_qualification_report"] = (
            "evidence/lid_behavior/report.json"
        )
        static_manifest_path.write_text(
            json.dumps(static_manifest, indent=2, sort_keys=True) + "\n"
        )

        profile_path = package_root / "articulation/device_profile.json"
        profile = json.loads(profile_path.read_text())
        profile["buttons"]["lid_open_button"]["causal_lid_transition"] = (
            "contact_qualified" if contact_ok and open_ok else "blocked"
        )
        profile["buttons"]["shutdown_button"][
            "observable_power_off_transition"
        ] = "contact_qualified" if shutdown_ok else "blocked"
        profile["runtime_qualification"] = {
            "status": report["status"],
            "runtime": "isaac41",
            "report": "evidence/lid_behavior/report.json",
        }
        profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")
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
