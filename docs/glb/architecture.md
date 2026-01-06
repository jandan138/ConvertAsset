# GLB Export Architecture

## Design Philosophy
The goal was to create a lightweight, "headless" GLB exporter that runs in a standard Python environment (with USD libraries) without requiring the heavy NVIDIA Omniverse Kit or SimulationApp.

## Implementation Details

### Core Classes

#### 1. `UsdToGlbConverter` (`convert_asset/glb/converter.py`)
- **Role**: The "Orchestrator".
- **Key Responsibilities**:
  - Initializes the `GlbWriter`.
  - Determines stage up-axis and root transform.
  - Iterates through the USD stage (via `UsdPrimRange`).
  - Delegates specific extraction tasks to helper modules (`UsdMeshExtractor`, `UsdMaterialExtractor`).
  - Coordinates texture processing and caching.

#### 2. `GlbWriter` (`convert_asset/glb/writer.py`)
- **Role**: The "Builder". Constructs the valid GLB binary file.
- **Key Responsibilities**:
  - **Binary Buffer Management**: Manages a `bytearray` buffer.
  - **Padding/Alignment**: Ensures 4-byte alignment for all chunks and accessors as per glTF 2.0 spec.
  - **JSON Construction**: Builds the `asset`, `scenes`, `nodes`, `meshes`, `accessors`, `bufferViews`, `materials` dictionaries.
  - **Export**: Writes the final `.glb` file with the standard header (`glTF` magic, version, length) + JSON Chunk + Binary Chunk.

#### 3. `UsdMeshExtractor` (`convert_asset/glb/usd_mesh.py`)
- **Role**: Geometry Extractor.
- **Key Responsibilities**:
  - Extracts positions, normals, and indices from `UsdGeom.Mesh`.
  - Handles **FaceVarying UV** topology by flattening vertices (exploding indices) to ensure correct texture mapping in glTF (which supports only Vertex-Interpolation).
  - Applies coordinate system transforms (Z-up to Y-up).

#### 4. `UsdMaterialExtractor` (`convert_asset/glb/usd_material.py`)
- **Role**: Material Graph Walker.
- **Key Responsibilities**:
  - Finds bound `UsdPreviewSurface` materials.
  - Extracts scalar parameters (BaseColor, Roughness, Metallic).
  - Robustly traverses connection paths to find texture files, handling nested connection lists and direct/indirect Prim references.

#### 5. `TextureUtils` (`convert_asset/glb/texture_utils.py`)
- **Role**: Image Processor.
- **Key Responsibilities**:
  - Reads image files using Pillow (PIL).
  - Converts images to in-memory PNG bytes.
  - **Channel Packing**: Merges Metallic (B) and Roughness (G) images into a single texture for glTF PBR compliance.

### Data Flow
1. **Input**: USD Stage (opened via `pxr.Usd`).
2. **Process**:
   - `UsdToGlbConverter` applies `root_transform` (Identity or Rotate X -90).
   - For each Mesh:
     - Get Points (Vec3f) -> Flatten to float array -> Add to Writer.
     - Get Normals (Vec3f) -> Flatten -> Add to Writer.
     - Get UVs (Vec2f) -> Flatten -> Add to Writer.
     - Get Indices (Int) -> Add to Writer.
     - Get Material -> Create Material in Writer -> Assign to Mesh.
3. **Output**: `.glb` file.

### Limitations & Roadmap
- **Animation**: No skeletal or blend shape animation support.
- **Instancing**: Point instancers are not currently resolved.
- **Multiple UV Sets**: Only the primary UV set (`st` or `uv`) is exported.
- **Hierarchy**: Scene hierarchy is currently flattened.

### Texture Handling (New)
The exporter now supports texture embedding with automatic channel packing.
- **Library**: Uses `Pillow` (PIL) for image reading and processing.
- **Base Color**: Read from `UsdPreviewSurface.diffuseColor` input texture. Converted to PNG.
- **Normal Map**: Read from `UsdPreviewSurface.normal` input texture.
- **Metallic/Roughness Packing**:
  - glTF requires a combined "Metallic-Roughness" texture where:
    - **Green (G)** channel = Roughness
    - **Blue (B)** channel = Metallic
  - The converter automatically reads independent `roughness` and `metallic` textures from USD, resizes them if necessary, and packs them into a single PNG.
- **Caching**: Processed images and packed textures are cached to avoid duplication in the GLB.

### Coordinate System
- **USD**: Right-handed, typically Z-up.
- **glTF**: Right-handed, Y-up.
- **Solution**: A root node is added to the glTF scene with a rotation matrix to align the axes.
