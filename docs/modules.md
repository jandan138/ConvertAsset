# 模块职责（Modules）

## 顶层入口
- `main.py`: 调用 `convert_asset.cli.main(argv)`，提供统一入口。
- `convert_asset/cli.py`: argparse CLI，默认子命令 `no-mdl`，打印结果映射与统计。

## no_mdl 子包
- `config.py`
  - 关键常量：`SUFFIX`、`ALLOW_OVERWRITE`、`MATERIAL_ROOT_HINTS`、`GROUP`、`UVSET` 等。
  - 贴图扩展名、MDL 常量 key、策略开关（如 `RESTORE_VARIANT_SELECTION`）。
- `path_utils.py`
  - `_to_posix`、`_relpath`、`_resolve`、`_sibling_noMDL_path`、`_resolve_abs_path`。
  - 统一路径风格，生成输出文件名，解析相对路径。
- `mdl_parse.py`
  - 轻量 MDL 文本解析（正则），用于读取常量/贴图线索。
- `materials.py`
  - `ensure_preview`：确保/创建 Preview 网络。
  - `find_mdl_shader`、`is_mdl_shader`：识别 MDL 着色器。
  - `read_mdl_basecolor_const`、`copy_textures`、`connect_preview`：将 MDL 信息映射到 Preview。
  - `remove_material_mdl_outputs`、`remove_all_mdl_shaders`：清理 MDL 相关节点与输出。
  - `verify_no_mdl`：校验导出只含 Preview 节点。
- `references.py`
  - `_collect_asset_paths(stage)`：扫描并收集 sublayers、references、payloads、variants、clips 的路径。
  - `_rewrite_assets_in_stage(stage, mapping)`：将路径改写到对应 `_noMDL` 文件（API + 元数据回退）。
- `convert.py`
  - `_material_belongs_to_root_layer`：仅处理当前导出层上的材质。
  - `convert_and_strip_mdl_in_this_file_only`：执行材质转换与剥离。
- `processor.py`
  - `Processor.run(top_usd)`：
    1) 读取顶层 Stage，收集依赖路径；
    2) 复制顶层到 `_noMDL`；
    3) 改写顶层中的依赖指向 `_noMDL`；
    4) 对顶层进行材质转换（只限本文件）；
    5) 导出保存并校验；
    6) 递归对子文件执行同样流程（去重防循环）。

## 兼容/备用脚本
- `scripts/usd_make_preview_copies.py`: 旧入口，仍可直接运行。
- `scripts/usd_no_mdl/*`: 首轮模块化版本，逻辑与 `convert_asset/no_mdl` 一致。
