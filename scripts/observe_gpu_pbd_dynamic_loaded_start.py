#!/usr/bin/env python3
"""Isaac 4.1 worker for one GPU-PBD dynamic-loaded-start phase."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any


SOURCE = "/World/Transfer/Source"
TARGET = "/World/Transfer/Target"
PARTICLES = "/World/Transfer/ParticleSet"
SUPPORT = "/World/Support"
PHYSICS_HZ = 120
OBSERVATION_STEPS = 960
TAIL_STEPS = 120


def _hard_runtime_errors(text: str) -> list[str]:
    markers = (
        "failed to cook GPU-compatible mesh",
        "Non-GPU-compatible convex mesh",
        "Particles feature is only supported on GPU",
        "CUDA error",
        "illegal memory access",
    )
    return [
        line.strip()
        for line in text.splitlines()
        if any(marker in line for marker in markers)
    ]


def _matrix(position: Any, orientation_wxyz: Any, np: Any) -> Any:
    w, x, y, z = [float(value) for value in orientation_wxyz]
    rotation = np.asarray(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)],
            [2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)],
            [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=float,
    )
    value = np.eye(4)
    value[:3, :3] = rotation
    value[3, :3] = position
    return value


def _tilt_deg(orientation_wxyz: Any, np: Any) -> float:
    rotation = _matrix(np.zeros(3), orientation_wxyz, np)[:3, :3]
    cosine = max(-1.0, min(1.0, float(rotation[2, 2])))
    return math.degrees(math.acos(cosine))


def _read_positions(stage: Any, np: Any) -> Any:
    prim = stage.GetPrimAtPath(PARTICLES)
    for name in ("points", "physxParticle:simulationPoints"):
        values = prim.GetAttribute(name).Get()
        if values is not None:
            return np.asarray(values, dtype=float)
    raise RuntimeError("particle positions unavailable")


def _inside_source(
    positions: Any,
    *,
    source_position: Any,
    source_orientation: Any,
    cavity: dict[str, Any],
    np: Any,
) -> Any:
    local = np.c_[positions, np.ones((len(positions), 1))] @ np.linalg.inv(
        _matrix(source_position, source_orientation, np)
    )
    return (
        (np.linalg.norm(local[:, :2], axis=1) <= float(cavity["radius_m"]))
        & (local[:, 2] >= float(cavity["floor_z_m"]))
        & (local[:, 2] <= float(cavity["rim_z_m"]))
    )


def _set_source_pose(stage: Any, pose: dict[str, Any], *, Gf: Any, UsdGeom: Any) -> None:
    prim = stage.GetPrimAtPath(SOURCE)
    prim.GetAttribute("xformOp:translate").Set(
        Gf.Vec3d(*[float(value) for value in pose["xyz_m"]])
    )
    orientation = [float(value) for value in pose["wxyz"]]
    xformable = UsdGeom.Xformable(prim)
    orient = prim.GetAttribute("xformOp:orient")
    if not orient:
        op = xformable.AddOrientOp(UsdGeom.XformOp.PrecisionFloat)
        orient = op.GetAttr()
    orient.Set(Gf.Quatf(orientation[0], *orientation[1:]))


def _set_particle_positions(stage: Any, positions: Any, *, Vt: Any) -> None:
    prim = stage.GetPrimAtPath(PARTICLES)
    values = Vt.Vec3fArray.FromNumpy(positions.astype("float32"))
    prim.GetAttribute("physxParticle:simulationPoints").Set(values)
    prim.GetAttribute("points").Set(values)
    zeros = Vt.Vec3fArray.FromNumpy(positions.astype("float32") * 0.0)
    prim.GetAttribute("velocities").Set(zeros)


def _run(args: argparse.Namespace) -> dict[str, Any]:
    from isaacsim import SimulationApp

    parsed = sys.argv
    sys.argv = [sys.argv[0]]
    try:
        app = SimulationApp(
            {
                "headless": True,
                "multi_gpu": False,
                "renderer": "RayTracedLighting",
                "width": 960,
                "height": 540,
            }
        )
    finally:
        sys.argv = parsed
    try:
        import carb
        import numpy as np
        import omni.kit.app
        import omni.physx
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.prims import RigidPrimView
        import omni.physx.bindings._physx as pb
        from pxr import Gf, UsdGeom, Vt

        settings = carb.settings.get_settings()
        log_path = Path(str(settings.get("/log/file")))
        log_offset = log_path.stat().st_size if log_path.exists() else 0
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        settings.set(pb.SETTING_UPDATE_PARTICLES_TO_USD, True)
        settings.set(pb.SETTING_UPDATE_VELOCITIES_TO_USD, True)
        settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
        settings.set_bool("/physics/suppressReadback", False)
        context = omni.usd.get_context()
        if not context.open_stage(str(args.scene.resolve())):
            raise RuntimeError(f"could not open {args.scene}")
        for _ in range(40):
            app.update()
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError(f"could not open {args.scene}")
        fixture_path = args.scene.resolve().with_name("transfer_fixture_profile.json")
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        cavity = fixture["source"]["cavity"]
        initial = fixture["source"]["initial_xyz_m"]
        target = stage.GetPrimAtPath(TARGET)
        target.SetActive(False)
        source = stage.GetPrimAtPath(SOURCE)
        particles = stage.GetPrimAtPath(PARTICLES)
        support = stage.GetPrimAtPath(SUPPORT)
        support.GetAttribute("xformOp:translate").Set(
            Gf.Vec3d(0.0, 0.0, float(args.support_plane_z_m) - 0.01)
        )

        upright = {"xyz_m": [initial[0], initial[1], args.support_plane_z_m], "wxyz": [1, 0, 0, 0]}
        pose = (
            json.loads(args.pose.read_text(encoding="utf-8"))
            if args.pose is not None
            else upright
        )
        _set_source_pose(stage, pose, Gf=Gf, UsdGeom=UsdGeom)
        source.GetAttribute("physics:kinematicEnabled").Set(args.mode == "pre-settle")
        if args.mode == "dry-settle":
            particles.SetActive(False)
        else:
            authored = np.asarray(
                particles.GetAttribute("physxParticle:simulationPoints").Get(),
                dtype=float,
            )
            if args.mode == "pre-settle":
                authored[:, 2] += float(args.support_plane_z_m)
                _set_particle_positions(stage, authored, Vt=Vt)
            else:
                state = json.loads(args.particle_state.read_text(encoding="utf-8"))
                local = np.asarray(state["positions"], dtype=float)
                world = np.c_[local, np.ones((len(local), 1))] @ _matrix(
                    pose["xyz_m"], pose["wxyz"], np
                )
                _set_particle_positions(stage, world[:, :3], Vt=Vt)

        world = World(
            stage_units_in_meters=1.0,
            physics_prim_path="/World/PhysicsScene",
            set_defaults=False,
            backend="numpy",
            device="cpu",
            physics_dt=1 / PHYSICS_HZ,
            rendering_dt=1 / PHYSICS_HZ,
        )
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        source_view = RigidPrimView(SOURCE, name="dynamic_loaded_source")
        world.scene.add(source_view)
        world.reset()

        root_positions = []
        root_orientations = []
        outside_counts = []
        for _ in range(OBSERVATION_STEPS):
            world.step(render=False)
            positions, orientations = source_view.get_world_poses()
            position = np.asarray(positions[0], dtype=float)
            orientation = np.asarray(orientations[0], dtype=float)
            root_positions.append(position)
            root_orientations.append(orientation)
            if args.mode != "dry-settle":
                live = _read_positions(stage, np)
                inside = _inside_source(
                    live,
                    source_position=position,
                    source_orientation=orientation,
                    cavity=cavity,
                    np=np,
                )
                outside_counts.append(int(len(live) - int(inside.sum())))

        tail_positions = np.asarray(root_positions[-TAIL_STEPS:], dtype=float)
        stable_xyz = np.median(tail_positions, axis=0)
        stable_orientation = np.median(
            np.asarray(root_orientations[-TAIL_STEPS:], dtype=float), axis=0
        )
        stable_orientation /= np.linalg.norm(stable_orientation)
        tail_drift = float(
            np.linalg.norm(tail_positions - stable_xyz[None, :], axis=1).max()
        )
        maximum_tilt = max(_tilt_deg(value, np) for value in root_orientations)
        errors = _hard_runtime_errors(
            log_path.read_text(encoding="utf-8", errors="replace")[log_offset:]
            if log_path.exists()
            else ""
        )
        runtime = {
            "kit_version": str(omni.kit.app.get_app().get_app_version()),
            "runtime": "isaac41",
        }

        if args.mode == "dry-settle":
            result = {
                "schema_version": "aan.gpu_pbd_dry_settle_observation.v1",
                "run_index": args.run_index,
                "stable_pose": {
                    "xyz_m": stable_xyz.tolist(),
                    "wxyz": stable_orientation.tolist(),
                },
                "entry_root_tail_drift_m": tail_drift,
                "maximum_entry_root_tilt_deg": maximum_tilt,
                "hard_runtime_errors": errors,
                "runtime": runtime,
                "overall_status": (
                    "pass"
                    if tail_drift <= 0.001 and maximum_tilt <= 2.0 and not errors
                    else "blocked"
                ),
            }
        elif args.mode == "pre-settle":
            live = _read_positions(stage, np)
            source_local = np.c_[live, np.ones((len(live), 1))] @ np.linalg.inv(
                _matrix(stable_xyz, stable_orientation, np)
            )
            result = {
                "schema_version": "aan.gpu_pbd_source_local_particle_state.v1",
                "coordinate_space": "source_entry_root_local",
                "particle_count": int(len(live)),
                "positions": source_local[:, :3].tolist(),
                "outside_source_count": max(outside_counts),
                "source_pose_used": {
                    "xyz_m": [float(value) for value in pose["xyz_m"]],
                    "wxyz": [float(value) for value in pose["wxyz"]],
                },
                "immutable_particle_parameters": fixture["liquid_parameters"],
                "claim_boundary": "Static pre-settle initialization only.",
                "runtime": runtime,
            }
        else:
            result = {
                "schema_version": "aan.gpu_pbd_dynamic_loaded_start_observation.v1",
                "run_index": args.run_index,
                "particle_count": len(outside_counts)
                and int(len(_read_positions(stage, np))),
                "maximum_outside_source_count": max(outside_counts),
                "entry_root_tail_drift_m": tail_drift,
                "maximum_entry_root_tilt_deg": maximum_tilt,
                "hard_runtime_errors": errors,
                "runtime": runtime,
                "overall_status": "observed",
            }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return result
    finally:
        app.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument(
        "--mode", required=True, choices=("dry-settle", "pre-settle", "validate")
    )
    parser.add_argument("--support-plane-z-m", required=True, type=float)
    parser.add_argument("--pose", type=Path)
    parser.add_argument("--particle-state", type=Path)
    parser.add_argument("--run-index", type=int)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.mode != "dry-settle" and args.pose is None:
        parser.error("--pose is required outside dry-settle mode")
    if args.mode == "validate" and args.particle_state is None:
        parser.error("--particle-state is required in validate mode")
    _run(args)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
