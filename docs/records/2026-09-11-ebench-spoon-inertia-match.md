# 2026-09-11 EBench 勺子惯性匹配诊断变体

## 背景与发现

EEOS 的控制动作在加宽几何回放中成功，但当前加宽资产同时改变了重心和惯性。
检查 `outputs/ebench_spoon_intervention_20260911_r2/native_{control,wide}_overlay.usda`
发现质量均为约 0.1，显式 `physics:centerOfMass` 的 X 分量从 0.00036004 变为
0.00192147；`physics:diagonalInertia` 的 Y/Z 分量也不同。这些为 USD 作者值，
不是运行时 PhysX 读回，不在此推断有效单位缩放或实际因果效应。

随后核实属性 customData 中的 `aan.provenance`：重心由 `local_bbox_center_v1`、
惯性由 `bbox_inertia_from_mass_v1` 生成。对应实现是
`convert_asset/asset_application_normalizer/physics_checks.py` 的
`_author_invalid_mass_properties`。原 Blender 文件没有这些显式有效值，差异出现在
资产规范化阶段；后续诊断应以最终交付资产为准。

## 实现与产物

新增 `scripts/build_ebench_inertia_matched_spoon.py`。保持目标加宽 overlay 为 sublayer，
从控制源复制质量、重心、对角惯性、主轴姿态。对组合后的全部原有 prim 检查属性值、
schema、材质连接与关系，仅允许目标刚体四项惯性属性不同。拒绝覆盖已有产物。

产物：`outputs/ebench_spoon_inertia_match_20260911_r3/native_wide_control_inertia.usda`。
SHA-256：`3f650440e6ddcda04792d0cd2e540d2bf02ec8fdf4b864c5f4143c714c4d9afb`。
同目录 JSON 报告记录两个源哈希和精确属性差异；实际仅重心与对角惯性改变。
这是依赖源资产的诊断 overlay，尚非独立可移植资产包。

首次两次尝试因 CopySpec 目标层缺少 prim spec 失败；r1/r2 保留为未成功产物。
改为显式 `Sdf.CreatePrimInLayer` 后 r3 静态验证通过，只有 r3 可供后续编译。

## 验证与交接

使用 EEOS 项目 Python 运行 `tests/test_ebench_inertia_matched_spoon.py` 与
`tests/test_ebench_spoon_intervention.py`，4 项通过；新增脚本和测试的 Ruff 检查通过。
真实源资产的组合比较也通过，证明此次属性修改未同时替换目标网格。

运行时读回、冷启动、接触行为与同动作回放尚未执行，不宣称物理等价或机制确认。
交接 EEOS：当前 GPU 重复队列结束后读回控制、加宽和匹配变体；若匹配生效，再比较
相同控制动作在后两者中的回放结果。所有诊断均不计入在线模型成功率。
本次修改与文档尚未提交；不表示整个跨仓库研究任务完成。
