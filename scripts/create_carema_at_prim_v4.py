# === Isaac Sim: Fit target while inheriting source camera rotation + pitch + relative height (ROW-MAJOR) ===
# 功能：
# 1) 继承源相机旋转（不改变 roll/yaw 基调）
# 2) 支持俯仰（绕右轴压视角）与“相对目标尺寸”的抬高
# 3) 基于目标 prim 的包围盒 + FOV 自动计算距离，确保完整入画
# 4) 打印新旧相机基向量角度差与 roll 差异，便于调试

from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
import omni.kit.viewport.utility as vp_utils
import math

# ------------------ Config ------------------
TARGET_PATH_STR        = "/Root/Meshes/Furnitures/table"          # 目标 prim；留空则使用当前选中（例如 "/Root/Meshes/Furnitures/table"）
SOURCE_CAMERA_PATH_STR = ""          # 源相机 prim；留空则用视口当前激活相机（建议先 Save Current View as Camera）
FOV_H_DEG              = 55.0        # 水平 FOV（度），大=更广
ASPECT_FALLBACK        = 16.0/9.0    # 读不到视口时的兜底宽高比
PADDING                = 1.08        # 安全留边比例（>1）
BACKOFF                = 0.3        # 在 fit 距离基础上再后退一点（>1 更远；也可 <1 更近）
FOCAL_MM               = 35.0        # 焦距（mm），用于与 FOV 推算胶片宽
NEAR_CLIP              = 0.01
FAR_CLIP               = 10000.0
CAMERA_BASENAME        = "/World/AutoCamInherit"

# 视角微调
PITCH_DOWN_DEG         = 0.0         # 俯仰角（度），正值=向下压视角（绕相机右轴旋转）

# 抬高方式（相对/绝对）
# - "bbox_z"   : 相对 bbox 高度（Z 维）
# - "bbox_max" : 相对三维尺寸最大值
# - "bbox_diag": 相对 bbox 对角线长度
# - "abs"      : 绝对单位（与旧逻辑一致）
HEIGHT_OFFSET_MODE     = "bbox_z"
HEIGHT_OFFSET_VALUE    = 0.5        # 相对模式=比例；abs 模式=绝对单位数值

# 可选：曝光/景深
ENABLE_SHUTTER_TWEAK   = False
SHUTTER_OPEN_SEC       = 0.0         # 0/0 表示无运动模糊（高速快门）
SHUTTER_CLOSE_SEC      = 0.0
ENABLE_DOF             = False
FOCUS_DISTANCE         = 300.0       # 对焦距离（与场景单位一致）
F_STOP                 = 4.0         # 光圈（越小景深越浅）

# ------------------ Helpers ------------------
def _ctx(): return omni.usd.get_context()
def _stage(): return _ctx().get_stage()

def _get_active_camera_prim_path_or_none():
    try:
        vp = vp_utils.get_active_viewport()
        if not vp: return None
        p = vp.get_active_camera()
        return p if p else None
    except Exception:
        return None

def _get_selected_path_or_none():
    sel = _ctx().get_selection()
    if not sel: return None
    paths = sel.get_selected_prim_paths()
    return paths[0] if paths else None

def _normalize(v):
    try: return v.GetNormalized()
    except Exception:
        L = v.GetLength()
        return v / max(L, 1e-9)

def _bbox_world_range(prim):
    purposes = [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy]
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), purposes, useExtentsHint=True)
    return cache.ComputeWorldBound(prim).ComputeAlignedRange()

def _active_viewport_aspect(default_aspect):
    try:
        vp = vp_utils.get_active_viewport()
        if vp:
            w, h = vp.get_texture_size()
            if w and h and h>0: return float(w)/float(h)
    except Exception:
        pass
    return default_aspect

def _world_basis_from_camera_prim(cam_prim):
    """Camera local axes: +X=right, +Y=up, -Z=forward."""
    xc = UsdGeom.XformCache(Usd.TimeCode.Default())
    M  = xc.GetLocalToWorldTransform(cam_prim)
    right   = _normalize(M.TransformDir(Gf.Vec3d(1,0,0)))
    up      = _normalize(M.TransformDir(Gf.Vec3d(0,1,0)))
    forward = _normalize(M.TransformDir(Gf.Vec3d(0,0,-1)))
    return right, up, forward

def _angles_between_bases(a, b):
    def ang(u,v):
        d = max(-1.0, min(1.0, float(Gf.Dot(u,v))))
        return math.degrees(math.acos(d))
    return tuple(ang(u,v) for u,v in zip(a,b))

def _roll_delta_on_forward(src_up, new_up, fwd):
    su = src_up - Gf.Dot(src_up, fwd)*fwd
    nu = new_up - Gf.Dot(new_up, fwd)*fwd
    if su.GetLength() < 1e-8 or nu.GetLength() < 1e-8:
        return 0.0
    su = _normalize(su); nu = _normalize(nu)
    c = max(-1.0, min(1.0, float(Gf.Dot(su, nu))))
    s = float(Gf.Dot(Gf.Cross(su, nu), fwd))
    return math.degrees(math.atan2(s, c))

def _build_world_matrix_rows(right, up, forward, eye):
    """Gf.Matrix4d 行主序：行0=right, 行1=up, 行2=back(= -forward), 行3=translation。"""
    m = Gf.Matrix4d(1.0)
    back = -forward
    m.SetRow(0, Gf.Vec4d(right[0],  right[1],  right[2],  0.0))
    m.SetRow(1, Gf.Vec4d(up[0],     up[1],     up[2],     0.0))
    m.SetRow(2, Gf.Vec4d(back[0],   back[1],   back[2],   0.0))
    m.SetRow(3, Gf.Vec4d(eye[0],    eye[1],    eye[2],    1.0))
    return m

def _rotate_vec_around_axis(v, axis_unit, ang_rad):
    # 轴须单位化；Rodrigues 公式
    c, s = math.cos(ang_rad), math.sin(ang_rad)
    return v*c + Gf.Cross(axis_unit, v)*s + axis_unit*Gf.Dot(axis_unit, v)*(1.0 - c)

def _length_diag(v3):
    return float((v3[0]*v3[0] + v3[1]*v3[1] + v3[2]*v3[2]) ** 0.5)

def _compute_height_offset_units(mode, value, size_vec):
    """根据模式返回最终抬高的“绝对单位”数值。"""
    if mode == "abs":
        return float(value)
    if mode == "bbox_z":
        ref = float(size_vec[2])
    elif mode == "bbox_max":
        ref = max(float(size_vec[0]), float(size_vec[1]), float(size_vec[2]))
    elif mode == "bbox_diag":
        ref = _length_diag(size_vec)
    else:
        # 未知模式时退回 bbox_max
        ref = max(float(size_vec[0]), float(size_vec[1]), float(size_vec[2]))
    return float(value) * ref

# ------------------ Main ------------------
stage = _stage()
if not stage: raise RuntimeError("No USD stage open.")

# Target prim
target_path = (TARGET_PATH_STR.strip() or _get_selected_path_or_none())
if not target_path:
    raise RuntimeError("请设置 TARGET_PATH_STR，或先选中一个 prim 再运行。")
target_prim = stage.GetPrimAtPath(Sdf.Path(target_path))
if not target_prim or not target_prim.IsValid():
    raise RuntimeError(f"Target prim not found: {target_path}")

# Source camera prim
src_cam_path = SOURCE_CAMERA_PATH_STR.strip() or (_get_active_camera_prim_path_or_none() or "")
if not src_cam_path:
    raise RuntimeError("未找到源相机。请先将当前视口保存为 Camera 并激活，或填写 SOURCE_CAMERA_PATH_STR。")
src_cam_prim = stage.GetPrimAtPath(Sdf.Path(src_cam_path))
if not src_cam_prim or not src_cam_prim.IsValid():
    raise RuntimeError(f"Source camera prim not found: {src_cam_path}")

# Target bbox
rng = _bbox_world_range(target_prim)
if rng.IsEmpty(): raise RuntimeError(f"Empty bbox for prim: {target_path}")
mn, mx = rng.GetMin(), rng.GetMax()
center = (mn + mx) * 0.5
size   = mx - mn
half   = Gf.Vec3d(max(size[0],1e-6)/2.0, max(size[1],1e-6)/2.0, max(size[2],1e-6)/2.0)

# Source basis
src_right, src_up, src_fwd = _world_basis_from_camera_prim(src_cam_prim)

# ---- 俯仰（绕右轴）；正值=向下压视角 ----
pitch_rad  = math.radians(PITCH_DOWN_DEG)
right_unit = _normalize(src_right)
adj_fwd = _rotate_vec_around_axis(src_fwd, right_unit, pitch_rad)
adj_up  = _rotate_vec_around_axis(src_up,  right_unit, pitch_rad)
# 正交化
adj_fwd   = _normalize(adj_fwd)
adj_right = _normalize(Gf.Cross(adj_fwd, adj_up))
adj_up    = _normalize(Gf.Cross(adj_right, adj_fwd))

# ---- 用“调整后的基向量”做装框拟合（计算距离）----
hx, hy, hz = float(half[0]), float(half[1]), float(half[2])
corners = [Gf.Vec3d(sx*hx, sy*hy, sz*hz) for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)]

w_half = 0.0; h_half = 0.0
for v in corners:
    w_half = max(w_half, abs(Gf.Dot(v, adj_right)))
    h_half = max(h_half, abs(Gf.Dot(v, adj_up)))

aspect = _active_viewport_aspect(ASPECT_FALLBACK)
fov_h  = math.radians(FOV_H_DEG)
fov_v  = 2.0 * math.atan( math.tan(fov_h/2.0) / max(aspect, 1e-6) )
dist_h = w_half / max(math.tan(fov_h/2.0), 1e-6)
dist_v = h_half / max(math.tan(fov_v/2.0), 1e-6)
distance = max(dist_h, dist_v) * PADDING * BACKOFF

# ---- 根据模式计算“抬高的绝对单位”，并应用到 eye ----
height_units = _compute_height_offset_units(HEIGHT_OFFSET_MODE, HEIGHT_OFFSET_VALUE, size)
eye = Gf.Vec3d(center) - adj_fwd * distance + adj_up * height_units
# 如果你想相对“世界 Z 轴”抬高，而不是相机 up 轴：把上一行改为 + Gf.Vec3d(0,0,1) * height_units（或 Y-up 用(0,1,0)）

# Create camera
cam_path = CAMERA_BASENAME
if stage.GetPrimAtPath(cam_path):
    i=1
    while stage.GetPrimAtPath(f"{CAMERA_BASENAME}_{i}"): i+=1
    cam_path = f"{CAMERA_BASENAME}_{i}"
new_cam = UsdGeom.Camera.Define(stage, Sdf.Path(cam_path))

# Intrinsics
H_APERTURE_MM = 2.0 * FOCAL_MM * math.tan(fov_h/2.0)
new_cam.GetFocalLengthAttr().Set(FOCAL_MM)
new_cam.GetHorizontalApertureAttr().Set(H_APERTURE_MM)
new_cam.GetVerticalApertureAttr().Set(H_APERTURE_MM / max(aspect, 1e-6))
new_cam.GetClippingRangeAttr().Set(Gf.Vec2f(NEAR_CLIP, FAR_CLIP))

# 可选：快门/景深
if ENABLE_SHUTTER_TWEAK:
    new_cam.GetShutterOpenAttr().Set(float(SHUTTER_OPEN_SEC))
    new_cam.GetShutterCloseAttr().Set(float(SHUTTER_CLOSE_SEC))
if ENABLE_DOF:
    new_cam.GetFocusDistanceAttr().Set(float(FOCUS_DISTANCE))
    new_cam.GetFStopAttr().Set(float(F_STOP))

# World transform（行：right, up, back; 行3=translation）
M = _build_world_matrix_rows(adj_right, adj_up, adj_fwd, eye)
xf = UsdGeom.Xformable(new_cam)
ops = xf.GetOrderedXformOps()
xop = ops[0] if (ops and ops[0].GetOpType()==UsdGeom.XformOp.TypeTransform) else xf.AddTransformOp()
xop.Set(M)

# Switch viewport
vp = vp_utils.get_active_viewport()
try:
    vp.set_active_camera(str(cam_path))
except Exception as e:
    print("[WARN] set_active_camera failed:", e)

# Verify new basis
xc2 = UsdGeom.XformCache(Usd.TimeCode.Default())
Mnew = xc2.GetLocalToWorldTransform(stage.GetPrimAtPath(Sdf.Path(cam_path)))
new_right = _normalize(Mnew.TransformDir(Gf.Vec3d(1,0,0)))
new_up    = _normalize(Mnew.TransformDir(Gf.Vec3d(0,1,0)))
new_fwd   = _normalize(Mnew.TransformDir(Gf.Vec3d(0,0,-1)))

# 与“调整后的基向量”的差异（应接近 0）
ang_right, ang_up, ang_fwd = _angles_between_bases((adj_right, adj_up, adj_fwd),
                                                   (new_right, new_up, new_fwd))
roll_delta = _roll_delta_on_forward(adj_up, new_up, adj_fwd)

def _t(v): return tuple(round(x,6) for x in (v[0],v[1],v[2]))
print("=== New Camera (inherit + pitch + relative height) ===")
print("Target prim        :", target_path)
print("Source camera      :", src_cam_path)
print("New camera path    :", cam_path)
print("Center             :", (float(center[0]), float(center[1]), float(center[2])))
print("Size (xyz)         :", (float(size[0]), float(size[1]), float(size[2])))
print("Aspect / FOV h/v   :", (float(aspect), FOV_H_DEG, math.degrees(fov_v)))
print("Distance           :", float(distance))
print("Eye                :", (float(eye[0]), float(eye[1]), float(eye[2])))
print("PitchDown          :", PITCH_DOWN_DEG)
print("Height mode/value  :", HEIGHT_OFFSET_MODE, HEIGHT_OFFSET_VALUE, "=> units:", height_units)

print("\n-- Basis (right/up/forward) --")
print("ADJ right/up/fwd   :", _t(adj_right), _t(adj_up), _t(adj_fwd))
print("NEW right/up/fwd   :", _t(new_right), _t(new_up), _t(new_fwd))

print("\n-- Angle diffs vs ADJ (deg) --")
print("right / up / fwd   :", round(ang_right,6), round(ang_up,6), round(ang_fwd,6))
print("roll delta on fwd  :", round(roll_delta,6))
print("=====================================")
