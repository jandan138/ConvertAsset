# 导出 MDL 材质球：代码全解析

本文从代码视角解释“export-mdl-materials”实现细节，便于二次开发。

关键文件：
- `convert_asset/export_mdl_materials.py`
- `convert_asset/cli.py`（命令行对接）
- 复用模块：`convert_asset/no_mdl/materials.py`（定位 MDL）

## 入口函数
- `export_from_stage(stage, out_dir_name, ascii_usd, placement, include_external, export_mode, emit_ball, assets_path_mode)`
  - 遍历 Stage 中的 `Material`；
  - 依据 `include_external` 与作者层判断过滤；
  - 通过 `find_mdl_shader(mat)` 判断该材质是否为 MDL；
  - 决定导出目录（作者层/顶层）；
  - `export_mode` 分流：
    - `mdl`：调用 `_export_mdl_material()` 生成 MDL 材质球；
    - `preview`：调用 `ensure_preview()/copy_textures()/connect_preview()` 生成预览材质球；
  - `emit_ball=True` 时，生成一个 _ball.usda（绑定球体引用材质），便于快速预览。

## 作者层定位
- `_authoring_layer_dir_for_prim(prim)`：从 PrimStack 最弱一侧开始寻找第一个非匿名层，取其 realPath/identifier 的目录作为“作者层目录”。

## MDL 导出核心
- `_export_mdl_material(new_stage, new_mat, mdl_shader_src, assets_path_mode)`：
  - 在新文件 `/Looks/<MatName>` 下定义 `Material` 与 `Shader "mdlShader"`；
  - 复制 `info:id`（无则设为 `mdlMaterial`）；
  - 复制所有 `info:mdl:*`、`info:implementationSource`、`info:sourceAsset` 属性；
    - 对 AssetPath 值调用 `_resolve_abs_path()` 得到绝对路径；
    - 基于 `assets_path_mode`：
      - `relative`：写为相对导出文件目录的相对路径；
      - `absolute`：直接写绝对路径；
  - `mdlShader.outputs:surface` 与 `Material.outputs:surface:mdl` 连接；
  - 复制所有 `inputs:*` 输入：
    - 在源输入为 AssetPath 时同样按上面的规则重写路径（优先以输入属性的作者层为锚点，回退到 `info:mdl:sourceAsset` 的锚点）。

## 预览材质导出（可选）
- `ensure_preview()`：在材质下创建 Preview 网络骨架（PreviewSurface、PrimvarReader、四个 UsdUVTexture）。
- `copy_textures()`：从 MDL pin 与 .mdl 文本尽可能解析贴图路径与常量；
- `connect_preview()`：接线 BaseColor/Roughness/Metallic/Normal 到 PreviewSurface。

## 预览球（emit_ball）
- 新建 Stage：`/World`（defaultPrim）与 `/Looks`；
- 在 `/Looks/<MatName>` 定义 Material 并添加对材质球 .usda 的 Reference（精确到 `/Looks/<MatName>`）；
- 在 `/World/Sphere` 定义球体并绑定该材质；
- 保存为 `<MatName>_ball.usda`。

## CLI 参数映射
- `convert_asset/cli.py` 的 `export-mdl-materials` 子命令：
  - `--out-dir-name`、`--placement`、`--no-external`、`--binary`、`--mode`、`--emit-ball`、`--assets-path-mode` 均对应上文参数。

## 扩展点建议
- 深拷输入网络（connected source）
- 贴图复制与相对路径重写的可选流程
- 批量报告（CSV/JSON）生成
