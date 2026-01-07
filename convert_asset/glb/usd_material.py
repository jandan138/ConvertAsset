# -*- coding: utf-8 -*-
"""
USD 材质提取模块。
负责查找绑定的材质，遍历着色器网络 (Shader Graph)，并提取参数和纹理路径。
"""
import os
from pxr import Usd, UsdShade

class UsdMaterialExtractor:
    @staticmethod
    def extract_material_data(usd_mesh):
        """
        查找绑定的材质并提取参数。
        
        Args:
            usd_mesh: UsdGeom.Mesh 对象。
            
        Returns:
            dict: 包含 'base_color', 'roughness', 'metallic', 'textures' 的字典。
            None: 如果未绑定材质或未找到 UsdPreviewSurface。
        """
        # 1. 查找绑定的材质
        # 使用 MaterialBindingAPI 计算当前 Mesh 绑定的材质
        bound = UsdShade.MaterialBindingAPI(usd_mesh).ComputeBoundMaterial()
        if not bound or not bound[0]:
            return None
            
        mat = bound[0]
        # 2. 查找 UsdPreviewSurface 着色器
        # 我们假设材质网络中包含一个 id 为 "UsdPreviewSurface" 的 Shader Prim
        shader = None
        for child in Usd.PrimRange(mat.GetPrim()):
            if child.GetTypeName() == "Shader":
                sh = UsdShade.Shader(child)
                if sh.GetIdAttr().Get() == "UsdPreviewSurface":
                    shader = sh
                    break
        
        if not shader:
            return None
            
        # 3. 获取基本材质参数
        # diffuseColor: 基础颜色 (RGB)
        diffuse = shader.GetInput("diffuseColor").Get()
        # roughness: 粗糙度 (Float)
        rough = shader.GetInput("roughness").Get()
        # metallic: 金属度 (Float)
        metal = shader.GetInput("metallic").Get()
        
        # 辅助函数：获取纹理路径
        def get_tex_path(input_name):
            """
            追踪 Shader Input 的连接源，查找纹理文件路径。
            """
            inp = shader.GetInput(input_name)
            if inp and inp.HasConnectedSource():
                  # 获取连接源列表
                  connections = inp.GetConnectedSources()
                  if connections:
                       # 稳健地解包嵌套列表结构 (在某些 USD 版本或复杂网络中出现)
                       # 例如: [[Info], []] 或 [Info]
                       val = connections[0]
                       if isinstance(val, list) and len(val) > 0:
                           val = val[0]

                       if hasattr(val, "source"): # UsdShadeConnectionSourceInfo
                             # source 可能是 ConnectableAPI, Usd.Prim 或 SdfPath
                             s = val.source
                             src = None
                             if isinstance(s, Usd.Prim):
                                 src = s
                             elif hasattr(s, "GetPrim"):
                                 src = s.GetPrim()
                             elif hasattr(s, "prim"):
                                 src = s.prim
                             
                             if src:
                                 pass # 已找到源 Prim
                             else:
                                 pass # 无法解析源 Prim
                             
                             src_name = val.sourceName
                       elif isinstance(val, (list, tuple)) and len(val) >= 2:
                            # 备用逻辑：如果结构不同（例如旧版 API 返回元组）
                            pass
                       else:
                            pass

                  # 再次尝试 GetConnectedSource (单数形式)，它是更高级的 API
                  # 返回 (sourceConnectable, sourceOutputName)
                  res = inp.GetConnectedSource()
                  src = None
                  if isinstance(res, tuple):
                      src_connectable = res[0]
                      if hasattr(src_connectable, "GetPrim"):
                          src = src_connectable.GetPrim()
                  
                  # 假设连接到了 UsdUVTexture
                  is_tex = False
                  if src:
                      # 检查 Prim 类型是否为 UsdUVTexture
                      if src.GetTypeName() == "UsdUVTexture":
                          is_tex = True
                      elif src.GetTypeName() == "Shader":
                          # 或者它是一个 Shader 但 info:id 是 UsdUVTexture
                          sh_src = UsdShade.Shader(src)
                          if sh_src.GetIdAttr().Get() == "UsdUVTexture":
                              is_tex = True
                  
                  if is_tex:
                      # 获取 inputs:file 属性
                      f_attr = src.GetAttribute("inputs:file")
                      if f_attr:
                          asset_path_obj = f_attr.Get()
                          path = None
                          if hasattr(asset_path_obj, "path"):
                              path = asset_path_obj.path # Sdf.AssetPath
                          else:
                              path = str(asset_path_obj)
                              
                          # 解析相对路径
                          # 如果路径不是绝对路径，假设它相对于当前层 (Layer)
                          if path and not os.path.isabs(path):
                              layer_path = src.GetStage().GetRootLayer().realPath
                              if layer_path:
                                  path = os.path.join(os.path.dirname(layer_path), path)
                          return path
            return None

        # 4. 提取各通道的纹理路径
        bc_path = get_tex_path("diffuseColor")
        rough_path = get_tex_path("roughness")
        metal_path = get_tex_path("metallic")
        norm_path = get_tex_path("normal")
        
        # 处理数据类型 (GfVec3f -> tuple) 并设置默认值
        if diffuse is None: diffuse = (1.0, 1.0, 1.0)
        else: diffuse = tuple(diffuse)
        
        # 补充 Alpha 通道 (1.0)
        if len(diffuse) == 3: diffuse = diffuse + (1.0,)
        
        if rough is None: rough = 0.5
        if metal is None: metal = 0.0
        
        return {
            "base_color": diffuse,
            "roughness": float(rough),
            "metallic": float(metal),
            "textures": {
                "diffuse": bc_path,
                "roughness": rough_path,
                "metallic": metal_path,
                "normal": norm_path
            }
        }
