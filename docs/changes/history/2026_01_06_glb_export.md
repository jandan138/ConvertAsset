# 2026-01-06: GLB Export Feature (Pure Python)

## Summary
Implemented a lightweight, pure Python GLB exporter to convert Asset-level USD files to GLB format. This feature is designed to work downstream of the `no-mdl` process.

## Motivation
- **Avoid Heavy Dependencies**: The previous approach required `omni.kit.asset_converter` which relies on the full Isaac Sim/Omniverse Kit runtime (`SimulationApp`). This was too heavy for simple geometry conversions.
- **Efficiency**: A direct binary writer allows for faster, headless conversion in lightweight container environments.

## Implementation
- **Module**: `convert_asset/glb/`
  - `converter.py`: Handles USD traversal, geometry extraction (Points, Normals, UVs), and coordinate system conversion (Z-up to Y-up).
  - `writer.py`: Implements a `GlbWriter` class that constructs the glTF JSON header and packs binary data with correct 4-byte alignment.
- **CLI**: Added `export-glb` subcommand to `main.py`.

## Key Technical Decisions
- **Standard Libraries**: Used `struct` for binary packing and `json` for metadata. No `pygltflib` dependency.
- **Dependencies**: Relies only on `pxr` (USD) and `numpy`.
- **Scope**: currently supports Geometry (Mesh) + Basic Color (Factor). Texture embedding is planned for future iterations.

## Usage
```bash
python main.py export-glb --input asset_noMDL.usd --output asset.glb
```
