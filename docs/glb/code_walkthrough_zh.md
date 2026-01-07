# GLB 转换器代码导读 (Code Walkthrough)

本文档对 `convert_asset/glb/` 目录下的代码进行逐步解析，旨在帮助开发者从代码层面理解转换工作是如何进行的。

---

## 1. 协调者：`converter.py`

[源代码](../../convert_asset/glb/converter.py)

这是程序的入口文件，负责管理高层流程：**打开 USD -> 提取数据 -> 写入 GLB**。

### 核心组件

-   **`UsdToGlbConverter` 类**:
    -   `__init__`: 初始化 `GlbWriter` 和纹理缓存 (`_image_cache`)，防止重复处理同一张图片。
    -   `process_stage(src_usd_path, out_glb_path)`:
        1.  使用 `Usd.Stage.Open` 打开 USD 场景。
        2.  **坐标系转换**: 检查 `UsdGeom.GetStageUpAxis`。如果是 Z-up（USD 标准），则创建一个旋转矩阵（绕 X 轴旋转 -90°）以适配 glTF 的 Y-up 系统。
        3.  **遍历**: 使用 `Usd.PrimRange` 遍历场景中的所有 Prim。筛选出 `UsdGeom.Mesh` 类型并调用 `_convert_mesh`。
        4.  **写入**: 最后调用 `writer.write()` 保存文件。

-   **`_convert_mesh(usd_mesh)`**:
    1.  调用 `UsdMeshExtractor.extract_mesh_data` 获取几何数据（点、法线、UV）。
    2.  调用 `UsdMaterialExtractor.extract_material_data` 获取材质信息（颜色、纹理）。
    3.  **纹理处理**: 如果发现纹理路径，通过 `_get_image_index` 调用 `texture_utils` 的函数进行处理。
        -   *注*: 它会生成缓存键（如文件路径），确保同一张图只在 GLB 中存储一次。
    4.  将所有数据传递给 `self.writer.add_mesh` 和 `self.writer.add_node`。

---

## 2. 几何提取：`usd_mesh.py`

[源代码](../../convert_asset/glb/usd_mesh.py)

该模块处理 USD 几何的复杂性，特别是 "FaceVarying" 拓扑结构。

### `UsdMeshExtractor.extract_mesh_data`

1.  **三角化检查**:
    -   读取 `faceVertexCounts`。如果任何面包含超过 3 个顶点，跳过该网格（GLB 仅支持三角形）。*提示：导出前请运行网格简化/三角化。*
2.  **顶点与变换**:
    -   读取顶点位置 (`GetPointsAttr`)。
    -   乘以 `root_transform`（在 `converter.py` 中计算）以修正 Up 轴方向。
3.  **法线**:
    -   读取法线 (`GetNormalsAttr`)。如有需要同样应用旋转。
4.  **UV 与拓扑（难点）**:
    -   从 `primvars:st` 读取 UV。
    -   检查 **插值方式 (Interpolation)**:
        -   `vertex`: 每个顶点一个 UV。简单（1:1 映射）。
        -   `faceVarying`: UV 定义在面角（face-corner）上（例如锐利的 UV 接缝）。
    -   **展平逻辑 (Flattening)**:
        -   glTF 仅支持 **Vertex** 插值（每个顶点只有一套属性）。
        -   如果我们遇到 `faceVarying` UV（即同一个顶点在不同面上拥有不同的 UV），我们必须**分裂**该顶点。
        -   代码检测到这种情况 (`needs_flattening`) 后会“炸开”网格：
            -   新顶点数 = 索引总数（3 * 面数）。
            -   它为每个面角复制位置/法线数据。
            -   这保证了视觉正确性，但增加了顶点数量。

---

## 3. 材质提取：`usd_material.py`

[源代码](../../convert_asset/glb/usd_material.py)

该模块遍历 USD 着色图（Shading Graph）以确定网格的外观。

### `UsdMaterialExtractor.extract_material_data`

1.  **绑定**: 使用 `UsdShade.MaterialBindingAPI` 找到网格绑定的材质。
2.  **查找 Shader**: 在材质图中寻找 `UsdPreviewSurface` 着色器。
3.  **读取参数**:
    -   读取 `diffuseColor`, `roughness`, `metallic` 的数值。
4.  **纹理路径解析 (`get_tex_path`)**:
    -   这是最复杂的部分。它追踪连接关系 (`GetConnectedSource`)。
    -   它能处理各种 USD 版本/结构（嵌套的连接列表）。
    -   它识别源是否为 `UsdUVTexture`。
    -   如果找到，提取文件路径 (`inputs:file`) 并将其解析为绝对路径。

---

## 4. 纹理处理：`texture_utils.py`

[源代码](../../convert_asset/glb/texture_utils.py)

使用 `Pillow` (PIL) 库处理图像。

-   **`process_texture(file_path)`**:
    -   打开图像，转换为 RGB/RGBA，并作为 PNG 保存到内存中的 `BytesIO` 缓冲区。
    -   返回原始字节。
-   **`pack_metallic_roughness(metal_path, rough_path)`**:
    -   **原因**: glTF 使用标准化的 PBR 纹理，其中：
        -   **蓝色 (B)** 通道 = 金属度 (Metallic)
        -   **绿色 (G)** 通道 = 粗糙度 (Roughness)
    -   该函数加载两张图像（如果存在），调整大小以匹配，并将它们的通道合并到一张新的 PNG 中。

---

## 5. 写入器：`writer.py`

[源代码](../../convert_asset/glb/writer.py)

该类构建实际的二进制 GLB 文件结构。它不了解 USD，只了解 glTF 规范。

### GLB 结构回顾
一个 GLB 文件包含 3 部分：
1.  **Header**: 12 字节 (Magic, Version, Length)。
2.  **JSON Chunk**: 描述场景（节点、网格、材质）。
3.  **Binary Chunk (BIN)**: 原始数据（顶点缓冲区、图片字节）。

### 关键方法

-   **`add_mesh`**:
    -   接收 numpy 数组（位置、法线等）。
    -   调用 `_add_accessor` 将原始数据写入 BIN 块。
    -   在 JSON 的 `"meshes"` 中创建条目。
-   **`_add_accessor`**:
    -   **对齐**: glTF 要求数据按 4 字节对齐。如有需要，该方法会添加填充字节 (`\x00`)。
    -   将数据写入 `self.buffer_data`。
    -   创建 `"bufferView"`（缓冲区切片）和 `"accessor"`（数据类型、极值描述）。
-   **`add_image` / `add_texture`**:
    -   将 PNG 字节嵌入 BIN 块。
    -   创建 JSON 中的 `"images"` 和 `"textures"` 条目。
-   **`write(path)`**:
    -   组装最终文件。
    -   计算总长度。
    -   按顺序写入 Header -> JSON -> BIN。

---

## 数据流总结

1.  **`converter.py`** 向 **`usd_mesh.py`** 请求顶点/索引数据。
2.  **`converter.py`** 向 **`usd_material.py`** 请求纹理路径。
3.  **`converter.py`** 请求 **`texture_utils.py`** 加载/打包这些纹理为字节流。
4.  **`converter.py`** 将所有原始数据（数组、字节）交给 **`writer.py`**。
5.  **`writer.py`** 将其格式化为 GLB 规范并保存文件。
