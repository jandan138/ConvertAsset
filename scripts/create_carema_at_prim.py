# ===== Isaac Sim / USD: create a camera that looks at a target prim (robust) =====
# 使用方式：
# 1) 优选：把 TARGET_PATH 改成你的物体 prim 路径；或
# 2) 不改 TARGET_PATH，先在 Stage/Viewport 里选中一个 prim，再运行脚本。
#
# 脚本会：
#   - 解析目标 prim（支持 instance proxy）
#   - 用 BBoxCache 计算世界包围盒，ComputeAlignedRange() 取 min/max
#   - 根据水平 FOV 自动算相机距离，让目标完整装入画面
#   - 生成 /World/AutoCamera_* 并切换到该相机

from pxr import Usd, UsdGeom, Gf, Sdf
import omni.usd
import omni.kit.viewport.utility as vp_utils
import math

# --------- 配置（可修改） ----------
TARGET_PATH_STR = "/Root/Meshes/Furnitures/bed/model_db2d46cc6932e68275c07f07ea229d2a_0/Instance/Group_bed_headboard_00"   # 例："/World/env_0/scene/Meshes/Furnitures/bed_01"；留空则用“当前选中”的 prim
AZIMUTH_DEG     = 45.0
ELEVATION_DEG   = 25.0
FOV_DEG         = 60.0     # 水平视场角（度）
PADDING         = 1.15     # >1 稍微拉远，避免裁切
FOCAL_MM        = 35.0
ASPECT          = 16.0/9.0 # 视口宽高比；若用方图改成 1.0
NEAR_CLIP       = 0.01
FAR_CLIP        = 10000.0
CAMERA_BASENAME = "/World/AutoCamera"

# --------- 工具函数 ----------
def _resolve_instance_proxy(prim):
    if prim and prim.IsInstanceProxy():
        fn = getattr(prim, "GetPrimInPrototype", None)
        if callable(fn):
            p2 = fn()
            if p2 and p2.IsValid():
                return p2
    return prim

def _unique_camera_path(stage, base):
    if not stage.GetPrimAtPath(base):
        return Sdf.Path(base)
    i = 1
    while True:
        p = Sdf.Path(f"{base}_{i}")
        if not stage.GetPrimAtPath(p):
            return p
        i += 1

def _get_stage_up_axis(stage):
    up = UsdGeom.GetStageUpAxis(stage)
    return Gf.Vec3d(0,0,1) if up == UsdGeom.Tokens.z else Gf.Vec3d(0,1,0)

def _compute_world_bbox(stage, prim):
    # 兼容常见 API：用标准构造函数（不要用 GetIncludedPurposesFromNames）
    purposes = [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy]
    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), purposes, useExtentsHint=True)
    return bbox_cache.ComputeWorldBound(prim)

def _look_at_matrix(eye, center, up):
    m = Gf.Matrix4d(1.0)
    m.SetLookAt(eye, center, up)
    return m

def _guess_similar_paths(stage, key, limit=8):
    # 小助手：当找不到 prim 时，给几个相似名字的候选
    res = []
    it = stage.Traverse() if stage else []
    key_low = key.lower()
    for p in it:
        name = p.GetPath().pathString
        if key_low in name.lower():
            res.append(name)
            if len(res) >= limit: break
    return res

# --------- 主流程 ----------
ctx = omni.usd.get_context()
stage = ctx.get_stage()
if stage is None:
    raise RuntimeError("No USD stage open.")

# 解析目标 prim 路径：优先用配置；否则用“当前选中”的第一个 prim
target_path = None
if TARGET_PATH_STR:
    target_path = Sdf.Path(TARGET_PATH_STR)
else:
    sel = ctx.get_selection()
    sel_paths = sel.get_selected_prim_paths() if sel else []
    if sel_paths:
        target_path = Sdf.Path(sel_paths[0])

if target_path is None:
    raise RuntimeError("No target specified. Set TARGET_PATH_STR or select a prim before running.")

target = stage.GetPrimAtPath(target_path)
if not target or not target.IsValid():
    # 给几个相似候选，便于你核对路径
    hints = _guess_similar_paths(stage, target_path.name, limit=8)
    msg = f"Target prim not found: {target_path}\n"
    if hints:
        msg += "Did you mean one of:\n  - " + "\n  - ".join(hints)
    raise RuntimeError(msg)

target = _resolve_instance_proxy(target)

# 取世界包围盒并计算中心/尺寸（修复：BBox3d 无 GetCenter，用 ComputeAlignedRange）
bbox = _compute_world_bbox(stage, target)
rng = bbox.ComputeAlignedRange()   # Gf.Range3d
if not rng.IsEmpty():
    mn = rng.GetMin()
    mx = rng.GetMax()
    center = (mn + mx) * 0.5
    size = mx - mn
else:
    center = Gf.Vec3d(0,0,0)
    size = Gf.Vec3d(0.5,0.5,0.5)

L = max(float(size[0]), float(size[1]), float(size[2]), 1e-4)
fov_rad = math.radians(FOV_DEG)
distance = (L * 0.5 * PADDING) / max(math.tan(fov_rad / 2.0), 1e-6)

az = math.radians(AZIMUTH_DEG)
el = math.radians(ELEVATION_DEG)
dir_to_target = Gf.Vec3d(
    math.cos(el) * math.cos(az),
    math.cos(el) * math.sin(az),
    math.sin(el)
)
eye = Gf.Vec3d(center) - dir_to_target * distance

# 建相机并设置参数
cam_path = _unique_camera_path(stage, CAMERA_BASENAME)
cam = UsdGeom.Camera.Define(stage, cam_path)

# 用水平 FOV 反推水平胶片宽（aperture）
H_APERTURE_MM = 2 * FOCAL_MM * math.tan(fov_rad / 2.0)
cam.GetFocalLengthAttr().Set(FOCAL_MM)
cam.GetHorizontalApertureAttr().Set(H_APERTURE_MM)
cam.GetVerticalApertureAttr().Set(H_APERTURE_MM / max(ASPECT, 1e-6))
cam.GetClippingRangeAttr().Set(Gf.Vec2f(NEAR_CLIP, FAR_CLIP))

# 设置外参（LookAt），up 取舞台 up 轴
up = _get_stage_up_axis(stage)
xf = UsdGeom.Xformable(cam)
ops = xf.GetOrderedXformOps()
xop = ops[0] if (ops and ops[0].GetOpType()==UsdGeom.XformOp.TypeTransform) else xf.AddTransformOp()
xop.Set(_look_at_matrix(eye, center, up))

# 切到该相机
vp = vp_utils.get_active_viewport()
try:
    vp.set_active_camera(str(cam_path))
except Exception as e:
    print("[WARN] Failed to set active camera:", e)

print("=== Auto Camera Created ===")
print("Target prim :", target_path)
print("Camera path :", cam_path)
print("Center      :", (float(center[0]), float(center[1]), float(center[2])))
print("BBox size   :", (float(size[0]), float(size[1]), float(size[2])))
print("Azimuth/Elv :", AZIMUTH_DEG, ELEVATION_DEG)
print("FOV (deg)   :", FOV_DEG)
print("Distance    :", float(distance))
print("Eye         :", (float(eye[0]), float(eye[1]), float(eye[2])))
print("Up axis     :", "Z-up" if up[2]==1.0 else "Y-up")
print("================================")
