# USD 材质入门（从零到可用）

这是一份面向新手的速成笔记，帮助你迅速建立“USD 里的材质是怎么组织和工作的”直觉。

## 1. 三个角色：Material / Shader / 绑定
- `UsdShade.Material`（材质）：一个容器，打包一组着色相关的节点和输出。它更像“材质资产”，可以被多个模型复用。
- `UsdShade.Shader`（着色器）：真正干活的“程序块”，例如 `UsdPreviewSurface`、`UsdUVTexture`、`UsdPrimvarReader_float2`、或第三方如 MDL Shader。
- 绑定（Binding）：把一个 `Material` 绑定到几何体（Mesh、PointInstancer 等）上，这样渲染时几何体会使用该材质。

简图：
```
Geometry --(MaterialBinding)--> Material --(networks)--> Shaders
```

## 2. 最常见的着色网络：PreviewSurface
- `UsdPreviewSurface` 是 USD 原生、跨 DCC 的 PBR 着色器。
- 常用输入：
  - `diffuseColor`（基色）、`roughness`（粗糙度）、`metallic`（金属度）、`normal`（法线）等。
- 贴图如何接进来？
  - 用 `UsdUVTexture` 读取 2D 图片（.png/.jpg/.exr 等），把 `rgb` 或 `r` 连到对应输入。
  - `UsdUVTexture.st` 需要接一份 UV 坐标（来自 `UsdPrimvarReader_float2` 的 `result`）。

数据流：
```
Geometry(UV) -> PrimvarReader(varname=st)-> UsdUVTexture(file, st) -> PreviewSurface(inputs) -> Material.outputs:surface
```

## 3. 什么是 UV？
- UV 是“把 3D 表面摊平到 2D 图片上的坐标”。
- 每个顶点通常都有一组或多组 UV（称为 UVSet，名字常见 `st`）。
- 贴图是 2D 图片；采样一个像素就需要一个 2D 坐标（UV）。

## 4. 材质是怎么被应用到几何上的？
- 在几何体上会有一个 `material:binding` 关系（Rel），指向某个 `UsdShade.Material` 的 prim 路径。
- 像 `Mesh` 可以在 prim 上或局部（faceSet）级别绑定材质。
- 渲染时，几何体通过该绑定获取材质网络，完成着色。

## 5. MDL 材质和 Preview 材质的关系
- MDL（NVIDIA 的材质系统）可以在 USD 里以 Shader 的形式出现，通常连接到材质的 `outputs:surface:mdl`。
- 我们项目会把 MDL 转换成 PreviewSurface 网络，连接到 `outputs:surface`，便于通用查看和跨 DCC 兼容。

## 6. Scope 有啥用？
- `Scope` 是一个分组节点，本身不渲染，只用来组织层级。
- 我们会在材质下建一个 `/{GROUP}` 的 Scope，把转换生成的节点（PreviewSurface、PrimvarReader、Tex_*）集中放进去，避免和原有节点混在一起。

## 7. 颜色空间与常见通道
- BaseColor（颜色贴图）使用 `sRGB` ；Roughness/Metallic/Normal（数据贴图）使用线性 `raw`。
- 法线贴图通常连接 `PreviewSurface.normal` 的 `Float3`；
- 粗糙度/金属度通常从纹理的 `r` 通道读取；
- 若没有纹理，可以给常量值（比如 `roughness=0.5`、`metallic=0.0`）。

## 8. 进阶：UDIM、wrap、以及多 UVSet
- UDIM：大图集切片方法，路径中可用 `<UDIM>` 占位符（如 `BaseColor.<UDIM>.exr`）。
- wrapS/wrapT：UV 超范围的采样行为，一般设 `repeat`；特定场景可用 `clamp/mirror`。
- 多 UVSet：不同用途可选择不同 UV（比如光照贴图用 `uv2`），在 `PrimvarReader` 的 `varname` 指定名字即可。

## 9. 常见问题
- 为什么打开文件看不到材质？
  - 可能材质未绑定到几何体，或 `defaultPrim` 未设置导致工具未显示主视图。
- 为什么贴图偏灰或偏色？
  - 可能把 BaseColor 当成 `raw`，或把数据贴图当成 `sRGB`；检查 `sourceColorSpace`。
- 为什么网络里有很多“Tex_*”节点？
  - 这是按通道拆分的纹理采样器，便于独立控制与调试。

## 10. 小结
- 记住三件事：`Material` 是容器、`Shader` 是网络节点、`Binding` 把材质挂到几何上。
- PBR 最小网络：`PrimvarReader -> UVTexture -> PreviewSurface -> Material.output`。
- 逐步掌握颜色空间、法线、以及 UV 的基础，就能在不同 DCC 之间顺利迁移材质。
