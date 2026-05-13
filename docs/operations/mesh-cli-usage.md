# 命令行用法（Python & C++ 后端）

## 统计面数

```bash
python -m convert_asset.cli mesh-faces <stage.usd>
```

## 仅规划目标面数（不减面）

```bash
python -m convert_asset.cli mesh-simplify <stage.usd> --target-faces 80000
```

CLI 会读取当前场景总三角面数，计算出一个建议的 `--ratio` 并打印，但不会实际执行减面。

## Python QEM 后端减面

```bash
python -m convert_asset.cli mesh-simplify <stage.usd> \
  --backend py \
  --ratio 0.5 \
  --apply \
  --out <out.usd> \
  --progress \
  --progress-interval-collapses 10000 \
  --time-limit 120
```

要点：
- 使用 `qem_simplify_ex`，在几何减面的同时保留 surviving faces 的 face‑varying UV；
- 支持 `--progress` 与 `--time-limit` 对单 Mesh 的进度和时限控制。

## C++ 可执行后端（几何-only，`--backend cpp`）

在已构建好 `native/meshqem/build/meshqem` 的前提下，可以走 C++ 命令行后端进行几何减面：

```bash
python -m convert_asset.cli mesh-simplify <stage.usd> \
  --backend cpp \
  --cpp-exe native/meshqem/build/meshqem \
  --ratio 0.5 \
  --apply \
  --out <out_cpp.usd> \
  --time-limit 120
```

行为：
- 对每个符合条件的 Mesh 写出临时三角 OBJ，调用 C++ 可执行 `meshqem`，读取回简化后的 OBJ，再写回 USD；
- 仅处理几何拓扑（points / faces），不处理 UV 或其它 primvars。

## C++ + UV-aware 后端（`--backend cpp-uv`）

在已构建 pybind11 模块 `meshqem_py` 并放置于 `convert_asset/mesh` 下时，可使用新 UV-aware C++ 后端：

```bash
python -m convert_asset.cli mesh-simplify <stage.usd> \
  --backend cpp-uv \
  --ratio 0.95 \
  --apply \
  --out <out_cpp_uv.usd>
```

行为：
- 从 `UsdGeom.Mesh` 提取几何与 face‑varying UV，构造 per-face UV triplets `(u0,v0,u1,v1,u2,v2)`；
- 调用 `meshqem_py.simplify_with_uv(...)` 在 C++ 端执行 QEM 减面，同时在压缩阶段同步 `Mesh::face_uvs`；
- C++ 返回新的顶点、三角与可选的 UV triplets，Python 再将其写回到 USD 的 points / topology / `primvars:st`。

Isaac/Omniverse 环境下，推荐使用仓库自带脚本：

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py mesh-simplify \
  "/abs/path/to/scene.usd" \
  --backend cpp-uv \
  --ratio 0.95 \
  --apply \
  --out "/abs/path/to/scene_qem_95pct_cpp_uv.usd"
```

更多构建和环境配置细节（conda、pybind11、CMake）参见仓库根目录 `README.md` 中的 "网格简化（mesh-simplify）" 小节。
