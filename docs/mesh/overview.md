# 概览（Overview）

本模块围绕网格简化（mesh-simplify）提供两套互补的实现：

- **Python QEM 后端**：纯 Python 参考实现，易读、易调试，适合验证与中小规模资产；
- **C++ QEM 后端**：原生 C++ 实现，提供命令行可执行与 pybind11 绑定版本，其中 `cpp-uv` 模式支持在 C++ 内部保留 face‑varying UV（只同步删除被丢弃的三角）。

共同特性：
- 仅处理活跃（Active）且 `purpose in {default, render}` 的 `UsdGeom.Mesh`；
- 跳过 Instance Proxy 与 `purpose in {proxy, guide}`；
- 仅处理三角网格（`faceVertexCounts == 3`），非三角将被统计为 `skipped_non_tri` 并跳过。

对应实现：
- Python 后端主体：`convert_asset/mesh/simplify.py` 的 `simplify_stage_meshes()`、`qem_simplify()`、`qem_simplify_ex()`；
- C++ 后端核心：`native/meshqem/src` 下的 `mesh.{hpp,cpp}`、`qem.{hpp,cpp}` 以及 `python_bindings.cpp`；
- Python ↔ C++ 桥接：`convert_asset/mesh/backend_cpp.py`（接口）与 `backend_cpp_impl.py`（实现细节），以及 CLI 入口 `convert_asset/cli.py` 的 `mesh-simplify` 子命令。

快速对比：
- Python：一次性在 Python 中构建拓扑与 UV triplets，调用 `qem_simplify_ex`，适合需要易于阅读/修改的场景；
- C++（cpp）：通过 OBJ 临时文件 + 外部 `meshqem` 可执行，只处理几何，无 UV；
- C++（cpp-uv）：通过 `meshqem_py` pybind11 模块在进程内传递顶点/三角与 per-face UV triplets，C++ 核心在压缩阶段同步 `face_uvs`，最后由 Python 把新的 UV triplets 写回 USD 的 `primvars:st`。
