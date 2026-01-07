# GLB 导出 (Pure Python)

该模块提供将 **USD 资产**（通常经过 `no-mdl` 流程处理）转换为 **GLB (glTF Binary)** 格式的功能。

## 文档索引

-   **[架构设计 (Architecture)](architecture_zh.md)**: 高层设计、类角色说明及局限性。
-   **[代码导读 (Code Walkthrough)](code_walkthrough_zh.md)**: **推荐初学者阅读**。对代码进行逐行级别的原理解析。

> **English Documentation**:
> - [README](README.md)
> - [Architecture](architecture.md)
> - [Code Walkthrough](code_walkthrough.md)

## 核心特性
- **纯 Python 实现**: 无需依赖庞大的 `omni.kit.asset_converter` 或 `SimulationApp`。仅依赖 `pxr` (USD) 和标准库即可运行。
- **轻量级**: 使用 `struct` 进行二进制打包，使用 `json` 构建结构，避免引入 `pygltflib` 等额外依赖。
- **支持 FaceVarying**: 通过展平网格拓扑 (Flattening)，正确处理复杂的 UV 映射。
- **稳健的材质处理**: 自动打包 Metallic/Roughness 纹理通道，并能追踪复杂的 USD 着色网络。

## 使用方法

### CLI 命令
GLB 导出功能已集成到主 CLI 中。

```bash
python main.py export-glb <path_to_usd_file> --out <path_to_glb_file>
```

### 选项
- `input_path`: 源 USD 文件路径。
- `--out`: 目标 GLB 文件路径。

## 环境要求
- 输入 USD **必须是三角化的** (面只能是三角形)。
- 输入 USD 最好使用 **UsdPreviewSurface** (PBR) 材质。
- Python 环境: `pxr` (USD), `numpy`, `Pillow` (PIL)。

## 开发者快速入门

如果你想理解代码是如何工作的，请从 **`convert_asset/glb/converter.py`** 开始阅读，这是整个流程的协调者。

如需深入了解具体逻辑（例如我们如何处理 UV 或二进制写入），请参考 **[代码导读 (Code Walkthrough)](code_walkthrough_zh.md)**。
