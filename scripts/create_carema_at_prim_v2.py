# === Isaac Sim: Smart room-fit camera (fits full room, not just a small object) ===
from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
import omni.kit.viewport.utility as vp_utils
import math

# --------- CONFIG ---------
TARGET_PATH     = "/Root/Meshes/Furnitures/pillow"  # 选一个物体；留空则使用当前选中 prim。例："/World/env_0/scene/Meshes/Furnitures/bed_01"
FIT_ROOT_PATH   = ""  # 建议填“房间/场景根”如 "/World/env_0/scene"；留空则自动向上找“更大父节点”
AZIMUTH_DEG     = 35.0
ELEVATION_DEG   = 20.0
FOV_H_DEG       = 60.0        # 水平FOV（度）
ASPECT          = 16.0/9.0    # 视口宽高比；如 4/3、1.0
PADDING         = 1.10        # >1 留边
FOCAL_MM        = 35.0
NEAR_CLIP       = 0.01
FAR_CLIP        = 10000.0
CAMERA_BASENAME = "/World/AutoRoomCam"

# --------- helpers ---------
def _stage():
    return omni.usd.get_context().get_stage()

def _sel_path_if_empty():
    ctx = omni.usd.get_context()
    sel = ctx.get_selection()
    if sel:
        s = sel.get_selected_prim_paths()
        if s: return s[0]
    return None

def _resolve_instance_proxy(prim):
    if prim and prim.IsInstanceProxy():
        fn = getattr(prim, "GetPrimInPrototype", None)
        if callable(fn):
            p2 = fn()
            if p2 and p2.IsValid(): return p2
    return prim

def _bbox_world(prim):
    stage = _stage()
    purposes = [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy]
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), purposes, useExtentsHint=True)
    return cache.ComputeWorldBound(prim)

def _range_center_size(rng):
    mn, mx = rng.GetMin(), rng.GetMax()
    center = (mn + mx) * 0.5
    size = mx - mn
    return center, size

def _diag_len(v):
    return float((v[0]*v[0] + v[1]*v[1] + v[2]*v[2])**0.5)

def _unique_path(stage, base):
    if not stage.GetPrimAtPath(base): return Sdf.Path(base)
    i = 1
    while True:
        p = Sdf.Path(f"{base}_{i}")
        if not stage.GetPrimAtPath(p): return p
        i += 1

def _up_axis_vec(stage):
    return Gf.Vec3d(0,0,1) if UsdGeom.GetStageUpAxis(stage)==UsdGeom.Tokens.z else Gf.Vec3d(0,1,0)

def _camera_fit_distance(w_half, h_half, fov_h_rad, fov_v_rad):
    # 对水平/垂直分别给出所需距离，取最大
    d_h = w_half / max(math.tan(fov_h_rad/2.0), 1e-6)
    d_v = h_half / max(math.tan(fov_v_rad/2.0), 1e-6)
    return max(d_h, d_v)

def _project_corners_extents(center, half_size, right, up):
    # 以中心和半长宽高生成 8 角点，投影到相机 right/up 轴，返回水平/垂直半宽
    hx, hy, hz = half_size[0], half_size[1], half_size[2]
    corners = [
        Gf.Vec3d( sx*hx, sy*hy, sz*hz ) for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)
    ]
    # 将 corners 从盒子局部（轴对齐）转到世界？这里我们用世界对齐盒，所以直接以 center 为基准
    # 实际只需相对 center 的向量投影到 right/up：因为盒子与世界轴对齐，corners 即相对向量。
    vals_r = []
    vals_u = []
    for c in corners:
        # 相对向量在 right/up 上的投影长度（世界对齐盒直接用分量乘以 right/up）
        # 由于 c 是世界轴向组合（±hx,±hy,±hz），投影 = dot(c, dir)
        vals_r.append(abs(Gf.Dot(c, right)))
        vals_u.append(abs(Gf.Dot(c, up)))
    return max(vals_r), max(vals_u)

def _pick_fit_root_from_target(target_prim):
    # 向上走，找“更像整屋”的父节点：对角线长度每次显著增大（> 2~3x），或到 /World
    stage = _stage()
    prev_rng = _bbox_world(target_prim).ComputeAlignedRange()
    prev_diag = _diag_len(prev_rng.GetMax() - prev_rng.GetMin())
    p = target_prim.GetParent()
    best = target_prim
    while p and p.GetPath() != Sdf.Path.absoluteRootPath:
        rng = _bbox_world(p).ComputeAlignedRange()
        diag = _diag_len(rng.GetMax() - rng.GetMin())
        if diag > prev_diag * 2.5:   # 阈值可调：越小越容易选到大场景
            best = p
            prev_diag = diag
        p = p.GetParent()
    return best

# --------- main ---------
stage = _stage()
if not stage:
    raise RuntimeError("No USD stage open.")

# 解析目标 prim
if not TARGET_PATH:
    maybe = _sel_path_if_empty()
    if not maybe:
        raise RuntimeError("TARGET_PATH 为空且未选中任何 prim。请设置 TARGET_PATH 或先在 Stage 里选中一个物体。")
    TARGET_PATH = maybe

target = stage.GetPrimAtPath(TARGET_PATH)
if not target or not target.IsValid():
    raise RuntimeError(f"Target prim not found: {TARGET_PATH}")
target = _resolve_instance_proxy(target)

# 决定“取景对象”（fit_root）
if FIT_ROOT_PATH:
    fit_root = stage.GetPrimAtPath(FIT_ROOT_PATH)
    if not fit_root or not fit_root.IsValid():
        raise RuntimeError(f"FIT_ROOT_PATH not found: {FIT_ROOT_PATH}")
else:
    fit_root = _pick_fit_root_from_target(target)

# 计算对齐范围
bbox = _bbox_world(fit_root)
rng  = bbox.ComputeAlignedRange()
if rng.IsEmpty():
    raise RuntimeError(f"Empty bbox for prim: {fit_root.GetPath()}")

center, size = _range_center_size(rng)
half_size = Gf.Vec3d(max(size[0],1e-6)/2.0, max(size[1],1e-6)/2.0, max(size[2],1e-6)/2.0)

# 相机朝向（由 azimuth/elevation 决定），以世界轴为参考
az = math.radians(AZIMUTH_DEG)
el = math.radians(ELEVATION_DEG)
forward = Gf.Vec3d(math.cos(el)*math.cos(az), math.cos(el)*math.sin(az), math.sin(el)).GetNormalized()
# camera 看向目标 => 视线方向 from eye -> center 是 forward，因此 eye = center - forward * dist
stage_up = _up_axis_vec(stage)
right = Gf.Cross(forward, stage_up).GetNormalized()
if right.GetLengthSq() < 1e-8:
    # 防止 forward 与 up 共线
    right = Gf.Cross(forward, Gf.Vec3d(1,0,0)).GetNormalized()
up = Gf.Cross(right, forward).GetNormalized()

# 计算在相机坐标下的水平/垂直半宽（“投影包围盒法”）
w_half_proj, h_half_proj = _project_corners_extents(center, half_size, right, up)

# 由 FOV 计算所需距离（同时满足水平和垂直）
fov_h = math.radians(FOV_H_DEG)
fov_v = 2.0 * math.atan( math.tan(fov_h/2.0) / max(ASPECT, 1e-6) )
distance = _camera_fit_distance(w_half_proj, h_half_proj, fov_h, fov_v) * PADDING

eye = Gf.Vec3d(center) - forward * distance

# 建相机
cam_path = _unique_path(stage, CAMERA_BASENAME)
cam = UsdGeom.Camera.Define(stage, cam_path)

# 设置内参（按水平FOV与焦距推胶片宽）
H_APERTURE_MM = 2.0 * FOCAL_MM * math.tan(fov_h/2.0)
cam.GetFocalLengthAttr().Set(FOCAL_MM)
cam.GetHorizontalApertureAttr().Set(H_APERTURE_MM)
cam.GetVerticalApertureAttr().Set(H_APERTURE_MM / max(ASPECT,1e-6))
cam.GetClippingRangeAttr().Set(Gf.Vec2f(NEAR_CLIP, FAR_CLIP))

# 设置外参（LookAt）
m = Gf.Matrix4d(1.0); m.SetLookAt(eye, center, up)
xf = UsdGeom.Xformable(cam)
ops = xf.GetOrderedXformOps()
xop = ops[0] if (ops and ops[0].GetOpType()==UsdGeom.XformOp.TypeTransform) else xf.AddTransformOp()
xop.Set(m)

# 切视口
vp = vp_utils.get_active_viewport()
try:
    vp.set_active_camera(str(cam_path))
except Exception as e:
    print("[WARN] set_active_camera failed:", e)

print("=== Smart Room Camera ===")
print("Target       :", TARGET_PATH)
print("Fit root     :", fit_root.GetPath())
print("Center       :", (float(center[0]), float(center[1]), float(center[2])))
print("Size (xyz)   :", (float(size[0]), float(size[1]), float(size[2])))
print("Proj half    :", ("w", float(w_half_proj)), ("h", float(h_half_proj)))
print("FOV (h/v)    :", (FOV_H_DEG, math.degrees(fov_v)))
print("Distance     :", float(distance))
print("Eye          :", (float(eye[0]), float(eye[1]), float(eye[2])))
print("=========================")
