# === Orbit-and-capture around vertical axis from current view ===
# - Uses active viewport's current camera as the starting orientation
# - Orbits around TARGET prim's bbox center about stage up-axis
# - Captures N evenly spaced views over 360° into <usd_dir>/nomdl_images
# - Restores the camera transform after capture

from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
import omni.kit.viewport.utility as vp_utils
import math, os

# ---------------- Config ----------------
TARGET_PATH_STR = "/Root/Meshes/Furnitures/table"   # 必填：围绕的目标 prim
NUM_SHOTS       = 10                                # 总张数
START_DEG       = 0.0                               # 起始角（度）
CW_ROTATE       = False                             # 顺时针？False=逆时针
FILE_PREFIX     = "orbit"                           # 文件前缀
IMG_EXT         = ".png"                            # 保存格式：.png/.jpg

# ---------------- Helpers ----------------
def _ctx(): return omni.usd.get_context()
def _stage(): return _ctx().get_stage()

def _get_active_vp():
    return vp_utils.get_active_viewport()

def _get_active_cam_path():
    vp = _get_active_vp()
    return vp.get_active_camera() if vp else None

def _normalize(v):
    try: return v.GetNormalized()
    except Exception:
        L = v.GetLength()
        return v / max(L, 1e-9)

def _world_up(stage):
    return Gf.Vec3d(0,0,1) if UsdGeom.GetStageUpAxis(stage)==UsdGeom.Tokens.z else Gf.Vec3d(0,1,0)

def _bbox_world_center(stage, prim_path):
    prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
    if not prim or not prim.IsValid():
        raise RuntimeError(f"Target prim not found: {prim_path}")
    purposes = [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy]
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), purposes, useExtentsHint=True)
    rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    if rng.IsEmpty():
        raise RuntimeError(f"Empty bbox for prim: {prim_path}")
    mn, mx = rng.GetMin(), rng.GetMax()
    return (mn + mx) * 0.5

def _xf_cache():
    return UsdGeom.XformCache(Usd.TimeCode.Default())

def _get_cam_world_matrix(cam_prim):
    return _xf_cache().GetLocalToWorldTransform(cam_prim)

def _set_cam_world_matrix(cam_prim, M):
    xf = UsdGeom.Xformable(cam_prim)
    ops = xf.GetOrderedXformOps()
    xop = ops[0] if (ops and ops[0].GetOpType()==UsdGeom.XformOp.TypeTransform) else xf.AddTransformOp()
    xop.Set(M)

def _look_at_matrix(eye, center, up):
    m = Gf.Matrix4d(1.0)
    m.SetLookAt(eye, center, up)
    return m

def _rotate_vec(v, axis_unit, ang_rad):
    c, s = math.cos(ang_rad), math.sin(ang_rad)
    return v*c + Gf.Cross(axis_unit, v)*s + axis_unit*Gf.Dot(axis_unit, v)*(1.0 - c)

def _capture(vp, out_path):
    ok = False
    try:
        vp.capture_image(out_path)
        ok = True
    except Exception:
        try:
            # older/newer utility fallback
            vp_utils.capture_viewport_to_file(vp, out_path)
            ok = True
        except Exception as e:
            print("[ERR] capture failed:", e)
    if ok:
        print("Saved:", out_path)

def _ensure_out_dir_under_usd(stage):
    # 尝试用 root layer 的 realPath；若不可用，退回用户目录
    layer = stage.GetRootLayer()
    usd_path = layer.realPath if layer and layer.realPath else layer.identifier
    try:
        base_dir = os.path.dirname(usd_path)
        if not base_dir or base_dir.startswith("omniverse://") or base_dir.startswith("omni://"):
            raise ValueError("Non-local path")
    except Exception:
        base_dir = os.path.expanduser("~/nomdl_fallback")
    out_dir = os.path.join(base_dir, "nomdl_images")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

# ---------------- Main ----------------
stage = _stage()
if not stage: raise RuntimeError("No USD stage open.")

target_path = TARGET_PATH_STR.strip()
if not target_path:
    raise RuntimeError("请设置 TARGET_PATH_STR 为你要围绕的 prim。")

vp = _get_active_vp()
if not vp: raise RuntimeError("No active viewport.")

cam_path = _get_active_cam_path()
if not cam_path: raise RuntimeError("Active viewport has no camera. 请先 Save Current View as Camera 并激活它。")
cam_prim = stage.GetPrimAtPath(Sdf.Path(cam_path))
if not cam_prim or not cam_prim.IsValid():
    raise RuntimeError(f"Active camera prim not found: {cam_path}")

# 轨道中心 & 上轴
center = _bbox_world_center(stage, target_path)
world_up = _normalize(_world_up(stage))

# 记录初始相机姿态
M0 = _get_cam_world_matrix(cam_prim)
eye0 = Gf.Vec3d(M0.ExtractTranslation())
# 从矩阵恢复当前朝向（避免 roll 偏差）
fwd0  = _normalize(_xf_cache().GetLocalToWorldTransform(cam_prim).TransformDir(Gf.Vec3d(0,0,-1)))
# 半径向量（中心->相机）
r_vec0 = eye0 - center
radius = r_vec0.GetLength()
if radius < 1e-6:
    # 极端情况：相机就在中心，给一个很小的半径
    r_vec0 = Gf.Vec3d(1,0,0)
    radius = 1.0

# 输出目录
out_dir = _ensure_out_dir_under_usd(stage)

# 角步进
step = (2.0 * math.pi) / max(1, NUM_SHOTS)
sign = -1.0 if CW_ROTATE else 1.0

# 逐帧拍摄
for i in range(NUM_SHOTS):
    theta = math.radians(START_DEG) + sign * step * i
    # 围绕世界竖直轴（world_up）旋转“相机相对中心”的矢量
    r_i = _rotate_vec(r_vec0, world_up, theta)
    eye_i = center + r_i

    # 用“零滚转、锁地平线”的朝向：看向 center，up≈world_up
    fwd_i = _normalize(center - eye_i)
    right_i = _normalize(Gf.Cross(fwd_i, world_up))
    if right_i.GetLength() < 1e-6:
        # 退化时换个 up
        tmp_up = Gf.Vec3d(1,0,0) if abs(world_up[0])<0.9 else Gf.Vec3d(0,1,0)
        right_i = _normalize(Gf.Cross(fwd_i, tmp_up))
    up_i = _normalize(Gf.Cross(right_i, fwd_i))

    # 设定相机世界矩阵（行：right, up, back, trans）
    M = Gf.Matrix4d(1.0)
    back = -fwd_i
    M.SetRow(0, Gf.Vec4d(right_i[0], right_i[1], right_i[2], 0.0))
    M.SetRow(1, Gf.Vec4d(up_i[0],    up_i[1],    up_i[2],    0.0))
    M.SetRow(2, Gf.Vec4d(back[0],    back[1],    back[2],    0.0))
    M.SetRow(3, Gf.Vec4d(eye_i[0],   eye_i[1],   eye_i[2],   1.0))
    _set_cam_world_matrix(cam_prim, M)

    # 触发截图
    fname = f"{FILE_PREFIX}_{i:02d}{IMG_EXT}"
    fpath = os.path.join(out_dir, fname)
    _capture(vp, fpath)

# 还原相机
_set_cam_world_matrix(cam_prim, M0)

print("=== Orbit capture done ===")
print("Camera restored to original pose.")
print("Output dir:", out_dir)
