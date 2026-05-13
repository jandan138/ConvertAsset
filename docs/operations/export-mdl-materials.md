# 导出 MDL 材质为独立材质球 USD（export-mdl-materials）

该命令用于从一个 USD 文件中，遍历其中的 MDL 材质，并为每一个材质生成一个独立的 UsdPreviewSurface 材质球 USD 文件（带贴图连接），以便素材资产库沉淀与复用。

- 只读源场景，不写回原文件
- 不进行 flatten，且不会修改任何外部引用文件
- 每个输出文件包含一个 Material（位于 `/Looks/<MaterialName>`）及其内部的 Preview 网络

---
## 基本用法

```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py export-mdl-materials \
  /abs/path/to/scene.usd \
  --out-dir-name mdl_materials \
  --placement authoring \
  # --no-external \
  # --binary
```

参数说明：
- `<scene.usd>`：需要扫描的 USD（顶层或子层均可）。
- `--out-dir-name`：输出子目录名称（会创建在目标目录下），默认 `mdl_materials`。
- `--placement`：输出文件放置策略：
  - `authoring`（默认）：将每个材质球写到“该材质作者层（通常是最小子 USD）”的同级目录下的 `--out-dir-name/` 中。
  - `root`：统一写到“当前打开的 USD 根层文件”的同级目录下的 `--out-dir-name/` 中。
- `--no-external`：只导出“根层拥有/定义”的材质，忽略外部引用进来的材质。
- `--binary`：输出二进制 `.usd`；默认写可读文本 `.usda`。

提示：如果你“不希望导出目录与场景顶层 USD 同目录”，请选择 `--placement authoring`（默认即该模式）。

---
## 导出结果结构
- 每个输出 USD 的典型内容：
  - `Scope /Root`（默认 Prim）
  - `Scope /Looks`
  - `def Material "/Looks/<MaterialName>"`：材质主体
    - 内含：`UsdPreviewSurface`、`UsdPrimvarReader_float2`、四个 `UsdUVTexture`（BaseColor/Roughness/Metallic/Normal）等节点
    - `outputs:surface` 指向 `UsdPreviewSurface.outputs:surface`
    - 贴图节点 `st` 连接 primvar 的 `result`，`wrapS/T=repeat`；BaseColor 纹理 `sourceColorSpace=sRGB`，其他为 `raw`

- 输出路径：
  - `authoring`：`<作者层所在目录>/<out-dir-name>/<MaterialName>.usda`
  - `root`：`<根层所在目录>/<out-dir-name>/<MaterialName>.usda`

- 文件名规则：对材质名进行轻度清洗（空格/特殊字符替换为 `_`）。

---
## 作者层（Authoring Layer）如何判定？
我们查看该 Material 的 PrimStack，从最弱一侧（底部）向上寻找第一个非匿名层（非 `anon:`），以其 `realPath`/`identifier` 的目录作为“作者层目录”。

这通常能定位到“最小子 USD”（首次定义该材质的文件），从而将材质球输出在它旁边，避免与顶层 USD 的目录混放。

---
## 贴图与参数
- 我们会尽最大可能从 MDL Shader 及其 `.mdl` 文本中解析出 BaseColor/Roughness/Metallic/Normal 的贴图路径。
- BaseColor 的 `sourceColorSpace` 设为 `sRGB`，其余通道为 `raw`；Roughness 支持常见的 Gloss→Roughness 反转（scale=-1, bias=1）。
- 若贴图缺失，会回落常量（如 BaseColor 使用解析到的常量色；Roughness/Metallic 设合理默认）。

---
## 与材质检查（inspect）的联动
导出完成后可用 `inspect` 子命令对单个材质 USD 进行核对：

```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect \
  /path/to/mdl_materials/MatA.usda usdpreview /Looks/MatA
```

你将看到 PreviewSurface 的关键输入（diffuseColor/roughness/metallic/normal）是常量还是贴图，以及贴图文件路径存在性。

---
## 示例
以仓库示例 `examples/inspect_demo.usda` 为例：

```bash
# 将每个材质导出至“作者层旁的 mdl_balls/”目录
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py export-mdl-materials \
  /opt/my_dev/ConvertAsset/examples/inspect_demo.usda \
  --placement authoring \
  --out-dir-name mdl_balls
```

输出示例：
```
Exported materials:
  /Looks_Mat -> /opt/my_dev/ConvertAsset/examples/mdl_balls/Looks_Mat.usda
```

随后可以检查其中一个导出的材质：

```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect \
  /opt/my_dev/ConvertAsset/examples/mdl_balls/Looks_Mat.usda \
  usdpreview \
  /Looks/Looks_Mat
```

---
## 常见问题
- 材质名重复：文件名按材质名清洗生成，若重复可能被覆盖；建议手动整理或调整输出目录。
- 贴图不存在：有些路径可能是相对路径且不在本机；导出不会拷贝贴图，仅记录路径。可结合 no-MDL 转换流程的贴图复制逻辑在资产侧处理。
- normal 通道缺失：部分源 MDL 网络没有可靠的法线贴图定义，导出会留空（inspect 会显示 Missing）。
- 仅导出本文件材质：使用 `--no-external`。

---
## 版本
- v1：初始版本，支持 `authoring/root` 放置策略，支持只读解析 MDL 并生成 Preview 材质球。
