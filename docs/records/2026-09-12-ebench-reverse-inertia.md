# 2026-09-12 EBench 原几何／加宽惯性互补变体

为 EEOS 的几何×惯性诊断补齐另一条件，复用已有惯性匹配脚本，以原 control 为几何
目标、wide 为惯性参考，没有修改生产者代码或历史资产。

产物：`outputs/ebench_spoon_reverse_inertia_20260912_r1/native_control_wide_inertia.usda`。
SHA-256：`d9db6457bc2ea7545e3c159cf131e14c6f88f41019f0e91d4c8b14895bdee14b`。
静态比较确认只改变 COM 与对角惯性；几何、材料连接和目标位姿保持不变。
同目录 JSON 保留两个来源和产物哈希。

EEOS 随后完成新条件的运行时读回，质量、COM 与惯性矩阵匹配 wide 参考，正在执行
固定动作回放。回放随后完成，在 1000 步窗口内没有达到勺子目标；不作更长窗口判断。
读回及结果证据位于其 `outputs/ebench_evolution/reverse_inertia_sequence_20260912_r1/`。
参数匹配不代表完整交互资格或任务成功；本资产仍是来源绑定的研究 overlay。
本次不改变通用规范，来源与适用范围沿用前一惯性匹配记录。修改尚未提交。
