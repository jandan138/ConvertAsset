# GLB 导出架构

## 设计哲学
我们的目标是创建一个轻量级、"无头 (headless)" 的 GLB 导出器，它能够在标准的 Python 环境（仅需 USD 库）中运行，而不需要依赖庞大的 NVIDIA Omniverse Kit 或 SimulationApp。

## 旧流程 vs 新流程（直观示意）

这次修复的核心变化是：导出器不再把每个 mesh 当成“已经摆到最终位置的世界空间物体”。

```text
旧流程（flat export）

USD Stage
  |
  +-- 扫描所有 Prim
        |
        +-- 如果 Prim 是 Mesh：
              - 读取 mesh-local points
              - 写一个 glTF mesh
              - 写一个顶层 glTF node
  |
  +-- 结果：所有 mesh 都被平铺到 scene root
            父级 Xform 层级语义丢失


新流程（保 hierarchy 的导出）

USD Stage
  |
  +-- 先构建 scene graph
  |     - 收集 Xform + Mesh 节点
  |     - 保留父子关系
  |     - 计算每个节点的 local matrix
  |     - 若舞台是 Z-up，则插入 synthetic root
  |
  +-- 再只转换 mesh-local 几何
  |
  +-- 最后把 mesh 挂回对应 glTF node
  |
  +-- 结果：scene graph 被保留
            mesh 仍然保持 local
            node matrix 负责摆放
```

通俗地说：旧流程导出的是“零件本身”，新流程导出的是“零件 + 装配关系”。

## 实现细节

### 核心类

#### 1. `UsdToGlbConverter` (`convert_asset/glb/converter.py`)
- **角色**: "协调者 (Orchestrator)"。
- **主要职责**:
  - 初始化 `GlbWriter`。
  - 确定舞台的 Up 轴 (Up-axis)，并在需要时插入 synthetic root 矩阵。
  - 调用 `UsdSceneGraphBuilder` 提取层级、局部矩阵与 scene roots。
  - 将具体的提取任务委托给辅助模块 (`UsdMeshExtractor`, `UsdMaterialExtractor`)。
  - 协调纹理的处理和缓存。

#### 2. `UsdSceneGraphBuilder` (`convert_asset/glb/usd_scene.py`)
- **角色**: 场景层级提取器。
- **主要职责**:
  - 将 USD prim tree 映射成 glTF node tree。
  - 计算每个导出节点的 local matrix。
  - 保留父子关系与 scene roots。
  - 在舞台为 Z-up 时插入 synthetic root。

#### 3. `GlbWriter` (`convert_asset/glb/writer.py`)
- **角色**: "构建者 (Builder)"。构建合法的 GLB 二进制文件。
- **主要职责**:
  - **二进制缓冲区管理**: 管理一个 `bytearray` 缓冲区。
  - **填充/对齐**: 确保所有块 (Chunks) 和访问器 (Accessors) 符合 glTF 2.0 规范的 4 字节对齐要求。
  - **JSON 构建**: 构建 `asset`, `scenes`, `nodes`, `meshes`, `accessors`, `bufferViews`, `materials` 等字典结构。
  - **场景树组装**: 支持显式 scene root 和 parent-child 挂接，不再强制扁平化。
  - **导出**: 写入最终的 `.glb` 文件，包含标准头（`glTF` 魔数、版本、长度）+ JSON 块 + Binary 块。

#### 4. `UsdMeshExtractor` (`convert_asset/glb/usd_mesh.py`)
- **角色**: 几何提取器。
- **主要职责**:
  - 从 `UsdGeom.Mesh` 中提取位置、法线和索引。
  - 处理 **FaceVarying UV** 拓扑：通过分裂顶点（展开索引）来确保在 glTF 中正确显示纹理（glTF 仅支持顶点插值）。
  - 保持 mesh-local 几何数据；场景空间关系由 node matrix 表达。

#### 5. `UsdMaterialExtractor` (`convert_asset/glb/usd_material.py`)
- **角色**: 材质图遍历器。
- **主要职责**:
  - 查找绑定的 `UsdPreviewSurface` 材质。
  - 提取标量参数（BaseColor, Roughness, Metallic）。
  - 稳健地遍历连接路径以查找纹理文件，处理嵌套的连接列表以及直接/间接的 Prim 引用。

#### 6. `TextureUtils` (`convert_asset/glb/texture_utils.py`)
- **角色**: 图像处理器。
- **主要职责**:
  - 使用 Pillow (PIL) 读取图像文件。
  - 将图像转换为内存中的 PNG 字节。
  - **通道打包 (Channel Packing)**: 将 Metallic（蓝色通道）和 Roughness（绿色通道）图像合并为一张纹理，以符合 glTF PBR 标准。

### 数据流
1. **输入**: USD Stage (通过 `pxr.Usd` 打开)。
2. **处理**:
   - `UsdSceneGraphBuilder` 提取导出节点、local matrix、父子关系与 scene roots。
   - `UsdToGlbConverter` 仅转换 mesh-local 几何与材质。
   - `GlbWriter` 将层级关系和几何 payload 组装为 glTF scene。
   - 对每个网格 (Mesh):
     - 获取顶点 (Vec3f) -> 展平为 float 数组 -> 添加到 Writer。
     - 获取法线 (Vec3f) -> 展平 -> 添加到 Writer。
     - 获取 UV (Vec2f) -> 展平 -> 添加到 Writer。
     - 获取索引 (Int) -> 添加到 Writer。
     - 获取材质 -> 在 Writer 中创建材质 -> 分配给网格节点。
3. **输出**: `.glb` 文件。

### 局限性与路线图
- **动画**: 目前不支持骨骼或 Blend Shape 动画。
- **实例化**: 目前未解析 Point Instancers。
- **UV 集**: 仅读取 `primvars:st`，`uv`、`st1` 等其它 UV 集不会导出。
- **Physics 回环**: articulation / joint schema 不会在 GLB 中保留；当前只保证静态 pose 的几何与层级保真。
- **法线**: 目前只导出与 points 数量一致的逐点法线；face-varying / indexed normals 仍未支持。

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
- **解决方案**: 当舞台是 Z-up 时，导出器会插入一个 synthetic root node，用其 matrix 将整棵场景树旋转到 glTF 的 Y-up 坐标系；mesh-local 顶点不会被额外 bake。
