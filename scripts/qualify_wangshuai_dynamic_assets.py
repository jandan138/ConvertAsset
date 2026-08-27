#!/usr/bin/env python3
"""Qualify the Wangshuai dynamic container assets in Isaac Sim 4.1.

Each invocation is one isolated cold start.  The worker first proves that the
asset responds to gravity, then reloads a fixture where the same dynamic body
is attached to a kinematic carrier and follows a 10 cm transport.  The carrier
is test equipment; the package root itself is never made kinematic.
"""

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


ASSETS = {
    "tube": {
        "package": "tube15_threaded_liquid_dynamic",
        "entry_prim": "/Tube15ThreadedLiquidReady",
        "height": 0.101,
    },
    "cap": {
        "package": "tube15_threaded_closed_cap_dynamic",
        "entry_prim": "/Tube15ThreadedClosedCap",
        "height": 0.01874,
    },
    "funnel": {
        "package": "funnel_small_v2_liquid_dynamic",
        "entry_prim": "/FunnelSmallV2LiquidReady",
        "height": 0.12,
    },
    "assembly": {
        "package": "threaded_tube15_red_closed_assembly",
        "entry_prim": "/ThreadedTube15RedClosed",
        "height": 0.1168,
    },
}


def classify_observation(
    *,
    initial_z: float,
    minimum_z: float,
    final_speed: float,
    maximum_abs_coordinate: float,
    transport_distance: float,
    transport_error: float,
    hard_errors: list[str],
) -> dict[str, Any]:
    checks = {
        "gravity_motion": initial_z - minimum_z >= 0.025,
        "finite_bounded_state": math.isfinite(maximum_abs_coordinate)
        and maximum_abs_coordinate <= 10.0,
        "settled_or_resting": math.isfinite(final_speed) and final_speed <= 0.08,
        "dynamic_fixed_joint_transport": transport_distance >= 0.095,
        "transport_tracking": transport_error <= 0.012,
        "no_hard_errors": not hard_errors,
    }
    return {
        "overall_status": "pass" if all(checks.values()) else "blocked",
        "checks": checks,
    }


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _physics_scene(stage: Any) -> None:
    from pxr import Sdf, UsdPhysics

    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr((0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr(9.81)
    prim = scene.GetPrim()
    prim.CreateAttribute("physxScene:broadphaseType", Sdf.ValueTypeNames.Token).Set(
        "GPU"
    )
    prim.CreateAttribute(
        "physxScene:enableGPUDynamics", Sdf.ValueTypeNames.Bool
    ).Set(True)
    prim.CreateAttribute("physxScene:solverType", Sdf.ValueTypeNames.Token).Set("TGS")
    prim.CreateAttribute(
        "physxScene:timeStepsPerSecond", Sdf.ValueTypeNames.UInt
    ).Set(120)


def _make_fixture(
    package: Path, entry_prim: str, fixture: Path, *, transport: bool
) -> None:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    stage = Usd.Stage.CreateNew(str(fixture))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    body = UsdGeom.Xform.Define(stage, "/World/Asset")
    body.GetPrim().GetReferences().AddReference(str(package), entry_prim)
    body.AddTranslateOp().Set((0.0, 0.0, 0.12))
    if transport:
        carrier = UsdGeom.Xform.Define(stage, "/World/Carrier")
        carrier.AddTranslateOp().Set((0.0, 0.0, 0.12))
        rigid = UsdPhysics.RigidBodyAPI.Apply(carrier.GetPrim())
        rigid.CreateRigidBodyEnabledAttr(True)
        rigid.CreateKinematicEnabledAttr(True)
        joint = UsdPhysics.FixedJoint.Define(stage, "/World/TransportJoint")
        joint.CreateBody0Rel().SetTargets([carrier.GetPath()])
        joint.CreateBody1Rel().SetTargets([body.GetPath()])
        joint.CreateLocalPos0Attr(Gf.Vec3f(0.0))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0.0))
        joint.CreateLocalRot0Attr(Gf.Quatf(1.0))
        joint.CreateLocalRot1Attr(Gf.Quatf(1.0))
    else:
        plane = UsdGeom.Plane.Define(stage, "/World/Ground")
        plane.CreateAxisAttr(UsdGeom.Tokens.z)
        plane.CreateDoubleSidedAttr(True)
        UsdPhysics.CollisionAPI.Apply(plane.GetPrim())
    _physics_scene(stage)
    stage.GetRootLayer().Save()


def _hard_errors(log: str) -> list[str]:
    markers = (
        "CUDA error",
        "illegal memory access",
        "PhysX error",
        "Failed to cook",
        "Particles feature is only supported on GPU",
    )
    return [line.strip() for line in log.splitlines() if any(m in line for m in markers)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-set", type=Path, required=True)
    parser.add_argument("--asset", choices=tuple(ASSETS), required=True)
    parser.add_argument("--run-index", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    saved_argv = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = saved_argv
    try:
        import carb
        import omni.kit.app
        import omni.physx
        import omni.physx.bindings._physx as pb
        import omni.usd
        from omni.isaac.core import World
        from pxr import Gf, UsdGeom

        spec = ASSETS[args.asset]
        asset_set = args.asset_set.resolve()
        package = asset_set / "packages" / spec["package"] / "asset.usda"
        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        drop_fixture = out.parent / f"{args.asset}_drop_fixture.usda"
        transport_fixture = out.parent / f"{args.asset}_transport_fixture.usda"
        _make_fixture(package, spec["entry_prim"], drop_fixture, transport=False)
        _make_fixture(package, spec["entry_prim"], transport_fixture, transport=True)

        settings = carb.settings.get_settings()
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
        log_path = Path(str(settings.get("/log/file")))
        log_offset = log_path.stat().st_size if log_path.exists() else 0
        context = omni.usd.get_context()

        def open_world(path: Path) -> tuple[Any, Any]:
            if not context.open_stage(str(path)):
                raise RuntimeError(f"could not open {path}")
            while context.get_stage_loading_status()[2] > 0:
                app.update()
            for _ in range(10):
                app.update()
            world_obj = World(
                stage_units_in_meters=1.0,
                physics_prim_path="/World/PhysicsScene",
                set_defaults=False,
                physics_dt=1 / 120,
                rendering_dt=1 / 120,
            )
            omni.physx.get_physx_interface().overwrite_gpu_setting(1)
            world_obj.reset()
            return context.get_stage(), world_obj

        stage, world = open_world(drop_fixture)
        body = stage.GetPrimAtPath("/World/Asset")
        cap_local_before = None
        if args.asset == "assembly":
            cap_local_before = UsdGeom.Xformable(
                stage.GetPrimAtPath("/World/Asset/Cap")
            ).GetLocalTransformation()
        cache = UsdGeom.XformCache()
        initial = cache.GetLocalToWorldTransform(body).ExtractTranslation()
        minimum_z = float(initial[2])
        maximum_abs = max(abs(float(v)) for v in initial)
        previous = initial
        final_speed = float("inf")
        for _ in range(480):
            world.step(render=False)
            cache.Clear()
            point = cache.GetLocalToWorldTransform(body).ExtractTranslation()
            minimum_z = min(minimum_z, float(point[2]))
            maximum_abs = max(maximum_abs, *(abs(float(v)) for v in point))
            final_speed = math.sqrt(sum(((float(point[i]) - float(previous[i])) * 120) ** 2 for i in range(3)))
            previous = point
        cap_relative_pose_invariant = True
        if args.asset == "assembly":
            cap_local_after = UsdGeom.Xformable(
                stage.GetPrimAtPath("/World/Asset/Cap")
            ).GetLocalTransformation()
            cap_relative_pose_invariant = cap_local_after == cap_local_before

        stage, world = open_world(transport_fixture)
        body = stage.GetPrimAtPath("/World/Asset")
        carrier = UsdGeom.Xformable(stage.GetPrimAtPath("/World/Carrier"))
        op = carrier.GetOrderedXformOps()[0]
        cache = UsdGeom.XformCache()
        start = cache.GetLocalToWorldTransform(body).ExtractTranslation()
        for step in range(241):
            z = 0.12 + 0.10 * min(step / 120.0, 1.0)
            op.Set(Gf.Vec3d(0.0, 0.0, z))
            world.step(render=False)
        cache.Clear()
        end = cache.GetLocalToWorldTransform(body).ExtractTranslation()
        distance = float(end[2] - start[2])
        error = math.sqrt(sum((float(end[i]) - (float(start[i]) + (0.1 if i == 2 else 0.0))) ** 2 for i in range(3)))

        log = log_path.read_text(errors="replace")[log_offset:] if log_path.exists() else ""
        hard = _hard_errors(log)
        result = classify_observation(
            initial_z=float(initial[2]),
            minimum_z=minimum_z,
            final_speed=final_speed,
            maximum_abs_coordinate=maximum_abs,
            transport_distance=distance,
            transport_error=error,
            hard_errors=hard,
        )
        result["checks"]["cap_relative_pose_invariant"] = cap_relative_pose_invariant
        result["overall_status"] = (
            "pass" if all(result["checks"].values()) else "blocked"
        )
        report = {
            "schema_version": "aan.wangshuai_dynamic_rigid_run.v1",
            "overall_status": result["overall_status"],
            "asset": args.asset,
            "run_index": args.run_index,
            "runtime": {"name": "isaac41", "kit_version": str(omni.kit.app.get_app().get_app_version())},
            "package_sha256": _sha(package),
            "checks": result["checks"],
            "observations": {
                "initial_z_m": float(initial[2]),
                "minimum_z_m": minimum_z,
                "tail_speed_m_s": final_speed,
                "maximum_abs_coordinate_m": maximum_abs,
                "transport_distance_m": distance,
                "transport_tracking_error_m": error,
                "hard_errors": hard,
            },
            "claims": {
                "effective_kinematic": False,
                "gravity_response": result["checks"]["gravity_motion"],
                "dynamic_fixed_joint_transport": result["checks"]["dynamic_fixed_joint_transport"],
                "cap_relative_pose_invariant": cap_relative_pose_invariant,
                "robot_policy_success": False,
                "task_success": False,
                "benchmark_success": False,
            },
        }
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True), flush=True)
        return 0 if report["overall_status"] == "pass" else 2
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
