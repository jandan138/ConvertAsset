# QEM 算法与 UV 携带策略概述

## 几何 QEM 回顾

无论是 Python 还是 C++ 后端，核心几何算法都基于 Quadric Error Metrics（QEM）：

1. 对每个三角面建立一个平面 quadric，并累积到该面的三个顶点上；
2. 在候选边集合中选择具有最小误差代价的边进行坍塌；
3. 为每次坍塌寻找最佳合并位置（求解 4x4 线性系统或使用端点中点作为回退）；
4. 重建邻接关系与候选边集合，直到达到目标面数或时间限制。

详细推导与 Python 实现可参考：
- `docs/mesh/legacy/algorithm_qem.md`
- `convert_asset/mesh/simplify.py` 中 `qem_simplify()` / `qem_simplify_ex()`。

## Python 的 UV 携带：`qem_simplify_ex`

Python 版本在几何 QEM 的基础上为每个三角维护一条 `face_uvs[fi] = (u0,v0,u1,v1,u2,v2)`：

- 初始阶段从 `faceVertexCounts` / `faceVertexIndices` 与 face‑varying `primvars:st` 解出每面三个 UV；
- 在边坍塌过程中，只跟踪几何拓扑（顶点/面 alive 标记与索引重映射），不对 UV 做任何插值；
- 当某个面被标记为 not alive 时，其对应的 `face_uvs[fi]` 直接丢弃；
- 在最终压缩阶段，仅对 still-alive faces 重建新的 `faces2` 与 `face_uvs2`，保持一一对应；
- 最终将 `faces2` 与 `face_uvs2` 写回 USD，作为新的拓扑与 face‑varying UV。

这一策略的优点是实现简单、行为可预测：几何删掉哪些面，UV 就删掉对应面角点；缺点是不会尝试进行高阶 UV 修复或重参数化。

## C++ 的 UV 携带：`Mesh::face_uvs`

在 C++ 后端中，`native/meshqem/src/mesh.hpp` 的 `Mesh` 结构增加了一个可选字段：

```cpp
struct Mesh {
    std::vector<Vec3> verts;
    std::vector<Tri>  faces;
    std::vector<std::array<double, 6>> face_uvs; // 每个三角一个 (u0,v0,u1,v1,u2,v2)
};
```

核心策略与 Python 一致：

- 算法主体（`qem_simplify`）在边坍塌阶段只关注几何拓扑；
- 在最终“压缩顶点与面”的阶段，若 `face_uvs.size() == faces.size()`：
  - 为每个 surviving face 构建新 triangle index，并同步将 `face_uvs[fi]` 追加到 `uv2`；
  - 完成后 `mesh.face_uvs.swap(uv2)`，保证 `mesh.faces` 与 `mesh.face_uvs` 长度一致；
- 若未提供 UV 或长度不匹配，则在压缩后清空 `face_uvs`。

这样可以在不干扰核心几何算法的前提下，为嵌入式调用（pybind11 模块）提供与 Python 版本对齐的 UV 携带行为。

## Python ↔ C++ UV 数据流

在 `convert_asset/mesh/backend_cpp.py` 中，新增加的 `simplify_mesh_with_cpp_uv` 做了以下工作：

1. 从 `UsdGeom.Mesh` 提取 points / faces 与 face‑varying UV（若存在且一致），构造：
   - `points: list[tuple[float, float, float]]`
   - `faces: list[tuple[int, int, int]]`
   - `face_uv_triplets: Optional[list[tuple[float, float, float, float, float, float]]]`
2. 调用 `meshqem_py.simplify_with_uv(points, faces, face_uv_triplets, ...)`：
   - 在 C++ 中填充 `Mesh::verts`、`Mesh::faces` 与可选的 `Mesh::face_uvs`；
   - 调用 `qem_simplify(mesh, options, report)`；
   - 返回新的 `verts2`、`faces2` 与可选的 `face_uvs2`；
3. 若设置 `apply=True`，则：
   - 将 `verts2` 和 `faces2` 写回 USD 的 points / face topology；
   - 若 `face_uvs2` 存在，则调用 `_write_facevarying_uv` 写回新的 `primvars:st`。

此流程使得 C++ 与 Python 版本在“几何删面 + UV 同步删除”的语义上保持一致，并允许在大型资产上利用 C++ 的性能优势。
