# -*- coding: utf-8 -*-
import os
from pxr import Usd, UsdShade

class UsdMaterialExtractor:
    @staticmethod
    def extract_material_data(usd_mesh):
        """
        Find bound material and extract parameters.
        Returns dict with: diffuse, roughness, metallic, texture_paths dict.
        Returns None if no material bound.
        """
        # Find bound material
        bound = UsdShade.MaterialBindingAPI(usd_mesh).ComputeBoundMaterial()
        if not bound or not bound[0]:
            return None
            
        mat = bound[0]
        # Find PreviewSurface shader
        shader = None
        for child in Usd.PrimRange(mat.GetPrim()):
            if child.GetTypeName() == "Shader":
                sh = UsdShade.Shader(child)
                if sh.GetIdAttr().Get() == "UsdPreviewSurface":
                    shader = sh
                    break
        
        if not shader:
            return None
            
        # Get diffuseColor
        diffuse = shader.GetInput("diffuseColor").Get()
        # Roughness/Metallic defaults
        rough = shader.GetInput("roughness").Get()
        metal = shader.GetInput("metallic").Get()
        
        # Helper to get texture path
        def get_tex_path(input_name):
            inp = shader.GetInput(input_name)
            if inp and inp.HasConnectedSource():
                  connections = inp.GetConnectedSources()
                  if connections:
                       # Robust unpacking for nested list structure (observed in debug: [[Info], []])
                       val = connections[0]
                       if isinstance(val, list) and len(val) > 0:
                           val = val[0]

                       if hasattr(val, "source"): # UsdShadeConnectionSourceInfo
                             # source can be ConnectableAPI, Usd.Prim, or SdfPath?
                             s = val.source
                             src = None
                             if isinstance(s, Usd.Prim):
                                 src = s
                             elif hasattr(s, "GetPrim"):
                                 src = s.GetPrim()
                             elif hasattr(s, "prim"):
                                 src = s.prim
                             
                             if src:
                                 pass # print(f"[DEBUG] Found connected source: {src.GetPath()} ({src.GetTypeName()})")
                             else:
                                 pass # print(f"[WARN] Could not resolve prim from source: {s} Type: {type(s)}")
                             
                             src_name = val.sourceName
                       elif isinstance(val, (list, tuple)) and len(val) >= 2:
                            # Fallback logic if structure is different
                            pass
                       else:
                            pass

                  # Try GetConnectedSource again if above failed or simplified
                  res = inp.GetConnectedSource()
                  src = None
                  if isinstance(res, tuple):
                      src_connectable = res[0]
                      if hasattr(src_connectable, "GetPrim"):
                          src = src_connectable.GetPrim()
                  
                  # Assume connected to UsdUVTexture
                  is_tex = False
                  if src:
                      if src.GetTypeName() == "UsdUVTexture":
                          is_tex = True
                      elif src.GetTypeName() == "Shader":
                          # Check info:id
                          sh_src = UsdShade.Shader(src)
                          if sh_src.GetIdAttr().Get() == "UsdUVTexture":
                              is_tex = True
                  
                  if is_tex:
                      f_attr = src.GetAttribute("inputs:file")
                      if f_attr:
                          asset_path_obj = f_attr.Get()
                          path = None
                          if hasattr(asset_path_obj, "path"):
                              path = asset_path_obj.path
                          else:
                              path = str(asset_path_obj)
                              
                          # Resolve path relative to layer? 
                          if path and not os.path.isabs(path):
                              layer_path = src.GetStage().GetRootLayer().realPath
                              if layer_path:
                                  path = os.path.join(os.path.dirname(layer_path), path)
                          return path
            return None

        bc_path = get_tex_path("diffuseColor")
        rough_path = get_tex_path("roughness")
        metal_path = get_tex_path("metallic")
        norm_path = get_tex_path("normal")
        
        # Handle types (GfVec3f -> tuple)
        if diffuse is None: diffuse = (1.0, 1.0, 1.0)
        else: diffuse = tuple(diffuse)
        
        # Add Alpha 1.0
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
