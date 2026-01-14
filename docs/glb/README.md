# GLB Export (Pure Python)

This module provides functionality to convert **Asset-level USD** files (typically processed by the `no-mdl` workflow) into **GLB (glTF Binary)** format.

## Documentation Index

-   **[Architecture](architecture.md)**: High-level design, class roles, and limitations.
-   **[Code Walkthrough](code_walkthrough.md)**: **Recommended for Beginners**. A line-by-line explanation of how the conversion works.

> **中文文档 (Chinese Documentation)**:
> - [GLB 导出说明 (README)](README_zh.md)
> - [架构设计 (Architecture)](architecture_zh.md)
> - [代码导读 (Code Walkthrough)](code_walkthrough_zh.md)

## Key Features
- **Pure Python**: No heavy dependencies like `omni.kit.asset_converter` or `SimulationApp`. Runs directly with `pxr` (USD) and standard libraries.
- **Lightweight**: Uses `struct` for binary packing and `json` for structure, avoiding extra dependencies like `pygltflib`.
- **FaceVarying Support**: Correctly handles complex UV mappings by flattening mesh topology.
- **Robust Material Handling**: Auto-packs Metallic/Roughness textures and traces complex USD shader graphs.

## Usage

### CLI Command
The GLB export is integrated into the main CLI.

#### 1. Direct Export (Basic)
If you already have a `*_noMDL.usd` file (processed via `no-mdl` command):

```bash
python main.py export-glb <path_to_usd_file> --out <path_to_glb_file>
```

#### 2. One-Step Pipeline (Recommended)
If you have a raw USD with MDL materials and want to convert it to GLB in one go (without managing intermediate files):

```bash
python main.py usd-to-glb <path_to_input.usd> --out <path_to_output.glb>
```

**Workflow**:
1.  **MDL Conversion**: Automatically runs `no-mdl` logic to generate a temporary `*_noMDL.usd` with PBR textures.
2.  **GLB Export**: Converts the temporary USD to GLB.
3.  **Cleanup**: Deletes the temporary `*_noMDL.usd` file (unless `--keep-intermediate` is used).

### Options
- `input_path`: Path to the source USD file.
- `--out`: Path to the destination GLB file.
- `--keep-intermediate`: (For `usd-to-glb`) Keep the generated `*_noMDL.usd` file for debugging.

## Requirements
- Input USD **must be triangulated** (faces must be triangles).
- Input USD should preferably use **UsdPreviewSurface** (PBR) materials.
- Python Environment: `pxr` (USD), `numpy`, `Pillow` (PIL).

## Quick Start for Developers

If you want to understand how the code works, start with **`convert_asset/glb/converter.py`**. This is the main orchestrator.

For a deep dive into specific logic (like how we handle UVs or Binary writing), refer to the **[Code Walkthrough](code_walkthrough.md)**.

