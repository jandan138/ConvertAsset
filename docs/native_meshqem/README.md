# meshqem 原生后端深度解析

本文面向 `--backend cpp` 的原生 C++ 网格简化实现，目标是“友好、详尽、实用”。

- 它是什么：一个极简、零依赖的三角网格 QEM（Quadric Error Metrics）减面器。
- 在哪里：源码在 `native/meshqem`（CMake 工程），Python 适配器在 `convert_asset/mesh/backend_cpp.py`。
- 为什么这样做：兼顾性能与可维护性，同时让代码足够易读、易移植。

## 快速导览（Quick Map）

- `src/mesh.hpp`, `src/mesh.cpp`：极简网格容器（`verts`、`faces`）。
- `src/io_obj.hpp`, `src/io_obj.cpp`：仅三角的 OBJ 读写（只处理位置）。
- `src/qem.hpp`, `src/qem.cpp`：QEM 核心（二次型、边堆、坍塌循环）。
- `src/main.cpp`：命令行封装；解析参数、调用 QEM、打印摘要。
- `CMakeLists.txt`：构建脚本（C++17，`-O3`）。

## 五分钟看懂 QEM

输入：
- 顶点 V = [(x,y,z)...]（double 精度）
- 三角形 F = [(i,j,k)...]（0 基索引）

步骤：
1) 对每个三角形 t=(i,j,k)，计算平面法线 n 与方程 `ax+by+cz+d=0`，构造 4×4 二次型 `K = p p^T`，其中 `p=[a,b,c,d]`。
2) 将 `K` 累加到三个端点的二次型：`Q[i]+=K`，`Q[j]+=K`，`Q[k]+=K`。
3) 对邻接图中的每条无向边 (u,v)，合并二次型 `Quv = Q[u]+Q[v]`，并在以下位置评估 `v'^T Quv v'` 作为坍塌代价：
   - 最优位置（解 3×3 线性方程），或
   - 回退：若退化则用端点中点。
4) 反复弹出代价最低的边，执行 v→u 坍塌（更新 u 位置、合并二次型、更新面与邻接），并为 u 周围重新推入候选边。
5) 达到目标面数或触发限时/最大坍塌数后停止；压缩数组并返回结果。

v1 有意不包含：属性保留（法线/UV）、边界/特征启发式、翻面检测等；目标是先保证“清晰 + 稳健”。

## 文件说明

### `mesh.hpp` / `mesh.cpp`
- `Vec3`、`Tri` 为轻量结构体，便于缓存友好访问。
- `Mesh` 保存 `verts`（点坐标）与 `faces`（三角索引），`clear()` 重置两者。

### `io_obj.hpp` / `io_obj.cpp`
- 仅读取 `v`（位置）与 `f`（三角），忽略 vt/vn/material/object 等。
- OBJ 1 基索引 ↔ 内部 0 基索引的对称转换。
- 基本健壮性：无法打开或没有几何时返回错误信息。

### `qem.hpp` / `qem.cpp`
- `Quadric`：4×4 行优先矩阵。
- `EdgeCand`：边候选（通过比较器反转构造“最小堆”）。
- `SimplifyOptions`：控制比率/目标面数、最大坍塌数、时间限制、进度频率。
- `qem_simplify`：核心引擎，代码内含大量逐步注释。

关键小工具：
- `plane_quadric(a,b,c,d)`：构造 `K = p p^T`。
- `solve3(A,b)`：3×3 高斯消元（部分选主元）。
- `quadric_eval(Q, v4)`：在齐次坐标 `[x,y,z,1]` 下计算 `v^T Q v`。

质量与安全：
- 构建二次型时丢弃零面积三角形（稳定性）。
- 坍塌回写位置使用中点（简单稳健）；如需更高保真可改用最优解 `x`。
- `time-limit` 会提前终止当前网格的简化，但保证返回合法（部分简化）的结果。

### `main.cpp`
- 极简 CLI。向 stdout 只打印两行摘要，便于 Python 解析：
  - `faces: M -> N`
  - `verts: A -> B`
- 进度（每 N 次坍塌）打印到 stderr。

## 构建与运行

构建：
```
mkdir -p native/meshqem/build
cd native/meshqem/build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j
```
直接运行：
```
./meshqem --in in.obj --out out.obj --ratio 0.5 --progress-interval 20000
```
推荐从 Python 侧调用：参见 `convert_asset/mesh/backend_cpp.py` 与 CLI `mesh-simplify --backend cpp`。

## 调优与扩展

- 建议用保守比率（如 0.9 或 0.7）先做验证。
- 使用 `--time-limit` 保证大网格可控；超时会跳过当前网格继续处理。
- 后续规划（v1 未实现）：
  - 边界保留与特征敏感度
  - 属性传递（法线/UV）与重投影
  - 翻面检测与质量指标
  - 多网格并行

## FAQ

- 为何只支持三角？简单高效；非三角网格可在上游先三角化。
- 为何用 double？减少多次坍塌带来的累计数值误差。
- 为何回写位置用中点而非最优 `x`？更稳更简单；代价仍使用最优 `x` 指导顺序。如需更高保真可切换实现。

## 故障排查

- “cannot open”：检查输入路径与权限。
- “empty mesh”：确保 OBJ 文件同时包含 `v` 与 `f` 行。
- 进度停滞：调大/调小 `--progress-interval`，或设置 `--time-limit`。

——
最后更新：2025-09-24
