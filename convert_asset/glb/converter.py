# -*- coding: utf-8 -*-
"""
High-level USD to GLB converter logic.
Traverses a USD stage, extracts geometry/material, and drives the GlbWriter.
"""
import os
import numpy as np
from PIL import Image
from io import BytesIO
from pxr import Usd, UsdGeom, UsdShade, Gf, Vt
from .writer import GlbWriter


class UsdToGlbConverter:
    def __init__(self):
        self.writer = GlbWriter()
        # Transform matrix to convert USD (usually Z-up or Y-up) to GLTF (Y-up)
        # We will compute this based on stage up-axis.
        self.root_transform = Gf.Matrix4d(1.0)
        
        # Cache for processed images (path -> glb_image_index)
        self._image_cache = {}

    def _process_texture(self, file_path):
        """
        Read image from path, convert to PNG bytes, add to writer.
        Returns image index.
        """
        if not file_path:
            return None
            
        # Resolve absolute path (simplistic resolution)
        # In a real USD pipeline, we need ArResolver. For now, assume file system paths.
        if not os.path.exists(file_path):
            print(f"[WARN] Texture not found: {file_path}")
            return None
            
        if file_path in self._image_cache:
            return self._image_cache[file_path]
            
        try:
            with Image.open(file_path) as img:
                # Convert to RGBA or RGB
                if img.mode != 'RGBA' and img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Export to PNG in memory
                buf = BytesIO()
                img.save(buf, format="PNG")
                img_bytes = buf.getvalue()
                
                idx = self.writer.add_image(img_bytes, mime_type="image/png")
                self._image_cache[file_path] = idx
                return idx
        except Exception as e:
            print(f"[ERROR] Failed to process texture {file_path}: {e}")
            return None

    def _pack_metallic_roughness(self, metal_path, rough_path):
        """
        Combine metallic (B) and roughness (G) into one texture.
        glTF expects: G=Roughness, B=Metallic.
        """
        key = f"MR_{metal_path}_{rough_path}"
        if key in self._image_cache:
            return self._image_cache[key]
            
        try:
            # Load images or create defaults
            metal_img = None
            rough_img = None
            size = (1, 1)
            
            if metal_path and os.path.exists(metal_path):
                metal_img = Image.open(metal_path).convert('L') # Grayscale
                size = metal_img.size
            
            if rough_path and os.path.exists(rough_path):
                rough_img = Image.open(rough_path).convert('L') # Grayscale
                size = rough_img.size
                
            # If mismatch size, resize to larger? or just first one.
            # For simplicity, resize to match if both exist
            if metal_img and rough_img and metal_img.size != rough_img.size:
                size = metal_img.size # Prioritize metallic size
                rough_img = rough_img.resize(size)
                
            # Create packed image (R=0, G=Rough, B=Metal, A=1)
            packed = Image.new('RGB', size, (255, 255, 255))
            r_ch = Image.new('L', size, 255) # Unused R
            
            g_ch = rough_img if rough_img else Image.new('L', size, 255) # Default Roughness 1.0
            b_ch = metal_img if metal_img else Image.new('L', size, 0)   # Default Metallic 0.0
            
            packed = Image.merge('RGB', (r_ch, g_ch, b_ch))
            
            buf = BytesIO()
            packed.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            
            idx = self.writer.add_image(img_bytes, mime_type="image/png")
            self._image_cache[key] = idx
            return idx
            
        except Exception as e:
            print(f"[ERROR] Failed to pack MetallicRoughness: {e}")
            return None

    def process_stage(self, src_usd_path, out_glb_path):
        """
        Main entry point: Open USD, traverse, convert, and save GLB.
        """
        stage = Usd.Stage.Open(src_usd_path)
        if not stage:
            raise RuntimeError(f"Failed to open USD stage: {src_usd_path}")

        # 1. Setup coordinate system conversion
        up_axis = UsdGeom.GetStageUpAxis(stage)
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)
        
        # GLTF is Y-up, meters.
        # We need a root transform to:
        #   - Rotate if Z-up
        #   - Scale to meters (optional, but good practice. For now let's keep unit scale 1:1 to avoid confusion, 
        #     or apply meters_per_unit if we want strict real-world scale. 
        #     Let's just handle Up-Axis rotation for now to match visual orientation).
        
        if up_axis == 'Z':
            # Rotate -90 degrees around X axis to bring Z+ to Y+
            # USD matrix is row-major in python API? Gf.Matrix4d is usually row-major.
            # Let's use Gf.Matrix4d().SetRotate()
            rot = Gf.Rotation(Gf.Vec3d(1, 0, 0), -90)
            self.root_transform = Gf.Matrix4d(rot, Gf.Vec3d(0))
        
        # 2. Traverse and convert meshes
        # We use UsdPrimRange to traverse all primitives
        for prim in Usd.PrimRange(stage.GetPseudoRoot()):
            if not prim.IsActive() or prim.IsInstanceProxy():
                continue
            
            if prim.GetTypeName() == "Mesh":
                self._convert_mesh(UsdGeom.Mesh(prim))
        
        # 3. Write output
        self.writer.write(out_glb_path)
        print(f"Exported GLB to: {out_glb_path}")
        print(f"  Nodes: {len(self.writer.nodes)}")
        print(f"  Meshes: {len(self.writer.meshes)}")
        print(f"  Materials: {len(self.writer.materials)}")

    def _convert_mesh(self, usd_mesh):
        """
        Extract data from UsdGeom.Mesh and add to GlbWriter.
        """
        # 1. Check topology (must be triangles)
        counts = usd_mesh.GetFaceVertexCountsAttr().Get()
        if not counts:
            return
            
        # Optimization: Check if all counts are 3 using numpy if available or simple loop
        # counts is a VtIntArray, acts like list
        # If not all triangles, we skip (assuming mesh-simplify was run) or warn
        # For efficiency in Python, we can just check a few or converting to numpy
        counts_np = np.array(counts)
        if not np.all(counts_np == 3):
            print(f"[WARN] Skipping mesh {usd_mesh.GetPath()}: Not triangulated (run mesh-simplify first).")
            return

        # 2. Extract Points (and apply root transform)
        points = usd_mesh.GetPointsAttr().Get()
        if not points:
            return
        
        # Convert to numpy (N, 3) float32
        points_np = np.array(points, dtype=np.float32)
        
        # Apply root transform (Z-up fix)
        # Gf Matrix is 4x4. We can do dot product.
        # Efficient way: transform points in place.
        # Only if transform is not identity.
        # Gf.Matrix4d equality check
        is_identity = (self.root_transform == Gf.Matrix4d(1.0))
        if not is_identity:
            # Convert Gf Matrix to numpy 4x4
            mat_np = np.array(self.root_transform).reshape(4, 4) # Gf returns flat list? No, usually object.
            # Actually Gf matrix access in python is a bit tricky, let's just use Gf for safety or construct numpy mat manually
            # Z-up to Y-up matrix:
            # [1  0  0  0]
            # [0  0  1  0]
            # [0 -1  0  0]
            # [0  0  0  1]
            # Let's just do manual swizzle if it's just Z-up rotation
            # y' = z, z' = -y
            # But let's stick to matrix mult for correctness
            pts_homo = np.hstack((points_np, np.ones((len(points_np), 1), dtype=np.float32)))
            # Transpose matrix because numpy dot is (N,4) x (4,4)
            # Gf.Matrix4d is row-major storage but acts as column vectors?
            # Standard: v_new = M * v
            # In numpy: v_new = v * M.T
            # Let's extract values
            m_flat = np.array([self.root_transform[i][j] for i in range(4) for j in range(4)]).reshape(4,4)
            # Points are transformed
            t_points = pts_homo @ m_flat
            points_np = t_points[:, :3].astype(np.float32)
            
            # Also transform normals if present
        
        # 3. Extract Normals
        normals_np = None
        normals = usd_mesh.GetNormalsAttr().Get()
        if normals and len(normals) == len(points): # Vertex normals
            normals_np = np.array(normals, dtype=np.float32)
            if not is_identity:
                 # Rotate normals (ignore translation)
                 # m_flat rotation part
                 m_rot = m_flat[:3, :3]
                 normals_np = normals_np @ m_rot
                 # Re-normalize? Usually rotation is orthogonal so length is preserved.

        # 4. Extract UVs (primvars:st)
        uvs_np = None
        st_pv = UsdGeom.PrimvarsAPI(usd_mesh).GetPrimvar("st")
        if st_pv and st_pv.HasValue():
            uv_data = st_pv.Get()
            indices = st_pv.GetIndices()
            
            # If indexed, we need to flatten because GLTF expects 1 UV per vertex (or indexed same as position)
            # USD allows different topology for UVs (FaceVarying).
            # GLTF requires strict correlation: Attribute i corresponds to Vertex i.
            # If USD has FaceVarying UVs (indices on faces, not vertices), we need to split vertices.
            # THIS IS A COMPLEXITY: "Splitting vertices"
            # For Phase 1, we assume Vertex Interpolation or simple mapping.
            # If interpolation is 'vertex', simple 1:1.
            # If 'faceVarying', logic is harder.
            
            interp = st_pv.GetInterpolation()
            if interp == UsdGeom.Tokens.vertex:
                 # 1:1 mapping if not indexed, or resolve indices
                 if indices:
                     uv_expanded = np.array([uv_data[i] for i in indices], dtype=np.float32)
                     uvs_np = uv_expanded
                 else:
                     uvs_np = np.array(uv_data, dtype=np.float32)
            elif interp == UsdGeom.Tokens.faceVarying:
                # For Phase 1, we might skip faceVarying UVs or just warn.
                # Or, if mesh-simplify was run with 'cpp-uv', it preserves faceVarying.
                # To support this in GLB, we must duplicate positions/normals for unique UVs.
                # This is "unindexing".
                # For simplicity in Phase 1: Skip UVs if faceVarying to avoid complex geometry splitting code.
                # User can refine this later.
                print(f"[WARN] Mesh {usd_mesh.GetPath()} has faceVarying UVs. Skipping UVs in Phase 1.")
                uvs_np = None
        
        # 5. Extract Indices
        indices = usd_mesh.GetFaceVertexIndicesAttr().Get()
        indices_np = np.array(indices, dtype=np.uint32) # Standardize to uint32
        
        # 6. Extract Material (BaseColor)
        # Find bound material
        mat_idx = None
        bound = UsdShade.MaterialBindingAPI(usd_mesh).ComputeBoundMaterial()
        if bound and bound[0]:
            mat = bound[0]
            # Find PreviewSurface shader
            # We assume no-mdl structure: mat/PreviewNetwork/PreviewSurface
            # or just search for UsdPreviewSurface in descendants
            shader = None
            for child in Usd.PrimRange(mat.GetPrim()):
                if child.GetTypeName() == "Shader":
                    sh = UsdShade.Shader(child)
                    if sh.GetIdAttr().Get() == "UsdPreviewSurface":
                        shader = sh
                        break
            
            if shader:
                # Get diffuseColor
                diffuse = shader.GetInput("diffuseColor").Get()
                # Roughness/Metallic defaults
                rough = shader.GetInput("roughness").Get()
                metal = shader.GetInput("metallic").Get()
                
                # Texture Paths (resolve asset path)
                def get_tex_path(input_name):
                    inp = shader.GetInput(input_name)
                    if inp and inp.HasConnectedSource():
                          connections = inp.GetConnectedSources()
                          if connections:
                               # GetConnectedSources returns list of Sdf.PathExpression.PathSource?
                               # Or list of (SdfPath, TfToken) tuples?
                               # Let's inspect what it returns.
                               # Actually, let's use GetConnectedSource() (singular) for single connection
                               # But wait, earlier error was "too many values to unpack".
                               # GetConnectedSource() returns (SdfPath, TfToken).
                               # GetConnectedSources() returns list of (SdfPath, TfToken).
                               
                               # The issue might be that `connections[0]` is a UsdShade.ConnectionSourceInfo object in newer USD versions?
                               # Or simply (prim, portName).
                               
                               # Let's try to unpack carefully.
                               val = connections[0]
                               if hasattr(val, "source"): # UsdShadeConnectionSourceInfo
                                    src = val.source.prim
                                    src_name = val.sourceName
                               elif isinstance(val, (list, tuple)) and len(val) >= 2:
                                    # If it returns (SdfPath, TfToken), we need to get Prim from Stage
                                    # Wait, GetConnectedSources returns (SdfPath, TfToken) usually?
                                    # Actually, let's look at the error "not enough values to unpack (expected 2, got 1)"
                                    # This means connections[0] is a single object, not a tuple.
                                    # It is likely UsdShade.ConnectionSourceInfo or just SdfPath if old API?
                                    
                                    # Let's try the safe way:
                                    src_info = val
                                    # If it is an SdfPath, get prim
                                    # If it is ConnectionSourceInfo
                                    pass
                               else:
                                    # Assume it's just SdfPath?
                                    # Let's print type if we could.
                                    pass

                               # Revert to GetConnectedSource for simplicity if we assume single connection
                               # The previous error "too many values to unpack (expected 2)" on GetConnectedSource() 
                               # implies it returned MORE than 2 values? Or maybe LESS?
                               # "ValueError: too many values to unpack (expected 2)" usually means it returned 3 or more.
                               # But GetConnectedSource returns (source, sourceName).
                               
                               # Ah, wait. `inp.GetConnectedSource()` returns `(source, sourceName)` where source is UsdShade.ConnectableAPI (wrapper).
                               # Maybe in this USD version it returns something else?
                               pass
                          
                          # Let's try GetConnectedSource again but inspect return
                          res = inp.GetConnectedSource()
                          if isinstance(res, tuple):
                              src_connectable = res[0]
                              # src_connectable is UsdShade.ConnectableAPI. GetPrim() gives Prim.
                              src = src_connectable.GetPrim()
                              # src_name = res[1]
                          else:
                              # What if it returned None? We checked HasConnectedSource.
                              return None
                          # Assume connected to UsdUVTexture
                          if src.GetTypeName() == "UsdUVTexture":
                             f_attr = src.GetInput("file")
                             if f_attr:
                                 path = f_attr.Get()
                                 # Resolve path relative to layer? 
                                 # Usd.Stage.ResolveUnits?
                                 # For simplicity, if path is relative, assume relative to USD file
                                 if path and not os.path.isabs(path):
                                     # Get layer dir
                                     layer_path = src.GetPrim().GetStage().GetRootLayer().realPath
                                     if layer_path:
                                         path = os.path.join(os.path.dirname(layer_path), path)
                                 return path
                    return None

                bc_path = get_tex_path("diffuseColor")
                rough_path = get_tex_path("roughness")
                metal_path = get_tex_path("metallic")
                norm_path = get_tex_path("normal")

                # Process Textures
                bc_tex_idx = None
                if bc_path:
                    img_idx = self._process_texture(bc_path)
                    if img_idx is not None:
                        bc_tex_idx = self.writer.add_texture(img_idx)
                
                mr_tex_idx = None
                if rough_path or metal_path:
                    # Need to pack
                    img_idx = self._pack_metallic_roughness(metal_path, rough_path)
                    if img_idx is not None:
                        mr_tex_idx = self.writer.add_texture(img_idx)
                        
                norm_tex_idx = None
                if norm_path:
                    img_idx = self._process_texture(norm_path)
                    if img_idx is not None:
                        norm_tex_idx = self.writer.add_texture(img_idx)
                
                # Handle types (GfVec3f -> tuple)
                if diffuse is None: diffuse = (1.0, 1.0, 1.0)
                else: diffuse = tuple(diffuse)
                
                # Add Alpha 1.0
                if len(diffuse) == 3: diffuse = diffuse + (1.0,)
                
                if rough is None: rough = 0.5
                if metal is None: metal = 0.0
                
                mat_idx = self.writer.add_material(
                    base_color=diffuse, 
                    metallic=float(metal), 
                    roughness=float(rough),
                    base_color_texture=bc_tex_idx,
                    metallic_roughness_texture=mr_tex_idx,
                    normal_texture=norm_tex_idx
                )

        # 7. Add to Writer
        mesh_idx = self.writer.add_mesh(
            name=usd_mesh.GetPath().name,
            positions=points_np,
            normals=normals_np,
            uvs=uvs_np,
            indices=indices_np,
            material_index=mat_idx
        )
        
        # 8. Add Node
        # We ignore hierarchy for Phase 1, just add all meshes as root nodes
        # If we wanted hierarchy, we'd need recursive traversal.
        # But for "Object Asset" (usually one root), flat is often okay.
        self.writer.add_node(name=usd_mesh.GetPath().name, mesh_index=mesh_idx)

