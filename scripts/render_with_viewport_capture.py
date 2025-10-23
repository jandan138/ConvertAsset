"""Render USD frames by driving SimulationApp with a specific camera."""

from __future__ import annotations

import argparse
import os
from typing import Optional

from isaacsim import SimulationApp


def _maybe_stage_timecode(stage, getter: str, checker: str | None = None):
    """Safely call stage time code accessors across USD/omni stage wrappers."""
    check_fn = getattr(stage, checker, None) if checker else None
    if callable(check_fn):
        try:
            if not check_fn():
                return None
        except Exception:
            return None
    get_fn = getattr(stage, getter, None)
    if callable(get_fn):
        try:
            return get_fn()
        except Exception:
            return None
    return None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture images from a USD stage camera")
    parser.add_argument("--usd-path", required=True, help="USD file to open")
    parser.add_argument("--camera", required=True, help="Camera prim path to use for rendering")
    parser.add_argument("--output-dir", required=True, help="Directory to store captured images")
    parser.add_argument("--prefix", default="frame", help="Output filename prefix")
    parser.add_argument("--ext", default="png", help="Image extension without dot")
    parser.add_argument("--width", type=int, default=1920, help="Capture width")
    parser.add_argument("--height", type=int, default=1080, help="Capture height")
    parser.add_argument("--start-frame", dest="start_frame", type=float, default=None,
                        help="Start frame (falls back to stage start or 0)")
    parser.add_argument("--end-frame", dest="end_frame", type=float, default=None,
                        help="End frame inclusive (falls back to stage end or start)")
    parser.add_argument("--frame-step", dest="frame_step", type=float, default=1.0,
                        help="Frame increment between captures")
    parser.add_argument("--digits", type=int, default=4, help="Zero padding for filenames")
    parser.add_argument("--wait-frames", dest="wait_frames", type=int, default=2,
                        help="Simulation frames to wait before each capture")
    parser.add_argument("--renderer", default="RayTracedLighting", help="Renderer preset")
    parser.add_argument("--headless", action="store_true", help="Run SimulationApp headless")
    return parser.parse_args()


def _create_simulation_app(args: argparse.Namespace) -> SimulationApp:
    config = {"sync_loads": True, "headless": args.headless, "renderer": args.renderer}
    return SimulationApp(launch_config=config)


def _enable_viewport_extension() -> None:
    import carb.settings
    from omni.kit.app import get_app

    ext_name = "omni.kit.viewport"
    settings = carb.settings.get_settings()
    ext_flag = f"/app/extensions/enabled/{ext_name}"
    if not settings.get_as_bool(ext_flag):
        settings.set(ext_flag, True)
    app = get_app()
    if app is None:
        raise RuntimeError("omni.kit.app.get_app() returned None")
    ext_mgr = app.get_extension_manager()
    if not ext_mgr.is_extension_enabled(ext_name):
        ext_mgr.set_extension_enabled_immediate(ext_name, True)


def _wait_frames(app: SimulationApp, count: int) -> None:
    for _ in range(max(1, count)):
        app.update()


def _open_stage(app: SimulationApp, usd_path: str):
    import omni.usd

    ctx = omni.usd.get_context()
    print(f"Opening stage {usd_path}", flush=True)
    ctx.open_stage(usd_path)
    while True:
        loading = False
        standby_fn = getattr(ctx, "is_standby", None)
        if callable(standby_fn):
            try:
                loading = loading or standby_fn()
            except Exception:
                loading = loading or False
        if hasattr(ctx, "is_stage_loading"):
            try:
                loading = loading or bool(ctx.is_stage_loading())
            except Exception:
                loading = loading or False
        if not loading:
            break
        _wait_frames(app, 1)
    stage = ctx.get_stage()
    if stage is None:
        raise RuntimeError(f"Failed to open stage: {usd_path}")
    return stage


def _resolve_frame_range(stage, start: Optional[float], end: Optional[float]) -> tuple[float, float]:
    if start is None:
        stage_start = _maybe_stage_timecode(stage, "GetStartTimeCode", "HasStartTimeCode")
        if stage_start is None:
            stage_start = _maybe_stage_timecode(stage, "GetStartTimeCode")
        start = stage_start if stage_start is not None else 0.0
    if end is None:
        stage_end = _maybe_stage_timecode(stage, "GetEndTimeCode", "HasEndTimeCode")
        if stage_end is None:
            stage_end = _maybe_stage_timecode(stage, "GetEndTimeCode")
        end = stage_end if stage_end is not None else start
    if end < start:
        raise ValueError(f"end-frame ({end}) earlier than start-frame ({start})")
    return float(start), float(end)


def _get_viewport(width: int, height: int):
    from omni.kit.viewport.utility import create_viewport_window, get_active_viewport_window

    window = get_active_viewport_window()
    viewport = None
    if window is None:
        try:
            window = create_viewport_window("CaptureViewport", width=width, height=height)
        except Exception:
            window = None
    if window is None:
        try:
            import omni.kit.viewport_legacy as vp_legacy
            from omni.kit.viewport.utility.legacy_viewport_window import LegacyViewportWindow

            iface = vp_legacy.get_viewport_interface()
            handle = iface.create_instance()
            assigned = iface.get_viewport_window_name(handle)
            window = LegacyViewportWindow(assigned)
            window.width = width
            window.height = height
        except Exception as exc:
            raise RuntimeError("Failed to acquire viewport in headless mode") from exc
    viewport = window.viewport_api
    try:
        viewport.set_texture_resolution(width, height)
    except Exception:
        try:
            viewport.set_texture_resolution((width, height))
        except Exception:
            pass
    return window, viewport


def _capture_sequence(app: SimulationApp, args: argparse.Namespace) -> None:
    from omni.kit.viewport.utility import capture_viewport_to_file
    import omni.timeline
    import omni.usd

    stage = _open_stage(app, args.usd_path)
    print(f"Opened stage {args.usd_path}", flush=True)
    start, end = _resolve_frame_range(stage, args.start_frame, args.end_frame)
    step = float(args.frame_step)
    if step <= 0:
        raise ValueError("frame-step must be > 0")

    tps = stage.GetTimeCodesPerSecond() or 0.0
    if tps <= 0:
        tps = 1.0

    os.makedirs(args.output_dir, exist_ok=True)
    print(f"Capturing to {os.path.abspath(args.output_dir)}", flush=True)

    viewport_window, viewport = _get_viewport(args.width, args.height)
    print("Viewport acquired", viewport_window, viewport, flush=True)
    viewport.camera_path = args.camera
    print(f"Camera bound: {viewport.camera_path}", flush=True)

    timeline = omni.timeline.get_timeline_interface()
    timeline.stop()
    timeline.set_looping(False)
    timeline.set_time_codes_per_second(tps)
    start_time = timeline.time_code_to_time(start)
    end_time = timeline.time_code_to_time(end)
    timeline.set_start_time(start_time)
    timeline.set_end_time(end_time)

    usd_context = omni.usd.get_context()
    # Ensure the USD context and timeline remain in sync when time stepping.
    try:
        usd_context.set_timeline(timeline.get_timeline_name())
    except AttributeError:
        pass

    t = start
    frame_index = 0
    while t <= end + 1e-6:
        timeline.set_current_time(timeline.time_code_to_time(t))
        _wait_frames(app, args.wait_frames)
        filename = f"{args.prefix}_{frame_index:0{args.digits}d}.{args.ext}"
        out_path = os.path.join(args.output_dir, filename)
        result = capture_viewport_to_file(viewport, out_path)
        print(f"Saved frame {frame_index} (time {t}) -> {out_path} [success={result}]", flush=True)
        frame_index += 1
        t += step



def main() -> None:
    args = _parse_args()
    print("Render script starting", args)
    app = _create_simulation_app(args)
    try:
        print("SimulationApp created")
        _wait_frames(app, 1)
        print("Post wait 1 frame")
        try:
            _enable_viewport_extension()
        except Exception as exc:
            print(f"Viewport extension enable failed: {exc}")
            raise
        print("Viewport extension enabled")
        _wait_frames(app, 2)
        print("Post wait 2 frames")
        try:
            _capture_sequence(app, args)
        except Exception as exc:
            import traceback

            print(f"Capture sequence failed: {exc}", flush=True)
            traceback.print_exc()
            raise
    finally:
        _wait_frames(app, 2)
        app.close()


if __name__ == "__main__":
    main()
