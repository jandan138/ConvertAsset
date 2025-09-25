# 概览（Overview）

Python QEM 后端在不依赖第三方库的前提下，为 USD 场景提供“仅三角网格”的减面能力。它适合小到中等规模的网格，或通过“时间上限”进行受控运行；在语义上尽可能与原生 C++ 后端对齐。

要点：
- 仅处理“活跃（Active）且 `purpose in {default, render}`”的 `UsdGeom.Mesh`；跳过 Instance Proxy 与 `proxy/guide`；
- 仅处理三角网格（`faceVertexCounts==3`），非三角将被跳过；
- 两种模式：
  - Dry-run：估算目标面数后的统计摘要，不回写；
  - Apply：计算新点位与三角拓扑，并写回 USD Stage，再可选择导出新 USD；

与实现的对应：
- 过滤逻辑见 `convert_asset/mesh/simplify.py` 中 `simplify_stage_meshes()` 的遍历部分；
- 面数统计的过滤策略一致，见 `convert_asset/mesh/faces.py` 中 `count_mesh_faces()`；
- CLI 的统一入口见 `convert_asset/cli.py` 的 `mesh-simplify` 与 `mesh-faces` 子命令。
