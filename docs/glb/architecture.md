# GLB Export Architecture

## Design Philosophy
The goal was to create a lightweight, "headless" GLB exporter that runs in a standard Python environment (with USD libraries) without requiring the heavy NVIDIA Omniverse Kit or SimulationApp.

## Implementation Details

### Core Classes

#### 1. `UsdToGlbConverter` (`convert_asset/glb/converter.py`)
- **Role**: The "Bridge". Traverses the USD stage and extracts data.
- **Key Responsibilities**:
  - **Traversal**: Iterates through `UsdGeom.Mesh` prims.
  - **Triangulation Check**: Verifies that meshes are triangulated (face vertex counts == 3).
  - **Coordinate Conversion**: Converts USD Z-up (default) to glTF Y-up using a root transform matrix.
  - **Material Extraction**: Reads `displayColor` or `UsdPreviewSurface` inputs (currently `diffuseColor`) to determine base color.
  - **Data Handoff**: Passes raw data (points, normals, indices, UVs) to the `GlbWriter`.

#### 2. `GlbWriter` (`convert_asset/glb/writer.py`)
- **Role**: The "Builder". Constructs the valid GLB binary file.
- **Key Responsibilities**:
  - **Binary Buffer Management**: Manages a `bytearray` buffer.
  - **Padding/Alignment**: Ensures 4-byte alignment for all chunks and accessors as per glTF 2.0 spec.
  - **JSON Construction**: Builds the `asset`, `scenes`, `nodes`, `meshes`, `accessors`, `bufferViews`, `materials` dictionaries.
  - **Export**: Writes the final `.glb` file with the standard header (`glTF` magic, version, length) + JSON Chunk + Binary Chunk.

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
- **Textures**: Currently, texture maps (BaseColor, Normal, Roughness, Metallic) are NOT embedded. Only uniform colors are supported.
- **Animation**: No skeletal or blend shape animation support.
- **Instancing**: Point instancers are not currently resolved.
- **Multiple UV Sets**: Only the primary UV set (`st` or `uv`) is exported.

### Coordinate System
- **USD**: Right-handed, typically Z-up.
- **glTF**: Right-handed, Y-up.
- **Solution**: A root node is added to the glTF scene with a rotation matrix to align the axes.
