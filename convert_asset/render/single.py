# -*- coding: utf-8 -*-
"""Single-asset rendering through the repository's local Isaac Sim runtime.

The module stays import-clean: Isaac, Omni, USD, cv2, and numpy are imported
inside runtime functions only, after SimulationApp has been created.
"""
from __future__ import annotations

import gc
import math
import os
from pathlib import Path
from typing import Iterable


VIEW_NAMES = ("front", "left", "back", "right")
DEFAULT_BACKGROUND_COLOR = (40, 40, 40)


def plan_output_paths(
    *,
    usd_path: str | os.PathLike[str],
    output_root: str | os.PathLike[str],
    sample_number: int,
    naming_style: str,
) -> list[Path]:
    """Return the PNG paths for a single render job without touching Isaac."""
    if int(sample_number) < 1:
        raise ValueError("sample_number must be positive")
    if naming_style not in {"index", "view"}:
        raise ValueError("naming_style must be 'index' or 'view'")

    usd = Path(usd_path)
    object_name = usd.stem or "asset"
    save_dir = Path(output_root) / object_name

    paths: list[Path] = []
    for idx in range(int(sample_number)):
        if naming_style == "view" and int(sample_number) == 4:
            filename = f"{VIEW_NAMES[idx]}.png"
        else:
            filename = f"{object_name}_{idx}.png"
        paths.append(save_dir / filename)
    return paths


def _collect_mdl_paths(cli_paths: Iterable[str] | None) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()

    def add_path(raw: str | None) -> None:
        if not raw:
            return
        path = os.path.abspath(os.path.expanduser(raw))
        if path in seen or not os.path.isdir(path):
            return
        seen.add(path)
        paths.append(path)

    for raw in cli_paths or []:
        add_path(raw)
    for raw in os.environ.get("MDL_SYSTEM_PATH", "").split(":"):
        add_path(raw.strip())
    return paths


def _configure_mdl_search_paths(paths: Iterable[str]) -> None:
    paths = list(paths)
    if not paths:
        return
    import carb.settings  # type: ignore

    settings = carb.settings.get_settings()
    existing = settings.get("/app/mdl/additionalSystemPaths") or []
    merged = list(existing)
    for path in paths:
        if path not in merged:
            merged.append(path)
    settings.set_string_array("/app/mdl/additionalSystemPaths", merged)
    print(f"[render-single] MDL search paths configured: {merged}")


def _parse_rgb_color(value) -> tuple[int, int, int]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
    else:
        parts = list(value)
    if len(parts) != 3:
        raise ValueError("background color must be R,G,B")
    color = tuple(int(part) for part in parts)
    if any(channel < 0 or channel > 255 for channel in color):
        raise ValueError("background color channels must be in 0..255")
    return color


def _configure_background_zero_alpha(settings) -> None:
    settings.set("/rtx/post/backgroundZeroAlpha/enabled", True)
    settings.set("/rtx/post/backgroundZeroAlpha/backgroundComposite", False)
    settings.set("/rtx/post/backgroundZeroAlpha/outputAlphaInComposite", True)
    settings.set("/app/captureFrame/setAlphaTo1", False)


def _find_builtin_hdri() -> str | None:
    roots: list[Path] = []

    def add_root(raw) -> None:
        if not raw:
            return
        root = Path(raw).expanduser()
        if root not in roots:
            roots.append(root)

    add_root(os.environ.get("ISAAC_SIM_ROOT"))

    try:
        import isaacsim  # type: ignore
    except Exception:
        pass
    else:
        package_file = getattr(isaacsim, "__file__", None)
        if package_file:
            package_dir = Path(package_file).resolve().parent
            add_root(package_dir)
            for parent in package_dir.parents:
                add_root(parent)
    add_root("/isaac-sim")

    for root in roots:
        for pattern in (
            "extscache/omni.kit.widget.material_preview-*/data/photo_studio_01_4k.hdr",
            "extscache/omni.kit.widget.material_preview-*/data/domeLight/photo_studio_01_4k.hdr",
        ):
            for candidate in sorted(root.glob(pattern)):
                if candidate.exists():
                    return str(candidate)
        direct = root / "extscache" / "omni.kit.widget.material_preview-1.0.16" / "data" / "photo_studio_01_4k.hdr"
        if direct.exists():
            return str(direct)
        direct_dome = root / "extscache" / "omni.kit.widget.material_preview-1.0.16" / "data" / "domeLight" / "photo_studio_01_4k.hdr"
        if direct_dome.exists():
            return str(direct_dome)
        if root.name.startswith("omni.kit.widget.material_preview-"):
            candidate = root / "data" / "photo_studio_01_4k.hdr"
            if candidate.exists():
                return str(candidate)
    return None


def _init_world(
    *,
    stage_units_in_meters: float = 1.0,
    physics_dt: float = 0.01,
    rendering_dt: float = 0.01,
):
    """Create a World whose metric interpretation matches the open USD stage."""
    from omni.isaac.core import World  # type: ignore

    world = World(
        stage_units_in_meters=float(stage_units_in_meters),
        physics_dt=float(physics_dt),
        rendering_dt=float(rendering_dt),
    )
    world.reset()
    return world


def _init_camera(name: str, width: int, height: int, focal_mm: float):
    from omni.isaac.sensor import Camera  # type: ignore

    camera = Camera(prim_path=f"/World/{name}", resolution=(int(width), int(height)))
    camera.initialize()
    camera.set_focal_length(float(focal_mm))
    camera.set_clipping_range(0.01, 1000000.0)
    camera.set_vertical_aperture(15.2908)
    camera.set_horizontal_aperture(20.0955)
    return camera


def _setup_environment(stage) -> None:
    from pxr import Gf, UsdGeom, UsdLux  # type: ignore

    UsdGeom.Xform.Define(stage, "/World")
    dome = UsdLux.DomeLight.Define(stage, "/World/default_dome_light")
    dome.CreateTextureFormatAttr(UsdLux.Tokens.latlong)

    hdri_path = _find_builtin_hdri()
    if hdri_path:
        dome.CreateIntensityAttr(1500.0)
        dome.CreateTextureFileAttr(hdri_path)
        dome.CreateColorAttr(Gf.Vec3f(1.0, 1.0, 1.0))
        try:
            import carb.settings  # type: ignore

            _configure_background_zero_alpha(carb.settings.get_settings())
        except Exception as exc:
            print(f"[render-single] Warning configuring transparent background: {exc}")
        print(f"[render-single] HDRI environment loaded: {hdri_path}")
        return

    dome.CreateIntensityAttr(1000.0)
    dome.CreateColorAttr(Gf.Vec3f(0.18, 0.18, 0.18))
    dome.CreateExposureAttr(0.0)
    print("[render-single] Built-in HDRI not found; using gray DomeLight fallback")


def _range_to_bbox(range_obj):
    import numpy as np  # type: ignore

    bbox = np.array([range_obj.min, range_obj.max], dtype=float)
    return bbox


def _is_valid_bbox(bbox) -> bool:
    import numpy as np  # type: ignore

    if bbox is None:
        return False
    return bool(np.isfinite(bbox).all() and np.linalg.norm(bbox[1] - bbox[0]) > 0)


def _bbox_cache_bbox(prim):
    from pxr import Usd, UsdGeom  # type: ignore

    purposes = [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy]
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), purposes, useExtentsHint=True)
    return _range_to_bbox(cache.ComputeWorldBound(prim).ComputeAlignedRange())


def _mesh_point_bbox(prim):
    import numpy as np  # type: ignore
    from pxr import Usd, UsdGeom  # type: ignore

    def is_default_visible(imageable, time) -> bool:
        if imageable.ComputeEffectiveVisibility(time=time) == UsdGeom.Tokens.invisible:
            return False
        return imageable.ComputePurpose() == UsdGeom.Tokens.default_

    def union_bbox(first, second):
        if first is None:
            return second
        if second is None:
            return first
        return np.array(
            [np.minimum(first[0], second[0]), np.maximum(first[1], second[1])],
            dtype=float,
        )

    time = Usd.TimeCode.Default()
    bbox = None
    for child in Usd.PrimRange(prim):
        imageable = UsdGeom.Imageable(child)
        if not is_default_visible(imageable, time):
            continue
        if child.IsA(UsdGeom.Mesh):
            points = child.GetAttribute("points").Get()
            if not points:
                continue
            try:
                points_np = np.array([point for point in points], dtype=float)
            except (TypeError, ValueError):
                continue
            if points_np.size == 0 or points_np.ndim != 2 or points_np.shape[1] != 3:
                continue

            transform = np.array(imageable.ComputeLocalToWorldTransform(time), dtype=float)
            ones = np.ones((points_np.shape[0], 1), dtype=float)
            points_h = np.hstack([points_np, ones])
            points_world_h = np.dot(points_h, transform)
            with np.errstate(divide="ignore", invalid="ignore"):
                points_world = points_world_h[:, :3] / points_world_h[:, 3][:, None]
            points_world = points_world[np.isfinite(points_world).all(axis=1)]
            if points_world.size == 0:
                continue

            child_bbox = np.array(
                [np.min(points_world, axis=0), np.max(points_world, axis=0)],
                dtype=float,
            )
            bbox = union_bbox(bbox, child_bbox)
            continue

        if child.IsA(UsdGeom.Boundable):
            boundable = UsdGeom.Boundable(child)
            bound_range = boundable.ComputeWorldBound(time, UsdGeom.Tokens.default_).ComputeAlignedBox()
            child_bbox = _range_to_bbox(bound_range)
            if _is_valid_bbox(child_bbox):
                bbox = union_bbox(bbox, child_bbox)
    return bbox


def _choose_bbox(
    authored_bbox,
    mesh_bbox,
    *,
    extent_fallback_ratio: float,
    center_offset_threshold: float,
):
    import numpy as np  # type: ignore

    if not np.isfinite(extent_fallback_ratio) or extent_fallback_ratio <= 0:
        raise ValueError("extent_fallback_ratio must be finite and positive")
    if not np.isfinite(center_offset_threshold) or center_offset_threshold <= 0:
        raise ValueError("center_offset_threshold must be finite and positive")

    if not _is_valid_bbox(mesh_bbox):
        return authored_bbox, "authored_no_mesh_fallback"
    if not _is_valid_bbox(authored_bbox):
        return mesh_bbox, "mesh_invalid_authored"

    authored_diagonal = np.linalg.norm(authored_bbox[1] - authored_bbox[0])
    mesh_diagonal = np.linalg.norm(mesh_bbox[1] - mesh_bbox[0])
    if mesh_diagonal <= 0 or not np.isfinite(mesh_diagonal):
        return authored_bbox, "authored_invalid_mesh_diagonal"
    if authored_diagonal / mesh_diagonal >= extent_fallback_ratio:
        return mesh_bbox, "mesh_extent_ratio"

    authored_center = (authored_bbox[0] + authored_bbox[1]) / 2.0
    mesh_center = (mesh_bbox[0] + mesh_bbox[1]) / 2.0
    center_offset_ratio = np.linalg.norm(authored_center - mesh_center) / mesh_diagonal
    if center_offset_ratio >= center_offset_threshold:
        return mesh_bbox, "mesh_center_offset"
    return authored_bbox, "authored"


def _compute_bbox(
    prim,
    *,
    extent_fallback_ratio: float = 5.0,
    center_offset_threshold: float = 1.0,
):
    authored_bbox = _bbox_cache_bbox(prim)
    mesh_bbox = _mesh_point_bbox(prim)
    return _choose_bbox(
        authored_bbox,
        mesh_bbox,
        extent_fallback_ratio=extent_fallback_ratio,
        center_offset_threshold=center_offset_threshold,
    )


def _set_camera_look_at(camera, target, *, distance: float, elevation: float, azimuth: float) -> None:
    import numpy as np  # type: ignore
    from scipy.spatial.transform import Rotation as R  # type: ignore

    elev_rad = math.radians(float(elevation))
    azim_rad = math.radians(float(azimuth))
    offset_x = float(distance) * math.cos(elev_rad) * math.cos(azim_rad)
    offset_y = float(distance) * math.cos(elev_rad) * math.sin(azim_rad)
    offset_z = float(distance) * math.sin(elev_rad)
    camera_position = target + np.array([offset_x, offset_y, offset_z], dtype=float)
    rot = R.from_euler("xyz", [0, float(elevation), float(azimuth) - 180.0], degrees=True).as_quat()
    quaternion = np.array([rot[3], rot[0], rot[1], rot[2]], dtype=float)
    camera.set_world_pose(position=camera_position, orientation=quaternion)


def _camera_rgba(camera):
    import numpy as np  # type: ignore

    frame = camera.get_rgba()
    if isinstance(frame, np.ndarray) and frame.size > 0:
        return frame
    return None


def _rgba_to_rgb(rgba, *, background_color=DEFAULT_BACKGROUND_COLOR):
    import numpy as np  # type: ignore

    arr = np.asarray(rgba)
    if arr.dtype != np.uint8:
        arr = np.nan_to_num(arr.astype(np.float32), nan=0.0, posinf=255.0, neginf=0.0)
        if arr.size and float(np.nanmax(arr)) <= 1.0:
            arr = arr * 255.0
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    if arr.ndim == 3 and arr.shape[2] == 4:
        alpha = arr[:, :, 3:4].astype(np.float32) / 255.0
        bg_color = np.array(_parse_rgb_color(background_color), dtype=np.float32).reshape(1, 1, 3)
        background = np.broadcast_to(bg_color, arr[:, :, :3].shape)
        return (arr[:, :, :3].astype(np.float32) * alpha + background * (1.0 - alpha)).astype(np.uint8)
    if arr.ndim == 3 and arr.shape[2] >= 3:
        return arr[:, :, :3].astype(np.uint8)
    return None


def _save_rgb_png(path: Path, rgb) -> bool:
    import cv2  # type: ignore

    path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)))


def _cleanup_cameras(cameras: list) -> None:
    for camera in cameras:
        try:
            if hasattr(camera, "_custom_annotators"):
                camera._custom_annotators.clear()
            if hasattr(camera, "_render_product"):
                camera._render_product = None
        except Exception as exc:
            print(f"[render-single] Warning cleaning camera: {exc}")


def run_render_single(
    *,
    usd_path: str | os.PathLike[str],
    output_root: str | os.PathLike[str],
    width: int = 512,
    height: int = 512,
    sample_number: int = 4,
    naming_style: str = "index",
    overwrite: bool = False,
    warmup_steps: int = 100,
    render_steps: int = 8,
    focal_mm: float = 18.0,
    elevation: float = 35.0,
    azimuth_offset: float = 0.0,
    min_distance: float = 0.1,
    background_color=DEFAULT_BACKGROUND_COLOR,
    extent_fallback_ratio: float = 5.0,
    center_offset_threshold: float = 1.0,
    renderer: str = "PathTracing",
    mdl_paths: Iterable[str] | None = None,
) -> int:
    """Render one USD from orbit views using local Isaac Sim.

    Returns 0 on success, 2 for bad inputs, 3 for runtime errors, and 4 if no
    PNG was produced.
    """
    usd = Path(usd_path).expanduser().resolve()
    if not usd.exists():
        print("[render-single] USD not found:", usd)
        return 2
    if int(width) <= 0 or int(height) <= 0 or int(sample_number) <= 0:
        print("[render-single] width, height, and views must be positive")
        return 2
    try:
        background_rgb = _parse_rgb_color(background_color)
        extent_fallback_ratio = float(extent_fallback_ratio)
        center_offset_threshold = float(center_offset_threshold)
        if (
            not math.isfinite(extent_fallback_ratio)
            or not math.isfinite(center_offset_threshold)
            or extent_fallback_ratio <= 0
            or center_offset_threshold <= 0
        ):
            raise ValueError("bbox fallback thresholds must be finite and positive")
    except (TypeError, ValueError) as exc:
        print("[render-single] Invalid render option:", exc)
        return 2

    planned_paths = plan_output_paths(
        usd_path=usd,
        output_root=Path(output_root).expanduser().resolve(),
        sample_number=int(sample_number),
        naming_style=naming_style,
    )
    if planned_paths and not overwrite and all(path.exists() for path in planned_paths):
        print(f"[render-single] Skip existing renders: {planned_paths[0].parent}")
        return 0

    try:
        from isaacsim import SimulationApp  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on Isaac runtime
        print("[render-single] Isaac Sim not available:", exc)
        return 3

    simulation_app = None
    cameras: list = []
    world = None
    show_prim_path = "/World/Show"
    delete_prim_func = None
    saved_count = 0

    try:
        simulation_app = SimulationApp({
            "headless": True,
            "anti_aliasing": 4,
            "multi_gpu": False,
            "renderer": str(renderer),
        })

        import numpy as np  # type: ignore
        import omni  # type: ignore
        from omni.isaac.core.utils.prims import delete_prim  # type: ignore
        from omni.isaac.core.utils.stage import add_reference_to_stage  # type: ignore

        delete_prim_func = delete_prim
        _configure_mdl_search_paths(_collect_mdl_paths(mdl_paths))

        world = _init_world()
        stage = omni.usd.get_context().get_stage()
        _setup_environment(stage)
        try:
            delete_prim(show_prim_path)
        except Exception:
            pass
        add_reference_to_stage(str(usd), show_prim_path)
        prim = stage.GetPrimAtPath(show_prim_path)
        if prim is None or not prim.IsValid():
            print("[render-single] Failed to load USD prim:", usd)
            return 3

        bbox, bbox_source = _compute_bbox(
            prim,
            extent_fallback_ratio=extent_fallback_ratio,
            center_offset_threshold=center_offset_threshold,
        )
        if not _is_valid_bbox(bbox):
            print("[render-single] Invalid bounding box:", usd)
            return 3

        bbox_min, bbox_max = bbox
        center = (bbox_min + bbox_max) / 2.0
        distance = max(
            float(min_distance),
            float(np.linalg.norm(bbox_max - bbox_min)),
        )
        print(
            f"[render-single] center={center.tolist()} distance={distance:.4f} "
            f"bbox_source={bbox_source}"
        )

        for idx in range(int(sample_number)):
            camera = _init_camera(f"render_camera_{idx}", int(width), int(height), float(focal_mm))
            azimuth = float(azimuth_offset) + idx * 360.0 / float(sample_number)
            _set_camera_look_at(
                camera,
                center,
                distance=distance,
                elevation=float(elevation),
                azimuth=azimuth,
            )
            cameras.append(camera)

        for _ in range(max(0, int(warmup_steps))):
            world.step(render=False)
        for _ in range(max(1, int(render_steps))):
            world.step(render=True)

        for path, camera in zip(planned_paths, cameras):
            if path.exists() and not overwrite:
                print("[render-single] Exists, skip:", path)
                saved_count += 1
                continue
            rgba = _camera_rgba(camera)
            rgb = _rgba_to_rgb(rgba, background_color=background_rgb) if rgba is not None else None
            if rgb is None:
                print("[render-single] Empty frame:", path)
                continue
            if _save_rgb_png(path, rgb):
                saved_count += 1
                print("[render-single] Saved:", path)
            else:
                print("[render-single] Failed to save:", path)

        return 0 if saved_count > 0 else 4
    except Exception as exc:
        print("[render-single] ERROR:", exc)
        return 3
    finally:
        _cleanup_cameras(cameras)
        if delete_prim_func is not None:
            try:
                delete_prim_func(show_prim_path)
            except Exception:
                pass
        if world is not None:
            try:
                world.reset()
            except Exception:
                pass
        gc.collect()
        if simulation_app is not None:
            try:
                simulation_app.close()
            except Exception:
                pass
