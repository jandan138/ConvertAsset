# export_mdl_materials.py 源码逐行解析

本文对 `convert_asset/export_mdl_materials.py` 的全部源码进行逐行/逐段中文解析，帮助理解导出“MDL 材质球”的实现细节与设计权衡。

> 文件位置：`/opt/my_dev/ConvertAsset/convert_asset/export_mdl_materials.py`
> 相关依赖：`convert_asset/no_mdl/materials.py` 中的材质/贴图工具函数

---

## 顶部文档字符串与导入

```python
"""Export MDL materials ..."""
from __future__ import annotations
from typing import List, Tuple
import os
from pxr import Usd, UsdShade, Sdf, UsdGeom  # type: ignore

from .no_mdl.materials import ensure_preview, find_mdl_shader, copy_textures, connect_preview, _resolve_abs_path, _anchor_dir_for_attr
```

- 顶部注释说明“导出 MDL 材质”为独立 USD 的目的与规则。
- `__future__` 打开注解前置，允许在运行时更灵活地使用类型注解。
- 引入 PXR USD 相关模块：`Usd`（Stage/Layer）、`UsdShade`（材质/着色）、`Sdf`（Schema/类型/AssetPath）、`UsdGeom`（几何体）。
- 从内部模块 `no_mdl.materials` 引入工具函数：
  - `find_mdl_shader(material)`：定位某个 `UsdShade.Material` 的 MDL Shader；
  - `ensure_preview/connect_preview/copy_textures`：仅在导出 Preview 模式时使用；
  - `_resolve_abs_path/_anchor_dir_for_attr`：用于根据属性作者层确定锚点目录，并解析 AssetPath 的绝对路径。

---

## _is_in_root_layer

```python
def _is_in_root_layer(stage: Usd.Stage, prim: Usd.Prim) -> bool:
    root_id = stage.GetRootLayer().identifier
    try:
        for spec in prim.GetPrimStack():
            if spec.layer.identifier == root_id:
                return True
    except Exception:
        pass
    return False
```

- 作用：判断某个 Prim 是否在当前“根层”中有作者条目（PrimSpec）。
- 背景：当 `include_external=False` 时，只导出由根层直接定义的材质，忽略外部引用文件中的材质。
- 实现：遍历 Prim 的 `PrimStack`，只要有一条 `spec.layer.identifier == root_id` 即视为根层作者存在。

---

## _authoring_layer_dir_for_prim

```python
def _authoring_layer_dir_for_prim(prim: Usd.Prim) -> str | None:
    ...
    for spec in reversed(list(stack)):
        lid = getattr(spec.layer, "identifier", "")
        if str(lid).startswith("anon:"):
            continue
        real = getattr(spec.layer, "realPath", None) or lid
        if real:
            return os.path.dirname(real)
    return None
```

- 作用：找到“最弱到最强”堆栈中，首个非 anonymous 的 Layer 的物理路径目录，作为该 Prim 的“作者层目录”。
- 用途：当 `placement == "authoring"` 时，导出文件应放在“材质定义所在的最小子文件”的同级新建目录下。
- 细节：跳过匿名层（`anon:`），优先使用 `realPath`，否则用 `identifier`；取其 `dirname`。

---

## _sanitize_name 与 _ensure_dir

```python
def _sanitize_name(name: str) -> str:
    s = name.strip().replace(" ", "_")
    bad = "<>:\\/|?*\"'`"
    for ch in bad:
        s = s.replace(ch, "_")
    return s or "Material"


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
```

- `_sanitize_name`：将材质名清洗为安全的文件名（替换空格与非法字符），且保证非空。
- `_ensure_dir`：确保导出目录存在。

---

## export_from_stage 主流程

```python
def export_from_stage(..., placement: str = "authoring", include_external: bool = True, export_mode: str = "mdl", emit_ball: bool = False, assets_path_mode: str = "relative") -> List[Tuple[str, str]]:
    results: List[Tuple[str, str]] = []
    root_dir = os.path.dirname(stage.GetRootLayer().realPath or stage.GetRootLayer().identifier)

    for prim in stage.Traverse():
        if prim.GetTypeName() != "Material":
            continue
        if (not include_external) and (not _is_in_root_layer(stage, prim)):
            continue
        mat = UsdShade.Material(prim)
        mdl = find_mdl_shader(mat)
        if not mdl:
            continue

        mat_name = _sanitize_name(prim.GetName())
        looks_path = "/Looks"
        if placement == "authoring":
            base_dir = _authoring_layer_dir_for_prim(prim) or root_dir
        else:
            base_dir = root_dir
        out_dir = os.path.join(base_dir, out_dir_name)
        _ensure_dir(out_dir)
        export_path = os.path.join(out_dir, f"{mat_name}.usda" if ascii_usd else f"{mat_name}.usd")

        new_stage = Usd.Stage.CreateNew(export_path)
        new_stage.SetDefaultPrim(new_stage.DefinePrim("/Root", "Scope"))
        new_stage.DefinePrim(looks_path, "Scope")
        new_mat = UsdShade.Material.Define(new_stage, f"{looks_path}/{mat_name}")

        if export_mode == "preview":
            ensure_preview(new_stage, new_mat)
            filled, has_c, c_rgb, bc_tex = copy_textures(new_stage, mdl, new_mat)
            connect_preview(new_stage, new_mat, filled, has_c, c_rgb, bc_tex)
        else:
            _export_mdl_material(new_stage, new_mat, mdl, assets_path_mode=assets_path_mode)

        new_stage.GetRootLayer().Save()
        results.append((prim.GetPath().pathString, export_path))
```

- 遍历所有 `Material` 类型的 prim。
- 根据 `include_external` 筛选是否仅处理根层作者材质。
- 通过 `find_mdl_shader` 检测是否为 MDL 材质，忽略非 MDL。
- 确定导出目录：
  - `authoring`：优先 “作者层目录”，否则回退到根目录；
  - `root`：统一使用根层目录。
- 创建新 stage，定义 `/Root` 和 `/Looks`，在 `/Looks/<MatName>` 定义新材质。
- 两种导出模式：
  - `preview`：构建 UsdPreviewSurface 网络，拷贝贴图并连接；
  - `mdl`（默认）：保留 MDL Shader 的元数据与输入，调用 `_export_mdl_material`。
- 保存新材质文件，记录结果映射。

### emit_ball 预览球体场景

```python
        if emit_ball:
            ball_path = os.path.join(out_dir, f"{mat_name}_ball.usda" if ascii_usd else f"{mat_name}_ball.usd")
            ball_stage = Usd.Stage.CreateNew(ball_path)
            world = ball_stage.DefinePrim("/World", "Xform")
            ball_stage.SetDefaultPrim(world)
            looks_prim = ball_stage.DefinePrim("/Looks", "Scope")
            mat_target = ball_stage.DefinePrim(f"/Looks/{mat_name}", "Material")
            mat_ref = Sdf.Reference(assetPath=os.path.relpath(export_path, os.path.dirname(ball_path)).replace("\\", "/"), primPath=f"/Looks/{mat_name}")
            mat_target.GetReferences().AddReference(mat_ref)
            sphere = UsdGeom.Sphere.Define(ball_stage, "/World/Sphere")
            sphere.CreateRadiusAttr(50.0)
            UsdShade.MaterialBindingAPI.Apply(sphere.GetPrim()).Bind(UsdShade.Material(mat_target))
            ball_stage.GetRootLayer().Save()
```

- 可选生成一个小场景文件 `<MatName>_ball.usda`：包含 `/World/Sphere` 与 `/Looks/<MatName>`，并将材质通过引用绑定到球体，开箱即看。
- 注意引用时 `assetPath` 使用相对 ball 文件的相对路径（规范化为 POSIX 分隔）。

- 函数返回：`List[(materialPrimPath, exportedFilePath)]`。

---

## _export_mdl_material：复制 MDL 元数据与输入

```python
def _export_mdl_material(new_stage, new_mat, mdl_shader_src, assets_path_mode="relative"):
    parent = new_mat.GetPath().pathString
    shader_path = f"{parent}/mdlShader"
    mdl_new = UsdShade.Shader.Define(new_stage, shader_path)
```

- 在新材质下创建 `mdlShader` 节点，作为 MDL 输出的来源。

### 复制 info:id

```python
    src_prim = mdl_shader_src.GetPrim()
    id_attr = src_prim.GetAttribute("info:id")
    if id_attr and id_attr.HasAuthoredValue():
        mdl_new.CreateIdAttr(id_attr.Get())
    else:
        mdl_new.CreateIdAttr("mdlMaterial")
```

- 尽量保留原始的 `info:id`，否则写入一个合理的默认值（`mdlMaterial`）。

### 复制 info:mdl:* 与实现元信息，重写 AssetPath

```python
    new_dir = os.path.dirname(new_stage.GetRootLayer().realPath or new_stage.GetRootLayer().identifier)
    for name in src_prim.GetPropertyNames():
        if name.startswith("info:mdl:") or name in ("info:implementationSource", "info:sourceAsset"):
            a_src = src_prim.GetAttribute(name)
            ...
            if a_src.HasAuthoredValue():
                v = a_src.Get()
                if isinstance(v, Sdf.AssetPath):
                    anchor_dir = _anchor_dir_for_attr(a_src)
                    abs_path = _resolve_abs_path(anchor_dir, (v.resolvedPath or v.path)) if (v and (v.resolvedPath or v.path)) else None
                    if abs_path:
                        if assets_path_mode == "absolute":
                            v = Sdf.AssetPath(abs_path)
                        else:
                            rel = os.path.relpath(abs_path, new_dir).replace("\\", "/")
                            v = Sdf.AssetPath(rel)
                a_dst = mdl_new.GetPrim().CreateAttribute(name, a_src.GetTypeName())
                a_dst.Set(v)
```

- 复制所有 `info:mdl:*` 属性，以及常见的实现提示（`info:implementationSource`、`info:sourceAsset`）。
- 对 AssetPath 类型做特殊处理：
  - 使用 `_anchor_dir_for_attr(a_src)` 找到作者层锚点目录；
  - 通过 `_resolve_abs_path(anchor_dir, path)` 计算绝对路径；
  - 根据 `assets_path_mode` 写入“绝对路径”或“相对新文件目录的相对路径”，并统一 POSIX 分隔。

### 创建 outputs:surface（mdl）

```python
    mdl_new.CreateOutput("surface", Sdf.ValueTypeNames.Token)
```

- 按 MDL Shader 约定创建 surface 输出口。

### 复制 inputs:*（含贴图 AssetPath 重写）

```python
    new_dir = os.path.dirname(new_stage.GetRootLayer().realPath or new_stage.GetRootLayer().identifier)
    mdl_sa_attr = src_prim.GetAttribute("info:mdl:sourceAsset")
    mdl_anchor_dir = _anchor_dir_for_attr(mdl_sa_attr) if mdl_sa_attr else None
    for inp in mdl_shader_src.GetInputs():
        i_dst = mdl_new.CreateInput(inp.GetBaseName(), inp.GetTypeName())
        try:
            val = inp.Get()
            if isinstance(val, Sdf.AssetPath):
                attr = src_prim.GetAttribute(f"inputs:{inp.GetBaseName()}")
                anchor_dir = _anchor_dir_for_attr(attr) if attr else None
                if not anchor_dir:
                    anchor_dir = mdl_anchor_dir
                abs_path = _resolve_abs_path(anchor_dir, (val.resolvedPath or val.path)) if (val and (val.resolvedPath or val.path)) else None
                if abs_path:
                    if assets_path_mode == "absolute":
                        i_dst.Set(Sdf.AssetPath(abs_path))
                    else:
                        rel = os.path.relpath(abs_path, new_dir).replace("\\", "/")
                        i_dst.Set(Sdf.AssetPath(rel))
                else:
                    i_dst.Set(val)
            else:
                if val is not None:
                    i_dst.Set(val)
        except Exception:
            pass
```

- 遍历源 MDL Shader 的所有 `inputs:*`：
  - 对 AssetPath 类型，优先从该输入属性的作者层推断锚点，其次回退到 `info:mdl:sourceAsset` 的作者层；
  - 解析绝对路径并按策略（absolute/relative）写回；
  - 非 Asset 值直接复制；
  - 这里不深拷贝连接子图，仅复制“值”，符合“最小可用”导出目标。

### 连接 Material 的 outputs:surface:mdl

```python
    out_mdl = new_mat.GetSurfaceOutput("mdl") or new_mat.CreateSurfaceOutput("mdl")
    out_mdl.ConnectToSource(mdl_new.GetOutput("surface"))
```

- 在新 `Material` 上创建/获取 `outputs:surface:mdl`，连接至 `mdlShader.outputs:surface`。

---

## 导出结果与使用建议

- 产物：每个 MDL 材质导出为一个独立 USD（默认 usda），位于 `--placement` 决定的目录下的 `--out-dir-name` 子目录中；可选生成 `<MatName>_ball.usda` 用于快速可视。
- 路径策略：
  - 若你要搬运文件夹并保持可用，推荐 `assets_path_mode=relative`（默认）；
  - 若加载失败或环境不一致，使用 `assets_path_mode=absolute` 保证能定位资源。
- 限制：不深拷贝 MDL 子图网络；如需完整克隆，可在此基础上扩展对连接的递归复制。

---

## 可能的增强点

- 深拷贝 MDL 网络连接，保留 procedural/graph。
- 导出后生成资源存在性报告（列出所有 AssetPath 并检查文件存在）。
- 可选复制贴图到导出目录结构下（带去重与重命名策略）。

---

文档到此结束，如需对特定行继续深钻（例如某些属性写入的边界条件），请指出具体片段。