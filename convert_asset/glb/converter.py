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
    def __init__(self):
        self.writer = GlbWriter()
        # Transform matrix to convert USD (usually Z-up or Y-up) to GLTF (Y-up)
        self.root_transform = Gf.Matrix4d(1.0)
        
        # Cache for processed images (path or key -> glb_image_index)
        self._image_cache = {}

    def _get_image_index(self, key, loader_func, *args):
        """
        Helper to handle image caching.
        key: Unique cache key (e.g. file path).
        loader_func: Function that returns (bytes, mime_type) or None.
        args: Arguments for loader_func.
        """
        if not key:
            return None
            
        if key in self._image_cache:
            return self._image_cache[key]
            
        result = loader_func(*args)
        if result:
            img_bytes, mime = result
            idx = self.writer.add_image(img_bytes, mime_type=mime)
            self._image_cache[key] = idx
            return idx
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
        
        # GLTF is Y-up. If Z-up, rotate -90 around X.
        if up_axis == 'Z':
            rot = Gf.Rotation(Gf.Vec3d(1, 0, 0), -90)
            self.root_transform = Gf.Matrix4d(rot, Gf.Vec3d(0))
        
        # 2. Traverse and convert meshes
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
        # 1. Extract Geometry
        mesh_data = UsdMeshExtractor.extract_mesh_data(usd_mesh, self.root_transform)
        if not mesh_data:
            return

        # 2. Extract Material
        mat_idx = None
        mat_data = UsdMaterialExtractor.extract_material_data(usd_mesh)
        
        if mat_data:
            # Process Textures
            textures = mat_data["textures"]
            bc_path = textures.get("diffuse")
            rough_path = textures.get("roughness")
            metal_path = textures.get("metallic")
            norm_path = textures.get("normal")

            bc_tex_idx = None
            if bc_path:
                img_idx = self._get_image_index(bc_path, process_texture, bc_path)
                if img_idx is not None:
                    bc_tex_idx = self.writer.add_texture(img_idx)
            
            mr_tex_idx = None
            if rough_path or metal_path:
                key = f"MR_{metal_path}_{rough_path}"
                img_idx = self._get_image_index(key, pack_metallic_roughness, metal_path, rough_path)
                if img_idx is not None:
                    mr_tex_idx = self.writer.add_texture(img_idx)
                    
            norm_tex_idx = None
            if norm_path:
                img_idx = self._get_image_index(norm_path, process_texture, norm_path)
                if img_idx is not None:
                    norm_tex_idx = self.writer.add_texture(img_idx)
            
            mat_idx = self.writer.add_material(
                base_color=mat_data["base_color"], 
                metallic=mat_data["metallic"], 
                roughness=mat_data["roughness"],
                base_color_texture=bc_tex_idx,
                metallic_roughness_texture=mr_tex_idx,
                normal_texture=norm_tex_idx
            )

        # 3. Add to Writer
        mesh_idx = self.writer.add_mesh(
            name=usd_mesh.GetPath().name,
            positions=mesh_data["positions"],
            normals=mesh_data["normals"],
            uvs=mesh_data["uvs"],
            indices=mesh_data["indices"],
            material_index=mat_idx
        )
        
        # 4. Add Node (Flat hierarchy)
        self.writer.add_node(name=usd_mesh.GetPath().name, mesh_index=mesh_idx)
