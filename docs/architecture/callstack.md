# 调用链与执行细节（Callstack & Details）

本文按“从命令行输入到最终输出”的顺序，逐步标注进入的文件与函数、关键变量与数据形态，以及每一步的作用和出口。

> 约定：`->` 表示函数调用；`[file]` 表示所属文件；`Stage` 指 pxr.Usd.Stage；`Layer` 指 pxr.Sdf.Layer。

## 1. 命令行入口
- 命令：
  - `/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py <src.usd>`
  - 省略子命令时，CLI 默认 `no-mdl`
- 进入：[main.py]
  - 顶层只做委托：`from convert_asset.cli import main as cli_main`，然后 `cli_main(sys.argv[1:])`

## 2. CLI 解析与分发
- 文件：[convert_asset/cli.py]
- 函数：`main(argv)`
  1) 构建 `argparse.ArgumentParser`
  2) 添加子命令 `no-mdl`
  3) 若未指定子命令，重写 argv 为 `no-mdl` 并重新解析
  4) 路由到 `no-mdl` 分支：
     - 读取 `args.src`
     - 规范化路径：`_to_posix(args.src)`（[no_mdl/path_utils.py]）
     - 实例化处理器：`proc = Processor()`（[no_mdl/processor.py]）
     - 执行：`out = proc.process(src)`

## 3. 递归处理器 Processor
- 文件：[convert_asset/no_mdl/processor.py]
- 类：`Processor`
  - 字段：
    - `done: dict[str,str]`：缓存“已处理源 -> 目标 _noMDL”映射，避免重复
    - `in_stack: set[str]`：检测循环引用

### 3.1 Processor.process(src_usd_abs)
- 规范化绝对路径：`src_usd_abs = _to_posix(os.path.abspath(src_usd_abs))`
- 防重/防循环：查 `done` 与 `in_stack`
- 打开 Stage：`stage = Usd.Stage.Open(src_usd_abs)`
- 收集依赖：`deps = _collect_asset_paths(stage)`（[no_mdl/references.py]）
  - 作用：遍历 root layer 的 sublayers、全场景 prim 的 references/payloads、variants 内的 refs/payloads、以及 clips，产出条目列表。
  - 每个条目形态：`(kind, holder, layer_dir, assetPath, prim_path, extra)`
    - `kind: str`：`sublayer|reference|payload|variant_ref|variant_payload|clip_asset|clip_manifest`
    - `holder`：定位归属，例如 `("prim", "/World/Geom")` 或 `("rootLayer", None)` 或 `(<primPath>, <vsName>, <variant>)`
    - `layer_dir: str`：当前 layer 的目录，用于解析相对路径
    - `assetPath: str`：待改写的资产路径（可能是相对路径）
    - `prim_path: Sdf.Path|None`：条目所在的 prim 路径
    - `extra`：ListOp 项或关键字，供回写参考
- 解析子路径为绝对：
  - `ldir = dirname(stage.GetRootLayer().realPath or identifier)`
  - 对 `deps` 遍历：`abs_child = _resolve(ldir, assetPath)`（[no_mdl/path_utils.py]）
  - 仅挑 USD 扩展：`.usd|.usda|.usdc|.usdz`
  - 汇总为 `child_abs_paths: set[str]`

### 3.2 先处理子节点并建立映射
- 初始化 `mapping: dict[str,str]`
- 对 `child_abs_paths` 排序后逐个：
  - `dst_c = self.process(c)` 递归处理子文件
  - `mapping[c] = dst_c` 记录“源 -> 目标”映射

### 3.3 复制当前 root layer 到 _noMDL 文件
- 计算目标路径：`dst_usd_abs = _sibling_noMDL_path(src_usd_abs)`（[no_mdl/path_utils.py]）
  - 若禁止覆盖且已存在：在后缀追加时间戳
- 导出 root layer 骨架：
  - `root_layer = stage.GetRootLayer()`
  - `root_layer.Export(dst_usd_abs)`
- 打开新 Stage：`dst_stage = Usd.Stage.Open(dst_usd_abs)`

### 3.4 在当前文件上改写“指向关系”
- 调用：`_rewrite_assets_in_stage(dst_stage, mapping)`（[no_mdl/references.py]）
  - sublayers：替换 `layer.subLayerPaths` 中的路径为相对 `ldir` 的 `_noMDL` 路径
  - references：读 `prim.GetMetadata("references")` ListOp，改写项的 `assetPath`，优先 API (`ClearReferences/AddReference`)，失败回退 `SetMetadata`
  - payloads：同上（`GetMetadata("payloads")` 或 `"payload"`）
  - variants：进入每个变体编辑上下文改写内层 references/payloads
  - clips：改写 `clips.clipAssetPaths` 和 `manifestAssetPath`

### 3.5 仅在当前文件执行材质转换
- 调用：`stats = convert_and_strip_mdl_in_this_file_only(dst_stage)`（[no_mdl/convert.py]）
  - 锁定材质根：`MATERIAL_ROOT_HINTS` 不存在则全局扫描
  - 仅处理“定义于当前导出层”的材质：`_material_belongs_to_root_layer`
  - 对每个发现的 MDL 材质：
    - `ensure_preview`（[no_mdl/materials.py]）：创建 `UsdPreviewSurface`、`UsdUVTexture`、`UsdPrimvarReader_float2`
    - `copy_textures`：
      - 优先从 MDL shader 输入 pin 读取贴图资产
      - 不足则尝试解析 `.mdl` 文本找线索
      - 处理粗糙度反转（gloss->roughness）
    - `connect_preview`：连接 baseColor/roughness/metallic/normal 到预览网络，必要时使用常量
  - 删除所有 MDL 输出/节点：`remove_material_mdl_outputs`、`remove_all_mdl_shaders`
  - 返回统计：`{"total":N, "mdl":M, "preview":K}`

### 3.6 兜底默认 Prim 并保存
- 若没有 `defaultPrim`：
  - 优先设置 `/World`；否则取任意根 prim
- 保存：`dst_stage.GetRootLayer().Export(dst_usd_abs)`
- 校验：`ok = verify_no_mdl(Usd.Stage.Open(dst_usd_abs))`
- 日志：`[DONE] src -> dst | materials processed: K/N, noMDL=ok`
- 记入 `self.done[src_usd_abs] = dst_usd_abs`，并从 `in_stack` 移除
- 返回 `dst_usd_abs`

## 4. 递归如何保证“不 flatten”
- 每个文件各自导出为一个 `_noMDL`，不把子文件内容内联到当前文件
- 仅改写“指向关系”的目标路径，组合类型不变（reference/payload/subLayer/variant/clip 原样保留）
- 子文件在它们各自步骤中转换材质与剥离 MDL，最终整棵树在打开顶层 `_noMDL` 时由 USD 组合器按原逻辑装配

## 5. 关键函数一览（按出现顺序）
- [main.py] `cli_main(argv)`
- [convert_asset/cli.py] `main(argv)`
- [convert_asset/no_mdl/processor.py] `Processor.process(src)`
- [convert_asset/no_mdl/references.py] `_collect_asset_paths(stage)`
- [convert_asset/no_mdl/path_utils.py] `_resolve(ldir, assetPath)`、`_sibling_noMDL_path(src)`
- [convert_asset/no_mdl/processor.py] `root_layer.Export(dst)`、`Usd.Stage.Open(dst)`
- [convert_asset/no_mdl/references.py] `_rewrite_assets_in_stage(stage, mapping)`
- [convert_asset/no_mdl/convert.py] `convert_and_strip_mdl_in_this_file_only(stage)`
  - [convert_asset/no_mdl/materials.py] `ensure_preview` / `copy_textures` / `connect_preview` / `remove_*`
- [convert_asset/no_mdl/materials.py] `verify_no_mdl(stage)`

## 6. 典型数据快照
- `mapping_src2dst: dict[str,str]` 示例：
  ```
  {
    "/path/A.usd": "/path/A_noMDL.usd",
    "/path/B.usd": "/path/B_noMDL.usd"
  }
  ```
- `deps` 条目示例：
  ```
  (
    "reference",
    ("prim", "/World/Props/Chair"),
    "/path/to/root/dir",
    "../models/chair.usd",
    Sdf.Path("/World/Props/Chair"),
    <Sdf.Reference ...>
  )
  ```

## 7. 错误处理与兼容性
- 打开 Stage 失败：打印错误并跳过该节点
- 旧版 USD 无 `GetReferences()` 读取：改用 `prim.GetMetadata("references")`/`"payloads"` 读取 ListOp
- 写入优先 API（`Clear*/Add*`），失败回退 `SetMetadata`
- 递归中检测循环：`in_stack` 防止环
