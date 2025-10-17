# === Safe Orbit Capture for MDL (non-destructive to your original camera) ===
# - Duplicates active camera to /World/OrbitCam (copy intrinsics + world xform)
# - Switches viewport to it, orbits around target bbox center about stage up-axis
# - Waits a few frames each step to ensure refresh, captures to <usd_dir>/mdl_images
# - Switches viewport BACK to your original camera. Original camera is untouched.

from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
import omni.kit.viewport.utility as vp_utils
import omni.kit.app
import asyncio, math, os

# ---------------- Config ----------------
TARGET_PATH_STR = "/Root/Meshes/Furnitures/table"  # 围绕的目标 prim
NUM_SHOTS       = 10                                 # 张数
START_DEG       = 0.0                                # 起始角
CW_ROTATE       = False                              # 顺时针？False=逆时针
RADIUS_SCALE    = 1.0                                # 半径缩放（<1更近，>1更远）
FILE_PREFIX     = "orbit_mdl"                       # 输出前缀（MDL 版）
IMG_EXT         = ".png"                           # ".png" 或 ".jpg"

ORBIT_CAM_PATH  = "/World/OrbitCam"                 # 轨道相机 prim 路径
WAIT_FRAMES     = 2                                  # 每步等待帧数，确保画面刷新
DELETE_AFTER    = False                              # 拍完是否删除临时相机

# 输出文件夹名（相对 USD 所在目录）
OUT_DIR_NAME    = "mdl_images"

# ---------------- Helpers ----------------
def _ctx(): return omni.usd.get_context()
def _stage(): return _ctx().get_stage()
def _vp(): return vp_utils.get_active_viewport()

def _normalize(v):
    try: return v.GetNormalized()
    except Exception:
        L = v.GetLength()
        return v / max(L, 1e-9)

def _world_up(stage):
    return Gf.Vec3d(0,0,1) if UsdGeom.GetStageUpAxis(stage)==UsdGeom.Tokens.z else Gf.Vec3d(0,1,0)

def _bbox_center_and_size(stage, path):
    prim = stage.GetPrimAtPath(Sdf.Path(path))
    if not prim or not prim.IsValid():
        raise RuntimeError(f"Target prim not found: {path}")
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(),
                              [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
                              useExtentsHint=True)
    rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    if rng.isEmpty if hasattr(rng, 'isEmpty') else rng.IsEmpty():
        raise RuntimeError(f"Empty bbox for prim: {path}")
    mn, mx = rng.GetMin(), rng.GetMax()
    return (mn + mx) * 0.5, (mx - mn)

def _ensure_out_dir_under_usd(stage):
    layer = stage.GetRootLayer()
    usd_path = layer.realPath if layer and layer.realPath else layer.identifier
    try:
        base_dir = os.path.dirname(usd_path)
        if not base_dir or base_dir.startswith("omniverse://") or base_dir.startswith("omni://"):
            raise ValueError("Non-local path")
    except Exception:
        base_dir = os.path.expanduser("~/mdl_fallback")
    out_dir = os.path.join(base_dir, OUT_DIR_NAME)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def _xf_cache():
    return UsdGeom.XformCache(Usd.TimeCode.Default())

def _get_cam_world_matrix(cam_prim):
    return _xf_cache().GetLocalToWorldTransform(cam_prim)

def _ensure_single_transform_op(prim):
    """确保 xformOpOrder 里只有一个 TransformOp；不删除旧 op，仅重排顺序。"""
    xf = UsdGeom.Xformable(prim)
    # 查找是否已有 TransformOp
    xop = None
    for op in xf.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTransform:
            xop = op
            break
    if xop is None:
        xop = xf.AddTransformOp()  # 新建一个
    # 把 op 顺序设置成只包含我们的 TransformOp（其他 op 不会被应用）
    xf.SetXformOpOrder([xop])
    return xop

def _set_transform_op_world_matrix(prim, M):
    xop = _ensure_single_transform_op(prim)
    xop.Set(M)

def _copy_intrinsics(dst_cam: UsdGeom.Camera, src_cam: UsdGeom.Camera):
    for getter, setter_name in [
        (src_cam.GetFocalLengthAttr,       "GetFocalLengthAttr"),
        (src_cam.GetHorizontalApertureAttr,"GetHorizontalApertureAttr"),
        (src_cam.GetVerticalApertureAttr,  "GetVerticalApertureAttr"),
        (src_cam.GetClippingRangeAttr,     "GetClippingRangeAttr"),
        (src_cam.GetFocusDistanceAttr,     "GetFocusDistanceAttr"),
        (src_cam.GetFStopAttr,             "GetFStopAttr"),
        (src_cam.GetShutterOpenAttr,       "GetShutterOpenAttr"),
        (src_cam.GetShutterCloseAttr,      "GetShutterCloseAttr"),
    ]:
        try:
            val = getter().Get()
            if val is not None:
                getattr(dst_cam, setter_name)().Set(val)
        except Exception:
            pass

def _rotate_vec(v, axis_unit, ang_rad):
    c, s = math.cos(ang_rad), math.sin(ang_rad)
    return v*c + Gf.Cross(axis_unit, v)*s + axis_unit*Gf.Dot(axis_unit, v)*(1.0 - c)

async def _wait_frames(n=1):
    app = omni.kit.app.get_app()
    for _ in range(max(1, n)):
        await app.next_update_async()

def _capture(vp, out_path):
    try:
        vp.capture_image(out_path)
    except Exception:
        vp_utils.capture_viewport_to_file(vp, out_path)

# ---------------- Main ----------------
async def main():
    stage = _stage()
    if not stage: raise RuntimeError("No USD stage open.")
    vp = _vp()
    if not vp: raise RuntimeError("No active viewport.")
    target_path = TARGET_PATH_STR.strip()
    if not target_path: raise RuntimeError("Please set TARGET_PATH_STR")

    center, size = _bbox_center_and_size(stage, target_path)
    world_up = _normalize(_world_up(stage))
    out_dir = _ensure_out_dir_under_usd(stage)

    # 记住原视口相机（路径），不改它
    orig_cam_path = vp.get_active_camera()
    if not orig_cam_path:
        raise RuntimeError("Active viewport has no camera. 请先 Save Current View as Camera 并激活。")
    orig_cam_prim = stage.GetPrimAtPath(Sdf.Path(orig_cam_path))
    if not orig_cam_prim or not orig_cam_prim.IsValid():
        raise RuntimeError(f"Original camera prim not found: {orig_cam_path}")
    orig_cam = UsdGeom.Camera(orig_cam_prim)

    # 准备/复用临时轨道相机
    orbit_prim = stage.GetPrimAtPath(Sdf.Path(ORBIT_CAM_PATH))
    if not orbit_prim or not orbit_prim.IsValid():
        orbit_cam = UsdGeom.Camera.Define(stage, Sdf.Path(ORBIT_CAM_PATH))
        orbit_prim = orbit_cam.GetPrim()
    else:
        orbit_cam = UsdGeom.Camera(orbit_prim)

    # 复制内参 + 世界矩阵
    _copy_intrinsics(orbit_cam, orig_cam)
    M0 = _get_cam_world_matrix(orig_cam_prim)
    _set_transform_op_world_matrix(orbit_prim, M0)

    # 切到临时相机
    vp.set_active_camera(ORBIT_CAM_PATH)
    await _wait_frames(WAIT_FRAMES)

    # 起始位姿
    M_start = _get_cam_world_matrix(orbit_prim)
    eye0 = Gf.Vec3d(M_start.ExtractTranslation())
    r0 = eye0 - center
    if r0.GetLength() < 1e-6:
        r0 = Gf.Vec3d(1,0,0)
    r0 = r0 * float(RADIUS_SCALE)

    step = (2.0 * math.pi) / max(1, NUM_SHOTS)
    sign = -1.0 if CW_ROTATE else 1.0
    start = math.radians(START_DEG)

    for i in range(NUM_SHOTS):
        theta = start + sign * step * i
        r_i = _rotate_vec(r0, world_up, theta)
        eye_i = center + r_i

        # 锁地平线，看向 center（零滚转）。如需保留原 roll，可把 up_i 改为 M0 的 up 在正交平面投影
        fwd_i = _normalize(center - eye_i)
        right_i = _normalize(Gf.Cross(fwd_i, world_up))
        if right_i.GetLength() < 1e-6:
            tmp_up = Gf.Vec3d(1,0,0) if abs(world_up[0])<0.9 else Gf.Vec3d(0,1,0)
            right_i = _normalize(Gf.Cross(fwd_i, tmp_up))
        up_i = _normalize(Gf.Cross(right_i, fwd_i))

        # 写世界矩阵（行：right, up, back, trans）
        M = Gf.Matrix4d(1.0)
        back = -fwd_i
        M.SetRow(0, Gf.Vec4d(right_i[0], right_i[1], right_i[2], 0.0))
        M.SetRow(1, Gf.Vec4d(up_i[0],    up_i[1],    up_i[2],    0.0))
        M.SetRow(2, Gf.Vec4d(back[0],    back[1],    back[2],    0.0))
        M.SetRow(3, Gf.Vec4d(eye_i[0],   eye_i[1],   eye_i[2],   1.0))
        _set_transform_op_world_matrix(orbit_prim, M)

        await _wait_frames(WAIT_FRAMES)
        fpath = os.path.join(out_dir, f"{FILE_PREFIX}_{i:02d}{IMG_EXT}")
        _capture(vp, fpath)
        print("Saved:", fpath)

    # 切回原相机（不改它任何 XformOps）
    vp.set_active_camera(orig_cam_path)
    await _wait_frames(WAIT_FRAMES)

    # 可选：删除临时相机
    if DELETE_AFTER:
        stage.RemovePrim(Sdf.Path(ORBIT_CAM_PATH))

    print("=== Orbit capture (MDL) done ===")
    print("Viewport restored to:", orig_cam_path)
    print("Output dir:", out_dir)

# 启动
asyncio.ensure_future(main())
