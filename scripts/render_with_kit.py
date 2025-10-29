"""Headless image capture using Isaac Sim / Kit.

Usage example:

    /isaac-sim/isaac_python.sh scripts/render_with_kit.py \
        --stage /abs/path/to/scene.usd \
        --camera /World/OrbitCam \
        --out-dir ./nomdl_images \
        --start-frame 0 --end-frame 15 --width 1920 --height 1080

The script opens the USD stage, switches the viewport to the given camera,
and captures a frame per time sample (supports animated camera authored in
USD, e.g. produced by convert-asset camera-orbit).

It is designed to run in offscreen/headless mode via isaac_python.sh.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Optional

import omni.kit.app
import omni.kit.viewport.utility as vp_utils
import omni.timeline
import omni.usd
from pxr import Usd


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Headless USD image capture with Kit")
    parser.add_argument("--stage", required=True, help="Path to USD stage to open")
    parser.add_argument("--camera", required=True, help="Camera prim path to render from")
    parser.add_argument("--out-dir", required=True, help="Directory to write images")
    parser.add_argument("--prefix", default="frame", help="Output filename prefix (default frame)")
    parser.add_argument("--ext", default="png", help="Image extension without dot (png/jpg, default png)")
    parser.add_argument("--width", type=int, default=1920, help="Capture width (default 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Capture height (default 1080)")
    parser.add_argument("--start-frame", dest="start_frame", type=float, default=None,
                        help="Start frame (time code). Falls back to stage start or 0.")
    parser.add_argument("--end-frame", dest="end_frame", type=float, default=None,
                        help="End frame (inclusive). Falls back to stage end or start.")
    parser.add_argument("--frame-step", dest="frame_step", type=float, default=1.0,
                        help="Frame increment per capture (default 1.0)")
    parser.add_argument("--digits", type=int, default=4, help="Zero padding digits (default 4)")
    parser.add_argument("--wait-frames", type=int, default=2,
                        help="Kit update ticks to wait before each capture (default 2)")
    return parser.parse_args()


async def _wait_frames(count: int = 1) -> None:
    app = omni.kit.app.get_app()
    for _ in range(max(1, count)):
        await app.next_update_async()


async def _open_stage(path: str) -> Usd.Stage:
    ctx = omni.usd.get_context()
    ctx.open_stage(path)
    while ctx.is_standby() or ctx.is_stage_loading():
        await _wait_frames(1)
    stage = ctx.get_stage()
    if stage is None:
        raise RuntimeError(f"Failed to open stage: {path}")
    return stage


def _resolve_frame_range(stage: Usd.Stage, start: Optional[float], end: Optional[float]) -> tuple[float, float]:
    if start is None:
        stage_start = stage.GetStartTimeCode() if stage.HasStartTimeCode() else None
        start = stage_start if stage_start is not None else 0.0
    if end is None:
        stage_end = stage.GetEndTimeCode() if stage.HasEndTimeCode() else None
        end = stage_end if stage_end is not None else start
    if end < start:
        raise ValueError(f"end-frame ({end}) is earlier than start-frame ({start})")
    return float(start), float(end)


async def _render_sequence(args: argparse.Namespace) -> None:
    stage = await _open_stage(args.stage)

    start, end = _resolve_frame_range(stage, args.start_frame, args.end_frame)
    step = float(args.frame_step)
    if step <= 0:
        raise ValueError("frame-step must be > 0")

    os.makedirs(args.out_dir, exist_ok=True)

    timeline = omni.timeline.get_timeline_interface()
    timeline.stop()
    timeline.set_looping(False)
    timeline.set_start_time(start)
    timeline.set_end_time(end)

    vp = vp_utils.get_active_viewport()
    if vp is None:
        raise RuntimeError("No active viewport available; ensure Kit is running in offscreen mode")
    vp.set_texture_resolution(args.width, args.height)
    vp.set_active_camera(args.camera)

    frame_index = 0
    t = start
    while t <= end + 1e-6:  # tolerance for float accumulation
        timeline.set_current_time(t)
        await _wait_frames(args.wait_frames)
        filename = f"{args.prefix}_{frame_index:0{args.digits}d}.{args.ext}"
        out_path = os.path.join(args.out_dir, filename)
        try:
            vp.capture_image(out_path)
        except Exception:
            vp_utils.capture_viewport_to_file(vp, out_path)
        print(f"Saved frame {frame_index} (time {t}) -> {out_path}")
        frame_index += 1
        t += step


async def _main_async(args: argparse.Namespace) -> None:
    try:
        await _render_sequence(args)
    finally:
        # Allow a couple of frames for clean shutdown
        await _wait_frames(2)
        omni.kit.app.get_app().post_quit()


def main() -> None:
    args = _parse_args()
    asyncio.ensure_future(_main_async(args))
    omni.kit.app.get_app().run()


if __name__ == "__main__":
    main()
