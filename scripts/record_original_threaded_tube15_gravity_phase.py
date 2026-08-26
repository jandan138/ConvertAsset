#!/usr/bin/env python3
"""Record the selected original-size gravity-only thread phase in Isaac 4.1."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--yaw-deg", type=float, default=255.0)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    from isaacsim import SimulationApp

    saved = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting", "multi_gpu": False})
    sys.argv = saved
    import carb
    import numpy as np
    import omni.physx
    import omni.physx.bindings._physx as pb
    import omni.timeline
    import omni.usd
    from pxr import Gf, Sdf, UsdGeom

    from convert_asset.render.single import (
        _camera_rgba,
        _init_camera,
        _rgba_to_rgb,
        _save_rgb_png,
        _set_camera_look_at,
    )

    settings = carb.settings.get_settings()
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
    current = cap.GetAttribute("xformOp:translate").Get()
    cap.GetAttribute("xformOp:translate").Set(Gf.Vec3d(float(current[0]), float(current[1]), 1.104))
    phase_name = "xformOp:rotateZ:threadPhase"
    cap.CreateAttribute(phase_name, Sdf.ValueTypeNames.Double).Set(float(args.yaw_deg))
    order_attr = cap.GetAttribute("xformOpOrder")
    order = list(order_attr.Get() or [])
    if phase_name in order:
        order.remove(phase_name)
    order.insert(1 if order and order[0] == "xformOp:translate" else 0, phase_name)
    order_attr.Set(order)
    cap.GetAttribute("physics:velocity").Set(Gf.Vec3f(0.0))
    cap.GetAttribute("physics:angularVelocity").Set(Gf.Vec3f(0.0))
    backdrop = UsdGeom.Cube.Define(stage, "/World/__EvidenceBackdrop")
    backdrop.CreateSizeAttr(1.0)
    backdrop.CreateDisplayColorAttr([Gf.Vec3f(0.12, 0.14, 0.18)])
    backdrop.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.65, 0.65))
    backdrop.AddScaleOp().Set(Gf.Vec3f(1.25, 0.02, 0.85))
    omni.physx.get_physx_interface().overwrite_gpu_setting(1)

    camera = _init_camera("OriginalThreadEvidenceCamera", 1280, 720, 36.0)
    _set_camera_look_at(
        camera,
        np.asarray([0.0, 0.0, 0.76], dtype=float),
        distance=3.4,
        elevation=14.0,
        azimuth=-75.0,
    )
    for _ in range(30):
        app.update()
    frames = args.out_dir.resolve() / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    frame_index = 0
    for update in range(480):
        app.update()
        if update % 2:
            continue
        rgba = _camera_rgba(camera)
        if rgba is None:
            continue
        rgb = _rgba_to_rgb(rgba, background_color=(24, 28, 36))
        if not _save_rgb_png(frames / f"frame_{frame_index:04d}.png", rgb):
            raise RuntimeError("could not save evidence frame")
        frame_index += 1
    timeline.stop()
    video = args.out_dir.resolve() / "original_thread_yaw255_gravity_only_isaac41.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", "30", "-i", str(frames / "frame_%04d.png"),
            "-vf", "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='Isaac Sim 4.1 | original 10x USD | yaw 255 deg | gravity only':x=24:y=24:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6,format=yuv420p",
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video),
        ],
        check=True,
        capture_output=True,
    )
    evidence = {
        "schema_version": "aan.original_threaded_tube15_gravity_video.v1",
        "runtime": "isaac41",
        "source": str(args.source.resolve()),
        "source_sha256": sha256(args.source.read_bytes()).hexdigest(),
        "yaw_deg": args.yaw_deg,
        "control_after_play": "none_gravity_only",
        "frame_count": frame_index,
        "fps": 30,
        "video": str(video),
        "video_sha256": sha256(video.read_bytes()).hexdigest(),
        "claim_boundary": "Original oversized colleague USD phase evidence only; not real-scale fused qualification.",
    }
    (args.out_dir.resolve() / "video_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2), flush=True)
    import os

    os._exit(0)


if __name__ == "__main__":
    main()
