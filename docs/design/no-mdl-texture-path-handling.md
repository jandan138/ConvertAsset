# noMDL 转换中的纹理路径处理

> 本文档回答一个具体问题：
> **输出的 `*_noMDL.usd` 文件中，纹理贴图（`.jpg`、`.png` 等）的路径是相对路径还是绝对路径？**

## 结论

**纹理路径会被转换为绝对路径，并以绝对路径写入输出文件。**

这与 USD 组合关系（sublayers / references / payloads）的处理方式相反——后者被重写为相对路径以保持可移植性。

---

## 处理流程（调用链）

```
processor.process()
  └─ convert_and_strip_mdl_in_this_file_only(dst_stage)
       └─ _convert_active_materials(stage, stats, processed)
            └─ copy_textures(stage, mdl_shader, mat)      ← 核心位置
                 ├─ _anchor_dir_for_attr(sa_attr)         ← 推导锚点目录
                 ├─ _set_tex(tag, path, anchor_dir=...)
                 │    └─ _resolve_abs_path(anchor_dir, path)  ← 转为绝对路径
                 │         └─ fin.Set(ap)                 ← 写入绝对路径
                 └─ dst_stage.GetRootLayer().Export(...)  ← 输出时路径已是绝对
```

---

## 关键代码位置

### 1. 读取纹理路径（`materials.py`，约第 261-291 行）

```python
# 优先读取 resolvedPath（在 Sdf.AssetPath 中通常已是绝对路径）
path = getattr(v, "resolvedPath", getattr(v, "path", None)) if v is not None else None
```

代码优先取 `resolvedPath` 而非 `path`，因为前者通常已经是绝对路径。

### 2. 锚点目录推导（`materials.py`，约第 182-201 行）

```python
def _anchor_dir_for_attr(attr):
    stack = attr.GetPropertyStack(Usd.TimeCode.Default())
    for spec in stack:
        real = getattr(spec.layer, "realPath", None) or lid
        return os.path.dirname(real)   # 返回该 layer 所在目录
```

`anchor_dir` 是 MDL 属性所在 layer 文件的目录，用于把相对路径解析为绝对路径。

### 3. 绝对路径化（`path_utils.py`，约第 36-43 行）

```python
def _resolve_abs_path(anchor_dir, pth):
    if os.path.isabs(pth):
        return _to_posix(os.path.normpath(pth))          # 已是绝对 → 直接返回
    if not anchor_dir:
        return _to_posix(pth)                             # 无锚点 → 原样返回
    return _to_posix(os.path.normpath(os.path.join(anchor_dir, pth)))  # 相对 → 绝对
```

相对路径 + `anchor_dir` → 绝对路径，**不会再转回相对路径**。

### 4. 写入属性（`materials.py`，`_set_tex` 内）

```python
fin.Set(ap)   # ap 是绝对路径字符串，直接写入 UsdUVTexture.inputs:file
```

---

## 输出文件中的实际形态

纹理路径写入 `UsdUVTexture` shader 的 `inputs:file` 属性：

```usda
def Shader "Tex_BaseColor"
{
    uniform token info:id = "UsdUVTexture"
    asset inputs:file = @/absolute/path/to/tex/albedo.jpg@   # ← 绝对路径
    token inputs:sourceColorSpace = "sRGB"
    token inputs:wrapS = "repeat"
    token inputs:wrapT = "repeat"
}
```

USD 中 `asset` 类型用 `@路径@` 语法，此处路径为绝对路径。

---

## 对比：USD 组合关系的路径处理

| 路径类型 | 转换方向 | 原因 |
|---|---|---|
| 纹理贴图（`.jpg`、`.png`） | 相对 → **绝对** | 确保任何位置打开均可定位贴图 |
| sublayers / references / payloads | 绝对 → **相对** | 维护项目目录结构的可移植性 |

这两种路径由不同模块处理：纹理路径在 `materials.py` 中处理，组合关系路径在 `references.py` 中处理。

---

## 含义与注意事项

1. **不可移植**：`_noMDL.usd` 中的纹理路径是绝对路径，因此该文件不能直接迁移到其他机器或不同根目录下使用，否则纹理会丢失。
2. **必须同路径使用**：如果要在其他机器上加载 `_noMDL.usd`，需要保证纹理文件仍在相同绝对路径下（或通过 USD 的 asset resolver 机制重映射）。
3. **后续 GLB 导出不受影响**：`glb/converter.py` 在导出 GLB 时会直接从磁盘读取纹理文件，绝对路径反而能可靠地定位到文件。
4. **edge case**：若 MDL 中纹理路径本身已是绝对路径，则 `_resolve_abs_path` 不做任何改变，直接原样保留。
