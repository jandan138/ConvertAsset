# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import math
from pxr import Usd, UsdGeom, Gf, Sdf, UsdLux  # type: ignore


@dataclass
class OrbitParams:
    target_prim_path: str
    source_camera_path: Optional[str] = None
    camera_basename: str = "/World/OrbitCam"
    num_shots: int = 10
    start_deg: float = 0.0
    cw_rotate: bool = False
    radius_scale: float = 1.0
    vertical_steps: int = 1
    vertical_sweep_deg: float = 0.0
    vertical_center_deg: float = 0.0
    fallback_fov_deg: float = 55.0
    fallback_aspect: float = 16.0 / 9.0
    fallback_padding: float = 1.08
    fallback_focal_mm: float = 35.0
    fallback_near_clip: float = 0.01
    fallback_far_clip: float = 10000.0


def _normalize(v: Gf.Vec3d) -> Gf.Vec3d:
    try:
        return v.GetNormalized()
    except Exception:
        L = v.GetLength()
        return v / max(L, 1e-9)


def _world_up(stage: Usd.Stage) -> Gf.Vec3d:
    return Gf.Vec3d(0, 0, 1) if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z else Gf.Vec3d(0, 1, 0)


def _should_ignore_for_bbox(node: Usd.Prim) -> bool:
    # Filter out common environment shells and dome lights so they do not distort the orbit radius.
    path_token = node.GetPath().pathString.lower()
    if "__default_setting" in path_token:
        return True
    if "hdr" in path_token and "sphere" in path_token:
        return True
    if "skydome" in path_token or "environment" in path_token:
        return True
    try:
        dome = UsdLux.DomeLight(node)
        if dome and dome.GetPrim().IsValid():
            return True
    except Exception:
        pass
    return False


def _is_viewer_observer_camera(prim: Usd.Prim, orbit_basename: str) -> bool:
    if not prim or not prim.IsValid():
        return False
    path_token = prim.GetPath().pathString.lower()
    name = prim.GetName().lower()
    if orbit_basename and path_token.startswith(orbit_basename.lower()):
        return True
    if path_token.startswith("/omniversekit") or path_token.startswith("/kit"):
        return True
    if "viewport" in name or "usdview" in name:
        return True
    if name.startswith("omniversekit") or name.startswith("defaultcamera"):
        return True
    return False


def _bbox_center_and_size(stage: Usd.Stage, path: str):
    prim = stage.GetPrimAtPath(Sdf.Path(path))
    if not prim or not prim.IsValid():
        raise RuntimeError(f"Target prim not found: {path}")

    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
        useExtentsHint=True,
    )

    def _range_is_sane(rng: Gf.Range3d) -> bool:
        if rng.IsEmpty():
            return False
        mn, mx = rng.GetMin(), rng.GetMax()
        vals = [mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]]
        if not all(math.isfinite(v) for v in vals):
            return False
        diag = (mx - mn).GetLength()
        if not math.isfinite(diag) or diag <= 0:
            return False
        # Guard against pathological extents coming from bad extents hints.
        return diag <= 1.0e9

    rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    top_center: Optional[Gf.Vec3d] = None
    top_size: Optional[Gf.Vec3d] = None
    if _range_is_sane(rng):
        mn, mx = rng.GetMin(), rng.GetMax()
        top_center = (mn + mx) * 0.5
        top_size = (mx - mn)

    # Aggregate finite child bounds while rejecting outliers and environment shells.
    bounds = []
    stack = [prim]
    while stack:
        node = stack.pop()
        if not node or not node.IsValid():
            continue
        if _should_ignore_for_bbox(node):
            continue
        stack.extend(list(node.GetChildren()))
        if not node.IsA(UsdGeom.Imageable):
            continue
        local_rng = cache.ComputeWorldBound(node).ComputeAlignedRange()
        if local_rng.IsEmpty():
            continue
        local_min, local_max = local_rng.GetMin(), local_rng.GetMax()
        vals = [
            local_min[0],
            local_min[1],
            local_min[2],
            local_max[0],
            local_max[1],
            local_max[2],
        ]
        if not all(math.isfinite(v) for v in vals):
            continue
        diag = (local_max - local_min).GetLength()
        if not math.isfinite(diag) or diag <= 0:
            continue
        if diag > 1.0e9:
            continue
        bounds.append((diag, local_min, local_max))

    if not bounds:
        if top_center is not None and top_size is not None:
            return top_center, top_size
        raise RuntimeError(f"Failed to compute finite bbox for prim: {path}")

    if len(bounds) > 1:
        diags = sorted(item[0] for item in bounds)
        typical = diags[len(diags) // 2]
        if math.isfinite(typical) and typical > 0.0:
            limit = max(typical * 20.0, typical + 10.0)
            filtered = [item for item in bounds if item[0] <= limit]
            if filtered:
                bounds = filtered

    mins = [math.inf, math.inf, math.inf]
    maxs = [-math.inf, -math.inf, -math.inf]
    for _, mn, mx in bounds:
        mins[0] = min(mins[0], mn[0])
        mins[1] = min(mins[1], mn[1])
        mins[2] = min(mins[2], mn[2])
        maxs[0] = max(maxs[0], mx[0])
        maxs[1] = max(maxs[1], mx[1])
        maxs[2] = max(maxs[2], mx[2])

    if not all(math.isfinite(v) for v in mins + maxs):
        raise RuntimeError(f"Non-finite bbox extrema for prim: {path}")

    mn = Gf.Vec3d(*mins)
    mx = Gf.Vec3d(*maxs)
    agg_center = (mn + mx) * 0.5
    agg_size = (mx - mn)

    if top_center is None or top_size is None:
        return agg_center, agg_size

    try:
        diag_top = float(top_size.GetLength())
    except Exception:
        diag_top = math.sqrt(top_size[0] ** 2 + top_size[1] ** 2 + top_size[2] ** 2)
    try:
        diag_agg = float(agg_size.GetLength())
    except Exception:
        diag_agg = math.sqrt(agg_size[0] ** 2 + agg_size[1] ** 2 + agg_size[2] ** 2)

    if not math.isfinite(diag_top) or diag_top <= 0:
        return agg_center, agg_size
    if math.isfinite(diag_agg) and diag_agg > 0:
        if diag_agg * 2.0 <= diag_top or diag_agg <= diag_top * 0.25:
            return agg_center, agg_size
    return top_center, top_size


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


def _perpendicular_right(world_up: Gf.Vec3d, hint: Optional[Gf.Vec3d] = None) -> Gf.Vec3d:
    candidates = []
    if hint is not None and hint.GetLength() > 1e-9:
        candidates.append(hint)
    candidates.extend([Gf.Vec3d(1, 0, 0), Gf.Vec3d(0, 1, 0), Gf.Vec3d(0, 0, 1)])
    for cand in candidates:
        if abs(Gf.Dot(world_up, cand)) > 0.95:
            continue
        try:
            v = _normalize(Gf.Cross(world_up, cand))
        except Exception:
            v = Gf.Vec3d(0, 0, 0)
        if v.GetLength() > 1e-6:
            return v
    # Last resort: pick an arbitrary orthogonal axis
    alt = Gf.Vec3d(1, 0, 0) if abs(world_up[0]) < abs(world_up[1]) else Gf.Vec3d(0, 1, 0)
    try:
        v = _normalize(Gf.Cross(world_up, alt))
    except Exception:
        v = Gf.Vec3d(1, 0, 0)
    return v if v.GetLength() > 1e-6 else Gf.Vec3d(1, 0, 0)


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

    # Copy intrinsics from a source camera if any, keep reference transform for orbit radius
    r0: Optional[Gf.Vec3d] = None
    fallback_used = False
    right_hint: Optional[Gf.Vec3d] = None
    height_offset = 0.0

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
                if _is_viewer_observer_camera(prim, params.camera_basename):
                    continue
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

        # Remember initial eye vector relative to orbit center for radius calc
        cache = UsdGeom.XformCache(Usd.TimeCode.Default())
        M0 = cache.GetLocalToWorldTransform(src_cam_prim)
        eye0 = Gf.Vec3d(M0.ExtractTranslation())
        candidate = eye0 - center
        if candidate.GetLength() < 1e-6:
            candidate = None  # type: ignore[assignment]
        if candidate is not None:
            horiz = candidate - world_up * Gf.Dot(candidate, world_up)
            horiz_len = horiz.GetLength()
            max_horizontal = max(float(abs(size[0])), float(abs(size[1])), 1.0)
            if not math.isfinite(horiz_len) or horiz_len < max_horizontal * 0.1:
                candidate = None  # too close or degenerate, fall back to bbox fit
            else:
                r0 = _normalize(horiz) * horiz_len
                height_offset = float(Gf.Dot(candidate, world_up))
                half_height = max(float(abs(size[2])) * 0.5, 0.0)
                height_offset = max(-half_height, min(half_height, height_offset))
                try:
                    right_hint = _normalize(Gf.Cross(world_up, _normalize(r0)))
                except Exception:
                    right_hint = None

    # Compute radius and start eye from any camera or from bbox
    # Prefer radius derived from source camera location so we match the author's interior viewpoint
    if r0 is not None:
        base_vec = r0 * float(params.radius_scale)
    else:
        fallback_used = True
        right0 = _perpendicular_right(world_up, right_hint)
        hx = float(size[0]) * 0.5
        hy = float(size[1]) * 0.5
        hz = float(size[2]) * 0.5
        corners = [
            Gf.Vec3d(sx * hx, sy * hy, sz * hz)
            for sx in (-1.0, 1.0)
            for sy in (-1.0, 1.0)
            for sz in (-1.0, 1.0)
        ]
        w_half = max(abs(Gf.Dot(corner, right0)) for corner in corners)
        h_half = max(abs(Gf.Dot(corner, world_up)) for corner in corners)
        fov_h = math.radians(max(1e-3, float(params.fallback_fov_deg)))
        aspect = max(1e-6, float(params.fallback_aspect))
        # Avoid div-zero by clamping denominator
        tan_h = max(1e-6, math.tan(fov_h * 0.5))
        fov_v = 2.0 * math.atan(math.tan(fov_h * 0.5) / aspect)
        tan_v = max(1e-6, math.tan(fov_v * 0.5))
        dist_h = w_half / tan_h
        dist_v = h_half / tan_v
        distance = max(dist_h, dist_v) * float(params.fallback_padding)
        base_radius = distance * float(params.radius_scale)
        base_vec = right0 * base_radius

    # Assign default intrinsics when falling back to synthetic camera settings
    if fallback_used:
        try:
            focal_mm = float(params.fallback_focal_mm)
            fov_h = math.radians(max(1e-3, float(params.fallback_fov_deg)))
            horiz_aperture = 2.0 * focal_mm * math.tan(fov_h * 0.5)
            aspect = max(1e-6, float(params.fallback_aspect))
            cam.GetFocalLengthAttr().Set(focal_mm)
            cam.GetHorizontalApertureAttr().Set(horiz_aperture)
            cam.GetVerticalApertureAttr().Set(horiz_aperture / aspect)
            cam.GetClippingRangeAttr().Set(
                Gf.Vec2f(float(params.fallback_near_clip), float(params.fallback_far_clip))
            )
        except Exception:
            pass

    # Ensure the camera's clipping range encloses the target so renders do not black out.
    try:
        radius = float(base_vec.GetLength())
    except Exception:
        radius = 0.0
    diag = float(size.GetLength()) if hasattr(size, "GetLength") else math.sqrt(size[0] ** 2 + size[1] ** 2 + size[2] ** 2)
    half_diag = max(0.5 * diag, 1.0)
    far_needed = max(radius + half_diag * 1.5, half_diag * 2.0, float(params.fallback_far_clip))
    clip_attr = cam.GetClippingRangeAttr()
    clip_val = clip_attr.Get()
    if clip_val is None or not all(math.isfinite(x) for x in clip_val):
        near = float(params.fallback_near_clip)
        far = float(params.fallback_far_clip)
    else:
        near, far = float(clip_val[0]), float(clip_val[1])
    near = max(float(params.fallback_near_clip), near)
    far = max(far, far_needed)
    if far <= near:
        # Keep a reasonable separation between near/far planes if the prior values collapse.
        far = max(far_needed, near * 10.0, near + 10.0)
    clip_attr.Set(Gf.Vec2f(float(near), float(far)))

    step = (2.0 * math.pi) / max(1, int(params.num_shots))
    sign = -1.0 if bool(params.cw_rotate) else 1.0
    start = math.radians(float(params.start_deg))
    vertical_count = max(1, int(params.vertical_steps))
    sweep_rad = math.radians(float(params.vertical_sweep_deg))
    center_rad = math.radians(float(params.vertical_center_deg))
    if vertical_count <= 1 or abs(sweep_rad) < 1.0e-6:
        pitch_angles = [center_rad]
    else:
        start_pitch = center_rad - sweep_rad * 0.5
        denom = max(1, vertical_count - 1)
        pitch_angles = [start_pitch + sweep_rad * (idx / denom) for idx in range(vertical_count)]
    orbit_origin = center + world_up * height_offset
    frame_index = 0

    # Ensure we have a transform op and author time-sampled matrices
    xf = UsdGeom.Xformable(cam)
    ops = xf.GetOrderedXformOps()
    xop = ops[0] if (ops and ops[0].GetOpType() == UsdGeom.XformOp.TypeTransform) else xf.AddTransformOp()

    for pitch in pitch_angles:
        for i in range(int(params.num_shots)):
            theta = start + sign * step * i
            r_vec = _rotate_vec(base_vec, world_up, theta)
            if abs(pitch) > 1.0e-6:
                axis = _normalize(Gf.Cross(world_up, r_vec))
                if axis.GetLength() < 1.0e-6:
                    axis = _normalize(_perpendicular_right(world_up, r_vec))
                r_vec = _rotate_vec(r_vec, axis, pitch)
            eye = orbit_origin + r_vec
            fwd = _normalize(center - eye)
            right = _normalize(Gf.Cross(fwd, world_up))
            if right.GetLength() < 1e-6:
                tmp2 = Gf.Vec3d(1, 0, 0) if abs(world_up[0]) < 0.9 else Gf.Vec3d(0, 1, 0)
                right = _normalize(Gf.Cross(fwd, tmp2))
            up = _normalize(Gf.Cross(right, fwd))
            M = _build_world_matrix_rows(right, up, fwd, eye)
            xop.Set(M, time=Usd.TimeCode(frame_index))
            frame_index += 1

    # Set stage frame range for convenience
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(max(0, frame_index - 1))
    stage.SetTimeCodesPerSecond(24)

    stage.Export(out_usd_path)
    return cam_path
