#!/usr/bin/env python3
"""Qualify true geometry-contact screw motion in Isaac Sim 4.1."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import traceback
from typing import Any


BODY = "/World/TubeBody"
CAP = "/World/Cap"
PHYSICS_HZ = 240
START_Z_M = 0.1092
ANGULAR_SPEED_RAD_S = 3.0
DOWN_FORCE_N = 0.001


def classify_thread_result(
    *,
    control_descent_m: float,
    forward_descent_m: float,
    reverse_rise_m: float,
    maximum_radial_offset_m: float,
    maximum_tilt_deg: float,
    hard_errors: list[str],
) -> dict[str, Any]:
    checks = {
        "preload_only_stable": control_descent_m <= 0.0005,
        "rotation_drives_descent": forward_descent_m >= 0.002,
        "reverse_rotation_drives_rise": reverse_rise_m >= 0.002,
        "coaxial": maximum_radial_offset_m <= 0.0005,
        "upright": maximum_tilt_deg <= 5.0,
        "no_hard_errors": not hard_errors,
    }
    return {
        "overall_status": "pass" if all(checks.values()) else "blocked",
        "checks": checks,
    }


def _tilt_deg(quat: Any) -> float:
    w, x, y, z = map(float, quat)
    # z component of the local +Z axis after quaternion rotation.
    zz = 1.0 - 2.0 * (x * x + y * y)
    return math.degrees(math.acos(max(-1.0, min(1.0, zz))))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    from isaacsim import SimulationApp

    saved = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = saved
    try:
        import carb
        import numpy as np
        import omni.kit.app
        import omni.physx
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.prims import RigidPrimView
        from pxr import Gf, Sdf, UsdPhysics

        settings = carb.settings.get_settings()
        log_path = Path(str(settings.get("/log/file")))
        log_offset = log_path.stat().st_size if log_path.exists() else 0
        context = omni.usd.get_context()
        if not context.open_stage(str(args.assembly.resolve())):
            raise RuntimeError("could not open threaded assembly")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(30):
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        body = stage.GetPrimAtPath(BODY)
        cap = stage.GetPrimAtPath(CAP)
        if not body.IsValid() or not cap.IsValid():
            raise RuntimeError("threaded assembly entries did not compose")
        UsdPhysics.RigidBodyAPI(body).CreateKinematicEnabledAttr().Set(True)
        UsdPhysics.RigidBodyAPI(cap).CreateKinematicEnabledAttr().Set(False)
        # Ideal coaxial gripper guide: lock X/Y and tilt, leave Z translation
        # and Z rotation free. This is deliberately not a screw/helical joint;
        # any axial motion must still come from mesh contact.
        guide = UsdPhysics.Joint.Define(stage, "/World/__ThreadCoaxialGuide")
        guide.CreateBody1Rel().SetTargets([CAP])
        guide.CreateLocalPos0Attr().Set(Gf.Vec3f(0.0))
        guide.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0))
        guide.CreateLocalRot0Attr().Set(Gf.Quatf(1.0))
        guide.CreateLocalRot1Attr().Set(Gf.Quatf(1.0))
        for axis in ("transX", "transY", "rotX", "rotY"):
            limit = UsdPhysics.LimitAPI.Apply(guide.GetPrim(), axis)
            limit.CreateLowAttr(0.0)
            limit.CreateHighAttr(0.0)
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
        ).Set(PHYSICS_HZ)

        world = World(
            stage_units_in_meters=1.0,
            physics_prim_path="/World/PhysicsScene",
            set_defaults=False,
            backend="numpy",
            device="cpu",
            physics_dt=1.0 / PHYSICS_HZ,
            rendering_dt=1.0 / PHYSICS_HZ,
        )
        cap_view = RigidPrimView(CAP, name="threaded_cap")
        world.scene.add(cap_view)
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        world.reset()
        for _ in range(30):
            world.step(render=False)

        identity = np.asarray([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
        zero = np.zeros((1, 3), dtype=np.float32)
        preload = np.asarray([[0.0, 0.0, -DOWN_FORCE_N]], dtype=np.float32)

        def pose():
            positions, orientations = cap_view.get_world_poses()
            p = np.asarray(positions[0], dtype=float)
            q = np.asarray(orientations[0], dtype=float)
            return p, q

        def prepare():
            cap_view.set_world_poses(
                positions=np.asarray([[0.0, 0.0, START_Z_M]], dtype=np.float32),
                orientations=identity,
            )
            cap_view.set_linear_velocities(zero)
            cap_view.set_angular_velocities(zero)
            world.step(render=False)
            return pose()

        def drive(sign: float, seconds: float):
            samples = []
            angular = np.asarray(
                [[0.0, 0.0, sign * ANGULAR_SPEED_RAD_S]], dtype=np.float32
            )
            for _ in range(round(seconds * PHYSICS_HZ)):
                cap_view.apply_forces(preload)
                cap_view.set_angular_velocities(angular)
                world.step(render=False)
                samples.append(pose())
            return samples

        settled_control, _ = prepare()
        control_samples = drive(0.0, 1.5)
        control_final = control_samples[-1][0]
        control_descent = max(0.0, float(settled_control[2] - control_final[2]))

        candidates = []
        for sign in (1.0, -1.0):
            start, _ = prepare()
            samples = drive(sign, 5.0)
            final = samples[-1][0]
            candidates.append((float(start[2] - final[2]), sign, samples, start))
        forward_descent, forward_sign, forward_samples, forward_start = max(
            candidates, key=lambda item: item[0]
        )
        forward_final = forward_samples[-1][0]
        reverse_samples = drive(-forward_sign, 5.0)
        reverse_final = reverse_samples[-1][0]
        reverse_rise = max(0.0, float(reverse_final[2] - forward_final[2]))
        all_samples = control_samples + forward_samples + reverse_samples
        max_radial = max(math.hypot(float(p[0]), float(p[1])) for p, _q in all_samples)
        max_tilt = max(_tilt_deg(q) for _p, q in all_samples)

        log = log_path.read_text(errors="replace")[log_offset:] if log_path.exists() else ""
        markers = ("CUDA error", "illegal memory access", "PhysX error")
        hard = list(
            dict.fromkeys(
                line for line in log.splitlines() if any(m in line for m in markers)
            )
        )
        result = {
            "schema_version": "aan.threaded_tube15_contact_observation.v1",
            "runtime": str(omni.kit.app.get_app().get_app_version()),
            "protocol": "dynamic_cap_angular_velocity_plus_down_force_no_z_command",
            "parameters": {
                "physics_hz": PHYSICS_HZ,
                "start_z_m": START_Z_M,
                "angular_speed_rad_s": ANGULAR_SPEED_RAD_S,
                "down_force_n": DOWN_FORCE_N,
            },
            "measurements": {
                "control_descent_m": control_descent,
                "forward_sign": forward_sign,
                "forward_descent_m": forward_descent,
                "reverse_rise_m": reverse_rise,
                "maximum_radial_offset_m": max_radial,
                "maximum_tilt_deg": max_tilt,
                "forward_start_z_m": float(forward_start[2]),
                "forward_final_z_m": float(forward_final[2]),
                "reverse_final_z_m": float(reverse_final[2]),
            },
            "hard_errors": hard,
        }
        result.update(
            classify_thread_result(
                control_descent_m=control_descent,
                forward_descent_m=forward_descent,
                reverse_rise_m=reverse_rise,
                maximum_radial_offset_m=max_radial,
                maximum_tilt_deg=max_tilt,
                hard_errors=hard,
            )
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)
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
    import os

    os._exit(code)
