# -*- coding: utf-8 -*-
"""Lazy Isaac viewport capture helpers."""
from __future__ import annotations

import os
from pathlib import Path
import inspect


def create_simulation_app(*, headless: bool = True, renderer: str = "RayTracedLighting"):
    from isaacsim import SimulationApp  # type: ignore

    return SimulationApp(
        launch_config={
            "sync_loads": True,
            "headless": bool(headless),
            "renderer": renderer,
        }
    )


def wait_frames(app, count: int) -> None:
    for _ in range(max(1, int(count))):
        app.update()


def _stage_is_loading(ctx) -> bool:
    status_fn = getattr(ctx, "get_stage_loading_status", None)
    if callable(status_fn):
        try:
            status = status_fn()
        except Exception:
            status = None
        if isinstance(status, (tuple, list)) and len(status) >= 3:
            try:
                return int(status[2]) > 0
            except (TypeError, ValueError):
                return bool(status[2])
        if isinstance(status, bool):
            return status
        if isinstance(status, (int, float)):
            return status > 0

    standby_fn = getattr(ctx, "is_standby", None)
    if callable(standby_fn):
        try:
            if bool(standby_fn()):
                return True
        except Exception:
            pass
    loading_fn = getattr(ctx, "is_stage_loading", None)
    if callable(loading_fn):
        try:
            return bool(loading_fn())
        except Exception:
            pass
    return False


def enable_viewport_extension() -> None:
    import carb.settings  # type: ignore
    from omni.kit.app import get_app  # type: ignore

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


def open_stage(app, usd_path: str, *, max_wait_frames: int = 600):
    import omni.usd  # type: ignore

    ctx = omni.usd.get_context()
    print(f"[target-capture] opening stage {usd_path}", flush=True)
    opened = ctx.open_stage(usd_path)
    if opened is False:
        raise RuntimeError(f"Failed to request stage open: {usd_path}")
    waited = 0
    while True:
        if not _stage_is_loading(ctx):
            break
        if waited >= max_wait_frames:
            raise TimeoutError(f"Timed out opening stage after {max_wait_frames} frames: {usd_path}")
        wait_frames(app, 1)
        waited += 1
    stage = ctx.get_stage()
    if stage is None:
        raise RuntimeError(f"Failed to open stage: {usd_path}")
    return stage


def get_viewport(width: int, height: int):
    from omni.kit.viewport.utility import create_viewport_window, get_active_viewport_window  # type: ignore

    window = get_active_viewport_window()
    if window is None:
        try:
            window = create_viewport_window("TargetCaptureViewport", width=int(width), height=int(height))
        except Exception:
            window = None
    if window is None:
        try:
            import omni.kit.viewport_legacy as vp_legacy  # type: ignore
            from omni.kit.viewport.utility.legacy_viewport_window import LegacyViewportWindow  # type: ignore

            iface = vp_legacy.get_viewport_interface()
            handle = iface.create_instance()
            assigned = iface.get_viewport_window_name(handle)
            window = LegacyViewportWindow(assigned)
            window.width = int(width)
            window.height = int(height)
        except Exception as exc:
            raise RuntimeError("Failed to acquire viewport in headless mode") from exc

    viewport = window.viewport_api
    try:
        viewport.set_texture_resolution(int(width), int(height))
    except Exception:
        try:
            viewport.set_texture_resolution((int(width), int(height)))
        except Exception:
            pass
    return window, viewport


def _wait_for_capture_result(result, *, completion_frames: int = 30) -> bool:
    if inspect.isawaitable(result):
        close_fn = getattr(result, "close", None)
        if callable(close_fn):
            close_fn()
        return True
    for method_name in ("wait_for_result", "wait_for_completion"):
        method = getattr(result, method_name, None)
        if not callable(method):
            continue
        try:
            value = method(completion_frames=int(completion_frames))
        except TypeError:
            value = method()
        if inspect.isawaitable(value):
            close_fn = getattr(value, "close", None)
            if callable(close_fn):
                close_fn()
            return True
        return True if value is None else bool(value)
    if isinstance(result, bool):
        return result
    return True


def capture_viewport_image(viewport, output_path: str | os.PathLike[str], *, app=None, wait_frames: int = 2) -> bool:
    from omni.kit.viewport.utility import capture_viewport_to_file  # type: ignore

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    result = capture_viewport_to_file(viewport, str(path))
    completion_frames = max(30, int(wait_frames))
    capture_ok = _wait_for_capture_result(result, completion_frames=completion_frames)
    if app is not None:
        for _ in range(completion_frames):
            app.update()
            if path.exists() and path.stat().st_size > 0:
                return capture_ok
    return capture_ok and path.exists() and path.stat().st_size > 0
