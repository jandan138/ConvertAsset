# -*- coding: utf-8 -*-
"""
High-level USD to GLB converter logic.
Traverses a USD stage, extracts geometry/material, and drives the GlbWriter.
"""
import os
import numpy as np
from pxr import Usd, UsdGeom, Gf

from .writer import GlbWriter
from .usd_mesh import UsdMeshExtractor
from .usd_material import UsdMaterialExtractor
from .texture_utils import process_texture, pack_metallic_roughness

class UsdToGlbConverter:
    """
    USD 到 GLB 转换器的主类。
    负责协调整个转换流程：初始化写入器、遍历 USD 场景、提取数据并写入 GLB。
    """
    def __init__(self):
        # 初始化 GLB 写入器，用于构建最终的二进制文件结构
        self.writer = GlbWriter()
        # 根变换矩阵，用于处理坐标系转换（通常是从 USD 的 Z-up 转为 GLTF 的 Y-up）
        # 默认为单位矩阵
        self.root_transform = Gf.Matrix4d(1.0)
        
        # 图片缓存，用于防止重复处理相同的纹理文件
        # 键为文件路径或唯一标识符，值为在 GLB 中的 image 索引
        self._image_cache = {}

    def _get_image_index(self, key, loader_func, *args):
        """
        辅助函数：处理图片的加载和缓存。
        
        Args:
            key: 缓存键（通常是文件路径）。
            loader_func: 加载图片的函数（如 process_texture），需返回 (bytes, mime_type)。
            *args: 传递给 loader_func 的参数。
            
        Returns:
            int: GLB 中的 image 索引，如果加载失败则返回 None。
        """
        if not key:
            return None
            
        # 如果该图片已经处理过，直接返回缓存的索引
        if key in self._image_cache:
            return self._image_cache[key]
            
        # 调用加载函数处理图片
        result = loader_func(*args)
        if result:
            img_bytes, mime = result
            # 将图片数据添加到 GLB 写入器中，并获取其索引
            idx = self.writer.add_image(img_bytes, mime_type=mime)
            # 存入缓存
            self._image_cache[key] = idx
            return idx
        return None

    def process_stage(self, src_usd_path, out_glb_path):
        """
        转换的主入口点。
        
        Args:
            src_usd_path: 输入 USD 文件的路径。
            out_glb_path: 输出 GLB 文件的路径。
        """
        # 1. 打开 USD 舞台 (Stage)
        stage = Usd.Stage.Open(src_usd_path)
        if not stage:
            raise RuntimeError(f"Failed to open USD stage: {src_usd_path}")

        # 2. 设置坐标系转换
        # 获取舞台的 Up 轴（通常是 'Y' 或 'Z'）
        up_axis = UsdGeom.GetStageUpAxis(stage)
        
        # GLTF 标准使用 Y-up。如果 USD 是 Z-up，我们需要绕 X 轴旋转 -90 度来对齐。
        if up_axis == 'Z':
            rot = Gf.Rotation(Gf.Vec3d(1, 0, 0), -90)
            self.root_transform = Gf.Matrix4d(rot, Gf.Vec3d(0))
        
        # 3. 遍历并转换网格
        # 使用 UsdPrimRange 遍历场景中的所有 Prim（图元）
        for prim in Usd.PrimRange(stage.GetPseudoRoot()):
            # 跳过非激活的 Prim 或实例代理（Instance Proxy，暂不处理复杂实例化）
            if not prim.IsActive() or prim.IsInstanceProxy():
                continue
            
            # 如果是 Mesh 类型，则调用转换逻辑
            if prim.GetTypeName() == "Mesh":
                self._convert_mesh(UsdGeom.Mesh(prim))
        
        # 4. 写入输出文件
        # 调用写入器的 write 方法生成最终的 .glb 文件
        self.writer.write(out_glb_path)
        
        # 打印统计信息
        print(f"Exported GLB to: {out_glb_path}")
        print(f"  Nodes: {len(self.writer.nodes)}")
        print(f"  Meshes: {len(self.writer.meshes)}")
        print(f"  Materials: {len(self.writer.materials)}")

    def _convert_mesh(self, usd_mesh):
        """
        将单个 UsdGeom.Mesh 转换为 GLB 数据。
        
        Args:
            usd_mesh: UsdGeom.Mesh 对象。
        """
        # 1. 提取几何数据 (点、法线、UV、索引)
        # 这一步会处理 FaceVarying 拓扑（如果需要展平网格）并应用根变换
        mesh_data = UsdMeshExtractor.extract_mesh_data(usd_mesh, self.root_transform)
        if not mesh_data:
            return # 如果提取失败（例如非三角形网格），则跳过

        # 2. 提取材质数据
        mat_idx = None
        mat_data = UsdMaterialExtractor.extract_material_data(usd_mesh)
        
        if mat_data:
            # 获取纹理路径字典
            textures = mat_data["textures"]
            bc_path = textures.get("diffuse")
            rough_path = textures.get("roughness")
            metal_path = textures.get("metallic")
            norm_path = textures.get("normal")

            # 处理 BaseColor 纹理
            bc_tex_idx = None
            if bc_path:
                img_idx = self._get_image_index(bc_path, process_texture, bc_path)
                if img_idx is not None:
                    bc_tex_idx = self.writer.add_texture(img_idx)
            
            # 处理 Metallic/Roughness 纹理
            # GLTF 需要将二者打包到同一张图的 B 和 G 通道
            mr_tex_idx = None
            if rough_path or metal_path:
                # 使用组合键作为缓存键
                key = f"MR_{metal_path}_{rough_path}"
                img_idx = self._get_image_index(key, pack_metallic_roughness, metal_path, rough_path)
                if img_idx is not None:
                    mr_tex_idx = self.writer.add_texture(img_idx)
                    
            # 处理法线贴图
            norm_tex_idx = None
            if norm_path:
                img_idx = self._get_image_index(norm_path, process_texture, norm_path)
                if img_idx is not None:
                    norm_tex_idx = self.writer.add_texture(img_idx)
            
            # 将材质添加到写入器，并获取索引
            mat_idx = self.writer.add_material(
                base_color=mat_data["base_color"], 
                metallic=mat_data["metallic"], 
                roughness=mat_data["roughness"],
                base_color_texture=bc_tex_idx,
                metallic_roughness_texture=mr_tex_idx,
                normal_texture=norm_tex_idx
            )

        # 3. 将网格数据添加到写入器
        mesh_idx = self.writer.add_mesh(
            name=usd_mesh.GetPath().name,
            positions=mesh_data["positions"],
            normals=mesh_data["normals"],
            uvs=mesh_data["uvs"],
            indices=mesh_data["indices"],
            material_index=mat_idx
        )
        
        # 4. 添加节点 (目前采用扁平层级，即所有 Mesh 都是根节点)
        self.writer.add_node(name=usd_mesh.GetPath().name, mesh_index=mesh_idx)
