# 2026-09-12 EBench 惯性属性单项匹配

为 EEOS 区分 COM 与惯性矩阵作用，惯性匹配脚本新增可重复的 `--property` 参数，
只允许选择既有四个惯性字段；空集合、重复或未知字段会被拒绝。默认行为保持原样。
对组合结果检查仅允许所选字段变化，未选择字段、几何、材质与变换保留目标值。

产物位于 `outputs/ebench_spoon_inertia_components_20260912_r1/`：
`wide_geometry_control_com.usda` 只改 COM，`wide_geometry_control_tensor.usda`
只改对角惯性。两者分别通过真实源资产静态比较，完整来源哈希见同名 JSON 报告。
旧实现留存在 `outputs/ebench_inertia_builder_history_20260912/`；新报告增加实现哈希。

4 项相关测试通过，覆盖默认匹配及两种单项匹配的未选字段保持，Ruff 检查通过。
EEOS 随后完成两项实际参数匹配与回放：所选字段和保留字段均匹配对应参考，
两个 1000 步回放窗口均未达到勺子目标。该结果是特定动作诊断，不是完整交互资格。
未改变通用归一化算法或源资产；新增功能与文档尚未提交。
