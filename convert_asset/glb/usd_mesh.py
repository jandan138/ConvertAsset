# -*- coding: utf-8 -*-
"""
USD 网格提取模块。
负责从 UsdGeom.Mesh 中提取几何数据（顶点、法线、UV、索引），并处理 FaceVarying 拓扑。
"""
import numpy as np
from pxr import Usd, UsdGeom, Gf

class UsdMeshExtractor:
    @staticmethod
    def extract_mesh_data(usd_mesh, root_transform=Gf.Matrix4d(1.0)):
        """
        从 UsdGeom.Mesh 提取数据。
        
        Args:
            usd_mesh: UsdGeom.Mesh 对象。
            root_transform: 根变换矩阵（用于坐标系转换，如 Z-up 到 Y-up）。
            
        Returns:
            dict: 包含 'positions', 'normals', 'uvs', 'indices' 的字典。
            None: 如果数据验证失败（如非三角形网格）。
        """
        # 1. 检查拓扑结构 (必须是三角形网格)
        # 获取每个面的顶点数数组
        counts = usd_mesh.GetFaceVertexCountsAttr().Get()
        if not counts:
            return None
            
        counts_np = np.array(counts)
        # 如果存在任何非三角形面（顶点数不为3），则跳过
        # GLB 要求网格必须是三角化的
        if not np.all(counts_np == 3):
            print(f"[WARN] Skipping mesh {usd_mesh.GetPath()}: Not triangulated (run mesh-simplify first).")
            return None

        # 2. 提取顶点 (Points) 并应用根变换
        points = usd_mesh.GetPointsAttr().Get()
        if not points:
            return None
        
        # 转换为 numpy (N, 3) float32 格式
        points_np = np.array(points, dtype=np.float32)
        
        # 应用根变换 (修正 Up 轴)
        is_identity = (root_transform == Gf.Matrix4d(1.0))
        if not is_identity:
            # 构造齐次坐标 (N, 4)
            pts_homo = np.hstack((points_np, np.ones((len(points_np), 1), dtype=np.float32)))
            # 将 Matrix4d 展平为 numpy 数组
            m_flat = np.array([root_transform[i][j] for i in range(4) for j in range(4)]).reshape(4,4)
            # 执行矩阵乘法
            t_points = pts_homo @ m_flat
            # 取回前三维坐标
            points_np = t_points[:, :3].astype(np.float32)
        
        # 3. 提取法线 (Normals)
        normals_np = None
        normals = usd_mesh.GetNormalsAttr().Get()
        # 仅处理顶点法线 (Vertex Normals)，即数量与顶点数一致的情况
        if normals and len(normals) == len(points): 
            normals_np = np.array(normals, dtype=np.float32)
            if not is_identity:
                 # 仅应用旋转部分 (左上角 3x3)
                 m_rot = m_flat[:3, :3]
                 normals_np = normals_np @ m_rot

        # 4. 提取 UV (primvars:st)
        uvs_np = None
        st_pv = UsdGeom.PrimvarsAPI(usd_mesh).GetPrimvar("st")
        
        needs_flattening = False
        uv_data = None
        uv_indices = None
        
        if st_pv and st_pv.HasValue():
            # 获取 UV 数据和索引
            uv_data = np.array(st_pv.Get(), dtype=np.float32)
            uv_indices = st_pv.GetIndices()
            if uv_indices:
                uv_indices = np.array(uv_indices, dtype=np.uint32)
                
            # 检查插值方式
            interp = st_pv.GetInterpolation()
            
            if interp == UsdGeom.Tokens.vertex:
                 # 顶点插值：每个顶点对应一个 UV，这是 glTF 原生支持的
                 # 如果有索引，解析索引；否则直接使用数据
                 if uv_indices is not None:
                     uvs_np = uv_data[uv_indices]
                 else:
                     uvs_np = uv_data
            elif interp == UsdGeom.Tokens.faceVarying:
                # 面变化插值：UV 定义在面角上（Face-Corner），同一个顶点在不同面上可能有不同 UV
                # glTF 不支持这种模式，必须展平网格（分裂顶点）
                needs_flattening = True
        
        # 5. 提取索引 (Indices)
        indices = usd_mesh.GetFaceVertexIndicesAttr().Get()
        indices_np = np.array(indices, dtype=np.uint32) # 标准化为 uint32
        
        # 处理 FaceVarying UV 的展平逻辑 (Mesh Flattening)
        if needs_flattening:
            # 我们必须将拓扑结构“炸开”：
            # 新的顶点数量 = 索引总数 (即所有面的角点总数)
            # 新位置[i] = 旧位置[旧索引[i]]
            
            # 扩展位置和法线数据
            points_np = points_np[indices_np]
            if normals_np is not None:
                normals_np = normals_np[indices_np]
                
            # 扩展 UV 数据
            # FaceVarying 数据通常直接对应面角点
            if uv_indices is not None and len(uv_indices) > 0:
                # 如果有索引，它们映射 FaceCorner -> UV Value
                if len(uv_indices) == len(indices_np):
                    uvs_np = uv_data[uv_indices]
                else:
                    print(f"[WARN] UV indices count {len(uv_indices)} != Face Vertex indices count {len(indices_np)}")
            else:
                # 如果没有索引，数据直接对应 FaceCorner
                if len(uv_data) == len(indices_np):
                    uvs_np = uv_data
                else:
                    print(f"[WARN] UV data count {len(uv_data)} != Face Vertex indices count {len(indices_np)}")

            # 重新生成索引：现在只是简单的 0..N-1 序列
            indices_np = np.arange(len(indices_np), dtype=np.uint32)
            
        return {
            "positions": points_np,
            "normals": normals_np,
            "uvs": uvs_np,
            "indices": indices_np
        }
