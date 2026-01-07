# -*- coding: utf-8 -*-
"""
低级 GLB 写入器实现，使用纯 Python (struct, json)。
处理二进制打包、对齐和 JSON 层级结构的构建。
"""
import json
import struct
import numpy as np


class GlbWriter:
    """
    负责构建符合 glTF 2.0 规范的二进制 (.glb) 文件。
    维护 JSON 结构（节点、网格、材质等）和二进制缓冲区（顶点数据、图片数据）。
    """
    def __init__(self):
        # GLTF 结构的容器列表
        self.nodes = []         # 场景节点
        self.meshes = []        # 网格定义
        self.materials = []     # 材质定义
        self.accessors = []     # 数据访问器（描述数据类型、布局）
        self.buffer_views = []  # 缓冲区视图（描述数据在 Buffer 中的位置）
        self.textures = []      # 纹理对象
        self.images = []        # 图片资源
        self.samplers = []      # 采样器（过滤模式、寻址模式）
        self.scenes = [{"nodes": []}] # 默认场景，包含根节点列表
        
        # 二进制缓冲区，用于存储所有原始数据（顶点、索引、图片字节）
        self.buffer_data = bytearray()
        
        # 辅助缓存，用于跟踪唯一材质以避免重复创建
        # 键: tuple(color_rgba, roughness, metallic, texture_indices...) -> 值: material_index
        self._material_cache = {}

    def add_node(self, name, mesh_index=None, translation=None, rotation=None, scale=None, matrix=None):
        """
        向场景层级中添加一个节点。
        
        Args:
            name: 节点名称。
            mesh_index: 关联的网格索引（可选）。
            translation: 平移向量 [x, y, z]。
            rotation: 旋转四元数 [x, y, z, w]。
            scale: 缩放向量 [x, y, z]。
            matrix: 4x4 变换矩阵（如果提供，将覆盖 T/R/S）。
            
        Returns:
            int: 新节点的索引。
        """
        node = {"name": name}
        if mesh_index is not None:
            node["mesh"] = mesh_index
        
        # 设置变换属性
        if matrix is not None:
            node["matrix"] = matrix
        else:
            if translation: node["translation"] = translation
            if rotation: node["rotation"] = rotation  # quaternion [x, y, z, w]
            if scale: node["scale"] = scale
            
        idx = len(self.nodes)
        self.nodes.append(node)
        # 目前将所有节点都添加到默认场景的根节点列表中（扁平层级）
        self.scenes[0]["nodes"].append(idx)
        return idx

    def add_mesh(self, name, positions, normals=None, uvs=None, indices=None, material_index=None):
        """
        添加一个包含单个图元 (Primitive) 的网格。
        
        Args:
            name: 网格名称。
            positions: 顶点位置数组 (N, 3) float32。
            normals: 法线数组 (N, 3) float32 或 None。
            uvs: UV 坐标数组 (N, 2) float32 或 None。
            indices: 索引数组 (M,) uint32/uint16 或 None。
            material_index: 关联的材质索引或 None。
            
        Returns:
            int: 新网格的索引。
        """
        attributes = {}
        
        # 1. 处理位置属性 (POSITION)
        # 计算包围盒 (Min/Max)，这是 glTF 规范要求的
        pos_min = positions.min(axis=0).tolist()
        pos_max = positions.max(axis=0).tolist()
        attributes["POSITION"] = self._add_accessor(
            positions, 
            component_type=5126, # 5126 = FLOAT
            count=len(positions),
            type_str="VEC3",
            min_val=pos_min,
            max_val=pos_max,
            target=34962 # 34962 = ARRAY_BUFFER (顶点属性)
        )
        
        # 2. 处理法线属性 (NORMAL)
        if normals is not None:
            attributes["NORMAL"] = self._add_accessor(
                normals,
                component_type=5126, # FLOAT
                count=len(normals),
                type_str="VEC3",
                target=34962 # ARRAY_BUFFER
            )
            
        # 3. 处理纹理坐标 (TEXCOORD_0)
        if uvs is not None:
            attributes["TEXCOORD_0"] = self._add_accessor(
                uvs,
                component_type=5126, # FLOAT
                count=len(uvs),
                type_str="VEC2",
                target=34962 # ARRAY_BUFFER
            )
            
        # 4. 处理索引 (INDICES)
        indices_idx = None
        if indices is not None:
            # 根据顶点数量决定使用 uint16 (5123) 还是 uint32 (5125)
            # 以节省空间并符合 WebGL 限制
            max_idx = indices.max()
            if max_idx < 65535:
                idx_data = indices.astype(np.uint16)
                comp_type = 5123 # UNSIGNED_SHORT
            else:
                idx_data = indices.astype(np.uint32)
                comp_type = 5125 # UNSIGNED_INT
                
            indices_idx = self._add_accessor(
                idx_data,
                component_type=comp_type,
                count=len(indices),
                type_str="SCALAR",
                target=34963 # 34963 = ELEMENT_ARRAY_BUFFER (索引缓冲)
            )
            
        # 构建图元定义
        primitive = {
            "attributes": attributes,
            "mode": 4 # 4 = TRIANGLES (三角形模式)
        }
        if indices_idx is not None:
            primitive["indices"] = indices_idx
        if material_index is not None:
            primitive["material"] = material_index
            
        # 构建网格定义
        mesh = {
            "name": name,
            "primitives": [primitive]
        }
        idx = len(self.meshes)
        self.meshes.append(mesh)
        return idx

    def add_image(self, image_bytes, mime_type="image/png"):
        """
        将图片数据嵌入到缓冲区，并创建一个 image 条目。
        
        Args:
            image_bytes: 图片文件的原始字节数据。
            mime_type: MIME 类型 (image/png 或 image/jpeg)。
            
        Returns:
            int: 新图片的索引。
        """
        # 为图片数据创建一个 BufferView
        # 确保起始位置 4 字节对齐
        self._align_buffer(4)
        offset = len(self.buffer_data)
        self.buffer_data.extend(image_bytes)
        length = len(image_bytes)
        
        bv_idx = len(self.buffer_views)
        self.buffer_views.append({
            "buffer": 0,
            "byteOffset": offset,
            "byteLength": length
        })
        
        # 创建 Image 条目，引用上述 BufferView
        img_idx = len(self.images)
        self.images.append({
            "bufferView": bv_idx,
            "mimeType": mime_type
        })
        return img_idx

    def add_texture(self, image_index):
        """
        创建一个指向图片的纹理条目。
        使用默认采样器（线性插值，重复平铺）。
        
        Args:
            image_index: add_image 返回的图片索引。
            
        Returns:
            int: 新纹理的索引。
        """
        # 确保默认采样器存在
        if not self.samplers:
            self.samplers.append({
                "magFilter": 9729, # LINEAR
                "minFilter": 9729, # LINEAR (为了安全起见，不用 mipmap，除非生成了 mipmap)
                "wrapS": 10497,    # REPEAT
                "wrapT": 10497     # REPEAT
            })
            
        tex_idx = len(self.textures)
        self.textures.append({
            "sampler": 0, # 使用第一个（默认）采样器
            "source": image_index
        })
        return tex_idx

    def add_material(self, base_color=(1.0, 1.0, 1.0, 1.0), metallic=0.0, roughness=0.5, 
                     base_color_texture=None, metallic_roughness_texture=None, normal_texture=None):
        """
        添加一个 PBR 金属粗糙度材质。
        
        Args:
            base_color: 基础颜色因子 (R, G, B, A)。
            metallic: 金属度因子 (0.0 - 1.0)。
            roughness: 粗糙度因子 (0.0 - 1.0)。
            *_texture: 纹理索引 (add_texture 返回的值)。
            
        Returns:
            int: 材质索引。
        """
        # 生成缓存键以避免重复材质
        key = (tuple(base_color), metallic, roughness, base_color_texture, metallic_roughness_texture, normal_texture)
        if key in self._material_cache:
            return self._material_cache[key]
            
        pbr = {
            "baseColorFactor": list(base_color),
            "metallicFactor": metallic,
            "roughnessFactor": roughness
        }
        
        if base_color_texture is not None:
            pbr["baseColorTexture"] = {"index": base_color_texture}
            
        if metallic_roughness_texture is not None:
            pbr["metallicRoughnessTexture"] = {"index": metallic_roughness_texture}

        mat = {
            "pbrMetallicRoughness": pbr,
            "doubleSided": True # 默认双面渲染
        }
        
        if normal_texture is not None:
            mat["normalTexture"] = {"index": normal_texture}
            
        idx = len(self.materials)
        self.materials.append(mat)
        self._material_cache[key] = idx
        return idx

    def _add_accessor(self, data_np, component_type, count, type_str, min_val=None, max_val=None, target=None):
        """
        为给定的 numpy 数据创建一个 bufferView 和 accessor。
        
        Args:
            data_np: numpy 数组。
            component_type: GL 数据类型常量 (如 5126 FLOAT)。
            count: 元素数量。
            type_str: 元素类型字符串 ("SCALAR", "VEC2", "VEC3" 等)。
            
        Returns:
            int: 新 Accessor 的索引。
        """
        # 确保数据起始位置 4 字节对齐
        self._align_buffer(4)
        
        offset = len(self.buffer_data)
        blob = data_np.tobytes()
        length = len(blob)
        
        # 将原始数据追加到主缓冲区
        self.buffer_data.extend(blob)
        
        # 创建 Buffer View
        bv_idx = len(self.buffer_views)
        bv = {
            "buffer": 0,
            "byteOffset": offset,
            "byteLength": length,
        }
        if target:
            bv["target"] = target
        self.buffer_views.append(bv)
        
        # 创建 Accessor
        acc_idx = len(self.accessors)
        acc = {
            "bufferView": bv_idx,
            "byteOffset": 0,
            "componentType": component_type,
            "count": count,
            "type": type_str,
        }
        if min_val is not None: acc["min"] = min_val
        if max_val is not None: acc["max"] = max_val
            
        self.accessors.append(acc)
        return acc_idx

    def _align_buffer(self, alignment):
        """用零填充缓冲区以满足对齐要求。"""
        current = len(self.buffer_data)
        # 计算需要的填充字节数
        padding = (alignment - (current % alignment)) % alignment
        if padding > 0:
            self.buffer_data.extend(b'\x00' * padding)

    def write(self, path):
        """
        将构建好的数据导出为 .glb 文件。
        
        Args:
            path: 输出文件路径。
        """
        # 1. 完成 JSON 结构
        gltf = {
            "asset": {"version": "2.0", "generator": "ConvertAsset_GlbWriter"},
            "scenes": self.scenes,
            "scene": 0,
            "nodes": self.nodes,
            "meshes": self.meshes,
            "materials": self.materials,
            "accessors": self.accessors,
            "bufferViews": self.buffer_views,
            "buffers": [{"byteLength": len(self.buffer_data)}]
        }
        
        # 添加可选列表（如果非空）
        if self.textures: gltf["textures"] = self.textures
        if self.images: gltf["images"] = self.images
        if self.samplers: gltf["samplers"] = self.samplers
        
        # 将 JSON 序列化为字节串（去除空格以减小体积）
        json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
        
        # 2. 计算填充
        # JSON 块必须 4 字节对齐（使用空格填充）
        json_padding = (4 - (len(json_bytes) % 4)) % 4
        json_bytes += b' ' * json_padding
        
        # BIN 块必须 4 字节对齐（使用 \x00 填充）
        bin_padding = (4 - (len(self.buffer_data) % 4)) % 4
        self.buffer_data.extend(b'\x00' * bin_padding)
        
        # 3. 写入文件头和数据块
        # GLB Header: magic (4) + version (4) + total length (4)
        # JSON Chunk: length (4) + type (4) + data
        # BIN Chunk: length (4) + type (4) + data
        
        total_len = 12 + (8 + len(json_bytes)) + (8 + len(self.buffer_data))
        
        with open(path, 'wb') as f:
            # GLB Header
            f.write(struct.pack('<I', 0x46546C67)) # 'glTF'
            f.write(struct.pack('<I', 2))          # version 2
            f.write(struct.pack('<I', total_len))
            
            # JSON Chunk
            f.write(struct.pack('<I', len(json_bytes)))
            f.write(struct.pack('<I', 0x4E4F534A)) # 'JSON'
            f.write(json_bytes)
            
            # BIN Chunk
            f.write(struct.pack('<I', len(self.buffer_data)))
            f.write(struct.pack('<I', 0x004E4942)) # 'BIN\0'
            f.write(self.buffer_data)
