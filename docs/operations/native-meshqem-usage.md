# 使用与集成（meshqem + Python 适配器）

本页面重点介绍如何从 Python 使用原生可执行文件以及如何直接运行它。

## 直接命令行接口

构建（仅需一次）：
```
mkdir -p native/meshqem/build
cd native/meshqem/build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j
```
运行：
```
./meshqem --in in.obj --out out.obj --ratio 0.5 \
  --max-collapses 200000 --time-limit 120 --progress-interval 20000
```
输出两行摘要到 stdout：
```
faces: <before> -> <after>
verts: <before> -> <after>
```
进度信息每 N 次坍塌输出到 stderr。

## Python 适配器

文件：`convert_asset/mesh/backend_cpp.py`

每个 `UsdGeom.Mesh` prim 的工作流程：
1) 提取点和拓扑，确保仅为三角形。
2) 写入临时 `in.obj`（位置 + 三角形索引）。
3) 使用所需标志（`--ratio` 或 `--target-faces`、时间限制等）执行原生 `meshqem`。
4) 解析 stdout 以获取前后计数；读取 `out.obj` 并在 `apply=True` 时写回 USD。

命令行集成（来自 `convert_asset/cli.py`）：
```
python -m convert_asset.cli mesh-simplify <stage.usd> \
  --backend cpp --cpp-exe native/meshqem/build/meshqem \
  --ratio 0.9 --apply --out <out.usd> --progress --time-limit 60
```

## 规划模式（干运行）

对于 C++ 后端，规划（`--target-faces` 不带 `--apply`）会提前返回建议比率，并跳过调用原生二进制。这避免了在只需要全局比率估算时不必要的原生运行。

## 使用提示

- 确保网格为三角形；非三角形网格会被适配器跳过。
- 在 Python CLI 中使用 `--progress` 查看每个网格的进度和超时。
- 从温和的比率开始，以验证管道质量，然后进行迭代。

---
