# 设计思路（Design）

## 目标
- 为包含 MDL 材质的 USD 资产生成基于 UsdPreviewSurface 的“无 MDL”版本。
- 保留引用（references）、载荷（payloads）、variants、clips 等装配结构，不做 flatten。
- 递归处理依赖：为每个被引用的 USD 文件生成相邻的 `_noMDL` 副本，并重定向到这些副本。
- 输出文件可单独打开，内部仅包含 UsdPreviewSurface/UsdUVTexture/UsdPrimvarReader 等 Preview 节点，无 MDL。

## 非目标
- 不求 1:1 视觉还原（如复杂 MDL 逻辑、程序化材质），而是生成合理的 Preview 近似。
- 不做烘焙（bake）贴图生成（除已支持的基础参数处理）。

## 关键设计
- 分层/模块化：`convert_asset/no_mdl/` 内拆分为 config、path_utils、mdl_parse、materials、references、convert、processor。
- 不平铺（no flatten）：保留层级、sublayers、variants、clips；只改写路径指向 `_noMDL` 文件。
- 仅在“当前导出层”转换材质：避免修改子文件内容；子文件由递归处理各自转换。
- 兼容旧版 USD：读取 ListOp 使用 `prim.GetMetadata("references")`/`"payloads"`；写入优先 API（Clear/Add），失败回退 SetMetadata。
- 输出命名：同目录同名加后缀 `_noMDL`，若存在且不允许覆盖则加时间戳。

## 约束与兼容性
- 运行时环境：Isaac Sim Python（包含 `pxr` USD）。
- MDL 解析：轻量正则与常用 key 读取（如 baseColor 常量）；缺失贴图则降级使用常量或默认值。
- 默认 Preview 网络：`UsdPreviewSurface`（baseColor/metallic/roughness/normal 支持），`UsdUVTexture`，`UsdPrimvarReader_float2`。

## 成功判定
- 导出文件验证只含 Preview 节点（noMDL=True）。
- 统计日志：`materials processed: X/Y, noMDL=True`。
