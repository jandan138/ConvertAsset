# -*- coding: utf-8 -*-
"""Scene target inventory and capture orchestration."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from convert_asset.camera.bounds import Bounds3D, compute_world_bounds
from convert_asset.camera.poses import CameraPoseSpec, plan_orbit_poses
from convert_asset.capture.manifest import CaptureRecord, append_capture_record, write_targets_json
from convert_asset.capture.targets import TargetConfig, TargetSpec, list_scene_targets, resolve_target_scope


def _open_usd_stage(scene_usd_path: str):
    from pxr import Usd  # type: ignore

    stage = Usd.Stage.Open(scene_usd_path)
    if stage is None:
        raise RuntimeError(f"Failed to open stage: {scene_usd_path}")
    return stage


def _scene_id(scene_usd_path: str) -> str:
    path = Path(scene_usd_path)
    if path.name == "layout.usd":
        return path.parent.name
    return path.stem


def _safe_bounds(stage, target: TargetSpec) -> Bounds3D | None:
    try:
        return compute_world_bounds(stage, target.prim_path)
    except Exception as exc:
        print(f"[target-list] warn: bbox failed for {target.prim_path}: {exc}")
        return None


def _targets_with_bounds(stage, targets: list[TargetSpec]) -> tuple[list[TargetSpec], dict[str, Bounds3D]]:
    valid_targets: list[TargetSpec] = []
    bounds_by_target: dict[str, Bounds3D] = {}
    for target in targets:
        bounds = _safe_bounds(stage, target)
        if bounds is None:
            continue
        valid_targets.append(target)
        bounds_by_target[target.target_id] = bounds
    return valid_targets, bounds_by_target


def _print_target_table(targets: Iterable[TargetSpec], bounds_by_target: dict[str, Bounds3D]) -> None:
    for index, target in enumerate(targets):
        bounds = bounds_by_target.get(target.target_id)
        bbox = ""
        if bounds is not None:
            bbox = (
                f" center=({bounds.center[0]:.3f},{bounds.center[1]:.3f},{bounds.center[2]:.3f})"
                f" size=({bounds.size[0]:.3f},{bounds.size[1]:.3f},{bounds.size[2]:.3f})"
            )
        print(
            f"{index:04d} category={target.category} id={target.target_id} "
            f"meshes={target.mesh_count} path={target.prim_path}{bbox}"
        )


def run_target_list(
    *,
    scene_usd_path: str,
    output_path: str | None = None,
    target_scope: str = "auto",
    target_level: str = "object",
    include_animation: bool = False,
    limit: int | None = None,
) -> int:
    """List logical capture targets for one scene USD."""
    stage = _open_usd_stage(scene_usd_path)
    config = TargetConfig(
        target_scope=target_scope,
        target_level=target_level,
        include_animation=include_animation,
        limit=limit,
    )
    scope_path = resolve_target_scope(stage, target_scope)
    discovered_targets = list_scene_targets(stage, config)
    targets, bounds_by_target = _targets_with_bounds(stage, discovered_targets)

    print(f"[target-list] scene={scene_usd_path}")
    print(f"[target-list] scope={scope_path} level={target_level}")
    print(f"[target-list] targets={len(targets)}")
    _print_target_table(targets, bounds_by_target)
    if output_path:
        write_targets_json(output_path, targets, bounds_by_target)
        print(f"[target-list] wrote {output_path}")
    return 0


def _normalize_vec(vec: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(float(v) * float(v) for v in vec))
    if length <= 1.0e-9 or not math.isfinite(length):
        return (0.0, 0.0, 0.0)
    return tuple(float(v) / length for v in vec)  # type: ignore[return-value]


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _ensure_camera(stage, camera_path: str, *, focal_mm: float, aspect: float) -> None:
    from pxr import Gf, Sdf, UsdGeom  # type: ignore

    parent = str(Sdf.Path(camera_path).GetParentPath())
    if parent and parent != "/":
        UsdGeom.Xform.Define(stage, Sdf.Path(parent))
    camera = UsdGeom.Camera.Define(stage, Sdf.Path(camera_path))
    fov_h = math.radians(55.0)
    horiz_aperture = 2.0 * float(focal_mm) * math.tan(fov_h * 0.5)
    camera.GetFocalLengthAttr().Set(float(focal_mm))
    camera.GetHorizontalApertureAttr().Set(float(horiz_aperture))
    camera.GetVerticalApertureAttr().Set(float(horiz_aperture) / max(float(aspect), 1.0e-6))
    camera.GetClippingRangeAttr().Set(Gf.Vec2f(0.01, 1000000.0))


def _prefer_session_edit_target(stage) -> None:
    try:
        session_layer = stage.GetSessionLayer()
        if session_layer is not None:
            stage.SetEditTarget(session_layer)
    except Exception:
        pass


def _validate_capture_options(*, views: int, width: int, height: int, focal_mm: float, wait_frames: int, image_ext: str) -> None:
    if int(views) <= 0:
        raise ValueError("--views must be > 0")
    if int(width) <= 0:
        raise ValueError("--width must be > 0")
    if int(height) <= 0:
        raise ValueError("--height must be > 0")
    if float(focal_mm) <= 0.0:
        raise ValueError("--focal-mm must be > 0")
    if int(wait_frames) < 0:
        raise ValueError("--wait-frames must be >= 0")
    if not image_ext or any(ch in image_ext for ch in "/\\"):
        raise ValueError("--image-ext must be a file extension, not a path")


def _set_camera_pose(stage, camera_path: str, pose: CameraPoseSpec) -> None:
    from pxr import Gf, Sdf, UsdGeom  # type: ignore

    prim = stage.GetPrimAtPath(Sdf.Path(camera_path))
    if not prim or not prim.IsValid():
        raise RuntimeError(f"Camera prim missing: {camera_path}")

    eye = tuple(float(v) for v in pose.position)
    target = tuple(float(v) for v in pose.target)
    forward = _normalize_vec((target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]))
    world_up = (0.0, 0.0, 1.0)
    right = _normalize_vec(_cross(forward, world_up))
    if right == (0.0, 0.0, 0.0):
        right = (1.0, 0.0, 0.0)
    up = _normalize_vec(_cross(right, forward))
    if up == (0.0, 0.0, 0.0):
        up = world_up

    matrix = Gf.Matrix4d(1.0)
    matrix.SetRow(0, Gf.Vec4d(right[0], right[1], right[2], 0.0))
    matrix.SetRow(1, Gf.Vec4d(up[0], up[1], up[2], 0.0))
    matrix.SetRow(2, Gf.Vec4d(-forward[0], -forward[1], -forward[2], 0.0))
    matrix.SetRow(3, Gf.Vec4d(eye[0], eye[1], eye[2], 1.0))

    xformable = UsdGeom.Xformable(prim)
    ops = xformable.GetOrderedXformOps()
    xop = None
    for op in ops:
        if op.GetOpType() == UsdGeom.XformOp.TypeTransform:
            xop = op
            break
    if xop is None:
        xop = xformable.AddTransformOp()
    xop.Set(matrix)


def _capture_output_path(
    output_root: Path,
    scene_id: str,
    target: TargetSpec,
    pose: CameraPoseSpec,
    *,
    image_ext: str,
) -> Path:
    return (
        output_root
        / scene_id
        / target.category
        / target.target_id
        / f"view_{pose.view_index:03d}.{image_ext.lstrip('.')}"
    )


def run_target_capture(
    *,
    scene_usd_path: str,
    output_dir: str | None = None,
    target_scope: str = "auto",
    target_level: str = "object",
    include_animation: bool = False,
    limit: int | None = None,
    views: int = 6,
    width: int = 1024,
    height: int = 768,
    focal_mm: float = 35.0,
    renderer: str = "RayTracedLighting",
    headless: bool = True,
    wait_frames: int = 2,
    camera_path: str = "/World/TargetCaptureCamera",
    resume: bool = True,
    image_ext: str = "png",
) -> int:
    """Capture multi-view images for logical targets in one scene USD."""
    from convert_asset.render.viewport import (
        capture_viewport_image,
        create_simulation_app,
        enable_viewport_extension,
        get_viewport,
        open_stage,
        wait_frames as wait_app_frames,
    )

    usd_path = Path(scene_usd_path).resolve()
    if not usd_path.exists():
        print("[target-capture] scene not found:", usd_path)
        return 2
    try:
        _validate_capture_options(
            views=views,
            width=width,
            height=height,
            focal_mm=focal_mm,
            wait_frames=wait_frames,
            image_ext=image_ext,
        )
    except ValueError as exc:
        print("[target-capture]", exc)
        return 2
    out_root = Path(output_dir).resolve() if output_dir else (usd_path.parent / "target_capture")
    scene_id = _scene_id(str(usd_path))
    scene_out = out_root / scene_id
    scene_out.mkdir(parents=True, exist_ok=True)
    manifest_path = scene_out / "manifest.jsonl"
    targets_path = scene_out / "targets.json"
    if manifest_path.exists():
        manifest_path.unlink()

    try:
        app = create_simulation_app(headless=headless, renderer=renderer)
    except Exception as exc:
        print("[target-capture] failed to start Isaac SimulationApp:", exc)
        return 3
    failures = 0
    try:
        wait_app_frames(app, 1)
        enable_viewport_extension()
        wait_app_frames(app, 2)
        stage = open_stage(app, str(usd_path))
        config = TargetConfig(
            target_scope=target_scope,
            target_level=target_level,
            include_animation=include_animation,
            limit=limit,
        )
        discovered_targets = list_scene_targets(stage, config)
        targets, bounds_by_target = _targets_with_bounds(stage, discovered_targets)
        write_targets_json(targets_path, targets, bounds_by_target)
        if not targets:
            print(f"[target-capture] no valid targets after bbox filtering; discovered={len(discovered_targets)}")
            return 4 if discovered_targets else 0

        _prefer_session_edit_target(stage)
        _ensure_camera(stage, camera_path, focal_mm=focal_mm, aspect=float(width) / max(float(height), 1.0))
        _window, viewport = get_viewport(width, height)
        viewport.camera_path = camera_path

        print(f"[target-capture] scene={usd_path}")
        print(f"[target-capture] targets={len(targets)} views={views} out={scene_out}")

        for target in targets:
            bounds = bounds_by_target.get(target.target_id)
            if bounds is None:
                failures += 1
                record = CaptureRecord(
                    scene_usd_path=str(usd_path),
                    target=target,
                    bounds=None,
                    pose=None,
                    output_path="",
                    status="failed",
                    error="bbox unavailable",
                )
                append_capture_record(manifest_path, record)
                continue

            for pose in plan_orbit_poses(bounds, views=views, aspect=float(width) / max(float(height), 1.0)):
                out_path = _capture_output_path(out_root, scene_id, target, pose, image_ext=image_ext)
                if resume and out_path.exists() and out_path.stat().st_size > 0:
                    status = "skipped"
                    error = None
                else:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        _set_camera_pose(stage, camera_path, pose)
                        wait_app_frames(app, wait_frames)
                        ok = capture_viewport_image(viewport, out_path, app=app, wait_frames=wait_frames)
                        status = "ok" if ok else "failed"
                        error = None if ok else "capture output missing or empty"
                    except Exception as exc:
                        status = "failed"
                        error = str(exc)
                if status == "failed":
                    failures += 1
                append_capture_record(
                    manifest_path,
                    CaptureRecord(
                        scene_usd_path=str(usd_path),
                        target=target,
                        bounds=bounds,
                        pose=pose,
                        output_path=str(out_path),
                        status=status,
                        error=error,
                    ),
                )
        return 0 if failures == 0 else 4
    finally:
        try:
            wait_app_frames(app, 1)
        except Exception:
            pass
        try:
            app.close()
        except Exception:
            pass
