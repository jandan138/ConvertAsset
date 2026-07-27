"""Isaac before/after inactivation evidence renders for workspace profiles.

Runs the repository's proven render flow (SimulationApp -> _init_world ->
add_reference_to_stage -> camera probes).  Heavy Isaac imports stay inside
functions so the module is import-clean for unit tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def compose_before_after(
    before_png: Path,
    after_png: Path,
    out_png: Path,
    *,
    before_label: str,
    after_label: str = "AFTER (inactive)",
    label_band: int = 36,
) -> None:
    """Compose a labeled side-by-side evidence image from two renders."""
    from PIL import Image, ImageDraw

    before = Image.open(before_png)
    after = Image.open(after_png)
    width, height = before.size
    canvas = Image.new("RGB", (width * 2, height + label_band), (24, 24, 24))
    canvas.paste(before, (0, label_band))
    canvas.paste(after, (width, label_band))
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 10), f"BEFORE  {before_label}", fill=(240, 240, 240))
    draw.text((width + 8, 10), after_label, fill=(240, 240, 240))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_png)


def render_inactivation_pair(
    usd_path: Path,
    *,
    anchor: tuple[float, float, float],
    inactive_paths: list[str],
    before_out: Path,
    after_out: Path,
    mount_path: str = "/World/Show",
    distance: float,
    elevation: float = 10.0,
    azimuth: float = 45.0,
    width: int = 512,
    height: int = 384,
    render_steps: int = 30,
) -> dict[str, Any]:
    """Render the same camera before and after deactivating prim roots.

    The caller selects the Isaac runtime (e.g. scripts/isaac_python.sh or an
    explicit isaac41 python); this function must run inside that runtime.
    """
    from isaacsim import SimulationApp  # type: ignore

    simulation_app = SimulationApp(
        {"headless": True, "anti_aliasing": 2, "multi_gpu": False, "renderer": "RayTracedLighting"}
    )
    try:
        import omni  # type: ignore
        from omni.isaac.core.utils.stage import add_reference_to_stage  # type: ignore

        from convert_asset.render.single import (  # noqa: PLC0415
            DEFAULT_BACKGROUND_COLOR,
            _camera_rgba,
            _init_camera,
            _init_world,
            _rgba_to_rgb,
            _set_camera_look_at,
            _setup_environment,
        )

        world = _init_world()
        stage = omni.usd.get_context().get_stage()
        _setup_environment(stage)
        add_reference_to_stage(str(usd_path), mount_path)
        camera = _init_camera("workspace_evidence_camera", width, height, 18.0)
        _set_camera_look_at(camera, anchor, distance=distance, elevation=elevation, azimuth=azimuth)

        def capture(path: Path) -> None:
            rgba = None
            for _ in range(max(1, render_steps)):
                world.step(render=True)
                rgba = _camera_rgba(camera)
                if rgba is not None:
                    break
            if rgba is None:
                raise RuntimeError("empty camera readback")
            rgb = _rgba_to_rgb(rgba, background_color=DEFAULT_BACKGROUND_COLOR)
            from PIL import Image

            path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(rgb).save(path)

        capture(before_out)
        deactivated = []
        for prim_path in inactive_paths:
            target = stage.GetPrimAtPath(
                prim_path if prim_path.startswith(mount_path) else mount_path + prim_path
            )
            if not target.IsValid():
                raise RuntimeError(f"inactive prim missing: {prim_path}")
            target.SetActive(False)
            deactivated.append(prim_path)
        capture(after_out)
        return {
            "status": "pass",
            "before": str(before_out),
            "after": str(after_out),
            "deactivated": deactivated,
        }
    finally:
        simulation_app.close()
