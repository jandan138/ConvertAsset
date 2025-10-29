import argparse
import sys
parser = argparse.ArgumentParser("Usd Load sample")
parser.add_argument(
    "--usd_path", type=str, help="Path to usd file", required=True
)
parser.add_argument(
    "--video_path", type=str, help="Path to save output video file", required=True
)
parser.add_argument("--headless", default=False, action="store_true", help="Run stage headless")
args, unknown = parser.parse_known_args()
# Start the omniverse application
CONFIG = {"sync_loads": True, "headless": False, "renderer": "RayTracedLighting"}
CONFIG["headless"] = args.headless

from isaacsim import SimulationApp
kit = SimulationApp(launch_config=CONFIG)



import omni.usd
from pxr import Gf, Sdf, UsdGeom, UsdShade
import numpy as np
import time
import os
import omni.isaac.core.utils.numpy.rotations as rot_utils
import matplotlib.pyplot as plt

def get_camera_rgba(camera: omni.isaac.sensor.Camera, save_path: str):
    if not os.path.exists(os.path.dirname(save_path)):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
    rgba_data = camera.get_rgba()
    plt.imsave(save_path, rgba_data)

def has_material_binding(prim):
    # 检查 prim 是否有效
    if not prim.IsValid():
        return False
    # 获取 prim 的材质绑定 API
    material_binding_api = UsdShade.MaterialBindingAPI(prim)
    # 尝试获取绑定的材质
    material_binding = material_binding_api.ComputeBoundMaterial()
    # 如果绑定的材质不为 None，则说明有 material binding
    if material_binding:
        return True
    else:
        return False

if not os.path.exists(args.video_path):
    os.makedirs(args.video_path)
stage_path = args.usd_path
omni.usd.get_context().open_stage(stage_path)
stage = omni.usd.get_context().get_stage()
print("Loading stage...")
# kit._wait_for_viewport()
for _ in range(10):
    kit.update()
print("Loading done!")


# 设置相机的初始参数
camera_distance = 100.0  # 相机距椅子中心的距离
initial_angle = 0.0  # 初始旋转角度

# 初始相机位置和旋转角度（四元数表示）
#initial_rotation = Gf.Quatd(0.7071, 0.7071, 0, 0)  # 绕 X 轴旋转 90 度
#camera_position = Gf.Vec3d(0, -500, 100)
#camera = create_camera("/World/Camera", camera_position, initial_rotation)
isaac_camera = omni.isaac.sensor.Camera(prim_path="/World/Camera", 
        #position=np.array([60, 60, 3]),
        frequency=60,
        #orientation=rot_utils.euler_angles_to_quats(np.array([0, 0, 0]), degrees=True),
        resolution=(1920, 1080))
isaac_camera.initialize()



from omni.kit.viewport.utility import get_active_viewport_window, create_viewport_window
viewport_window = get_active_viewport_window()
viewport_window.viewport_api.camera_path = "/World/Camera"


# omni.timeline.get_timeline_interface().play()
# 执行切换material操作：
materials = []
world_prim = stage.GetDefaultPrim()
print(world_prim.GetChildren())
materiali_prims = world_prim.GetPrimAtPath("Looks").GetChildren()
for mtl_prim in materiali_prims:
    mtl = UsdShade.Material(mtl_prim)
    materials.append(mtl)
mtl_len = len(materials)

# 定义一个函数来更新椅子旋转
def update_chair_rotation(chair_prim, angle):
    orient_attr = chair_prim.GetAttribute("xformOp:orient")
    if orient_attr:
        current_rotation = orient_attr.Get()
        axis = Gf.Vec3d(0, 0, 1) # 绕z轴转
        rotation_quatd = Gf.Rotation(axis, angle).GetQuat()
        rotation_quatf = Gf.Quatf(rotation_quatd.GetReal(),
                                   rotation_quatd.GetImaginary()[0],
                                   rotation_quatd.GetImaginary()[1],
                                   rotation_quatd.GetImaginary()[2])
        new_rotation = current_rotation * rotation_quatf
        orient_attr.Set(new_rotation)
        #print(f"Current rotation: {new_rotation}")

##随机
def random_mtl(prim):
    for child in prim.GetChildren():
        #if has_material_binding(child):
        #    #print(f"change material for prim {str(child.GetPath())}")
        #    UsdShade.MaterialBindingAPI(child).Bind(materials[np.random.randint(mtl_len)], UsdShade.Tokens.strongerThanDescendants)
        #else:
        for grandchild in child.GetChildren():
            if has_material_binding(grandchild):
                #print(f"change material for prim {str(grandchild.GetPath())}")
                UsdShade.MaterialBindingAPI(grandchild).Bind(materials[np.random.randint(mtl_len)], UsdShade.Tokens.strongerThanDescendants)
    #print("****camare working, updated material****")



omni.timeline.get_timeline_interface().play()
for _ in range(10):
    kit.update()

total_angle = 0.0
for i in range(1800):
    total_angle = 0.8  # 累计旋转角度，转变值可改变旋转频率
    for prim in world_prim.GetPrimAtPath("objs").GetChildren():
        ## chair物品的下一级或者下下级才会绑定材质属性
        update_chair_rotation(prim, total_angle)
        if (i % 10 == 0):
            random_mtl(prim)
    png_path = args.video_path + "/" +str(i) + ".png"
    print(f"{i}th step")
    get_camera_rgba(isaac_camera, png_path)
    kit.update()
