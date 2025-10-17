# -*- coding: utf-8 -*-
"""Camera fitting utilities (pure pxr, no Kit/viewport needed).

Ported from scripts/create_carema_at_prim_v4.py to be used in CLI:
 - Computes a camera that inherits rotation from a source camera (optionally a pitch tweak)
 - Frames a target prim's world-space bbox at a specified horizontal FOV and aspect
 - Supports height offset in multiple modes
 - Writes the camera into the stage and exports to a new USD file
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import math
from pxr import Usd, UsdGeom, Gf, Sdf  # type: ignore


@dataclass
class FitParams:
    target_prim_path: str
    source_camera_path: Optional[str] = None
    fov_h_deg: float = 55.0
    aspect: float = 16.0 / 9.0
    padding: float = 1.08
    backoff: float = 0.3
    focal_mm: float = 35.0
    near_clip: float = 0.01
    far_clip: float = 10000.0
    camera_basename: str = "/World/AutoCamInherit"
    # View tweaks
    pitch_down_deg: float = 0.0
    height_offset_mode: str = "bbox_z"  # bbox_z | bbox_max | bbox_diag | abs
    height_offset_value: float = 0.5     # ratio for relative modes; absolute units when mode=abs


@dataclass
class FitResult:
    out_stage_path: str
    camera_prim_path: str
    center: Tuple[float, float, float]
    size_xyz: Tuple[float, float, float]
    aspect: float
    fov_h_deg: float
    fov_v_deg: float
    distance: float
    eye: Tuple[float, float, float]


def _normalize(v: Gf.Vec3d) -> Gf.Vec3d:
    try:
        return v.GetNormalized()
    except Exception:
        L = v.GetLength()
        return v / max(L, 1e-9)


def _bbox_world_range(prim: Usd.Prim):
    purposes = [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy]
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), purposes, useExtentsHint=True)
    return cache.ComputeWorldBound(prim).ComputeAlignedRange()


def _world_basis_from_camera_prim(cam_prim: Usd.Prim):
    """Camera local axes: +X=right, +Y=up, -Z=forward."""
    xc = UsdGeom.XformCache(Usd.TimeCode.Default())
    M = xc.GetLocalToWorldTransform(cam_prim)
    right = _normalize(M.TransformDir(Gf.Vec3d(1, 0, 0)))
    up = _normalize(M.TransformDir(Gf.Vec3d(0, 1, 0)))
    fwd = _normalize(M.TransformDir(Gf.Vec3d(0, 0, -1)))
    return right, up, fwd


def _rotate_vec_around_axis(v: Gf.Vec3d, axis_unit: Gf.Vec3d, ang_rad: float) -> Gf.Vec3d:
    # Rodrigues
    c, s = math.cos(ang_rad), math.sin(ang_rad)
    return v * c + Gf.Cross(axis_unit, v) * s + axis_unit * Gf.Dot(axis_unit, v) * (1.0 - c)


def _length_diag(v3: Gf.Vec3d) -> float:
    return float((v3[0] * v3[0] + v3[1] * v3[1] + v3[2] * v3[2]) ** 0.5)


def _compute_height_offset_units(mode: str, value: float, size_vec: Gf.Vec3d) -> float:
    if mode == "abs":
        return float(value)
    if mode == "bbox_z":
        ref = float(size_vec[2])
    elif mode == "bbox_max":
        ref = max(float(size_vec[0]), float(size_vec[1]), float(size_vec[2]))
    elif mode == "bbox_diag":
        ref = _length_diag(size_vec)
    else:
        ref = max(float(size_vec[0]), float(size_vec[1]), float(size_vec[2]))
    return float(value) * ref


def _build_world_matrix_rows(right: Gf.Vec3d, up: Gf.Vec3d, forward: Gf.Vec3d, eye: Gf.Vec3d) -> Gf.Matrix4d:
    m = Gf.Matrix4d(1.0)
    back = -forward
    m.SetRow(0, Gf.Vec4d(right[0], right[1], right[2], 0.0))
    m.SetRow(1, Gf.Vec4d(up[0], up[1], up[2], 0.0))
    m.SetRow(2, Gf.Vec4d(back[0], back[1], back[2], 0.0))
    m.SetRow(3, Gf.Vec4d(eye[0], eye[1], eye[2], 1.0))
    return m


def fit_camera_and_export(src_usd_path: str, out_usd_path: str, params: FitParams) -> FitResult:
    stage = Usd.Stage.Open(src_usd_path)
    if stage is None:
        raise RuntimeError(f"Failed to open stage: {src_usd_path}")

    target_prim = stage.GetPrimAtPath(Sdf.Path(params.target_prim_path))
    if not target_prim or not target_prim.IsValid():
        raise RuntimeError(f"Target prim not found: {params.target_prim_path}")

    # Source camera
    src_cam_prim: Optional[Usd.Prim] = None
    if params.source_camera_path:
        p = Sdf.Path(params.source_camera_path)
        prim = stage.GetPrimAtPath(p)
        if prim and prim.IsValid() and prim.GetTypeName() == "Camera":
            src_cam_prim = prim
        else:
            raise RuntimeError(f"Source camera prim not found or not a Camera: {params.source_camera_path}")
    else:
        # Try to find any camera in the stage
        for prim in stage.Traverse():
            if prim.GetTypeName() == "Camera":
                src_cam_prim = prim
                break
        if src_cam_prim is None:
            # Fall back to world-forward basis
            world_right = Gf.Vec3d(1, 0, 0)
            world_up = Gf.Vec3d(0, 0, 1)
            world_fwd = Gf.Vec3d(0, 1, 0)  # arbitrary; Z-up world => forward=+Y
            src_right, src_up, src_fwd = world_right, world_up, world_fwd
        else:
            src_right, src_up, src_fwd = _world_basis_from_camera_prim(src_cam_prim)

    if src_cam_prim is not None:
        src_right, src_up, src_fwd = _world_basis_from_camera_prim(src_cam_prim)

    # Target bbox
    rng = _bbox_world_range(target_prim)
    if rng.IsEmpty():
        raise RuntimeError(f"Empty bbox for prim: {params.target_prim_path}")
    mn, mx = rng.GetMin(), rng.GetMax()
    center = (mn + mx) * 0.5
    size = mx - mn
    half = Gf.Vec3d(max(size[0], 1e-6) / 2.0, max(size[1], 1e-6) / 2.0, max(size[2], 1e-6) / 2.0)

    # Pitch tweak around right axis
    pitch_rad = math.radians(params.pitch_down_deg)
    right_unit = _normalize(src_right)
    adj_fwd = _rotate_vec_around_axis(src_fwd, right_unit, pitch_rad)
    adj_up = _rotate_vec_around_axis(src_up, right_unit, pitch_rad)
    # Orthonormalize
    adj_fwd = _normalize(adj_fwd)
    adj_right = _normalize(Gf.Cross(adj_fwd, adj_up))
    adj_up = _normalize(Gf.Cross(adj_right, adj_fwd))

    # Frame fit
    hx, hy, hz = float(half[0]), float(half[1]), float(half[2])
    corners = [Gf.Vec3d(sx * hx, sy * hy, sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    w_half = 0.0
    h_half = 0.0
    for v in corners:
        w_half = max(w_half, abs(Gf.Dot(v, adj_right)))
        h_half = max(h_half, abs(Gf.Dot(v, adj_up)))

    aspect = float(params.aspect)
    fov_h = math.radians(params.fov_h_deg)
    fov_v = 2.0 * math.atan(max(1e-9, math.tan(fov_h / 2.0)) / max(aspect, 1e-9))
    dist_h = w_half / max(math.tan(fov_h / 2.0), 1e-9)
    dist_v = h_half / max(math.tan(fov_v / 2.0), 1e-9)
    distance = max(dist_h, dist_v) * float(params.padding) * float(params.backoff)

    # Height offset
    height_units = _compute_height_offset_units(params.height_offset_mode, params.height_offset_value, size)
    eye = Gf.Vec3d(center) - adj_fwd * distance + adj_up * height_units

    # Create camera prim path
    cam_path = params.camera_basename
    if stage.GetPrimAtPath(cam_path):
        i = 1
        while stage.GetPrimAtPath(f"{params.camera_basename}_{i}"):
            i += 1
        cam_path = f"{params.camera_basename}_{i}"
    new_cam = UsdGeom.Camera.Define(stage, Sdf.Path(cam_path))

    # Intrinsics from FOV + focal
    H_APERTURE_MM = 2.0 * float(params.focal_mm) * math.tan(fov_h / 2.0)
    new_cam.GetFocalLengthAttr().Set(float(params.focal_mm))
    new_cam.GetHorizontalApertureAttr().Set(float(H_APERTURE_MM))
    new_cam.GetVerticalApertureAttr().Set(float(H_APERTURE_MM) / max(aspect, 1e-9))
    new_cam.GetClippingRangeAttr().Set(Gf.Vec2f(float(params.near_clip), float(params.far_clip)))

    # Xform
    M = _build_world_matrix_rows(adj_right, adj_up, adj_fwd, eye)
    xf = UsdGeom.Xformable(new_cam)
    ops = xf.GetOrderedXformOps()
    xop = ops[0] if (ops and ops[0].GetOpType() == UsdGeom.XformOp.TypeTransform) else xf.AddTransformOp()
    xop.Set(M)

    # Export to new usd
    stage.Export(out_usd_path)

    return FitResult(
        out_stage_path=out_usd_path,
        camera_prim_path=cam_path,
        center=(float(center[0]), float(center[1]), float(center[2])),
        size_xyz=(float(size[0]), float(size[1]), float(size[2])),
        aspect=aspect,
        fov_h_deg=float(params.fov_h_deg),
        fov_v_deg=math.degrees(fov_v),
        distance=float(distance),
        eye=(float(eye[0]), float(eye[1]), float(eye[2])),
    )
