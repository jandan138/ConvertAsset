# 2026-03-17 USD -> GLB Implementation Survey

## 背景

本记录用于沉淀一次针对仓库内 `USD -> GLB` 实现的只读调研结果，覆盖 CLI 入口、`convert_asset/glb/` 模块职责、实际数据流、实现约束，以及当前文档与代码的不一致点。

本次工作**未修改源码行为**；仅做代码与文档核对，并补充一份可复用的调研记录。

## 调研范围

- 入口：
  - `main.py`
  - `convert_asset/cli.py`
- GLB 模块：
  - `convert_asset/glb/converter.py`
  - `convert_asset/glb/usd_mesh.py`
  - `convert_asset/glb/usd_material.py`
  - `convert_asset/glb/texture_utils.py`
  - `convert_asset/glb/writer.py`
  - `convert_asset/glb/__init__.py`
- 相关文档：
  - `docs/glb/README.md`
  - `docs/glb/architecture.md`
  - `docs/glb/code_walkthrough.md`
  - `docs/changes/history/2026_01_06_glb_export.md`
  - `docs/no_mdl/feature_specs/texture_path_preservation.md`

## 入口链路

### 1. 总入口

- `main.py:8-12`
  - 仅负责把 `sys.argv[1:]` 转发给 `convert_asset.cli.main(...)`

### 2. `export-glb`

- `convert_asset/cli.py:82-85`
  - 注册 `export-glb` 子命令
  - 参数是位置参数 `src` 与必选 `--out`
- `convert_asset/cli.py:390-405`
  - 校验输入文件是否存在
  - 延迟导入 `from .glb.converter import UsdToGlbConverter`
  - 实例化 `UsdToGlbConverter` 后调用 `process_stage(src, out)`
  - 任何异常都会打印 traceback，并返回退出码 `3`

### 3. `usd-to-glb`

- `convert_asset/cli.py:87-91`
  - 注册 `usd-to-glb` 子命令
  - 参数是位置参数 `src`、必选 `--out`、可选 `--keep-intermediate`
- `convert_asset/cli.py:407-461`
  - 这是三段式流水线：
    1. `no-mdl`：设置 `no_mdl.processor.RUNTIME_ONLY_NEW_USD = True`，然后通过 `Processor().process(src)` 生成中间 `*_noMDL.usd`
    2. `export-glb`：对中间 USD 调用 `UsdToGlbConverter.process_stage(...)`
    3. cleanup：若未传 `--keep-intermediate`，删除中间 USD，并尝试删除同名 `.validate.txt`
  - 中间文件生成失败时返回退出码 `4`
  - 其他异常打印 traceback，并返回退出码 `3`

## `convert_asset/glb/` 模块职责

### `convert_asset/glb/converter.py`

- `converter.py:15-29`
  - `UsdToGlbConverter` 持有一个 `GlbWriter`
  - 维护 `root_transform`（只用于坐标系 Up-axis 修正）
  - 维护 `_image_cache`，只缓存 image，不缓存 texture 或 mesh
- `converter.py:61-102`
  - `process_stage(...)` 打开 USD stage
  - 若 stage 是 Z-up，则构造绕 X 轴 `-90` 度的矩阵赋给 `root_transform`
  - 遍历 `Usd.PrimRange(stage.GetPseudoRoot())`
  - 仅跳过 `inactive prim` 与 `instance proxy`
  - 对每个 `Mesh` prim 调 `_convert_mesh(...)`
  - 最后调用 `writer.write(out_glb_path)`
- `converter.py:104-174`
  - `_convert_mesh(...)` 负责：
    - 调 `UsdMeshExtractor.extract_mesh_data(...)`
    - 调 `UsdMaterialExtractor.extract_material_data(...)`
    - 用 `texture_utils` 读纹理 / 打包 metallic-roughness
    - 用 `writer.add_material(...)`、`writer.add_mesh(...)`、`writer.add_node(...)` 填充 glTF 结构

### `convert_asset/glb/usd_mesh.py`

- `usd_mesh.py:9-11`
  - 提供静态方法 `UsdMeshExtractor.extract_mesh_data(...)`
- `usd_mesh.py:23-34`
  - 强制要求 mesh 全部三角化；任一面不是三角形就整 mesh 跳过
- `usd_mesh.py:36-65`
  - 读取 `points`
  - 仅应用 `root_transform`，不计算 prim 自身或父层级的 xform
  - normals 只在“法线数量 == 点数量”时才导出；否则忽略
- `usd_mesh.py:67-128`
  - 只读取 `primvars:st`
  - `vertex` 插值时直接映射为 glTF 顶点 UV
  - `faceVarying` 插值时做顶点炸开：
    - 按 face-corner 展开 position / normal
    - UV 也按 face-corner 对齐
    - 索引重建为 `0..N-1`

### `convert_asset/glb/usd_material.py`

- `usd_material.py:22-40`
  - 通过 `UsdShade.MaterialBindingAPI(...).ComputeBoundMaterial()` 找绑定材质
  - 在材质子树内找第一个 `info:id == "UsdPreviewSurface"` 的 shader
- `usd_material.py:42-48`
  - 提取 `diffuseColor` / `roughness` / `metallic`
- `usd_material.py:50-128`
  - `get_tex_path(...)` 沿输入连接找 `UsdUVTexture`
  - 读取 `inputs:file`
  - 若 `inputs:file.path` 是相对路径，则按 `src.GetStage().GetRootLayer().realPath` 所在目录拼成绝对路径
- `usd_material.py:136-156`
  - 默认值：
    - base color: `(1, 1, 1, 1)`
    - roughness: `0.5`
    - metallic: `0.0`
  - 返回四个纹理槽：
    - `diffuse`
    - `roughness`
    - `metallic`
    - `normal`

### `convert_asset/glb/texture_utils.py`

- `texture_utils.py:10-42`
  - `process_texture(...)` 用 Pillow 读取原图
  - 统一转成 `RGB` / `RGBA`
  - 重新编码成内存 PNG 后返回
- `texture_utils.py:44-103`
  - `pack_metallic_roughness(...)`
  - 生成 glTF 所需的 packed texture：
    - `G = roughness`
    - `B = metallic`
    - `R = 255`
  - 两张图尺寸不一致时，以 metallic 图尺寸为准重采样 roughness 图

### `convert_asset/glb/writer.py`

- `writer.py:16-33`
  - 维护 glTF JSON 各数组，以及统一二进制缓冲 `buffer_data`
- `writer.py:35-66`
  - `add_node(...)` 支持 matrix / TRS，但 converter 当前没有传这些变换
  - 所有 node 都被直接挂到默认 scene 的根节点列表中
- `writer.py:68-157`
  - `add_mesh(...)` 为每个 USD mesh 创建一个只含单个 primitive 的 glTF mesh
  - `POSITION` / `NORMAL` / `TEXCOORD_0` / `INDICES` 都通过 `_add_accessor(...)` 写入
- `writer.py:159-217`
  - `add_image(...)` 把图片直接嵌入 BIN chunk
  - `add_texture(...)` 使用单个默认 sampler
- `writer.py:219-261`
  - `add_material(...)` 只构建 PBR metallic-roughness 材质
  - 默认 `doubleSided = True`
  - 通过 `_material_cache` 做材质去重
- `writer.py:263-378`
  - `_add_accessor(...)` 负责 bufferView / accessor 创建
  - `write(...)` 负责 JSON chunk、BIN chunk 的 4-byte 对齐，以及最终 GLB header 写出

### `convert_asset/glb/__init__.py`

- 当前为空文件，仅作为 package 标记

## 实际数据流

## 1. CLI 到 converter

`main.py` -> `convert_asset.cli.main(...)` -> `export-glb` / `usd-to-glb` -> `UsdToGlbConverter.process_stage(...)`

## 2. Stage 到 Mesh / Material

- `converter.py:69-96`
  - `Usd.Stage.Open(src_usd_path)`
  - `UsdGeom.GetStageUpAxis(stage)` 决定是否做统一的 Z-up -> Y-up 旋转
  - `Usd.PrimRange(stage.GetPseudoRoot())` 遍历所有 prim
- `converter.py:111-120`
  - 每个 mesh 分别走 geometry 提取与材质提取

## 3. Mesh 到 glTF buffers

- `usd_mesh.py:37-54`
  - `points -> numpy float32`
- `usd_mesh.py:56-65`
  - `normals -> numpy float32`
- `usd_mesh.py:67-128`
  - `st primvar -> numpy float32`
  - faceVarying 时炸开顶点和索引
- `writer.py:89-138`
  - positions / normals / uvs / indices 被追加到统一 BIN buffer
  - 同时生成 `bufferViews` 和 `accessors`

## 4. Material / Texture 到 glTF materials / images

- `usd_material.py:130-155`
  - 输出 scalar 因子与纹理路径
- `converter.py:129-161`
  - `diffuse`、`normal` 纹理经 `process_texture(...)`
  - `roughness + metallic` 经 `pack_metallic_roughness(...)`
  - 图片先进入 `writer.add_image(...)`
  - 再由 `writer.add_texture(...)` 形成 glTF texture
  - 最后 `writer.add_material(...)` 写入 `materials`

## 5. Nodes / Scene / File

- `converter.py:163-174`
  - 每个 mesh 创建一个 glTF mesh 和一个 glTF node
- `writer.py:62-66`
  - 所有 nodes 扁平挂到默认 scene 根下
- `writer.py:327-378`
  - 组装 glTF JSON，并写成 `.glb`

## 关键假设与限制

### 1. 只支持三角网格

- 代码位置：`convert_asset/glb/usd_mesh.py:23-34`
- 任何非三角面都会让整 mesh 跳过，不做自动三角化

### 2. 只处理 `Mesh` prim，不处理场景实例展开

- 代码位置：`convert_asset/glb/converter.py:85-92`
- 跳过 `instance proxy`
- 文档也提到了 point instancer 未支持，但实现层面更广义地说，当前逻辑只是“见到 Mesh 就导出”

### 3. 只读取一个 UV 集

- 代码位置：`convert_asset/glb/usd_mesh.py:69`
- 当前只读 `primvars:st`
- 没有读取 `uv`、`st1` 等别名或多 UV 集

### 4. 法线只支持逐点法线

- 代码位置：`convert_asset/glb/usd_mesh.py:56-65`
- face-varying normals、indexed normals 没有单独展开逻辑

### 5. 层级与局部/世界变换基本被忽略

- `UsdMeshExtractor` 只应用 `root_transform`，代码位置：`convert_asset/glb/usd_mesh.py:44-54`
- `GlbWriter.add_node(...)` 虽然支持 matrix/TRS，但 converter 没有传，代码位置：`convert_asset/glb/converter.py:173-174`
- 结果是：
  - 场景层级被扁平化
  - prim 自身及父级 Xform 没有被显式编码进导出的 node
  - 当前实现更接近“导出 mesh authored points”，而不是“保留 USD 场景空间关系”

### 6. 材质仅覆盖 UsdPreviewSurface 的一部分

- 代码位置：`convert_asset/glb/usd_material.py:42-48`, `convert_asset/glb/writer.py:219-261`
- 当前覆盖：
  - base color
  - roughness
  - metallic
  - normal
- 未见：
  - opacity / alpha mode
  - emissive
  - occlusion
  - clearcoat / transmission 等扩展

### 7. 纹理路径解析依赖 root layer

- 代码位置：`convert_asset/glb/usd_material.py:121-127`
- 相对纹理路径直接相对 `stage.GetRootLayer().realPath` 解析
- 没有按“材质实际 authoring layer”或 `resolvedPath` 做更细粒度处理

### 8. glb 贴图全部重新编码为 PNG

- 代码位置：`convert_asset/glb/texture_utils.py:28-39`, `convert_asset/glb/texture_utils.py:91-99`
- 原始 JPEG / PNG / 其他格式不会原样嵌入，都会转成 PNG bytes

## 文档与代码不一致

### 1. 坐标系转换实现方式

- 文档：`docs/glb/architecture.md:81`
  - 写的是“添加一个 root node，并在 root node 上挂旋转矩阵”
- 代码：
  - `convert_asset/glb/converter.py:79-81`
  - `convert_asset/glb/usd_mesh.py:44-54`
  - `convert_asset/glb/converter.py:173-174`
  - 实际做法是把 `root_transform` 直接乘到顶点/法线上，再创建无 matrix 的扁平 node

### 2. UV 集描述过宽

- 文档：`docs/glb/architecture.md:63`
  - 写的是“Only the primary UV set (`st` or `uv`) is exported.”
- 代码：
  - `convert_asset/glb/usd_mesh.py:69`
  - 只读取 `GetPrimvar("st")`

### 3. 纹理路径解析说明与实现不符

- 文档：`docs/no_mdl/feature_specs/texture_path_preservation.md:433`
  - 声称 `glb/usd_material.py` 通过 `SdfComputeAssetPathRelativeToLayer` 或 `resolvedPath` 读取纹理实际位置
- 代码：
  - `convert_asset/glb/usd_material.py:114-127`
  - 实际只读取 `inputs:file.path`，并在相对路径场景下按 `stage root layer` 所在目录拼接
  - 未出现 `SdfComputeAssetPathRelativeToLayer`
  - 未使用 `resolvedPath`

### 4. 历史变更文档中的 CLI 用法已过期

- 文档：`docs/changes/history/2026_01_06_glb_export.md:21-24`
  - 示例写的是 `python main.py export-glb --input asset_noMDL.usd --output asset.glb`
- 当前 CLI：
  - `convert_asset/cli.py:83-85`
  - 实际参数是 `export-glb <src> --out <dst>`

## 本次文档修订
- `docs/glb/architecture.md` / `docs/glb/architecture_zh.md`：将坐标系旋转说明为对每个 mesh 直接应用 [`convert_asset/glb/converter.py:61-98`](../../convert_asset/glb/converter.py#L61) 中的 `root_transform`，并强调导出的是顶层扁平节点与 `primvars:st`。
- `docs/glb/code_walkthrough.md` / `docs/glb/code_walkthrough_zh.md`：补充了 mesh 变换无需根节点、纹理路径按 `stage.GetRootLayer().realPath` 解析以及只阅读 `st` 的细节，对应 [`convert_asset/glb/usd_mesh.py:36-128`](../../convert_asset/glb/usd_mesh.py#L36) 与 [`convert_asset/glb/usd_material.py:22-127`](../../convert_asset/glb/usd_material.py#L22)。
- `docs/changes/history/2026_01_06_glb_export.md`：更新 CLI 示例为真实的 `export-glb <src> --out <dst>` 用法，对应 [`convert_asset/cli.py:82-91`](../../convert_asset/cli.py#L82)。
- `docs/no_mdl/feature_specs/texture_path_preservation.md`：澄清 `glb/usd_material.py` 并未使用 `SdfComputeAssetPathRelativeToLayer` / `resolvedPath`，而是直接根据 stage root layer 拼相对路径。
- `docs/changes/2026-03-17_usd_to_glb_implementation_survey.md`：为这次调研新增手段/验证记录与风险建议，方便后续参考。

## 验证

本次调研执行了以下只读验证：

```bash
./scripts/isaac_python.sh ./main.py export-glb --help
./scripts/isaac_python.sh ./main.py usd-to-glb --help
```

验证结果：

- `export-glb` 当前帮助文本为：`convert-asset export-glb [-h] --out OUT src`
- `usd-to-glb` 当前帮助文本为：`convert-asset usd-to-glb [-h] --out OUT [--keep-intermediate] src`

这与 `convert_asset/cli.py` 当前实现一致，也进一步确认历史文档中的 `--input/--output` 写法已经过期。

## 结论

当前仓库中的 USD -> GLB 实现是一条相对直接的“mesh/material 抽取 + 纯 Python glTF 写出”流水线：

- 入口清晰，`export-glb` 与 `usd-to-glb` 分别覆盖“直接导出”和“先 no-mdl 再导出”两种模式
- `convert_asset/glb/` 内部边界也比较清楚：`converter` 编排、`usd_mesh` 提 geometry、`usd_material` 提材质/纹理路径、`texture_utils` 处理图片、`writer` 负责 glTF/GLB 序列化
- 真正需要特别注意的不是入口，而是实现假设：
  - 只支持三角网格
  - 只读 `st`
  - 只覆盖部分 PBR 参数
  - 目前没有把 USD 层级 / xform 语义完整映射进 glTF scene

后续若要继续扩展或修正文档，应优先同步 `docs/glb/architecture.md`、`docs/glb/README.md` 与 `docs/no_mdl/feature_specs/texture_path_preservation.md` 中与上述实现不一致的部分。
