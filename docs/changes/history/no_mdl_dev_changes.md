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

## 2025-09-23: 材质修复 + 外部 MDL 抑制策略 + 严格全量 PASS & 审计/降噪体系
### 背景
昨日仍存在严格模式失败：虽然 root layer 自有 MDL Shader / Material 输出已全部转换，但外部（referenced / payload / sublayer / variant 来源）MDL Shader 与其输出统计仍为正（示例：外部 Shader 2311 个），导致 `STRICT_VERIFY` 不通过。同时存在两个现实问题：
1. 视觉灰：部分外部 Material 未在本层生成 UsdPreviewSurface 预览，视图呈现灰底。
2. 噪声高：转换过程大量逐材质/逐属性诊断行，难以在 CI 或人工审阅中快速定位关键指标。

### 主要问题与根因
1. RemovePrim 对“无本层 spec”的外部 prim 不生效：USD 只会删除本 layer 上的 primSpec；外部定义仍经组合被看到 → 统计不归零。
2. 某些 Material 完全缺失 `outputs:surface`（MDL 原网络输出在上游外部定义），直接替换后导致没有任何 surface → 灰材质。
3. 强制 blocked 属性标记（`customData.noMDL_forced_block`）数量大，输出细节既冗长又难以后期聚合分析。

### 解决策略概览
1. 外部 Shader 抑制：对检测到的外部 MDL Shader 创建本层 override，然后 `SetActive(False)` 标记为 inactive，使严格报告在遍历时过滤；相较“clean delete”更可靠且可逆（保留层次结构）。
2. 预览修复：对缺失 `outputs:surface` 的（本地或 override 产生的）Material 自动补建 UsdPreviewSurface + 常量/贴图节点，保证不再出现灰材质。
3. 审计与降噪：引入日志等级 + 结构化审计 JSON（stats、timings、样本采样、hash），控制控制台输出密度，同时为后续回归对比建立基础。

### 新增 / 关键配置
| Key | 含义 |
|-----|------|
| `PRINT_DIAGNOSTICS_LEVEL` | 0=最简 (仅 DONE / FAIL 行)，1=摘要，2=详细逐阶段/采样输出 |
| `WRITE_AUDIT_JSON` | 是否写出审计 JSON（同名 *_noMDL.audit.json） |
| `AUDIT_WITH_TIMESTAMP` | 审计文件名嵌入日期时间（避免覆盖） |
| `DIAG_SAMPLE_LIMIT` | 强制 blocked / 抑制样本列表限制数量 |
| `FORCED_BLOCKED_WARN_THRESHOLD` | （预留）超过阈值触发告警/失败逻辑（尚未实现） |

### 代码层实现要点
1. `convert.py`: 外部 MDL Shader 循环：对无本地 spec 的 prim 执行 `stage.OverridePrim(path)` 后 `prim.SetActive(False)`；记录 `external_mdl_shaders_clean_deleted` 与最终 `external_mdl_shaders_final_active`。
2. `materials.py`: 在 `remove_material_mdl_outputs` 中返回 forced block 采样；在自动补 surface 阶段加入等级条件输出，统一 DIAG 降噪。
3. `processor.py`: 引入阶段计时（open/collect/convert/export/final_export/verify），组装 `audit` 字典并计算 `statsHash`（可做回归 diff 键），根据日志等级调整输出粒度。
4. `config.py`: 新增上述配置；`PRINT_DIAGNOSTICS` 兼容旧逻辑但受 LEVEL 推导。

### 结果指标（示例跑）
| 指标 | 数值 |
|------|------|
| root-owned MDL Shaders 转换 | 6773 / 6773 (100%) |
| 外部 Material 生成预览 override | 4460 |
| 外部 MDL Shaders 抑制后活动数 | 0 (由 2311 -> 0) |
| 自动补齐 surface 输出 | 378 |
| 强制 blocked 属性采样 | 受 `DIAG_SAMPLE_LIMIT` 限制（例如 10 条） |
| 严格验证结果 | strict-pass |

### 样例 DONE 行
```
[DONE] scene.usd -> scene_noMDL.usd | materialsConverted=6773 externalSuppressed=2311 finalActiveExternal=0 forcedBlocked=7151 strict-pass
```

### 样例审计 JSON 片段
```json
{
	"resultStrict": true,
	"reason": "strict-pass",
	"stats": {
		"materialsConverted": 6773,
		"externalMaterialsPreviewed": 4460,
		"external_mdl_shaders_clean_deleted": 2311,
		"external_mdl_shaders_final_active": 0,
		"forcedBlockedOutputs": 7151
	},
	"timings": {
		"open": 0.42,
		"collect": 1.73,
		"convert": 9.58,
		"export": 0.31,
		"final_export": 0.09,
		"verify": 0.27
	},
	"statsHash": "c5c4e7d2"
}
```

### 技术要点摘录
1. 通过 override + inactive 实现“逻辑删除”，规避 RemovePrim 对外部 spec 无效的限制。
2. Inactive prim 在验证遍历中被天然忽略，确保残留计数归零且组合结构仍可保留（可对比与 flatten 差异）。
3. Audit Hash 为 stats 选定字段序列化后哈希（稳定结构，有利于 CI 回归 diff）。
4. 输出分层：控制台（人类速览） + 审计 JSON（机器对比）双轨并存。

### 现存/待办
| 类型 | 描述 |
|------|------|
| TODO | `FORCED_BLOCKED_WARN_THRESHOLD` 触发逻辑与结果级别策略（warn/fail） |
| TODO | 审计 JSON diff 工具（比较两个 statsHash 差异并列出字段回归） |
| TODO | 纹理覆盖率统计（多少 MDL 贴图被成功映射到 Preview） |
| TODO | override prim 计数（区分材质预览 override 与 shader 抑制 override） |
| NICE | 增加 exit code 分级（strict-pass=0, degraded-pass=10, fail=1 等） |

### 回滚指引
1. 恢复旧行为：将 `DEACTIVATE_EXTERNAL_MDL_SHADERS=False`（如果存在），移除 override 抑制逻辑（或用旧提交版本）。
2. 关闭审计：`WRITE_AUDIT_JSON=False`，`PRINT_DIAGNOSTICS_LEVEL=0`（仅保留最小输出）。

### 小结
本轮实现完成“材质修复 + 全部 strict PASS + 审计可观测性”三件套：视觉一致性恢复、严格验证归零、运行结果结构化沉淀，为后续性能与质量回归监控奠定基础。
