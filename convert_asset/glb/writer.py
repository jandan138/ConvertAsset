# -*- coding: utf-8 -*-
"""
Low-level GLB writer implementation using pure Python (struct, json).
Handles binary packing, alignment, and JSON hierarchy construction.
"""
import json
import struct
import numpy as np


class GlbWriter:
    def __init__(self):
        # GLTF structure containers
        self.nodes = []
        self.meshes = []
        self.materials = []
        self.accessors = []
        self.buffer_views = []
        self.scenes = [{"nodes": []}]
        
        # Binary buffer
        self.buffer_data = bytearray()
        
        # Helper to track unique materials to avoid duplication
        # Key: tuple(color_rgba, roughness, metallic) -> Value: material_index
        self._material_cache = {}

    def add_node(self, name, mesh_index=None, translation=None, rotation=None, scale=None, matrix=None):
        """Add a node to the scene hierarchy."""
        node = {"name": name}
        if mesh_index is not None:
            node["mesh"] = mesh_index
        if matrix is not None:
            node["matrix"] = matrix
        else:
            if translation: node["translation"] = translation
            if rotation: node["rotation"] = rotation  # quaternion [x, y, z, w]
            if scale: node["scale"] = scale
            
        idx = len(self.nodes)
        self.nodes.append(node)
        # Add to default scene root for now (flat hierarchy)
        self.scenes[0]["nodes"].append(idx)
        return idx

    def add_mesh(self, name, positions, normals=None, uvs=None, indices=None, material_index=None):
        """
        Add a mesh with primitives.
        Args:
            positions: np.ndarray (N, 3) float32
            normals: np.ndarray (N, 3) float32 or None
            uvs: np.ndarray (N, 2) float32 or None
            indices: np.ndarray (M,) uint32/uint16 or None
            material_index: int or None
        """
        attributes = {}
        
        # 1. POSITION
        pos_min = positions.min(axis=0).tolist()
        pos_max = positions.max(axis=0).tolist()
        attributes["POSITION"] = self._add_accessor(
            positions, 
            component_type=5126, # FLOAT
            count=len(positions),
            type_str="VEC3",
            min_val=pos_min,
            max_val=pos_max,
            target=34962 # ARRAY_BUFFER
        )
        
        # 2. NORMAL
        if normals is not None:
            attributes["NORMAL"] = self._add_accessor(
                normals,
                component_type=5126, # FLOAT
                count=len(normals),
                type_str="VEC3",
                target=34962 # ARRAY_BUFFER
            )
            
        # 3. TEXCOORD_0
        if uvs is not None:
            attributes["TEXCOORD_0"] = self._add_accessor(
                uvs,
                component_type=5126, # FLOAT
                count=len(uvs),
                type_str="VEC2",
                target=34962 # ARRAY_BUFFER
            )
            
        # 4. INDICES
        indices_idx = None
        if indices is not None:
            # Decide between uint16 (5123) and uint32 (5125) based on vertex count
            max_idx = indices.max()
            if max_idx < 65535:
                idx_data = indices.astype(np.uint16)
                comp_type = 5123
            else:
                idx_data = indices.astype(np.uint32)
                comp_type = 5125
                
            indices_idx = self._add_accessor(
                idx_data,
                component_type=comp_type,
                count=len(indices),
                type_str="SCALAR",
                target=34963 # ELEMENT_ARRAY_BUFFER
            )
            
        primitive = {
            "attributes": attributes,
            "mode": 4 # TRIANGLES
        }
        if indices_idx is not None:
            primitive["indices"] = indices_idx
        if material_index is not None:
            primitive["material"] = material_index
            
        mesh = {
            "name": name,
            "primitives": [primitive]
        }
        idx = len(self.meshes)
        self.meshes.append(mesh)
        return idx

    def add_material(self, base_color=(1.0, 1.0, 1.0, 1.0), metallic=0.0, roughness=0.5):
        """
        Add a simple PBR material (solid color).
        base_color: (r, g, b, a)
        """
        key = (tuple(base_color), metallic, roughness)
        if key in self._material_cache:
            return self._material_cache[key]
            
        mat = {
            "pbrMetallicRoughness": {
                "baseColorFactor": list(base_color),
                "metallicFactor": metallic,
                "roughnessFactor": roughness
            },
            "doubleSided": True # Safer for generic assets
        }
        idx = len(self.materials)
        self.materials.append(mat)
        self._material_cache[key] = idx
        return idx

    def _add_accessor(self, data_np, component_type, count, type_str, min_val=None, max_val=None, target=None):
        """
        Create a bufferView and accessor for the given numpy data.
        """
        # Ensure 4-byte alignment of the start
        self._align_buffer(4)
        
        offset = len(self.buffer_data)
        blob = data_np.tobytes()
        length = len(blob)
        
        self.buffer_data.extend(blob)
        
        # Buffer View
        bv_idx = len(self.buffer_views)
        bv = {
            "buffer": 0,
            "byteOffset": offset,
            "byteLength": length,
        }
        if target:
            bv["target"] = target
        self.buffer_views.append(bv)
        
        # Accessor
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
        """Pad buffer with zeros to satisfy alignment."""
        current = len(self.buffer_data)
        padding = (alignment - (current % alignment)) % alignment
        if padding > 0:
            self.buffer_data.extend(b'\x00' * padding)

    def write(self, path):
        """Export to .glb file."""
        # 1. Finalize JSON
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
        
        json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
        
        # 2. Calculate padding
        # JSON chunk must be 4-byte aligned
        json_padding = (4 - (len(json_bytes) % 4)) % 4
        json_bytes += b' ' * json_padding
        
        # Binary chunk must be 4-byte aligned (already handled in _add_accessor, but check end)
        bin_padding = (4 - (len(self.buffer_data) % 4)) % 4
        self.buffer_data.extend(b'\x00' * bin_padding)
        
        # 3. Header
        # magic (4) + version (4) + total length (4)
        # JSON chunk header: length (4) + type (4)
        # BIN chunk header: length (4) + type (4)
        
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

