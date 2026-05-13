# GLB Converter Code Walkthrough

This document provides a detailed, step-by-step explanation of the codebase in `convert_asset/glb/`. It is designed to help new developers understand **how** the conversion works at a code level.

---

## 1. The Orchestrator: `converter.py`

[Source Code](../../convert_asset/glb/converter.py)

This file is the entry point. It manages the high-level flow: **Open USD -> Extract Data -> Write GLB**.

### Key Components

-   **`UsdToGlbConverter` Class**:
    -   `__init__`: Initializes the `GlbWriter` and a texture cache (`_image_cache`) to avoid processing the same image twice.
    -   `process_stage(src_usd_path, out_glb_path)`:
        1.  Opens the USD stage using `Usd.Stage.Open`.
        2.  **Coordinate Conversion**: Checks `UsdGeom.GetStageUpAxis`. If it's Z-up, it prepares a synthetic root matrix (Rotate X -90°) instead of baking that rotation into every mesh.
        3.  **Scene Graph Extraction**: Calls `UsdSceneGraphBuilder.build(...)` to get exported nodes, parent-child relationships, and local matrices.
        4.  **Mesh Conversion**: Converts only mesh-local geometry and materials, then attaches the resulting mesh index to the correct node.
        5.  **Write**: Finally calls `writer.write()` to save the file.

-   **`_convert_mesh(usd_mesh)`**:
    1.  Calls `UsdMeshExtractor.extract_mesh_data` to get geometry (points, normals, UVs).
    2.  Calls `UsdMaterialExtractor.extract_material_data` to get material info (colors, textures).
    3.  **Texture Handling**: If textures are found, it calls `texture_utils` functions via `_get_image_index`.
        -   *Note*: It creates a cache key (e.g., file path) to ensure we don't store the same image twice in the GLB.
    4.  Feeds everything into `self.writer.add_mesh`; node creation is handled separately by the scene graph path.

---

## 2. Scene Graph Extraction: `usd_scene.py`

[Source Code](../../convert_asset/glb/usd_scene.py)

This module is responsible for preserving hierarchy.

### `UsdSceneGraphBuilder.build`

1.  **Mesh Selection**:
    -   Reuses the current exporter mesh-selection semantics: active prims only, and skip `instance proxy`.
2.  **Ancestor Collection**:
    -   For each exported mesh, it walks up the parent chain and keeps all xformable ancestors that are needed to preserve the scene graph.
3.  **Local Matrix Extraction**:
    -   Uses each prim's local USD transform as the glTF node matrix.
4.  **Synthetic Root**:
    -   If the source stage is Z-up, it inserts a synthetic root node that carries the up-axis conversion matrix.

---

## 3. Geometry Extraction: `usd_mesh.py`

[Source Code](../../convert_asset/glb/usd_mesh.py)

This module handles the complexity of USD geometry, particularly the "FaceVarying" topology.

### `UsdMeshExtractor.extract_mesh_data`

1.  **Triangulation Check**:
    -   It reads `faceVertexCounts`. If any face has more than 3 vertices, it skips the mesh (GLB requires triangles). *Tip: Run mesh simplification/triangulation before export.*
2.  **Points**:
    -   Reads points (`GetPointsAttr`).
    -   Keeps them in mesh-local space. Scene-space placement is now expressed via glTF node matrices.
3.  **Normals**:
    -   Reads normals (`GetNormalsAttr`) only when the normals count matches the points count.
4.  **UVs & Topology (The Tricky Part)**:
    -   Reads UVs from `primvars:st` and ignores other sets such as `uv` or `st1`.
    -   Checks **Interpolation**:
        -   `vertex`: One UV per vertex. Easy (1:1 mapping).
        -   `faceVarying`: UVs are defined per face-corner (e.g., a sharp UV seam).
    -   **Flattening Logic**:
        -   glTF only supports **Vertex** interpolation (one set of attributes per vertex).
        -   If we have `faceVarying` UVs (where one vertex has multiple UVs depending on which face uses it), we must **split** that vertex.
        -   The code detects this (`needs_flattening`) and "explodes" the mesh:
            -   New Vertex Count = Total number of indices (3 * num_faces).
            -   It duplicates position/normal data for every face corner.
            -   This ensures visual correctness at the cost of higher vertex count.

---

## 4. Material Extraction: `usd_material.py`

[Source Code](../../convert_asset/glb/usd_material.py)

This module traverses the USD shading graph to find what the mesh looks like.

### `UsdMaterialExtractor.extract_material_data`

1.  **Binding**: Finds the material bound to the mesh using `UsdShade.MaterialBindingAPI`.
2.  **Shader Search**: Looks for a `UsdPreviewSurface` shader inside the material graph.
3.  **Parameter Reading**:
    -   Reads `diffuseColor`, `roughness`, `metallic` values.
4.  **Texture Path Resolution (`get_tex_path`)**:
    -   This is the most complex part. It traces connections (`GetConnectedSource`).
    -   It handles various USD versions/structures (nested lists of connections).
    -   It identifies if the source is a `UsdUVTexture` shader.
    -   If found, it extracts the file path (`inputs:file`) and, if the path is relative, rebases it against `src.GetStage().GetRootLayer().realPath`; it does not rely on `SdfComputeAssetPathRelativeToLayer` or `resolvedPath` for this step.

---

## 5. Texture Processing: `texture_utils.py`

[Source Code](../../convert_asset/glb/texture_utils.py)

Handles image manipulation using the `Pillow` (PIL) library.

-   **`process_texture(file_path)`**:
    -   Opens an image, converts it to RGB/RGBA, and saves it to an in-memory `BytesIO` buffer as PNG.
    -   Returns the raw bytes.
-   **`pack_metallic_roughness(metal_path, rough_path)`**:
    -   **Why?** glTF uses a standardized PBR texture where:
        -   **Blue (B)** channel = Metallic
        -   **Green (G)** channel = Roughness
    -   This function loads both images (if present), resizes them to match, and merges their channels into a new PNG.

---

## 6. The Writer: `writer.py`

[Source Code](../../convert_asset/glb/writer.py)

This class builds the actual binary GLB file structure. It doesn't know about USD; it only knows about glTF.

### GLB Structure Refresher
A GLB file has 3 parts:
1.  **Header**: 12 bytes (Magic, Version, Length).
2.  **JSON Chunk**: Describes the scene (nodes, meshes, materials).
3.  **Binary Chunk (BIN)**: The raw data (vertex buffers, image bytes).

### Key Methods

-   **`add_mesh`**:
    -   Takes numpy arrays (positions, normals, etc.).
    -   Calls `_add_accessor` to write raw data to the BIN chunk.
    -   Creates a JSON entry in `"meshes"`.
-   **`add_node` / `add_scene_root` / `attach_child`**:
    -   `add_node` creates the node payload.
    -   `add_scene_root` explicitly marks scene roots.
    -   `attach_child` builds the parent-child tree without forcing every node into the scene root list.
-   **`_add_accessor`**:
    -   **Alignment**: glTF requires data to be aligned to 4 bytes. The method adds padding bytes (`\x00`) if needed.
    -   Writes data to `self.buffer_data`.
    -   Creates a `"bufferView"` (slice of the buffer) and an `"accessor"` (description of the data type, min/max values).
-   **`add_image` / `add_texture`**:
    -   Embeds PNG bytes into the BIN chunk.
    -   Creates `"images"` and `"textures"` entries in JSON.
-   **`write(path)`**:
    -   Assembles the final file.
    -   Calculates total length.
    -   Writes Header -> JSON -> BIN.

---

## Summary of Data Flow

1.  **`converter.py`** asks **`usd_scene.py`** for the exported node tree.
2.  **`converter.py`** asks **`usd_mesh.py`** for mesh-local geometry.
3.  **`converter.py`** asks **`usd_material.py`** for texture paths.
4.  **`converter.py`** asks **`texture_utils.py`** to load/pack those textures into bytes.
5.  **`converter.py`** hands scene-graph info and raw payloads to **`writer.py`**.
6.  **`writer.py`** formats it into GLB spec and saves the file.
