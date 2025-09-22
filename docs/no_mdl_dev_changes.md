# no-MDL Conversion Development Change Log

本文件记录每次对 *no-flatten* MDL->UsdPreviewSurface 转换管线的增量修改（包括失败/回滚尝试），用于审计与问题追踪。按时间倒序追加；所有条目保持精炼（~200 中文字或等价）。

## 2025-09-22: 诊断对齐 forced block 标记 + 初始日志文件建立
- 新建本日志文件，补全既往修改总览：脚本已模块化 (config/materials/processor/diagnostics/references/mdl_parse/path_utils)，支持在生成兄弟 *_noMDL.usd* 文件时保持 references/payloads/variants/clips 结构不打平。
- 材质转换：构建 UsdPreviewSurface + 纹理节点 + Gloss->Roughness 反转；仅处理本 root layer 拥有的 MDL（implementationSource=sourceAsset 且扩展 .mdl 或 info:mdl:* 标记）。
- MDL 输出移除策略多轮叠加：disconnect -> RemoveProperty -> Block -> 解除实例 (BREAK_INSTANCE_FOR_MDL) -> OverridePrim -> 强制属性 spec + customData.noMDL_forced_block 兜底。
- 增强 verify_no_mdl_report：拆分本地/外部，允许外部宽松；统计 blocked（含 forced）。
- diagnostics.analyze_mdl 今日更新：识别 customData.noMDL_forced_block 为 blocked，修复此前 report 与 diagnostics 口径不一致问题；仍待区分 native 与 forced 的独立计数。
- 仍未实现：Variant 遍历清理 (CLEAN_VARIANT_MDL)、native vs forced 分离统计、STRICT_VERIFY 在仅剩 external/forced 情况的自动宽松降级。

## Backlog Quick List
1. 变体遍历与 per-variant 统计
2. blocked(native/forced) 双计数
3. 自动宽松降级策略
4. 更细粒度诊断输出（per-layer attr stack 可选采样缓存）

## 2025-09-22: 子 USD 未生成问题修复（layer_dir 解析）
- 问题：部分子 usd（例： models/.../instance.usd）未生成对应 *_noMDL 文件。
- 根因：依赖收集虽返回每条记录的 layer_dir，但 Processor 递归解析子路径时统一使用 root layer 目录，导致相对路径（相对于子 layer）指向错误位置，被忽略。
- 修复：在 `processor.process` 中按条目使用各自的 `layer_dir` 解析；若解析结果不存在再回退 root 目录并打印诊断 (`[DIAG][resolve-fallback]` / `[DIAG][resolve-miss]`)。
- 影响：应当开始为所有实际存在的 referenced/payload/sublayer/variant/clips USD 生成兄弟 *_noMDL.usd；Mapping 更完整，后续结构改写不会遗漏。
- 后续：可添加统计“递归处理的子文件数量”以及未生成原因分类（缺失路径 / 非 USD 扩展）。
