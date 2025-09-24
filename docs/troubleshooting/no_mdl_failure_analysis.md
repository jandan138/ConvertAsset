# noMDL 转换失败诊断与排查指南

## 1. 典型现象
- 日志出现大量 `Could not open asset ...` / `cannot open:` 警告。
- 统计显示 `materials processed: X/X` 但最终 `noMDL=False`。
- 转换输出文件结构仍引用原始含 MDL 的子资产。

## 2. 根本原因分类
| 分类 | 描述 | 解决方向 |
|------|------|----------|
| 缺失引用 (Missing Children) | 子 USD 文件在磁盘上不存在或路径错误，递归无法进入 | 修复路径/补齐资源；或使用宽松判定（见下） |
| 外部残留 MDL | 子文件未生成 *_noMDL 版本，原始 MDL Shader / outputs:surface:mdl 仍暴露 | 先解决缺失引用；若资源暂不可得，可在非严格模式下产出临时文件 |
| 只读/权限问题 | 删除 MDL 输出属性或 Shader 失败（只读层） | 确认写层权限；在自己的可写层做 override 删除 |
| 真实转换缺漏 | 逻辑 Bug 导致 root layer 自有材质未清理干净 | 打开 PRINT_DIAGNOSTICS，检查 root_owned 列表定位 |

## 3. 新增配置开关说明 (`convert_asset/no_mdl/config.py`)
- `PRINT_DIAGNOSTICS` (默认 True): 输出更详细的 MDL 残留分类与缺失引用列表。
- `STRICT_VERIFY` (默认 True): 任意 MDL 残留（包括外部）都算失败。
- `IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN` (默认 False): 严格模式下，如果存在缺失子文件且 root layer 自己干净，则忽略外部残留判定成功。
- `TRY_OVERRIDE_EXTERNAL_MATERIALS` (默认 False): 预留；未来用于对外部材质做本层 override 移除 MDL（高风险）。

### 宽松判定策略对比
| 场景 | STRICT_VERIFY | IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN | 结果 |
|------|---------------|------------------------------------------|------|
| root layer 干净，外部残留，无缺失引用 | True | False | 失败 |
| root layer 干净，外部残留，有缺失引用 | True | True | 成功 (reason=strict-ignore-missing-external) |
| root layer 干净，外部残留 | False | 任意 | 成功 (reason=non-strict-root-clean) |
| root layer 仍有 MDL | 任意 | 任意 | 失败 |

## 4. 日志关键行解读
- `[DIAG] missing_children= N` 列出递归前发现的不可打开文件。
- `[DIAG] mdl_report ok=... shaders= S mat_outputs= M` 基础场景内残留数。
- `[DIAG] root_owned shaders=R mat_outputs=Q` 表示仍需在当前 root layer 清理的数量（不应>0）。
- `[DIAG] external shaders=E mat_outputs=F` 来自外部（未递归子文件）的残留分类。
- `[DONE] ... noMDL=BOOL (reason=...)` 最终判定与放宽原因。

## 5. 处理步骤推荐顺序
1. 打开 `PRINT_DIAGNOSTICS=True` 运行一次，收集 `missing_children` 列表。  
2. 修复或补齐缺失文件，确保所有引用可打开。  
3. 再次运行，若 `root_owned` 列表仍非空，聚焦这些 prim（真正逻辑问题或权限问题）。  
4. 如果短期无法补齐引用但需生成预览：
   - 方案 A：`STRICT_VERIFY=False` （整体宽松）。
   - 方案 B：保持 `STRICT_VERIFY=True` 但设 `IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN=True` 仅对缺失引用外部放宽。
5. 最终期望：所有缺失引用消失；`root_owned_*` 与 `external_*` 统计都为 0；`reason=strict-pass`。

## 6. 何时谨慎使用 override 外部材质
暂未实装自动 override；若未来启用：
- 仅在外部共享资源不计划回写、且渲染链路要求强行消除 MDL 时考虑。
- 风险：覆盖层可能改变其他消费方的期望表现；务必保留原文件与变更日志。

## 7. FAQ
Q: 日志显示 `materials processed: 1/1` 但仍失败？  
A: 只说明当前 root layer 里唯一的本地 Material 已转换；外部或缺失子文件残留没有被处理。

Q: 为什么有时没有 `missing_children` 却仍失败？  
A: 所有引用都能打开 → 外部残留说明对应子文件未被映射替换（可能之前运行过旧版本、或写权限/路径映射问题）。

Q: 如何快速列出仍含 MDL 的 prim？  
A: 查看 `[DIAG] mdl_report` 输出的 `shaders=` 和 `mat_outputs=`；若需要更详细可扩展 `diagnostics.analyze_mdl`。

## 8. 回退策略
若不需要诊断增强：
- 将 `STRICT_VERIFY=True`, `IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN=False`, `PRINT_DIAGNOSTICS=False`。
- 或回退到引入 diagnostics 之前的提交版本。

---
(Generated diagnostics guide)
