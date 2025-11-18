# 性能与限制（Python vs C++ 后端）

## Python QEM 后端

优点：
- 实现完全在 `simplify.py` 中，可读性与可调试性好；
- 无需额外编译或系统依赖，适合快速验证与中小规模资产。

限制：
- 运行时完全在 Python 层，单线程，受 GIL 与解释器性能限制；
- 大规模资产或极高面数 Mesh 上，可能需要较大的 `time_limit` 或更保守的 `ratio`。

## C++ QEM 后端（可执行 `cpp`）

优点：
- 针对几何减面，C++ 可执行通常比 Python 后端更快；
- 使用 OBJ 作为中间格式，便于调试与外部工具接入。

限制：
- 仅处理几何，不处理 UV；
- 长流程中频繁写读临时 OBJ，I/O 可能成为瓶颈。

## C++ QEM 后端（UV-aware `cpp-uv`）

优点：
- 使用 pybind11 在进程内交换数据，无需磁盘中间文件；
- C++ 内部同时维护 `Mesh::verts`、`Mesh::faces` 与可选 `Mesh::face_uvs`，在压缩阶段同步保留 UV；
- 在相同目标面数与时间限制下，相比 Python 实现通常有显著加速。

限制与注意事项：
- 需要额外的构建步骤（pybind11 + CMake），并确保 `meshqem_py` 模块在运行时可导入；
- 当前 UV 处理采用“只删面”的策略：不重新参数化，不对 UV 进行插值或拉伸校正，仅随 surviving faces 同步删除被丢弃面的 UV triplets；
- 依赖输入 Mesh 拥有一致的 face‑varying UV（详见 `uv-audit` 文档）。

## 选择建议

- 需要最简单路径或环境约束较多 → 选择 `--backend py`；
- 只关心几何减面，不在意 UV → 可以选择 `--backend cpp`；
- 既关心性能，又希望保留 UV 拓扑的一致性 → 推荐 `--backend cpp-uv`，并配合 `uv-audit` 检查结果。
