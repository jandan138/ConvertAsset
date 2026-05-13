# USD 入门：Shading 输出、Token 类型与 MDL→Preview 切换

适合读者：完全不了解 USD/材质系统的新手。

本文用最直白的方式，带你理解三件事：
- 什么是材质的“表面输出 outputs:surface”？它和连接（ConnectToSource）是怎么工作的？
- 什么是 `Sdf.ValueTypeNames.Token`？为什么用在 surface 终端、wrapS/T、varname 等地方？
- 我们的转换代码里，如何把“MDL 分支”切换到“UsdPreviewSurface 分支”？

---

## 1. USD 中的“输出”是什么？

- 一个 USD 材质（`UsdShade.Material`）或着色器（`UsdShade.Shader`）可以有“输出口”（output）。
- 输出口像是“接口插头”，可以被别的节点“接上”。
- 典型输出：
  - `Material.outputs:surface`（通用表面输出）
  - `Material.outputs:surface:mdl`（MDL 专用表面输出）
  - `Shader.outputs:rgb`（颜色输出）、`Shader.outputs:r`（单通道输出）

连接（`ConnectToSource`）就是在 A 的输出与 B 的输入之间画一条线。渲染时，数据沿着这条线从源传到目标。

### 1.1 为什么要有 `outputs:surface`？
- 渲染器最终需要一个“表面着色结果”。USD 约定材质的“表面终端”叫 `outputs:surface`。
- 你可以把它理解为：告诉渲染器“这个材质的最终表面由谁来算”。
- 我们用的 `UsdPreviewSurface` 是一个通用、跨渲染器都能理解的着色器。把 `Material.outputs:surface` 指到它，就能让渲染器走 Preview 管线。

### 1.2 MDL 专用的输出
- 有些资产用 NVIDIA 的 MDL 着色系统，Material 上常见 `outputs:surface:mdl` 或 `outputs:mdl:surface`。这是一条“MDL 分支”。
- 如果这条分支还连着 MDL shader，渲染器可能会优先走 MDL 分支（视渲染器实现而定）。
- 所以我们在切换到 Preview 时，会“断开并删除”这条 MDL 专用输出，避免误用。

---

## 2. `Sdf.ValueTypeNames.Token` 是什么？

- USD 里每个属性都有“类型”。常见有 `Float`、`Color3f`、`Asset`、`Token` 等。
- `Token` 是“短字符串枚举值”，适合“从固定集合里选一个”的场景：
  - 例如 `wrapS` 只能是 `repeat`/`clamp`/`mirror`；
  - `sourceColorSpace` 通常是 `raw` 或 `sRGB`；
  - `outputs:surface` 的类型也是 `Token`，表示它是“表面终端”这种角色。

和 `String` 相比：
- `Token` 性能更好（内部驻留、比较快），并倾向用于规范化的选项值；
- `String` 则是自由文本，没有“枚举/受控词表”的语义。

在 Python 里，给 `Token` 赋值时依然用普通字符串：
```python
attr = shader.CreateInput("wrapS", Sdf.ValueTypeNames.Token)
attr.Set("repeat")  # 直接传 str 即可
```

---

## 3. 我们的“MDL → Preview”切换做了什么？

核心步骤只有两步：

1) 把 `Material.outputs:surface` 接到 `UsdPreviewSurface.outputs:surface`
```python
mat.CreateSurfaceOutput().ConnectToSource(
    prev.CreateOutput("surface", Sdf.ValueTypeNames.Token)
)
```
- 含义：让材质的最终表面结果由 PreviewSurface 负责。
- `CreateSurfaceOutput()`/`CreateOutput(..., Token)` 会“确保存在 + 返回”对应的输出口。

2) 断开并删除 MDL 专用输出
```python
# 断开 outputs:surface:mdl 的所有连接
attr = mat.GetSurfaceOutput("mdl").GetAttr()
attr.SetConnections([])
# 删除 MDL 专用属性，避免误用
for prop in ("outputs:surface:mdl", "outputs:mdl:surface"):
    prim.RemoveProperty(prop)
```
- 断开的目的是防止还从 MDL 分支取值；
- 删除属性是为了从根上杜绝“看起来还有 MDL 终端”的歧义。

这两步合起来，形成一个“闭环切换”：
- 接上 Preview → 断掉 MDL → 渲染器自然只会走 Preview。

---

## 4. 常见名词速查
- Stage：一个打开的 USD 场景实例。
- Layer：承载 USD 数据的文件或匿名层；多个 Layer 通过“分层/合成”叠加。
- EditTarget：当前写入的目标 Layer。`Create*`/`Set*` 都会写到这里。
- Prim：USD 的节点（类似文件系统里的文件/文件夹）。
- Attribute / Relationship：属性 / 关系。
- UsdShade：USD 的材质与着色网络 API。

---

## 5. 和我们代码的对应关系
- `ensure_preview`：
  - 创建 Preview 网络骨架（Scope、PrimvarReader、UVTexture、PreviewSurface），
  - 把 `Material.outputs:surface` 指到 PreviewSurface（用 Token 类型）。
- `remove_material_mdl_outputs`：
  - 断开 + 删除 `outputs:surface:mdl`（及变体写法）。
- `verify_no_mdl`：
  - 校验场景中不再有 MDL shader 或 MDL 输出残留。

---

## 6. 入门建议
- 使用带图形界面的 USD 浏览器查看节点与连接（例如 USDView）。
- 亲手画一个最小的 Preview 材质：PrimvarReader(st) → UsdUVTexture(file) → UsdPreviewSurface(diffuseColor)。
- 对照本项目 `docs/materials.md`，理解四个通道（BaseColor、Roughness、Metallic、Normal）的接线规范。

---

以上内容力求“最小够用”。当你需要更深入（如 Layer 的 ListOp、VariantSet、Clips、Payload 等），可以翻看本项目其它文档或官方 USD 手册。