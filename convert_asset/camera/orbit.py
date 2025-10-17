# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import math
from pxr import Usd, UsdGeom, Gf, Sdf  # type: ignore


@dataclass
class OrbitParams:
    target_prim_path: str
    source_camera_path: Optional[str] = None
    camera_basename: str = "/World/OrbitCam"
    num_shots: int = 10
    start_deg: float = 0.0
    cw_rotate: bool = False
    radius_scale: float = 1.0


def _normalize(v: Gf.Vec3d) -> Gf.Vec3d:
    try:
        return v.GetNormalized()
    except Exception:
        L = v.GetLength()
        return v / max(L, 1e-9)


def _world_up(stage: Usd.Stage) -> Gf.Vec3d:
    return Gf.Vec3d(0, 0, 1) if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z else Gf.Vec3d(0, 1, 0)


def _bbox_center_and_size(stage: Usd.Stage, path: str):
    prim = stage.GetPrimAtPath(Sdf.Path(path))
    if not prim or not prim.IsValid():
        raise RuntimeError(f"Target prim not found: {path}")
    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
        useExtentsHint=True,
    )
    rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    if rng.IsEmpty():
        raise RuntimeError(f"Empty bbox for prim: {path}")
    mn, mx = rng.GetMin(), rng.GetMax()
    return (mn + mx) * 0.5, (mx - mn)


def _rotate_vec(v: Gf.Vec3d, axis_unit: Gf.Vec3d, ang_rad: float) -> Gf.Vec3d:
    c, s = math.cos(ang_rad), math.sin(ang_rad)
    return v * c + Gf.Cross(axis_unit, v) * s + axis_unit * Gf.Dot(axis_unit, v) * (1.0 - c)


def _build_world_matrix_rows(right: Gf.Vec3d, up: Gf.Vec3d, forward: Gf.Vec3d, eye: Gf.Vec3d) -> Gf.Matrix4d:
    m = Gf.Matrix4d(1.0)
    back = -forward
    m.SetRow(0, Gf.Vec4d(right[0], right[1], right[2], 0.0))
    m.SetRow(1, Gf.Vec4d(up[0], up[1], up[2], 0.0))
    m.SetRow(2, Gf.Vec4d(back[0], back[1], back[2], 0.0))
    m.SetRow(3, Gf.Vec4d(eye[0], eye[1], eye[2], 1.0))
    return m


def create_orbit_camera_animation_and_export(src_usd_path: str, out_usd_path: str, params: OrbitParams) -> str:
    """Create/overwrite an Orbit camera, author per-frame xform samples for an orbit, and export stage.

    Returns the created camera prim path.
    """
    stage = Usd.Stage.Open(src_usd_path)
    if stage is None:
        raise RuntimeError(f"Failed to open stage: {src_usd_path}")

    center, size = _bbox_center_and_size(stage, params.target_prim_path)
    world_up = _normalize(_world_up(stage))

    # Prepare camera prim
    cam_path = params.camera_basename
    if stage.GetPrimAtPath(cam_path):
        i = 1
        while stage.GetPrimAtPath(f"{params.camera_basename}_{i}"):
            i += 1
        cam_path = f"{params.camera_basename}_{i}"
    cam = UsdGeom.Camera.Define(stage, Sdf.Path(cam_path))

    # Copy intrinsics from a source camera if any
    src_cam_prim = None
    if params.source_camera_path:
        p = Sdf.Path(params.source_camera_path)
        prim = stage.GetPrimAtPath(p)
        if prim and prim.IsValid() and prim.GetTypeName() == "Camera":
            src_cam_prim = prim
    else:
        for prim in stage.Traverse():
            if prim.GetTypeName() == "Camera":
                src_cam_prim = prim
                break
    if src_cam_prim is not None:
        s = UsdGeom.Camera(src_cam_prim)
        for getter, setter_name in [
            (s.GetFocalLengthAttr, "GetFocalLengthAttr"),
            (s.GetHorizontalApertureAttr, "GetHorizontalApertureAttr"),
            (s.GetVerticalApertureAttr, "GetVerticalApertureAttr"),
            (s.GetClippingRangeAttr, "GetClippingRangeAttr"),
            (s.GetFocusDistanceAttr, "GetFocusDistanceAttr"),
            (s.GetFStopAttr, "GetFStopAttr"),
            (s.GetShutterOpenAttr, "GetShutterOpenAttr"),
            (s.GetShutterCloseAttr, "GetShutterCloseAttr"),
        ]:
            try:
                val = getter().Get()
                if val is not None:
                    getattr(cam, setter_name)().Set(val)
            except Exception:
                pass

    # Compute radius and start eye from any camera or from bbox
    # Use a simple default: place starting eye along +X from center at radius ~ max(size) * 2
    max_extent = max(float(size[0]), float(size[1]), float(size[2]))
    base_radius = max_extent * 2.0

    step = (2.0 * math.pi) / max(1, int(params.num_shots))
    sign = -1.0 if bool(params.cw_rotate) else 1.0
    start = math.radians(float(params.start_deg))

    # Ensure we have a transform op and author time-sampled matrices
    xf = UsdGeom.Xformable(cam)
    ops = xf.GetOrderedXformOps()
    xop = ops[0] if (ops and ops[0].GetOpType() == UsdGeom.XformOp.TypeTransform) else xf.AddTransformOp()

    for i in range(int(params.num_shots)):
        theta = start + sign * step * i
        r = base_radius * float(params.radius_scale)
        # Orbit on plane orthogonal to world_up; choose a right vector perpendicular to world_up
        # Pick an initial radial vector not parallel to world_up
        tmp = Gf.Vec3d(1, 0, 0)
        if abs(Gf.Dot(tmp, world_up)) > 0.9:
            tmp = Gf.Vec3d(0, 1, 0)
        right0 = _normalize(Gf.Cross(world_up, tmp))
        r_vec = _rotate_vec(right0 * r, world_up, theta)
        eye = center + r_vec
        fwd = _normalize(center - eye)
        right = _normalize(Gf.Cross(fwd, world_up))
        if right.GetLength() < 1e-6:
            tmp2 = Gf.Vec3d(1, 0, 0) if abs(world_up[0]) < 0.9 else Gf.Vec3d(0, 1, 0)
            right = _normalize(Gf.Cross(fwd, tmp2))
        up = _normalize(Gf.Cross(right, fwd))
        M = _build_world_matrix_rows(right, up, fwd, eye)
        xop.Set(M, time=Usd.TimeCode(i))

    # Set stage frame range for convenience
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(max(0, int(params.num_shots) - 1))
    stage.SetTimeCodesPerSecond(24)

    stage.Export(out_usd_path)
    return cam_path
