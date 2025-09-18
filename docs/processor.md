# Processor 源码逐步解析（convert_asset/no_mdl/processor.py）

本文详细解析 `convert_asset/no_mdl/processor.py`，逐行说明其职责、数据流与关键设计点。

## 1. 文件概览
- 角色：无 MDL 转换的“调度与递归控制中心”。
- 主要职责：
  1) 打开源 USD，收集依赖（子 USD 路径）
  2) 先递归处理子文件，获得“源->目标”的映射
  3) 为当前文件生成 `_noMDL` 版本，复制 root layer 骨架
  4) 在当前文件上改写 references/payloads/subLayers/variants/clips 的目标路径
  5) 仅在当前文件做材质转换并剥离 MDL
  6) 保存、校验、记录映射，返回输出路径

## 2. 关键依赖
- `from pxr import Usd`：打开/操作 USD Stage
- `from .path_utils import _to_posix, _sibling_noMDL_path, _resolve`：路径规范、输出路径生成、相对->绝对解析
- `from .references import _collect_asset_paths, _rewrite_assets_in_stage`：依赖收集与改写
- `from .convert import convert_and_strip_mdl_in_this_file_only`：材质转换
- `from .materials import verify_no_mdl`：校验输出无 MDL

## 3. 类 Processor
- `done: dict[str, str]`：缓存“已处理源 -> 目标 _noMDL 路径”，避免重复工作
- `in_stack: set[str]`：当前递归调用栈，用于检测环状引用（防止无限递归）

## 4. 方法 Processor.process(src_usd_abs)

### 4.1 入口与去重
- 将输入规范化为绝对的 POSIX 风格路径，利于做字典 key 与日志输出：
  - `src_usd_abs = _to_posix(os.path.abspath(src_usd_abs))`
- 快速返回：若在 `done` 中，直接返回目标路径
- 环检测：若在 `in_stack` 中，打印警告并返回已知结果或源路径自身

### 4.2 打开 Stage 与收集依赖
- 打开源 Stage：`Usd.Stage.Open(src_usd_abs)`；失败则报错并返回
- 调用 `_collect_asset_paths(stage)` 获取一组依赖条目；
  - 每个条目包含持有者（root layer/某 prim/某变体）、anchor 目录、资产相对路径、以及 ListOp/关键字等“回写辅助信息”
- 将条目中的 `assetPath` 解析为绝对路径，过滤 USD 扩展，汇总为 `child_abs_paths`

### 4.3 先递归处理子节点，建立映射
- 初始化空 `mapping`
- 对 `child_abs_paths` 排序后逐个递归调用 `self.process(c)`；
  - 将返回的目标 `_noMDL` 路径记入 `mapping[c] = dst_c`

### 4.4 复制当前 root layer 到 `_noMDL` 文件
- `dst_usd_abs = _sibling_noMDL_path(src_usd_abs)`
- `root_layer.Export(dst_usd_abs)`：仅输出当前文件的 root layer 骨架（不 flatten 不内联）

### 4.5 改写当前文件中的“指向关系”
- 打开 `dst_stage = Usd.Stage.Open(dst_usd_abs)`
- 调用 `_rewrite_assets_in_stage(dst_stage, mapping)`：
  - subLayers：替换为 `_noMDL` 相对路径
  - references/payloads：读取 metadata ListOp 改写，优先使用 `Clear+Add` API，失败回写 metadata
  - variants：进入每个变体编辑上下文改写内层 refs/payloads
  - clips：改写 `clipAssetPaths` 与 `manifestAssetPath`

### 4.6 当前文件内进行材质转换与剥离
- 调用 `convert_and_strip_mdl_in_this_file_only(dst_stage)`：
  - 仅处理当前导出层定义的材质
  - MDL → UsdPreviewSurface 网络，连接贴图/常量
  - 移除所有 MDL 输出与 Shader 节点
- 兜底 defaultPrim：若没有默认 prim，则优先 `/World`，否则取任意根 prim
- 导出保存：`dst_stage.GetRootLayer().Export(dst_usd_abs)`
- 验证无 MDL：`verify_no_mdl(Usd.Stage.Open(dst_usd_abs))`
- 打印统计并登记 `self.done[src_usd_abs] = dst_usd_abs`

## 5. 为什么这保证“不 flatten”
- 每个文件只复制自己 root layer 到新文件；从不把子文件内容写进来
- 只改写“指向关系”的目标路径；组合类型（reference/payload/sublayer/variant/clip）保持不变
- 子文件在自身步骤中转换并输出 `_noMDL`，顶层统一由 USD 组合器进行装配

## 6. 关键边界与错误处理
- 打开失败、路径解析失败：打印警告/错误，尽量不中断整个批处理
- 环检测：通过 `in_stack` 防止死循环
- 兼容旧版 USD：依赖收集读取 metadata ListOp；写入优先 API 回退 metadata
- defaultPrim 兜底：避免某些查看器/工具打开时没有默认 prim 导致空白

## 7. 输出与状态
- 返回值：当前源文件对应的 `_noMDL` 绝对路径
- 辅助状态：
  - `self.done`：可用于最终 SUMMARY 打印所有“源->目标”映射
  - 日志包含：`[DONE] <src> -> <dst> | materials processed: <preview>/<total>, noMDL=<bool>`
