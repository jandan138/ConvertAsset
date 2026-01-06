# GLB Export (Pure Python)

This module provides functionality to convert **Asset-level USD** files (typically processed by the `no-mdl` workflow) into **GLB (glTF Binary)** format.

## Key Features
- **Pure Python**: No heavy dependencies like `omni.kit.asset_converter` or `SimulationApp`. Runs directly with `pxr` (USD) and standard libraries.
- **Lightweight**: Uses `struct` for binary packing and `json` for structure, avoiding extra dependencies like `pygltflib`.
- **Pipeline Integration**: Designed to consume the output of the `no-mdl` process (triangulated mesh + UsdPreviewSurface).

## Usage

### CLI Command
The GLB export is integrated into the main CLI.

```bash
python main.py export-glb --input <path_to_usd_file> --output <path_to_glb_file>
```

### Options
- `--input`: Path to the source USD file.
- `--output`: Path to the destination GLB file.
- `--verbose`: Enable verbose logging.

## Requirements
- Input USD **must be triangulated** (faces must be triangles).
- Input USD should preferably use **UsdPreviewSurface** (PBR) materials.
- Python Environment: `pxr` (USD), `numpy`, `Pillow` (PIL).

## Current Status
- ✅ **Geometry**: Vertex points, Normals, UV coordinates (0).
- ✅ **Topology**: Triangle indices.
- ✅ **Material**: Basic BaseColor (Factor).
- 🚧 **Textures**: Texture packing and embedding (Coming Soon).
- 🚧 **Hierarchy**: Node hierarchy is flattened or simplified (Currently single mesh per primitive).

For technical details, see [Architecture](architecture.md).
