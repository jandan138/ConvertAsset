# 变更记录：材质修复 + 全量外部 MDL 抑制 + 严格 PASS & 审计/降噪

日期：2025-09-23

## 背景与动机
在此前版本中：
- root layer 自有 MDL Shader/Material 输出均已转换为 UsdPreviewSurface，但严格验证仍失败，原因是外部（referenced / payload / sublayer / variant）MDL Shader 统计为正，且 RemovePrim 对无本地 primSpec 的外部定义不生效。
- 部分外部材质未生成本地 Preview 网络，显示为灰材质，影响视觉确认。
- 控制台诊断行海量（逐属性 blocked/forced 输出），缺乏结构化审计数据，不利于回归与 CI 集成。

## 目标
1. 使严格模式 (`STRICT_VERIFY`) 在不打平（保持 references/payloads/variants/clips）的前提下 PASS。
2. 解决灰材质：保证所有参与渲染的 Material 均有可用 `outputs:surface`（UsdPreviewSurface）。
3. 降噪并引入结构化审计：最小化必要控制台输出，生成可机器解析的 JSON 供后续对比与监控。

## 核心方案
| 问题 | 方案 | 关键点 |
|------|------|--------|
| 外部 MDL Shader 无法删除 | override + SetActive(False) 抑制 | 逻辑删除，不破坏组合；inactive 在验证遍历中被忽略 |
| 灰材质 (缺失 surface) | 自动补建 PreviewSurface 网络 | 常量+贴图节点；若已存在则跳过 |
| 噪声大 | 日志等级 + 审计 JSON | 0/1/2 级别；JSON 聚合 stats / timings / 样本 |
| 回归难 | statsHash | 选定统计字段序列化哈希，快速比较是否变化 |

## 新/修改配置
- `PRINT_DIAGNOSTICS_LEVEL` (int): 0=最简, 1=摘要, 2=详细。
- `WRITE_AUDIT_JSON` (bool): 输出 `*_noMDL.audit.json`。
- `AUDIT_WITH_TIMESTAMP` (bool): 审计文件名加时间戳避免覆盖。
- `DIAG_SAMPLE_LIMIT` (int): 样本（forced block / 抑制列表）最大输出数。
- `FORCED_BLOCKED_WARN_THRESHOLD` (int): 预留阈值，尚未启用逻辑。

## 主要代码改动
### `convert_asset/no_mdl/convert.py`
- 外部 MDL Shader 处理：检测 root layer 非拥有 → `stage.OverridePrim(path)` → `prim.SetActive(False)`。
- 统计：`external_mdl_shaders_clean_deleted`, `external_mdl_shaders_final_active`。

### `convert_asset/no_mdl/materials.py`
- `remove_material_mdl_outputs` 返回强制 blocked 样本；输出受日志等级控制。
- `ensure_surface_output` 自动补齐缺失 surface；添加 DIAG gating。

### `convert_asset/no_mdl/processor.py`
- 计时：`open/collect/convert/export/final_export/verify`。
- 组装 `audit`：`resultStrict`, `reason`, `stats`, `timings`, `missingChildren`, `report`, `statsHash`。
- 不同日志等级下调整 DONE 行展示字段数量。

### `convert_asset/no_mdl/config.py`
- 集中新增开关；`PRINT_DIAGNOSTICS` 与旧逻辑兼容但由 LEVEL 推导。

## 指标示例
| 指标 | 数值 (示例) |
|------|-------------|
| root-owned MDL Shaders 转换 | 6773 |
| 外部材质生成预览 override | 4460 |
| 外部 MDL Shaders 抑制后活动数 | 0 (由 2311 -> 0) |
| 自动补齐 surface 输出 | 378 |
| 强制 blocked 属性总数 | 7151 (仅采样输出) |
| 严格结果 | strict-pass |

## 示例 DONE 行
```
[DONE] scene.usd -> scene_noMDL.usd | materialsConverted=6773 externalSuppressed=2311 finalActiveExternal=0 forcedBlocked=7151 strict-pass
```

## 示例审计 JSON 片段
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
  "timings": {"open":0.42,"collect":1.73,"convert":9.58,"export":0.31,"final_export":0.09,"verify":0.27},
  "statsHash": "c5c4e7d2"
}
```

## 技术说明
1. Override+Inactive：避免破坏路径稳定性，后续可恢复/重装配；与 flatten 方案相比对下游差异最小。
2. 验证过滤 Inactive：借助 USD 原生遍历 semantics，无需额外过滤表。
3. statsHash 设计：对核心 stats dict 进行字段顺序稳定化（排序键）后序列化 + 哈希，忽略与统计无关的临时字段。
4. 审计与日志解耦：控制台适合人工快速确认；JSON 适合 CI (diff/hash) 与数据看板。

## 未完成 / 后续计划
| 类别 | 描述 |
|------|------|
| Warning 策略 | 基于 `FORCED_BLOCKED_WARN_THRESHOLD` 输出 WARNING 或失败码 |
| Diff 工具 | 比较两份审计 JSON，列出指标增减与哈希变化原因 |
| 纹理统计 | 统计成功映射/失败纹理数、唯一纹理文件数 |
| Override 分层 | 分别统计 材质预览 override 与 shader 抑制 override 数量 |
| Exit Code | 定义多级退出码：0=pass,1=fail,10=degraded |

## 回滚指引
- 关闭抑制：移除/回退 override + inactive 逻辑提交。
- 关闭审计/降噪：`WRITE_AUDIT_JSON=False`, `PRINT_DIAGNOSTICS_LEVEL=0`。

## 价值总结
本次升级实现：
- 严格通过：外部残留计数归零，不牺牲组合结构。
- 视觉一致：无灰材质，均有 PreviewSurface。
- 可观测：指标、计时、采样、哈希具备回归对比基础。
- 可扩展：保留阈值与 diff 钩子，后续质量红线易于落地。

---
(Generated change log for 2025-09-23)
