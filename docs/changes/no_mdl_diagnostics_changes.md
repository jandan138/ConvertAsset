# 变更记录：noMDL 诊断与宽松验证增强

## 时间
(填写提交日期)

## 背景
在实际运行中出现：大量缺失引用导致递归未覆盖全部子资产，最终虽然当前 root layer 的本地材质全部转换成功，整体仍被判定 `noMDL=False`；缺乏细粒度报告不利于定位原因。

## 目标
1. 提供结构化诊断：缺失引用 / root layer 残留 / 外部残留。  
2. 可配置严格度：允许在资源不完整条件下生成临时合格文件。  
3. 保持原核心转换逻辑（材质建网、MDL 删除）不被修改，向后兼容 `verify_no_mdl`。  

## 新增 / 修改内容
| 文件 | 变更 | 说明 |
|------|------|------|
| `convert_asset/no_mdl/config.py` | 新增诊断与验证相关开关 | `PRINT_DIAGNOSTICS`, `STRICT_VERIFY`, `IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN`, `TRY_OVERRIDE_EXTERNAL_MATERIALS` |
| `convert_asset/no_mdl/diagnostics.py` | 新文件 | 收集缺失引用、分析 MDL 残留归属（root vs external） |
| `convert_asset/no_mdl/materials.py` | 新增 `verify_no_mdl_report` | 结构化报告函数，不影响原 `verify_no_mdl` |
| `convert_asset/no_mdl/processor.py` | 集成诊断逻辑 | 缺失引用筛选、调用报告、基于配置决定最终成功判定，扩展日志格式 |
| `docs/troubleshooting/no_mdl_failure_analysis.md` | 新文档 | 排查指南与配置说明 |
| `docs/changes/no_mdl_diagnostics_changes.md` | 新文档 | 本变更记录 |

## 关键逻辑概述
1. 递归阶段收集子 USD 路径时，如文件不存在 → 记录到 `missing_children`，不进入递归。  
2. 转换完成后：
   - 使用 `verify_no_mdl` 做基础快速判断。
   - 使用 `verify_no_mdl_report` 收集残留明细（Shader / Material outputs）。
   - 使用 `analyze_mdl` 再区分 root 拥有与 external。  
3. 根据配置：
   - `STRICT_VERIFY=True` → 任意残留失败；除非同时 `IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN=True` 且 root 干净且存在缺失引用。  
   - `STRICT_VERIFY=False` → root 干净即可成功（外部残留发 WARNING）。

## 结果输出格式变化
示例：
```
[DIAG] missing_children= 5
    - /path/missing_a.usd
[DIAG] mdl_report ok= False shaders= 12 mat_outputs= 7
[DIAG] root_owned shaders= 0 mat_outputs= 0
[DIAG] external shaders= 12 mat_outputs= 7
[DONE] scene.usd -> scene_noMDL.usd | materials processed: 3/3, noMDL=True (reason=strict-ignore-missing-external)
```

`reason` 字段取值：
- `strict-pass`：严格模式下完全干净。
- `non-strict-root-clean`：非严格模式放宽，root 干净，外部残留忽略。
- `strict-ignore-missing-external`：严格模式 + 缺失引用放宽策略。

## 向后兼容性
- 原 `verify_no_mdl(stage)` 未被移除；脚本/调用链若仅依赖布尔返回无需修改。
- 默认配置保持严格行为（与旧版本判断一致）。

## 回退方式
- 将配置恢复为：`STRICT_VERIFY=True`, `IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN=False`, `PRINT_DIAGNOSTICS=False` 即接近旧行为。
- 或 Git 回滚至引入 diagnostics 前的提交。

## 下一步潜在扩展（未实现）
- `TRY_OVERRIDE_EXTERNAL_MATERIALS=True` 时，对 external Material 自动创建本层 override，移除其 MDL 输出。
- 输出 JSON 形式的诊断摘要，方便集成 CI 统计。
- 添加单元测试覆盖典型场景（缺失引用 / 仅外部残留 / root 残留）。

---
(Generated change log)
