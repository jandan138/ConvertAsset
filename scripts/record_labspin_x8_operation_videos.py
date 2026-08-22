#!/usr/bin/env python3
"""Record LABSPIN X8 scripted Isaac 4.1 insertion and low-speed videos."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


FPS = 24
PHYSICS_DT = 1.0 / 240.0
SUBSTEPS_PER_FRAME = 10
LID_CLOSED_RAD = 0.0
LID_OPEN_RAD = -1.30
CENTRIFUGE_ROOT = "/World/Centrifuge"
TUBE_PROBE_ROOT = "/World/TubeProbe"
SPIN_TUBE_ROOTS = ("/World/SpinTubeA", "/World/SpinTubeB")
WIDTH = 1920
HEIGHT = 1080


CAMERA_MAIN = {
    "target": (-0.03, -0.02, 0.24),
    "distance": 1.12,
    "elevation": 34.0,
    "azimuth": 0.0,
    "focal_mm": 36.0,
}
CAMERA_REVEAL = {
    "target": (-0.03, 0.005, 0.29),
    "distance": 0.62,
    "elevation": 64.0,
    "azimuth": 0.0,
    "focal_mm": 42.0,
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _smoothstep(value: float) -> float:
    t = min(1.0, max(0.0, value))
    return t * t * (3.0 - 2.0 * t)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp3(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return tuple(_lerp(a[index], b[index], t) for index in range(3))


def _lerp_camera(a: dict[str, Any], b: dict[str, Any], t: float) -> dict[str, Any]:
    return {
        "target": _lerp3(a["target"], b["target"], t),
        "distance": _lerp(a["distance"], b["distance"], t),
        "elevation": _lerp(a["elevation"], b["elevation"], t),
        "azimuth": _lerp(a["azimuth"], b["azimuth"], t),
        "focal_mm": _lerp(a["focal_mm"], b["focal_mm"], t),
    }


def build_insert_keyframes(*, aperture: tuple[float, float, float], bottom: tuple[float, float, float], axis_out: tuple[float, float, float]) -> list[dict[str, Any]]:
    park = (aperture[0] - 0.12, aperture[1] - 0.14, aperture[2] + 0.12)
    hover = tuple(aperture[index] + axis_out[index] * 0.005 for index in range(3))
    phases = [
        ("closed_hold", 12),
        ("lid_open", 36),
        ("open_hold", 12),
        ("tube_position", 36),
        ("tube_release", 54),
        ("inserted_hold", 12),
        ("socket_reveal", 20),
        ("reveal_hold", 12),
        ("reveal_return", 20),
        ("lid_close", 48),
        ("final_hold", 24),
    ]
    frames: list[dict[str, Any]] = []
    for phase, count in phases:
        for frame_index in range(count):
            t = _smoothstep(frame_index / (count - 1)) if count > 1 else 1.0
            if phase == "closed_hold":
                lid = LID_CLOSED_RAD
            elif phase == "lid_open":
                lid = _lerp(LID_CLOSED_RAD, LID_OPEN_RAD, t)
            elif phase == "lid_close":
                lid = _lerp(LID_OPEN_RAD, LID_CLOSED_RAD, t)
            elif phase == "final_hold":
                lid = LID_CLOSED_RAD
            else:
                lid = LID_OPEN_RAD
            if phase in {"closed_hold", "lid_open", "open_hold"}:
                position: tuple[float, float, float] | None = park
            elif phase == "tube_position":
                position = _lerp3(park, hover, t)
            else:
                position = None
            camera = CAMERA_MAIN
            if phase == "socket_reveal":
                camera = _lerp_camera(CAMERA_MAIN, CAMERA_REVEAL, t)
            elif phase == "reveal_hold":
                camera = CAMERA_REVEAL
            elif phase == "reveal_return":
                camera = _lerp_camera(CAMERA_REVEAL, CAMERA_MAIN, t)
            frames.append(
                {
                    "phase": phase,
                    "lid_rad": lid,
                    "tube_position_m": list(position) if position is not None else None,
                    "camera": camera,
                    "expected_bottom_m": list(bottom),
                }
            )
    return frames


def encode_mp4(frames_dir: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    return output


def evidence_payload(*, mode: str, tube_label: str, mp4: Path, centrifuge_asset_sha: str, tube_asset_sha: str, observations: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "aan.labspin_x8_operation_video.v1",
        "engine": "isaac_sim_4.1",
        "mode": mode,
        "tube_label": tube_label,
        "method": "scripted_articulation_with_package_true_collisions",
        "robot_policy_success": False,
        "rated_high_speed_spin": False,
        "centrifuge_asset_usd_sha256": centrifuge_asset_sha,
        "tube_asset_usd_sha256": tube_asset_sha,
        "mp4": str(mp4),
        "mp4_sha256": _sha(mp4),
        "fps": FPS,
        "resolution": [WIDTH, HEIGHT],
        "observations": observations,
        "claim_boundary": (
            "Isaac Sim 4.1 scripted asset-interaction evidence only; not a "
            "robot policy, benchmark result, rated-speed calibration, or "
            "canonical Task 10 success claim."
        ),
    }


def _socket_world(profile: dict[str, Any], index: int) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    socket = profile["tube_sockets"][index]
    rotor_origin = (-0.03, 0.005, 0.27)
    aperture = tuple(rotor_origin[i] + socket["aperture_rotor_local_m"][i] for i in range(3))
    bottom = tuple(rotor_origin[i] + socket["inserted_bottom_rotor_local_m"][i] for i in range(3))
    axis = tuple(float(value) for value in socket["axis_out_rotor_local"])
    return aperture, bottom, axis


def _orientation_z_to(axis: tuple[float, float, float]) -> tuple[float, float, float, float]:
    # Unit quaternion rotating +Z to the socket outward axis.
    dot = max(-1.0, min(1.0, axis[2]))
    if dot < -0.999999:
        return (0.0, 1.0, 0.0, 0.0)
    cross = (-axis[1], axis[0], 0.0)
    scale = math.sqrt((1.0 + dot) * 2.0)
    return (scale * 0.5, cross[0] / scale, cross[1] / scale, cross[2] / scale)


def _compose_tube(stage: Any, *, root_path: str, tube_asset: Path, tube_entry: str) -> Any:
    from pxr import Sdf, UsdGeom, UsdPhysics

    root = UsdGeom.Xform.Define(stage, root_path).GetPrim()
    root.GetReferences().AddReference(str(tube_asset), Sdf.Path(tube_entry))
    api = UsdPhysics.RigidBodyAPI(root)
    if not api:
        api = UsdPhysics.RigidBodyAPI.Apply(root)
    api.CreateKinematicEnabledAttr(True)
    return root


def _set_joint(articulation: Any, positions: Any, name_to_index: dict[str, int], name: str, value: float) -> Any:
    import numpy as np

    result = np.asarray(positions, dtype=float).copy()
    result[name_to_index[name]] = value
    articulation.set_joint_positions(result)
    articulation._articulation_view.set_joint_position_targets(
        positions=np.asarray([result], dtype=float)
    )
    return result


def _capture_frame(camera: Any, destination: Path, world: Any) -> None:
    from convert_asset.render.single import _camera_rgba, _rgba_to_rgb, _save_rgb_png

    rgba = None
    for _ in range(8):
        rgba = _camera_rgba(camera)
        if rgba is not None:
            break
        world.step(render=True)
    if rgba is None:
        raise RuntimeError("camera returned no RGBA frame after render warmup")
    rgb = _rgba_to_rgb(rgba)
    if rgb is None or not _save_rgb_png(destination, rgb):
        raise RuntimeError(f"could not save frame: {destination}")


def _record_insert(*, centrifuge_asset: Path, tube_asset: Path, tube_entry: str, profile: dict[str, Any], frames_dir: Path, socket_index: int) -> dict[str, Any]:
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting"})
    try:
        import numpy as np
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from omni.isaac.core.prims import RigidPrimView
        from pxr import UsdPhysics

        from convert_asset.render.single import _init_camera, _set_camera_look_at, _setup_environment
        from scripts.qualify_centrifuge_task_interactions import _reset_and_sync

        context = omni.usd.get_context()
        if not context.open_stage(str(centrifuge_asset)):
            raise RuntimeError(f"could not open {centrifuge_asset}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(30):
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        _setup_environment(stage)
        tube_root = _compose_tube(stage, root_path=TUBE_PROBE_ROOT, tube_asset=tube_asset, tube_entry=tube_entry)
        kinematic = UsdPhysics.RigidBodyAPI(tube_root).GetKinematicEnabledAttr()
        world = World(stage_units_in_meters=1.0, physics_dt=PHYSICS_DT, rendering_dt=PHYSICS_DT)
        articulation = world.scene.add(Articulation(CENTRIFUGE_ROOT, name="labspin_x8"))
        tube_view = RigidPrimView(TUBE_PROBE_ROOT, name="labspin_tube")
        _reset_and_sync(
            world,
            app,
            steps=30,
            unregistered_kinematic_views=[tube_view],
        )
        if not articulation.handles_initialized:
            raise RuntimeError("centrifuge articulation did not initialize")
        names = list(articulation.dof_names)
        name_to_index = {name: index for index, name in enumerate(names)}
        for required in ("lid_hinge_joint", "rotor_spin_joint"):
            if required not in name_to_index:
                raise RuntimeError(f"missing runtime DOF {required}; got {names}")
        positions = np.asarray(articulation.get_joint_positions(), dtype=float)
        positions = _set_joint(
            articulation, positions, name_to_index, "lid_hinge_joint", LID_CLOSED_RAD
        )
        aperture, bottom, axis = _socket_world(profile, socket_index)
        orientation = np.asarray([_orientation_z_to(axis)], dtype=np.float32)
        keyframes = build_insert_keyframes(aperture=aperture, bottom=bottom, axis_out=axis)
        camera = _init_camera("LabSpinX8Camera", WIDTH, HEIGHT, CAMERA_MAIN["focal_mm"])
        frames_dir.mkdir(parents=True, exist_ok=True)
        released = False
        for frame_index, keyframe in enumerate(keyframes):
            positions = _set_joint(
                articulation,
                positions,
                name_to_index,
                "lid_hinge_joint",
                float(keyframe["lid_rad"]),
            )
            tube_position = keyframe["tube_position_m"]
            if tube_position is None:
                if not released:
                    kinematic.Set(False)
                    released = True
            else:
                tube_view.set_world_poses(
                    positions=np.asarray([tube_position], dtype=np.float32),
                    orientations=orientation,
                )
            camera_spec = keyframe["camera"]
            _set_camera_look_at(
                camera,
                np.asarray(camera_spec["target"], dtype=float),
                distance=float(camera_spec["distance"]),
                elevation=float(camera_spec["elevation"]),
                azimuth=float(camera_spec["azimuth"]),
            )
            camera.set_focal_length(float(camera_spec["focal_mm"]))
            for _ in range(SUBSTEPS_PER_FRAME - 1):
                world.step(render=False)
            world.step(render=True)
            world.step(render=True)
            _capture_frame(camera, frames_dir / f"frame_{frame_index:04d}.png", world)
        observed_position, _ = tube_view.get_world_poses()
        observed = tuple(float(value) for value in observed_position[0])
        error = math.dist(observed, bottom)
        final_lid = float(articulation.get_joint_positions()[name_to_index["lid_hinge_joint"]])
        return {
            "status": "pass" if error <= 0.020 and abs(final_lid) <= 0.06 else "fail",
            "runtime_dof_names": names,
            "socket_index": socket_index,
            "expected_bottom_m": list(bottom),
            "observed_tube_root_m": list(observed),
            "tube_bottom_error_m": error,
            "final_lid_rad": final_lid,
            "free_physical_release": True,
            "frame_count": len(keyframes),
        }
    finally:
        pass


def _record_spin(*, centrifuge_asset: Path, tube_asset: Path, tube_entry: str, profile: dict[str, Any], frames_dir: Path) -> dict[str, Any]:
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting"})
    try:
        import numpy as np
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from omni.isaac.core.prims import RigidPrimView
        from pxr import UsdPhysics

        from convert_asset.render.single import _init_camera, _set_camera_look_at, _setup_environment
        from scripts.qualify_centrifuge_task_interactions import _reset_and_sync

        context = omni.usd.get_context()
        if not context.open_stage(str(centrifuge_asset)):
            raise RuntimeError(f"could not open {centrifuge_asset}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(30):
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        _setup_environment(stage)
        roots = [
            _compose_tube(stage, root_path=root, tube_asset=tube_asset, tube_entry=tube_entry)
            for root in SPIN_TUBE_ROOTS
        ]
        world = World(stage_units_in_meters=1.0, physics_dt=PHYSICS_DT, rendering_dt=PHYSICS_DT)
        articulation = world.scene.add(Articulation(CENTRIFUGE_ROOT, name="labspin_x8_spin"))
        views = [
            RigidPrimView(root, name=f"spin_tube_{index}")
            for index, root in enumerate(SPIN_TUBE_ROOTS)
        ]
        _reset_and_sync(
            world,
            app,
            steps=20,
            unregistered_kinematic_views=views,
        )
        names = list(articulation.dof_names)
        name_to_index = {name: index for index, name in enumerate(names)}
        rotor_index = name_to_index["rotor_spin_joint"]
        lid_index = name_to_index["lid_hinge_joint"]
        positions = np.asarray(articulation.get_joint_positions(), dtype=float)
        positions = _set_joint(
            articulation, positions, name_to_index, "lid_hinge_joint", LID_OPEN_RAD
        )
        sockets = (0, 12)
        for root, view, socket_index in zip(roots, views, sockets):
            _, bottom, axis = _socket_world(profile, socket_index)
            view.set_world_poses(
                positions=np.asarray([bottom], dtype=np.float32),
                orientations=np.asarray([_orientation_z_to(axis)], dtype=np.float32),
            )
            UsdPhysics.RigidBodyAPI(root).GetKinematicEnabledAttr().Set(False)
        for _ in range(60):
            world.step(render=False)
        camera = _init_camera("LabSpinX8SpinCamera", WIDTH, HEIGHT, CAMERA_MAIN["focal_mm"])
        frames_dir.mkdir(parents=True, exist_ok=True)
        frame_count = 144
        start_angle = float(articulation.get_joint_positions()[rotor_index])
        for frame_index in range(frame_count):
            velocities = np.zeros(len(names), dtype=float)
            velocities[rotor_index] = 5.0 if 24 <= frame_index < 120 else 0.0
            articulation._articulation_view.set_joint_velocity_targets(
                velocities=np.asarray([velocities], dtype=float)
            )
            positions[lid_index] = LID_CLOSED_RAD
            _set_camera_look_at(
                camera,
                np.asarray(CAMERA_MAIN["target"], dtype=float),
                distance=CAMERA_MAIN["distance"],
                elevation=CAMERA_MAIN["elevation"],
                azimuth=CAMERA_MAIN["azimuth"],
            )
            camera.set_focal_length(CAMERA_MAIN["focal_mm"])
            for _ in range(SUBSTEPS_PER_FRAME - 1):
                world.step(render=False)
            world.step(render=True)
            world.step(render=True)
            _capture_frame(camera, frames_dir / f"frame_{frame_index:04d}.png", world)
        end_angle = float(articulation.get_joint_positions()[rotor_index])
        final_positions = [tuple(float(v) for v in view.get_world_poses()[0][0]) for view in views]
        retained = all(0.15 <= position[2] <= 0.42 and math.hypot(position[0] + 0.03, position[1] - 0.005) <= 0.25 for position in final_positions)
        return {
            "status": "pass" if retained and abs(end_angle - start_angle) >= 1.0 else "fail",
            "runtime_dof_names": names,
            "target_velocity_rad_s": 5.0,
            "lid_state": "open_for_visual_evidence_only",
            "safety_interlock_claim": False,
            "rotor_angle_delta_rad": end_angle - start_angle,
            "balanced_socket_indices": list(sockets),
            "final_tube_root_positions_m": [list(position) for position in final_positions],
            "tubes_retained": retained,
            "frame_count": frame_count,
        }
    finally:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--centrifuge-package", type=Path, required=True)
    parser.add_argument("--tube-package", type=Path, required=True)
    parser.add_argument("--tube-entry", required=True)
    parser.add_argument("--tube-label", required=True)
    parser.add_argument("--device-profile", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("insert", "spin"), default="insert")
    parser.add_argument("--socket-index", type=int, default=0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    centrifuge_asset = args.centrifuge_package.resolve() / "asset.usd"
    tube_asset = args.tube_package.resolve() / "asset.usd"
    profile = json.loads(args.device_profile.resolve().read_text(encoding="utf-8"))
    out_dir = args.out_dir.resolve()
    frames_dir = out_dir / "frames"
    if args.mode == "insert":
        observations = _record_insert(
            centrifuge_asset=centrifuge_asset,
            tube_asset=tube_asset,
            tube_entry=args.tube_entry,
            profile=profile,
            frames_dir=frames_dir,
            socket_index=args.socket_index,
        )
        mp4_name = f"scripted_{args.tube_label}_open_insert_close.mp4"
        evidence_mode = "scripted_insert"
    else:
        observations = _record_spin(
            centrifuge_asset=centrifuge_asset,
            tube_asset=tube_asset,
            tube_entry=args.tube_entry,
            profile=profile,
            frames_dir=frames_dir,
        )
        mp4_name = "scripted_balanced_pair_low_speed_spin.mp4"
        evidence_mode = "scripted_low_speed_spin"
    mp4 = encode_mp4(frames_dir, out_dir / mp4_name)
    payload = evidence_payload(
        mode=evidence_mode,
        tube_label=args.tube_label,
        mp4=mp4,
        centrifuge_asset_sha=_sha(centrifuge_asset),
        tube_asset_sha=_sha(tube_asset),
        observations=observations,
    )
    evidence = out_dir / "evidence.json"
    evidence.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"mp4": str(mp4), "evidence": str(evidence), "observations": observations}, indent=2))
    return 0 if observations.get("status") == "pass" else 2


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    import os

    os._exit(code)
