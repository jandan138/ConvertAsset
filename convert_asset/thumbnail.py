# -*- coding: utf-8 -*-
"""Isaac Sim based multi-view thumbnail generator (with background).

Exposes run_thumbnail_pipeline() for CLI integration.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np


def _compute_2d_bbox_area(b: Tuple[int, float, float, float, float, float]) -> float:
    return max(0.0, float(b[3] - b[1])) * max(0.0, float(b[4] - b[2]))


def _compute_area_ratio(
    tight: Tuple[int, float, float, float, float, float],
    loose: Tuple[int, float, float, float, float, float],
) -> float:
    a_t = _compute_2d_bbox_area(tight)
    a_l = _compute_2d_bbox_area(loose)
    return (a_t / a_l) if a_l > 0.0 else 0.0


# --- Minimal Isaac helpers (lazy-import inside functions to avoid hard dependency) ---

def _init_world():
    from omni.isaac.core import World  # type: ignore

    world = World(stage_units_in_meters=1.0, physics_dt=0.01, rendering_dt=0.01)
    world.reset()
    return world


def _init_camera(name: str, w: int, h: int):
    from omni.isaac.sensor import Camera  # type: ignore

    cam = Camera(prim_path=f"/World/{name}", resolution=(int(w), int(h)))
    return cam


def _setup_camera(cam, focal_mm: float = 9.0, with_bbox2d: bool = True) -> None:
    cam.initialize()
    cam.set_focal_length(float(focal_mm))
    cam.set_clipping_range(0.01, 1000000.0)
    cam.set_vertical_aperture(15.2908)
    cam.set_horizontal_aperture(20.0955)
    cam.add_distance_to_image_plane_to_frame()
    if with_bbox2d:
        cam.add_bounding_box_2d_tight_to_frame()
        cam.add_bounding_box_2d_loose_to_frame()


def _get_rgb(cam) -> np.ndarray | None:
    frame = cam.get_rgba()
    if isinstance(frame, np.ndarray) and frame.size > 0:
        return frame[:, :, :3]
    return None


def _get_bbox2d_tight(cam):
    annot = cam._custom_annotators["bounding_box_2d_tight"]
    data = annot.get_data()
    return data["data"], data["info"]["idToLabels"]


def _get_bbox2d_loose(cam):
    annot = cam._custom_annotators["bounding_box_2d_loose"]
    data = annot.get_data()
    return data["data"], data["info"]["idToLabels"]


def _draw_bbox2d(image: np.ndarray, bbox2d) -> np.ndarray:
    im = np.array(image)
    x_min = int(bbox2d[1]); y_min = int(bbox2d[2])
    x_max = int(bbox2d[3]); y_max = int(bbox2d[4])
    im[y_min:y_min+2, x_min:x_max] = [255, 0, 0]
    im[y_max-2:y_max, x_min:x_max] = [255, 0, 0]
    im[y_min:y_max, x_min:x_min+2] = [255, 0, 0]
    im[y_min:y_max, x_max-2:x_max] = [255, 0, 0]
    return im


def _switch_all_lights(stage, action: str = "on") -> None:
    from pxr import UsdGeom  # type: ignore

    action = action.lower().strip()
    types = {"DistantLight", "SphereLight", "DiskLight", "RectLight", "CylinderLight"}
    for prim in stage.Traverse():
        if prim.GetTypeName() in types:
            img = UsdGeom.Imageable(prim)
            (img.MakeVisible() if action == "on" else img.MakeInvisible())


def _compute_bbox(prim):
    from pxr import Usd, UsdGeom  # type: ignore

    img = UsdGeom.Imageable(prim)
    t = Usd.TimeCode.Default()
    bound = img.ComputeWorldBound(t, UsdGeom.Tokens.default_)
    box = bound.ComputeAlignedBox()
    return np.array([box.min, box.max])


def _set_camera_look_at(cam, target: np.ndarray, distance: float, elevation: float, azimuth: float) -> None:
    import math
    import numpy as _np
    from scipy.spatial.transform import Rotation as R  # type: ignore

    elev_rad = math.radians(elevation)
    azim_rad = math.radians(azimuth)
    off_x = distance * math.cos(elev_rad) * math.cos(azim_rad)
    off_y = distance * math.cos(elev_rad) * math.sin(azim_rad)
    off_z = distance * math.sin(elev_rad)
    cam_pos = target + _np.array([off_x, off_y, off_z])
    rot = R.from_euler("xyz", [0, elevation, azimuth - 180], degrees=True).as_quat()
    quat = _np.array([rot[3], rot[0], rot[1], rot[2]])
    cam.set_world_pose(position=cam_pos, orientation=quat)


def _get_all_mesh_prims_from_scope(stage, scope_name: str = "scene/Instances"):
    from pxr import Usd  # type: ignore

    meshes: list = []
    scope_path = scope_name if scope_name.startswith("/") else f"/World/{scope_name}"
    scope = stage.GetPrimAtPath(scope_path)
    if not scope or not scope.IsValid():
        return meshes
    for child in scope.GetChildren():
        meshes.extend(_get_all_mesh_prims(child))
    return meshes


def _get_all_mesh_prims(root_prim):
    from pxr import Usd  # type: ignore

    out: list = []
    if not root_prim or not root_prim.IsValid():
        return out
    try:
        for p in Usd.PrimRange(root_prim):
            try:
                if p.GetTypeName() == "Mesh":
                    out.append(p)
            except Exception:
                continue
    except Exception:
        pass
    return out


def run_thumbnail_pipeline(
    *,
    scene_usd_path: str,
    output_dir: str | None = None,
    instance_scope: str = "scene/Instances",
    image_width: int = 600,
    image_height: int = 450,
    views: int = 6,
    warmup_steps: int = 1000,
    render_steps: int = 8,
    focal_mm: float = 9.0,
    bbox_threshold: float = 0.8,
    draw_bbox: bool = True,
    skip_model_filter: bool = True,
) -> int:
    """Run the multi-view thumbnail pipeline.

    Returns 0 on success, non-zero on failure.
    """
    import cv2  # type: ignore

    try:
        from isaacsim import SimulationApp  # type: ignore
    except Exception as e:  # pragma: no cover - runtime environment specific
        print("[ERROR] Isaac Sim not available:", e)
        return 3

    # Initialize Isaac Sim headless
    simulation_app = SimulationApp({
        "headless": True,
        "anti_aliasing": 4,
        "multi_gpu": False,
        "renderer": "PathTracing",
    })

    try:
        import omni  # type: ignore
        from omni.isaac.core.utils.stage import add_reference_to_stage  # type: ignore
        from omni.isaac.core.utils.semantics import add_update_semantics, remove_all_semantics  # type: ignore

        usd_path = Path(scene_usd_path).resolve()
        if not usd_path.exists():
            print("[ERROR] Scene USD not found:", usd_path)
            return 2

        out_dir = Path(output_dir).resolve() if output_dir else (usd_path.parent / "thumbnails" / "multi_views_with_bg")
        out_dir.mkdir(parents=True, exist_ok=True)
        print("[thumbnails] Output dir:", out_dir)

        # World + stage
        world = _init_world()
        add_reference_to_stage(str(usd_path), "/World/scene")
        stage = omni.usd.get_context().get_stage()
        _switch_all_lights(stage, "on")

        # Cameras
        sample_number = max(1, int(views))
        if sample_number % 2 != 0:
            sample_number += 1  # enforce even to split top/bottom halves
        cameras = []
        for i in range(sample_number):
            cam = _init_camera(f"camera_{i}", image_width, image_height)
            _setup_camera(cam, focal_mm=focal_mm, with_bbox2d=True)
            cameras.append(cam)

        instance_mesh_prims = _get_all_mesh_prims_from_scope(stage, scope_name=instance_scope)

        # Optional model filtering: check models directory next to USD (scene authoring layout often differs, so default is skip)
        extracted_object_names: set[str] | None = None
        if not skip_model_filter:
            models_dir = usd_path.parent / "models"
            if models_dir.exists():
                try:
                    extracted_object_names = {p.name for p in models_dir.iterdir() if p.is_dir()}
                except Exception:
                    extracted_object_names = None

        from tqdm import tqdm  # type: ignore
        for index, mesh_prim in enumerate(tqdm(instance_mesh_prims)):
            name = mesh_prim.GetName()
            if extracted_object_names is not None and name not in extracted_object_names:
                continue
            mesh_dir = out_dir / name
            if mesh_dir.exists() and any(mesh_dir.iterdir()):
                continue
            mesh_dir.mkdir(parents=True, exist_ok=True)

            add_update_semantics(mesh_prim, semantic_label=f"instance_{index}", type_label="class")
            bbox_min, bbox_max = _compute_bbox(mesh_prim)
            center = (bbox_min + bbox_max) / 2.0
            distance = float(np.linalg.norm(bbox_max - bbox_min)) * 1.0

            top_half = max(1, sample_number // 2)
            for i in range(sample_number):
                azimuth = 30.0 + i * 360.0 / float(top_half)
                elevation = 35.0 if i < top_half else -35.0
                _set_camera_look_at(cameras[i], center, distance=distance, elevation=elevation, azimuth=azimuth)

            for _ in range(int(warmup_steps)):
                world.step(render=False)
            for _ in range(int(render_steps)):
                world.step(render=True)

            all_top_valid = True
            for idx, cam in enumerate(cameras):
                rgb = _get_rgb(cam)
                save = True
                try:
                    bbox2d_tight = _get_bbox2d_tight(cam)[0]
                    bbox2d_loose = _get_bbox2d_loose(cam)[0]
                    detected = len(bbox2d_tight) > 0 and len(bbox2d_loose) > 0
                except Exception:
                    detected = False
                if detected:
                    t0 = bbox2d_tight[0]
                    l0 = bbox2d_loose[0]
                    ratio = _compute_area_ratio(t0, l0)
                    if ratio >= float(bbox_threshold):
                        if draw_bbox and rgb is not None:
                            rgb = _draw_bbox2d(rgb, t0)
                    else:
                        save = False
                else:
                    save = False
                    if idx < top_half:
                        all_top_valid = False
                if not all_top_valid and idx >= top_half:
                    save = False

                if save and rgb is not None:
                    import cv2  # local to avoid import cost when skipping
                    out_path = mesh_dir / f"{name}_with_bg_{idx}.png"
                    cv2.imwrite(str(out_path), cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB))

            # cleanup semantics to avoid accumulation
            from omni.isaac.core.utils.semantics import remove_all_semantics  # type: ignore
            remove_all_semantics(mesh_prim)

        return 0
    finally:
        try:
            simulation_app.close()
        except Exception:
            pass
