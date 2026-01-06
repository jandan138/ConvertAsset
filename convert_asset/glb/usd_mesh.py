# -*- coding: utf-8 -*-
import numpy as np
from pxr import Usd, UsdGeom, Gf

class UsdMeshExtractor:
    @staticmethod
    def extract_mesh_data(usd_mesh, root_transform=Gf.Matrix4d(1.0)):
        """
        Extract data from UsdGeom.Mesh.
        Returns dict with: positions, normals, uvs, indices.
        Returns None if validation fails.
        """
        # 1. Check topology (must be triangles)
        counts = usd_mesh.GetFaceVertexCountsAttr().Get()
        if not counts:
            return None
            
        counts_np = np.array(counts)
        if not np.all(counts_np == 3):
            print(f"[WARN] Skipping mesh {usd_mesh.GetPath()}: Not triangulated (run mesh-simplify first).")
            return None

        # 2. Extract Points (and apply root transform)
        points = usd_mesh.GetPointsAttr().Get()
        if not points:
            return None
        
        # Convert to numpy (N, 3) float32
        points_np = np.array(points, dtype=np.float32)
        
        # Apply root transform (Z-up fix)
        is_identity = (root_transform == Gf.Matrix4d(1.0))
        if not is_identity:
            pts_homo = np.hstack((points_np, np.ones((len(points_np), 1), dtype=np.float32)))
            m_flat = np.array([root_transform[i][j] for i in range(4) for j in range(4)]).reshape(4,4)
            t_points = pts_homo @ m_flat
            points_np = t_points[:, :3].astype(np.float32)
        
        # 3. Extract Normals
        normals_np = None
        normals = usd_mesh.GetNormalsAttr().Get()
        if normals and len(normals) == len(points): # Vertex normals
            normals_np = np.array(normals, dtype=np.float32)
            if not is_identity:
                 m_rot = m_flat[:3, :3]
                 normals_np = normals_np @ m_rot

        # 4. Extract UVs (primvars:st)
        uvs_np = None
        st_pv = UsdGeom.PrimvarsAPI(usd_mesh).GetPrimvar("st")
        
        needs_flattening = False
        uv_data = None
        uv_indices = None
        
        if st_pv and st_pv.HasValue():
            uv_data = np.array(st_pv.Get(), dtype=np.float32)
            uv_indices = st_pv.GetIndices()
            if uv_indices:
                uv_indices = np.array(uv_indices, dtype=np.uint32)
                
            interp = st_pv.GetInterpolation()
            
            if interp == UsdGeom.Tokens.vertex:
                 # 1:1 mapping if not indexed, or resolve indices
                 if uv_indices is not None:
                     uvs_np = uv_data[uv_indices]
                 else:
                     uvs_np = uv_data
            elif interp == UsdGeom.Tokens.faceVarying:
                # Need to flatten the mesh
                needs_flattening = True
        
        # 5. Extract Indices
        indices = usd_mesh.GetFaceVertexIndicesAttr().Get()
        indices_np = np.array(indices, dtype=np.uint32) # Standardize to uint32
        
        # Handle Flattening for FaceVarying UVs
        if needs_flattening:
            # Points & Normals expansion
            points_np = points_np[indices_np]
            if normals_np is not None:
                normals_np = normals_np[indices_np]
                
            # UV expansion
            if uv_indices is not None and len(uv_indices) > 0:
                # If indices are present, they map face corner -> uv value
                if len(uv_indices) == len(indices_np):
                    uvs_np = uv_data[uv_indices]
                else:
                    print(f"[WARN] UV indices count {len(uv_indices)} != Face Vertex indices count {len(indices_np)}")
            else:
                # Not indexed, check length
                if len(uv_data) == len(indices_np):
                    uvs_np = uv_data
                else:
                    print(f"[WARN] UV data count {len(uv_data)} != Face Vertex indices count {len(indices_np)}")

            # New indices are just 0..N-1
            indices_np = np.arange(len(indices_np), dtype=np.uint32)
            
        return {
            "positions": points_np,
            "normals": normals_np,
            "uvs": uvs_np,
            "indices": indices_np
        }
