# 2026-01-06 - GLB Module Refactoring and Enhancements

## Refactoring
- Split `convert_asset/glb/converter.py` into specialized sub-modules for better maintainability:
  - `usd_mesh.py`: Handles mesh geometry extraction and FaceVarying topology processing.
  - `usd_material.py`: Handles material binding traversal and texture path resolution.
  - `texture_utils.py`: Handles image processing and Metallic/Roughness packing.
  - `converter.py`: Now serves as the main orchestrator.

## Enhancements
- **Robust Texture Extraction**: Improved handling of USD connection lists (nested structures) and support for both `UsdShade.ConnectableAPI` and raw `Usd.Prim` sources.
- **FaceVarying UV Support**: Implemented mesh flattening logic to correctly export UVs mapped with `faceVarying` interpolation (common in assets from DCC tools).
- **Documentation**: Updated `docs/glb/architecture.md` to reflect the new modular design.
