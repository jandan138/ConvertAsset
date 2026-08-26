#!/usr/bin/env python3
"""Record GUI-like slow rotation, gravity slide, and closed stop in Isaac 4.1."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _quat_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    from isaacsim import SimulationApp

    saved = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting", "multi_gpu": False})
    sys.argv = saved
    import carb
    import cv2
    import numpy as np
    import omni.physx
    import omni.physx.bindings._physx as pb
    import omni.timeline
    import omni.usd
    from omni.isaac.dynamic_control import _dynamic_control
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

    from convert_asset.render.single import (
        _camera_rgba,
        _init_camera,
        _rgba_to_rgb,
        _save_rgb_png,
        _set_camera_look_at,
    )

    settings = carb.settings.get_settings()
    log_path = Path(str(settings.get("/log/file")))
    log_offset = log_path.stat().st_size if log_path.exists() else 0
    settings.set(pb.SETTING_UPDATE_TO_USD, True)
    context = omni.usd.get_context()
    if not context.open_stage(str(args.source.resolve())):
        raise RuntimeError("could not open source")
    while context.get_stage_loading_status()[2] > 0:
        app.update()
    for _ in range(30):
        app.update()
    stage = context.get_stage()
    stage.SetEditTarget(stage.GetSessionLayer())
    cap = stage.GetPrimAtPath("/World/cap")
    translate = cap.GetAttribute("xformOp:translate")
    value = translate.Get()
    translate.Set(Gf.Vec3d(float(value[0]), float(value[1]), 1.104))
    cap.GetAttribute("physics:velocity").Set(Gf.Vec3f(0.0))
    cap.GetAttribute("physics:angularVelocity").Set(Gf.Vec3f(0.0))

    # Verified 15 mL red PP cap appearance, session-only.
    material = UsdShade.Material.Define(stage, "/World/__EvidenceLooks/VerifiedRedCap")
    shader = UsdShade.Shader.Define(stage, "/World/__EvidenceLooks/VerifiedRedCap/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.56, 0.004, 0.008))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.42)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath("/World/cap/node_/mesh_")).Bind(material)
    # Close the inherited open sleeve with the producer-declared 1.5 mm top.
    top = UsdGeom.Cylinder.Define(stage, "/World/cap/__EvidenceClosedTop")
    top.CreateAxisAttr(UsdGeom.Tokens.z)
    top.CreateRadiusAttr(8.90)
    top.CreateHeightAttr(1.50)
    # The source cap's local +Z maps to world -Z after its authored composed
    # orientation, so the visible top opening is at the negative local end.
    top.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -8.60))
    UsdShade.MaterialBindingAPI.Apply(top.GetPrim()).Bind(material)
    # Evidence-only visual closure.  It must not alter the original source
    # contact protocol being measured below.
    backdrop = UsdGeom.Cube.Define(stage, "/World/__EvidenceBackdrop")
    backdrop.CreateSizeAttr(1.0)
    backdrop.CreateDisplayColorAttr([Gf.Vec3f(0.10, 0.12, 0.16)])
    backdrop.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.48, 1.04))
    backdrop.AddScaleOp().Set(Gf.Vec3f(0.42, 0.02, 0.30))
    omni.physx.get_physx_interface().overwrite_gpu_setting(1)

    camera = _init_camera("SlowThreadEvidenceCamera", 1280, 720, 48.0)
    _set_camera_look_at(
        camera,
        np.asarray([0.0, 0.0, 1.04], dtype=float),
        distance=1.55,
        elevation=10.0,
        azimuth=-75.0,
    )
    for _ in range(30):
        app.update()

    out_dir = args.out_dir.resolve()
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_index = 0

    def capture_frame(label: str, angle_deg: float, relative_z: float, delta_z: float):
        nonlocal frame_index
        rgba = None
        for _ in range(8):
            rgba = _camera_rgba(camera)
            if rgba is not None:
                break
            app.update()
        if rgba is None:
            raise RuntimeError("camera returned no frame after render warmup")
        rgb = _rgba_to_rgb(rgba, background_color=(24, 28, 36))
        if rgb is None:
            raise RuntimeError("camera RGB conversion failed")
        bgr = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
        lines = [
            "Isaac Sim 4.1 | original 10x USD | GUI-like slow yaw | Z from PhysX",
            f"{label}   angle={angle_deg:5.2f} deg   z={relative_z:1.4f} m   dz={delta_z*1000:5.1f} mm",
        ]
        for index, text in enumerate(lines):
            cv2.putText(bgr, text, (24, 38 + index * 36), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2, cv2.LINE_AA)
        rgb_out = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        if not _save_rgb_png(frames_dir / f"frame_{frame_index:04d}.png", rgb_out):
            raise RuntimeError("could not save frame")
        frame_index += 1

    def usd_position(path: str):
        matrix = UsdGeom.XformCache(Usd.TimeCode.Default()).GetLocalToWorldTransform(stage.GetPrimAtPath(path))
        return tuple(float(v) for v in matrix.ExtractTranslation())

    body_initial = usd_position("/World/shiguan")
    cap_initial = usd_position("/World/cap")
    relative_initial = cap_initial[2] - body_initial[2]
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    app.update()
    dc = _dynamic_control.acquire_dynamic_control_interface()
    cap_handle = dc.get_rigid_body("/World/cap")
    initial_pose = dc.get_rigid_body_pose(cap_handle)
    base_quat = (float(initial_pose.r.x), float(initial_pose.r.y), float(initial_pose.r.z), float(initial_pose.r.w))
    angle_deg = 0.0
    stopped = False
    stop_update = None
    hold_remaining = 0
    trace = []
    # Measure first, render second.  Camera readback/app updates can otherwise
    # perturb this phase-sensitive source contact state.
    for update in range(1440):
        app.update()
        bp = usd_position("/World/shiguan")
        cp = usd_position("/World/cap")
        relative_z = cp[2] - bp[2]
        if not stopped:
            angle_deg -= 15.0 / 60.0
            pose = dc.get_rigid_body_pose(cap_handle)
            yaw = math.radians(angle_deg)
            quat = _quat_mul((0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)), base_quat)
            dc.set_rigid_body_pose(cap_handle, _dynamic_control.Transform((bp[0], bp[1], float(pose.p.z)), quat))
            if abs(angle_deg) >= 5.0 and relative_z <= 1.080:
                stopped = True
                stop_update = update
                hold_remaining = 120
        else:
            pose = dc.get_rigid_body_pose(cap_handle)
            yaw = math.radians(angle_deg)
            quat = _quat_mul((0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)), base_quat)
            dc.set_rigid_body_pose(cap_handle, _dynamic_control.Transform((bp[0], bp[1], float(pose.p.z)), quat))
            hold_remaining -= 1
        trace.append(
            {
                "update": update,
                "angle_deg": angle_deg,
                "relative_z_m": relative_z,
                "cap_position": cp,
                "cap_quaternion_xyzw": quat,
            }
        )
        if math.hypot(cp[0] - bp[0], cp[1] - bp[1]) > 0.10 or relative_z < 0.90:
            break
        if stopped and hold_remaining <= 0:
            break
    timeline.stop()

    final_z = trace[-1]["relative_z_m"]
    final_angle = angle_deg
    tail = [float(sample["relative_z_m"]) for sample in trace[-min(60, len(trace)):]]

    # Replay the measured PhysX trajectory with physics stopped.  This keeps
    # camera readback from changing the trajectory while retaining Isaac's own
    # renderer and the exact measured transforms.
    cap_translate = cap.GetAttribute("xformOp:translate")
    cap_orient = cap.GetAttribute("xformOp:orient")

    def set_replay_pose(position, quaternion_xyzw):
        cap_translate.Set(Gf.Vec3d(*position))
        cap_orient.Set(
            Gf.Quatf(
                float(quaternion_xyzw[3]),
                Gf.Vec3f(*[float(v) for v in quaternion_xyzw[:3]]),
            )
        )
        app.update()

    set_replay_pose(cap_initial, base_quat)
    for _ in range(60):
        capture_frame("INITIAL HOLD", 0.0, relative_initial, 0.0)
    replay_until = stop_update + 1 if stop_update is not None else len(trace)
    for sample in trace[:replay_until]:
        set_replay_pose(sample["cap_position"], sample["cap_quaternion_xyzw"])
        for _ in range(4):
            capture_frame(
                "MEASURED PHYSX TRAJECTORY",
                sample["angle_deg"],
                sample["relative_z_m"],
                relative_initial - sample["relative_z_m"],
            )
    if stopped:
        final_sample = trace[-1]
        set_replay_pose(final_sample["cap_position"], final_sample["cap_quaternion_xyzw"])
        for _ in range(60):
            capture_frame("ROTATION STOPPED", final_angle, final_z, relative_initial - final_z)

    video = out_dir / "original_thread_slow_rotate_red_cap_stop_isaac41.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-framerate", "30", "-i", str(frames_dir / "frame_%04d.png"), "-frames:v", str(frame_index), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)],
        check=True,
        capture_output=True,
    )
    log = log_path.read_text(errors="replace")[log_offset:] if log_path.exists() else ""
    markers = ("CUDA error", "illegal memory access", "PhysX error")
    hard = list(dict.fromkeys(line for line in log.splitlines() if any(m in line for m in markers)))
    evidence = {
        "schema_version": "aan.original_threaded_tube15_slow_rotate_video.v1",
        "runtime": "isaac41",
        "source_sha256": sha256(args.source.read_bytes()).hexdigest(),
        "visual_override": {"cap": "verified_15ml_red_pp", "closed_top_thickness_mm": 1.5},
        "controller": "gui_like_yaw_and_xy_alignment_z_from_physx",
        "video_method": "isaac_render_replay_of_same_run_measured_physx_trace",
        "relative_z_initial_m": relative_initial,
        "relative_z_final_m": final_z,
        "descent_m": relative_initial - final_z,
        "rotation_deg_at_stop": final_angle,
        "stop_update": stop_update,
        "relative_z_at_stop_m": trace[stop_update]["relative_z_m"] if stop_update is not None else None,
        "tail_span_m": max(tail) - min(tail),
        "hard_errors": hard,
        "video": str(video),
        "video_sha256": sha256(video.read_bytes()).hexdigest(),
        "frame_count": frame_index,
        "fps": 30,
        "claim_boundary": "Isaac-rendered replay of the same-run measured PhysX trajectory on the original 10x USD; GUI-like yaw/centering is controlled while Z remains PhysX-derived. It is not native continuous screw coupling or real-scale qualification.",
    }
    (out_dir / "slow_rotate_video_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2), flush=True)
    import os

    os._exit(0 if stopped and not hard else 2)


if __name__ == "__main__":
    main()
