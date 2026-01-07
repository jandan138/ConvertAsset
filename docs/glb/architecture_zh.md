# GLB 导出架构

## 设计哲学
我们的目标是创建一个轻量级、"无头 (headless)" 的 GLB 导出器，它能够在标准的 Python 环境（仅需 USD 库）中运行，而不需要依赖庞大的 NVIDIA Omniverse Kit 或 SimulationApp。

## 实现细节

### 核心类

#### 1. `UsdToGlbConverter` (`convert_asset/glb/converter.py`)
- **角色**: "协调者 (Orchestrator)"。
- **主要职责**:
  - 初始化 `GlbWriter`。
  - 确定舞台的 Up 轴 (Up-axis) 和根变换矩阵。
  - 遍历 USD 舞台（通过 `UsdPrimRange`）。
  - 将具体的提取任务委托给辅助模块 (`UsdMeshExtractor`, `UsdMaterialExtractor`)。
  - 协调纹理的处理和缓存。

#### 2. `GlbWriter` (`convert_asset/glb/writer.py`)
- **角色**: "构建者 (Builder)"。构建合法的 GLB 二进制文件。
- **主要职责**:
  - **二进制缓冲区管理**: 管理一个 `bytearray` 缓冲区。
  - **填充/对齐**: 确保所有块 (Chunks) 和访问器 (Accessors) 符合 glTF 2.0 规范的 4 字节对齐要求。
  - **JSON 构建**: 构建 `asset`, `scenes`, `nodes`, `meshes`, `accessors`, `bufferViews`, `materials` 等字典结构。
  - **导出**: 写入最终的 `.glb` 文件，包含标准头（`glTF` 魔数、版本、长度）+ JSON 块 + Binary 块。

#### 3. `UsdMeshExtractor` (`convert_asset/glb/usd_mesh.py`)
- **角色**: 几何提取器。
- **主要职责**:
  - 从 `UsdGeom.Mesh` 中提取位置、法线和索引。
  - 处理 **FaceVarying UV** 拓扑：通过分裂顶点（展开索引）来确保在 glTF 中正确显示纹理（glTF 仅支持顶点插值）。
  - 应用坐标系转换（从 Z-up 到 Y-up）。

#### 4. `UsdMaterialExtractor` (`convert_asset/glb/usd_material.py`)
- **角色**: 材质图遍历器。
- **主要职责**:
  - 查找绑定的 `UsdPreviewSurface` 材质。
  - 提取标量参数（BaseColor, Roughness, Metallic）。
  - 稳健地遍历连接路径以查找纹理文件，处理嵌套的连接列表以及直接/间接的 Prim 引用。

#### 5. `TextureUtils` (`convert_asset/glb/texture_utils.py`)
- **角色**: 图像处理器。
- **主要职责**:
  - 使用 Pillow (PIL) 读取图像文件。
  - 将图像转换为内存中的 PNG 字节。
  - **通道打包 (Channel Packing)**: 将 Metallic（蓝色通道）和 Roughness（绿色通道）图像合并为一张纹理，以符合 glTF PBR 标准。

### 数据流
1. **输入**: USD Stage (通过 `pxr.Usd` 打开)。
2. **处理**:
   - `UsdToGlbConverter` 应用 `root_transform` (单位矩阵或绕 X 轴旋转 -90度)。
   - 对每个网格 (Mesh):
     - 获取顶点 (Vec3f) -> 展平为 float 数组 -> 添加到 Writer。
     - 获取法线 (Vec3f) -> 展平 -> 添加到 Writer。
     - 获取 UV (Vec2f) -> 展平 -> 添加到 Writer。
     - 获取索引 (Int) -> 添加到 Writer。
     - 获取材质 -> 在 Writer 中创建材质 -> 分配给网格。
3. **输出**: `.glb` 文件。

### 局限性与路线图
- **动画**: 目前不支持骨骼或 Blend Shape 动画。
- **实例化**: 目前未解析 Point Instancers。
- **多套 UV**: 仅导出主 UV 集 (`st` 或 `uv`)。
- **层级**: 场景层级目前被展平（每个 Primitive 作为单层节点）。

### 纹理处理 (新增)
导出器现在支持带有自动通道打包功能的纹理嵌入。
- **库**: 使用 `Pillow` (PIL) 进行图像读取和处理。
- **Base Color**: 从 `UsdPreviewSurface.diffuseColor` 输入纹理读取。转换为 PNG。
- **Normal Map**: 从 `UsdPreviewSurface.normal` 输入纹理读取。
- **Metallic/Roughness 打包**:
  - glTF 要求一个组合的 "Metallic-Roughness" 纹理，其中：
    - **绿色 (G)** 通道 = 粗糙度 (Roughness)
    - **蓝色 (B)** 通道 = 金属度 (Metallic)
  - 转换器会自动从 USD 中读取独立的 `roughness` 和 `metallic` 纹理，如有必要进行缩放，并将它们打包成单张 PNG。
- **缓存**: 处理后的图像和打包纹理会被缓存，避免在 GLB 中重复存储。

### 坐标系
- **USD**: 右手系，通常为 Z-up。
- **glTF**: 右手系，Y-up。
- **解决方案**: 在 glTF 场景中添加一个根节点，并应用旋转矩阵以对齐坐标轴。
