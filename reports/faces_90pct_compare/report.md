# 90% faces 保留对比报告（Python vs C++ UV-aware）

## 1. 测试场景与目标

- 源文件：
  - `asset/test_scene/scenes/MV7J6NIKTKJZ2AABAAAAADA8_usd/models/object/others/bed/28d4d65318a0bfb8bf07e713aec1227c/instance.usd`
- 原始统计（两次运行一致）：
  - faces_before = 857791
  - verts_before = 433164
- 目标：保留约 90% faces（`--ratio 0.9`），并保持 face-varying UV 一致性。

## 2. 命令与运行环境

在同一机器和同一 Isaac/pxr 环境下运行：

```bash
cd /opt/my_dev/ConvertAsset
source /root/miniconda3/bin/activate usd-render
export PYTHONPATH=/opt/my_dev/ConvertAsset
```

### 2.1 Python 后端（`--backend py`）

```bash
time python main.py mesh-simplify \
  asset/test_scene/scenes/MV7J6NIKTKJZ2AABAAAAADA8_usd/models/object/others/bed/28d4d65318a0bfb8bf07e713aec1227c/instance.usd \
  --backend py \
  --ratio 0.9 \
  --apply \
  --out reports/faces_90pct_compare/instance_90_py.usd
```

### 2.2 C++ UV-aware 后端（`--backend cpp-uv`）

```bash
time python main.py mesh-simplify \
  asset/test_scene/scenes/MV7J6NIKTKJZ2AABAAAAADA8_usd/models/object/others/bed/28d4d65318a0bfb8bf07e713aec1227c/instance.usd \
  --backend cpp-uv \
  --ratio 0.9 \
  --apply \
  --out reports/faces_90pct_compare/instance_90_cpp_uv.usd
```

## 3. 结果统计

### 3.1 faces / verts 概览

| Backend | faces_before | faces_after | verts_before | verts_after | faces_after / faces_before |
|--------:|-------------:|------------:|-------------:|------------:|----------------------------:|
| py      | 857791       | 771994      | 433164       | 389373      | ~0.900                     |
| cpp-uv  | 857791       | 771993      | 433164       | 389372      | ~0.900                     |

观察：
- 两个后端在相同 `ratio=0.9` 下的 faces_after / verts_after 几乎完全一致，仅在 1 faces / 1 verts 的量级存在差异，属于算法内部整数舍入与贪心路径的细节差别。

### 3.2 性能对比（墙钟时间）

从 shell `time` 输出读取：

- Python 后端：
  - `real    43m57.321s`
  - `user    43m42.375s`
  - `sys     0m4.139s`
- C++ UV-aware 后端：
  - `real    0m22.785s`
  - `user    0m22.030s`
  - `sys     0m0.746s`

粗略加速比（按墙钟时间）：

- `43m57 / 0m22.8 ≈ 116x`

说明：
- Python 后端几乎整个时间都在 Python 层执行 QEM 算法（`user ≈ real`）；
- C++ UV-aware 后端的绝大部分工作在 C++ 内核中完成，Python 仅负责 USD I/O 与数据拼装，因此在相同场景下快近两数量级。

## 4. UV 一致性检查

使用仓库自带 `uv_audit.py` 对两个输出进行检查：

### 4.1 Python 输出

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/scripts/uv_audit.py \
  "reports/faces_90pct_compare/instance_90_py.usd" \
  --limit 20
```

输出摘要：

```text
[SUMMARY] meshes=13 with_uv=13 faceVarying_uv=13 mismatches=0
```

### 4.2 C++ UV-aware 输出

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/scripts/uv_audit.py \
  "reports/faces_90pct_compare/instance_90_cpp_uv.usd" \
  --limit 20
```

输出摘要：

```text
[SUMMARY] meshes=13 with_uv=13 faceVarying_uv=13 mismatches=0
```

结论：
- 在该资产上，两种后端在 90% faces 简化后均能保持 face-varying UV 拓扑一致性；
- 没有出现常见的“values 长度未裁剪 / indices 长度与面角点不匹配”等问题。

## 5. 行为与稳定性

- 两个后端均只处理 `faceVertexCounts == 3` 的网格，本场景 `skipped_non_tri = 0`；
- 简化过程中未触发 `time_limit` 提前终止；
- 输出统计中 `meshes total=13 tri=13 skipped_non_tri=0` 一致，说明过滤逻辑对两种后端统一。

## 6. 总结

- **质量方面**：
  - 在该资产、`ratio=0.9` 条件下，Python 与 C++ UV-aware 后端的 faces/verts 结果几乎一致，并且 UV 一致性检查均通过；
  - 即便在大幅减面（10% 删除）下，现有的“只删面” UV 携带策略在该场景中没有引入可检测的拓扑错误。

- **性能方面**：
  - C++ UV-aware 后端在相同场景下相较 Python 后端快约 100x 以上（本次测量约 116x），对大资产和批处理场景非常有价值；
  - Python 后端仍然有参考和调试价值，但不适合作为重度生产路径。

- **建议**：
  - 对性能敏感且有 UV 质量要求的场景，优先使用 `--backend cpp-uv`；
  - Python 后端推荐用于算法理解、单 Mesh 调试或在无法使用 C++ 编译环境时的 fallback。
