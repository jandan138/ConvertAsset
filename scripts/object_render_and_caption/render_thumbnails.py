# Rendering the object to the thumbnail images and thumbnails with their corresponding background.
# Input: 1. the object usd file. 2. the usd file after instance segmentation. 
# Output: 1. the thumbnail images. 2. the thumbnails with their corresponding background.
import argparse
import os
import sys
import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path
from natsort import natsorted
from typing import Tuple

parser = argparse.ArgumentParser(description="Render multi-view thumbnails of scene instances with background using Isaac Sim")
parser.add_argument("--objects_dir", required=False, help="Path to objects root, e.g., /path/to/instances")
parser.add_argument("--scene_dir", required=False, help="Absolute path to scenes root, e.g., /path/to/GRScenes")
parser.add_argument('--part', type=int, default=1, help="Partition index (e.g., 1 => part1)")
parser.add_argument('--usd', type=int, required=False, help="USD index under part, e.g., 0 => 0_usd")
parser.add_argument("--scene", type=str, default=None, help="Optional specific scene name to process (structured mode)")
parser.add_argument("--scene-usd", dest="scene_usd", type=str, default=None, help="Single-USD mode: absolute path to a .usd file to render")
parser.add_argument("--output-dir", dest="output_dir", type=str, default=None, help="Output directory for thumbnails (defaults next to USD)")
parser.add_argument("--instance-scope", dest="instance_scope", type=str, default="scene/Instances", help="Scope under /World containing instances (single-USD mode)")
parser.add_argument("--skip-model-filter", dest="skip_model_filter", action="store_true", help="Skip filtering by models dir names")
args = parser.parse_args()

try:
    from isaacsim import SimulationApp
except Exception as e:
    print("[ERROR] Failed to import isaacsim. Please run inside Omniverse Isaac Sim Python environment.")
    print(f"Detail: {e}")
    sys.exit(1)

simulation_app = SimulationApp({
    "headless": True,
    "anti_aliasing": 4,
    "multi_gpu": False,
    "renderer": "PathTracing",
})

import omni
from pxr import Usd
from omni.isaac.core.utils.stage import add_reference_to_stage                          # type: ignore
from omni.isaac.core.utils.prims import delete_prim, create_prim                        # type: ignore
from omni.isaac.core.utils.semantics import add_update_semantics, remove_all_semantics  # type: ignore

from render_utils import init_world, switch_all_lights, init_camera, setup_camera
from render_utils import get_all_mesh_prims_from_scope, compute_bbox, set_camera_look_at, get_src, draw_bbox2d
from render_utils import find_all_files_in_folder

def compute_2d_bbox_area(bbox2d_data: Tuple[int, float, float, float, float, float]) -> float:
    width = bbox2d_data[3] - bbox2d_data[1]
    height = bbox2d_data[4] - bbox2d_data[2]
    area = width * height
    return area

def compute_2d_bbox_area_ratio(
    bbox2d_tight    : Tuple[int, float, float, float, float, float], 
    bbox2d_loose: Tuple[int, float, float, float, float, float]
    ) -> float:
    tight_area = compute_2d_bbox_area(bbox2d_tight)
    loose_area = compute_2d_bbox_area(bbox2d_loose)
    # print(f"[DEBUG] tight_area: {tight_area}, loose_area: {loose_area}")
    if loose_area > 0:
        return tight_area / loose_area
    else:
        return 0.0
        
def render_thumbnail_with_bg(scene_usd_path, object_usd_dir, thumbnail_with_bg_dir, show_bbox2d=True, instance_scope: str = "scene/Instances", skip_model_filter: bool = False):
    # Auto exposure
    omni.kit.commands.execute('ChangeSetting', path='/rtx/post/histogram/enabled', value=True)
    omni.kit.commands.execute('ChangeSetting', path='/rtx/post/histogram/whiteScale', value=10.0)
    # Ensure output dir is a Path object
    from pathlib import Path as _Path
    if not isinstance(thumbnail_with_bg_dir, _Path):
        thumbnail_with_bg_dir = _Path(thumbnail_with_bg_dir)

    # World settings
    world = init_world()
    add_reference_to_stage(scene_usd_path, "/World/scene")
    stage = omni.usd.get_context().get_stage()
    switch_all_lights(stage, 'on')
    # Camera settings
    sample_number = 3 + 3
    cameras = []
    for i in range(sample_number):
        camera = init_camera(f"camera_{i}", image_width=600, image_height=450)
        setup_camera(camera, with_bbox2d=show_bbox2d, focal_length=9.0)
        cameras.append(camera)
    instance_mesh_prims = get_all_mesh_prims_from_scope(stage, scope_name=instance_scope)
    extracted_object_names = None
    if (not skip_model_filter) and object_usd_dir is not None:
        object_models_dir = object_usd_dir / "models"
        if os.path.exists(object_models_dir):
            extracted_object_names = natsorted(os.listdir(object_models_dir))
    for index, mesh_prim in enumerate(tqdm(instance_mesh_prims)):
        # # debug
        # if mesh_prim.GetName() != "___1986702865_1":
        #     continue
        mesh_prim_name = mesh_prim.GetName()
        if extracted_object_names is not None:
            if mesh_prim_name not in extracted_object_names:
                print(f"[GRGenerator: Render Thumbnail With Background] {mesh_prim_name} is not extracted, skip.")
                continue
        mesh_dir = thumbnail_with_bg_dir / mesh_prim.GetName()
        if os.path.exists(mesh_dir) and len(os.listdir(mesh_dir)) > 0:
            continue
        add_update_semantics(mesh_prim, semantic_label=f"instance_{index}", type_label="class")
        bbox_min, bbox_max = compute_bbox(mesh_prim)
        center = (bbox_min + bbox_max) / 2
        distance = np.linalg.norm(bbox_max - bbox_min) * 1.0
        print(f"[DEBUG] {mesh_prim.GetName()} bbox_min: {bbox_min}, bbox_max: {bbox_max}, center: {center}, distance: {distance}")
        top_half = sample_number // 2
        for i in range(sample_number):
            azimuth = 30 + i * 360 / max(1, top_half)
            elevation = 35 if i < top_half else -35
            set_camera_look_at(cameras[i], center, azimuth=azimuth, elevation=elevation, distance=distance)
        for _ in range(1000):
            world.step(render=False)
        for _ in range(8):
            world.step(render=True)
        os.makedirs(thumbnail_with_bg_dir / mesh_prim.GetName(), exist_ok=True)
        all_top_views_valid = True
        for idx, camera in enumerate(cameras):
            rgb = get_src(camera, "rgb")
            need_save = True
            if show_bbox2d:
                bbox2d_tight = get_src(camera, "bbox2d_tight")[0]
                bbox2d_loose = get_src(camera, "bbox2d_loose")[0]
                print(f"[DEBUG] bbox2d_tight: {bbox2d_tight}, bbox2d_loose: {bbox2d_loose}")
                is_detected = len(bbox2d_tight) > 0 and len(bbox2d_loose) > 0
                if is_detected:
                    bbox2d_tight_data = bbox2d_tight[0]  # get the first row data
                    bbox2d_loose_data = bbox2d_loose[0]  # get the first row data
                    area_ratio = compute_2d_bbox_area_ratio(bbox2d_tight_data, bbox2d_loose_data)
                    if area_ratio >= 0.8:
                        rgb = draw_bbox2d(rgb, bbox2d_tight_data)
                    else:
                        need_save = False
                else:
                    print(f"[GRGenerator: Render Thumbnail With Background] {mesh_prim.GetName()}_{idx} bbox2d is not detected.")
                    need_save = False  
                    if idx < top_half:
                        all_top_views_valid = False
                if not all_top_views_valid and idx >= top_half:
                    need_save = False
            if need_save and rgb is not None:
                cv2.imwrite(f"{mesh_dir}/{mesh_prim.GetName()}_with_bg_{idx}.png", cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB))
        remove_all_semantics(mesh_prim)


if __name__ == '__main__':
    if args.scene_usd:
        # Single-USD mode
        scene_usd_path = Path(args.scene_usd).resolve()
        if not scene_usd_path.exists():
            print(f"[ERROR] scene_usd not found: {scene_usd_path}")
            simulation_app.close()
            sys.exit(1)
        # Default output dir next to usd
        if args.output_dir:
            thumbnail_with_bg_dir = Path(args.output_dir).resolve()
        else:
            thumbnail_with_bg_dir = scene_usd_path.parent / "thumbnails" / "multi_views_with_bg"

        os.makedirs(thumbnail_with_bg_dir, exist_ok=True)
        print(f"[INFO] Output dir: {thumbnail_with_bg_dir}")
        # In single-USD mode, skip model filtering by default unless user forces otherwise
        skip_filter = True if not args.skip_model_filter else True
        render_thumbnail_with_bg(
            str(scene_usd_path),
            object_usd_dir=None,
            thumbnail_with_bg_dir=thumbnail_with_bg_dir,
            show_bbox2d=True,
            instance_scope=args.instance_scope,
            skip_model_filter=skip_filter,
        )
        simulation_app.close()
        sys.exit(0)
    else:
        # Structured mode (legacy layout with part/usd/scene)
        missing = []
        if not args.objects_dir:
            missing.append("--objects_dir")
        if not args.scene_dir:
            missing.append("--scene_dir")
        if args.usd is None:
            missing.append("--usd")
        if missing:
            print(f"[ERROR] Missing required args for structured mode: {', '.join(missing)}")
            simulation_app.close()
            sys.exit(1)

        usd_index   = f"part{args.part}/{args.usd}_usd"
        objects_dir = Path(args.objects_dir).resolve()
        scene_dir   = Path(args.scene_dir).resolve()

        # Basic path validation
        if not objects_dir.exists():
            print(f"[ERROR] objects_dir not found: {objects_dir}")
            simulation_app.close()
            sys.exit(1)
        if not scene_dir.exists():
            print(f"[ERROR] scene_dir not found: {scene_dir}")
            simulation_app.close()
            sys.exit(1)

        object_dir = objects_dir / usd_index
        scene_root_dir = scene_dir / usd_index
        if args.scene:
            scene_list = [args.scene]
        else:
            if not object_dir.exists():
                print(f"[ERROR] object_dir not found: {object_dir}")
                simulation_app.close()
                sys.exit(1)
            scene_list = natsorted(os.listdir(object_dir))

        for scene_name in scene_list:
            object_usd_dir        = object_dir / scene_name
            scene_usd_dir         = scene_root_dir / scene_name
            source_object_usd_dir = object_usd_dir / "models"
            output_thumbnail_dir  = object_usd_dir / "thumbnails"
            thumbnail_with_bg_dir = output_thumbnail_dir / "multi_views_with_bg"

            if not scene_usd_dir.exists():
                print(f"[WARN] scene_usd_dir not found, skip scene: {scene_usd_dir}")
                continue

            # Check the source usd file(s).
            scene_usd_list = find_all_files_in_folder(scene_usd_dir, suffix='.usd')
            if not scene_usd_list:
                print(f"[WARN] No USD files found under: {scene_usd_dir}, skip.")
                continue
            preferred = [f for f in scene_usd_list if 'copy.usd' in os.path.basename(f)]
            scene_copy_usd_path = preferred[0] if preferred else scene_usd_list[0]
            print(f"[INFO] Using scene USD: {scene_copy_usd_path}")

            # Check the source object usd dir.
            if not source_object_usd_dir.exists():
                print(f"[WARN] models dir not found, skip scene: {source_object_usd_dir}")
                continue

            try:
                object_usd_list_length  = len(os.listdir(source_object_usd_dir))
            except Exception as e:
                print(f"[WARN] Failed to list models dir: {source_object_usd_dir}, err: {e}")
                continue

            has_rendered_thumbnail_with_bg = os.path.exists(thumbnail_with_bg_dir) and \
                                           len(os.listdir(thumbnail_with_bg_dir)) == object_usd_list_length

            if not has_rendered_thumbnail_with_bg:
                os.makedirs(thumbnail_with_bg_dir, exist_ok=True)
                render_thumbnail_with_bg(scene_copy_usd_path, object_usd_dir, thumbnail_with_bg_dir)

        # Cleanly close Isaac Sim
        simulation_app.close()


        


