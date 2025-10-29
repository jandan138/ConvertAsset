import math
import os
import numpy as np
from pxr import Usd, UsdGeom
from typing import Dict
from scipy.spatial.transform import Rotation as R
import omni.isaac.core.utils.numpy.rotations as rot_utils         # type: ignore
from omni.isaac.sensor import Camera                              # type: ignore
from omni.isaac.core import World                                 # type: ignore
from omni.isaac.core.prims import XFormPrim                       # type: ignore
from omni.isaac.core.utils.semantics import add_update_semantics  # type: ignore
from natsort import natsorted

def init_world(
    stage_units_in_meters: float = 1.0,
    physics_dt: float = 0.01,
    rendering_dt: float = 0.01,
) -> World:
    world = World(
        stage_units_in_meters=stage_units_in_meters,
        physics_dt=physics_dt,
        rendering_dt=rendering_dt,
    )
    world.reset()
    return world

def init_camera(
    camera_name: str = "camera",
    image_width: int = 640,
    image_height: int = 480,
    position: np.ndarray = np.array([0.0, 0.0, 0.0]),
    orientation: np.ndarray = np.array([0.0, 0.0, 0.0, 1.0]),
) -> Camera:
    camera = Camera(
        prim_path=f"/World/{camera_name}",
        resolution=(image_width, image_height),
        position=position,
        orientation=orientation
    )
    return camera

def setup_camera(
    camera: Camera,
    focal_length: float = 18.0,
    clipping_range_min: float = 0.01,
    clipping_range_max: float = 1000000.0,
    vertical_aperture: float = 15.2908,
    horizontal_aperture: float = 20.0955,
    with_distance: bool = True,
    with_semantic: bool = False,
    with_bbox2d: bool = False,
    with_bbox3d: bool = False,
    with_motion_vector: bool = False,
    camera_params: dict | None = None,
    panorama: bool = False,
) -> None:
    camera.initialize()
    camera.set_focal_length(focal_length)
    camera.set_clipping_range(clipping_range_min, clipping_range_max)
    camera.set_vertical_aperture(vertical_aperture)
    camera.set_horizontal_aperture(horizontal_aperture)
    if with_distance:
        camera.add_distance_to_image_plane_to_frame()
    if with_semantic:
        camera.add_semantic_segmentation_to_frame()
    if with_bbox2d:
        camera.add_bounding_box_2d_tight_to_frame()
        camera.add_bounding_box_2d_loose_to_frame()
    if with_bbox3d:
        camera.add_bounding_box_3d_to_frame()
    if with_motion_vector:
        camera.add_motion_vectors_to_frame()
    if panorama:
        camera.set_projection_type("fisheyeSpherical")

def get_all_mesh_prims_from_scope(stage, scope_name: str = "Instances"):
    """Return all Mesh prims under a given scope path.

    scope_name can be either relative to /World (e.g., "scene/Instances")
    or an absolute prim path (e.g., "/World/scene/Instances").
    """
    all_mesh_list: list[Usd.Prim] = []
    scope_path = scope_name if scope_name.startswith("/") else f"/World/{scope_name}"
    instance_scope = stage.GetPrimAtPath(scope_path)
    if not instance_scope or not instance_scope.IsValid():
        return all_mesh_list
    for type_scope in instance_scope.GetChildren():
        mesh_list = get_all_mesh_prims(type_scope, f"{scope_path}/{type_scope.GetName()}")
        all_mesh_list.extend(mesh_list)
    return all_mesh_list


def get_all_mesh_prims(root_prim: Usd.Prim, root_path: str | None = None) -> list[Usd.Prim]:
    """Collect all Mesh prims under the given prim.

    Args:
        root_prim: The prim to traverse from.
        root_path: Optional label for debugging; not used functionally.

    Returns:
        A list of Usd.Prim objects of type "Mesh".
    """
    meshes: list[Usd.Prim] = []
    if root_prim and root_prim.IsValid():
        for p in root_prim.Traverse():
            try:
                if p.GetTypeName() == "Mesh":
                    meshes.append(p)
            except Exception:
                # Be defensive against odd prim types
                continue
    return meshes

def switch_all_lights(stage, action="on"):
    action_list = ["on", "off"]
    assert action in action_list, f"Invalid action {action}, should be one of {action_list}"
    light_types = [
        "DistantLight",
        "SphereLight",
        "DiskLight",
        "RectLight",
        "CylinderLight"
    ]

    for prim in stage.Traverse():
        prim_type_name = prim.GetTypeName()
        if prim_type_name in light_types:
            if action == "on":
                UsdGeom.Imageable(prim).MakeVisible()
            else:
                UsdGeom.Imageable(prim).MakeInvisible()


def compute_bbox(prim: Usd.Prim) -> np.ndarray:
    """
    Compute Bounding Box using ComputeWorldBound at UsdGeom.Imageable

    Args:
        prim: A prim to compute the bounding box.

    Returns: 
        bound_range: A numpy array, [(min_x, min_y, min_z), (max_x, max_y, max_z)]
    """
    imageable: UsdGeom.Imageable = UsdGeom.Imageable(prim)
    time = Usd.TimeCode.Default()
    bound = imageable.ComputeWorldBound(time, UsdGeom.Tokens.default_)
    bound_range = bound.ComputeAlignedBox()
    bbox_min = bound_range.min
    bbox_max = bound_range.max
    bound_range = np.array([bbox_min, bbox_max])
    return bound_range
            

def set_camera_look_at(
    camera: Camera,
    target: XFormPrim | np.ndarray,
    distance: float = 0.4,
    elevation: float = 90.0,
    azimuth: float = 0.0,
) -> None:
    if isinstance(target, XFormPrim):
        # print("[DEBUG]: target is XFormPrim")
        target_position, _ = target.get_world_pose()
    else:
        target_position = target
    # print("target_position: ", target_position)
    elev_rad = math.radians(elevation)
    azim_rad = math.radians(azimuth)
    offset_x = distance * math.cos(elev_rad) * math.cos(azim_rad)
    offset_y = distance * math.cos(elev_rad) * math.sin(azim_rad)
    offset_z = distance * math.sin(elev_rad)
    camera_position = target_position + np.array([offset_x, offset_y, offset_z])
    rot = R.from_euler("xyz", [0, elevation, azimuth - 180], degrees=True)
    quaternion = rot.as_quat()
    quaternion = np.array([quaternion[3], quaternion[0], quaternion[1], quaternion[2]])
    # print("target_position: ", target_position)
    # print("camera_position: ", camera_position)
    # print("quaternion: ", quaternion)
    camera.set_world_pose(position=camera_position, orientation=quaternion)


def get_src(camera: Camera, type: str) -> np.ndarray | dict | None:
    if type == "rgb":
        return get_rgb(camera)
    if type == "bbox2d_tight":
        return get_bounding_box_2d_tight(camera)
    if type == "bbox2d_loose":
        return get_bounding_box_2d_loose(camera)

def get_rgb(camera: Camera) -> np.ndarray | None:
    frame = camera.get_rgba()
    if isinstance(frame, np.ndarray) and frame.size > 0:
        frame = frame[:, :, :3]
        return frame
    else:
        return None

def get_bounding_box_2d_tight(camera: Camera) -> tuple[np.ndarray, dict]:
    annotator = camera._custom_annotators["bounding_box_2d_tight"]
    annotation_data = annotator.get_data()
    bbox = annotation_data["data"]
    info = annotation_data["info"]
    return bbox, info["idToLabels"]

def get_bounding_box_2d_loose(camera: Camera) -> tuple[np.ndarray, dict]:
    annotator = camera._custom_annotators["bounding_box_2d_loose"]
    annotation_data = annotator.get_data()
    bbox = annotation_data["data"]
    info = annotation_data["info"]
    return bbox, info["idToLabels"]


def draw_bbox2d(image, bbox2d):
    image = np.array(image)
    x_min = int(bbox2d[1])
    y_min = int(bbox2d[2])
    x_max = int(bbox2d[3])
    y_max = int(bbox2d[4])
    image[y_min:y_min+2, x_min:x_max] = [255, 0, 0]
    image[y_max-2:y_max, x_min:x_max] = [255, 0, 0]
    image[y_min:y_max, x_min:x_min+2] = [255, 0, 0]
    image[y_min:y_max, x_max-2:x_max] = [255, 0, 0]
    return image


def find_all_files_in_folder(root: str | os.PathLike, suffix: str) -> list[str]:
    """
    Recursively find all files under `root` ending with `suffix`.

    Args:
        root: Root directory to search.
        suffix: File name suffix, e.g., ".usd".

    Returns:
        A naturally-sorted list of absolute file paths.
    """
    root = os.fspath(root)
    results: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(suffix):
                results.append(os.path.join(dirpath, fn))
    return natsorted(results)