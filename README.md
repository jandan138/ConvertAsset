# ConvertAsset

ConvertAsset 提供两类核心能力：

- **no-MDL 转换**：将包含 MDL 材质的 USD 资产批量转换为基于 `UsdPreviewSurface` 的无 MDL 版本，保留引用 / 载荷 / variants / clips，不做 flatten，并在原始目录旁生成 `*_noMDL.usd` 文件；
- **资产增值工具链**：包括网格简化（mesh-simplify）、UV 体检（uv-audit）、缩略图渲染（thumbnails）、材质检查（inspect）、MDL 材质导出等。

## Quick Start

假设你已有一个 USD 场景 `/abs/path/to/scene.usd`，并可以使用 Isaac Sim 的 Python 运行环境：

```bash
cd /opt/my_dev/ConvertAsset

# 简单 no-MDL 转换
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py no-mdl "/abs/path/to/scene.usd"

# 对同一个场景做一次 50% 网格简化（Python 后端）
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py mesh-simplify \
	"/abs/path/to/scene.usd" \
	--backend py \
	--ratio 0.5 \
	--apply \
	--out "/abs/path/to/scene_qem_50pct_py.usd"
```

更多细节用法，见下文各功能小节和 `docs/` 目录。

## 运行环境与入口

推荐使用仓库内的包装脚本（自动定位 Isaac Sim 安装）：

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py "/abs/path/to/top.usd"
```

该脚本会按以下优先级查找 Isaac Sim 的 `python.sh`：
1. 显式环境变量：`ISAAC_SIM_ROOT`（需包含 `python.sh`）
2. Docker 容器内的 `/isaac-sim/python.sh`
3. 本地用户目录：`~/.local/share/ov/pkg/isaac_sim-*`（选择最高版本）
4. 常见系统安装路径：`/opt/nvidia/isaac-sim`、`/opt/NVIDIA/isaac-sim`、`/opt/omniverse/isaac-sim`

若无法自动定位，请手动：

```bash
export ISAAC_SIM_ROOT="/abs/path/to/isaac_sim-<version>"
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py "/abs/path/to/top.usd"
```

也可以显式指定子命令，例如：

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py no-mdl "/abs/path/to/top.usd"
# 仅输出 *_noMDL.usd（不写旁路的 summary/audit 文件）
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py no-mdl "/abs/path/to/top.usd" --only-new-usd

提示：`--only-new-usd` 只是在本次运行中抑制生成旁路文件；如果目标目录里已存在旧的 `*_noMDL_summary.txt` / `*_noMDL_audit.json`，它们不会被删除。
```

仍可使用旧脚本：

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/scripts/usd_make_preview_copies.py "/abs/path/to/top.usd"
```

## 功能概览

- **no-mdl**：生成 `_noMDL.usd` 版本，移除 MDL 材质，建立 UsdPreviewSurface 网络；
- **mesh-faces / mesh-simplify**：统计面数与网格简化，支持纯 Python 与 C++（含 UV-aware）后端；
- **uv-audit**：检查 Mesh UV（face-varying）的一致性与长度匹配；
- **inspect**：分析指定 Material（MDL / UsdPreviewSurface）的着色网络；
- **export-mdl-materials**：将场景内 MDL 材质导出为独立材质球 USD；
- **export-glb**：将 USD 资产转换为 GLB 格式（支持 FaceVarying UV 与材质贴图烘焙/链接）；
- **usd-to-glb**：一站式管道命令，自动执行 MDL 转换 -> GLB 导出 -> 清理中间文件；
- **thumbnails**：在 Isaac Sim 中批量渲染带背景的多视角缩略图。

更详细的设计和实现说明参见：

- 网格简化：`docs/mesh/overview.md`、`docs/mesh/cli_usage.md`；
- C++ QEM 后端：`docs/native_meshqem/README.md`、`usage_and_integration.md`；
- 材质与 no-MDL 流程：`docs/no_mdl/`；
- 缩略图：`docs/thumbnails/`。

## 网格简化（mesh-simplify）

#### Python QEM 后端（默认，带 UV 保留）

保留约 99% 面数（按三角面计）的示例（Python 后端，写入新文件并打印进度）：

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py mesh-simplify \
	"/abs/path/to/scene.usd" \
	--backend py \
	--ratio 0.99 \
	--apply \
	--out "/abs/path/to/scene_qem_99pct.usd" \
	--progress
```

结果示例：

```text
[APPLY] meshes total=13 tri=13 skipped_non_tri=0
faces: 857791 -> 849199
verts: 433164 -> 428500
Exported: /opt/my_dev/ConvertAsset/asset/test_scene/models/object/others/bed/28d4d65318a0bfb8bf07e713aec1227c/instance_qem_99pct.usd
```

说明：
- `--ratio`: 目标保留比例（0.99 ≈ 保留 99% 面数）
- `--backend py`: 使用 Python 后端，调用 `qem_simplify_ex`（保留 surviving faces 的 face‑varying UV）
- `--apply`: 将简化结果写入导出 USD
- `--out`: 输出文件路径（默认与源同目录）
- `--progress`: 打印每个组件的进度

#### C++ QEM 后端（可选，含 UV-aware 路径）

本仓库提供一个基于 C++/pybind11 的 QEM 实现，用于在 Python 进程内高效调用 C++ 版网格简化，并在 `cpp-uv` 模式下保留 surviving faces 的 face‑varying UV。使用前需要完成一次性的 C++ 构建和绑定配置。

**1）在 conda 环境中安装 pybind11（推荐 usd-render 环境）**

```bash
source /root/miniconda3/bin/activate usd-render
python -m pip install --upgrade "pybind11[global]"
```

> 说明：`pybind11[global]` 会额外安装带 CMake 配置的 `pybind11_global`，以便 `find_package(pybind11)` 正常工作。

**2）构建 C++ 可执行与 pybind11 模块**

```bash
cd /opt/my_dev/ConvertAsset/native/meshqem
mkdir -p build
cd build
cmake -DBUILD_MESHQEM_PY=ON ..
cmake --build . --config Release -j4
```

构建成功后将生成：

- `native/meshqem/build/meshqem`：C++ 命令行可执行（`--backend cpp` 使用）
- `native/meshqem/build/meshqem_py.cpython-<ver>-x86_64-linux-gnu.so`：pybind11 Python 模块（`--backend cpp-uv` 使用）

随后将模块放入 Python 包路径（`convert_asset/mesh`）下，供包内相对导入：

```bash
cd /opt/my_dev/ConvertAsset/native/meshqem/build
cp meshqem_py.cpython-*.so ../../../convert_asset/mesh/
```

**3）运行前设置 Python 环境**

所有 CLI 调用前，推荐在 `usd-render` 环境下设置：

```bash
cd /opt/my_dev/ConvertAsset
source /root/miniconda3/bin/activate usd-render
export PYTHONPATH=/opt/my_dev/ConvertAsset
```

这样可以确保：

- `convert_asset` 作为包可被正常导入；
- `convert_asset.mesh.backend_cpp` 能通过 `from . import meshqem_py` 找到刚刚复制的 `.so`。

**4）使用 C++ 后端执行减面**

- 只用 C++ 可执行（几何-only，不处理 UV）：

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py mesh-simplify \
	"/abs/path/to/scene.usd" \
	--backend cpp \
	--ratio 0.95 \
	--apply \
	--out "/abs/path/to/scene_qem_95pct_cpp.usd"
```

- 使用 C++ + UV-aware 后端（pybind11 模块，保留 face‑varying UV）：

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py mesh-simplify \
	"/abs/path/to/scene.usd" \
	--backend cpp-uv \
	--ratio 0.95 \
	--apply \
	--out "/abs/path/to/scene_qem_95pct_cpp_uv.usd"
```

结果示例（UV-aware C++ 后端）：

```text
[APPLY] meshes total=13 tri=13 skipped_non_tri=0
faces: 857791 -> 814891
verts: 433164 -> 411060
Exported: /tmp/instance_simplified_95_cpp_uv.usd
```

说明：

- `--backend cpp`：走磁盘中间文件（OBJ）+可执行 `meshqem`，只简化几何；
- `--backend cpp-uv`：通过 `meshqem_py` 模块在 Python 进程内调用 C++，并在内部维护 per-face UV triplets，同步保留 surviving faces 的 face‑varying UV；
- 两种 C++ 后端都要求输入网格为纯三角面（`faceVertexCounts == 3`），非三角网格会被跳过计入 `skipped_non_tri`。

## UV 体检（uv-audit）

检查场景/资产中的 Mesh UV 一致性（是否为 `faceVarying` 且长度/indices 与面角点数匹配）。需在 Isaac Sim Python 环境运行：

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/scripts/uv_audit.py \
	"/abs/path/to/scene_or_asset.usd" \
	--limit 50
```

输出示例（存在不一致时）：

```text
[SUMMARY] meshes=13 with_uv=13 faceVarying_uv=13 mismatches=13
[DETAIL] first 13 mismatches:
- /Root/.../component12 primvar=st interp=faceVarying reason=values length != face corners expectedCorners=95526 valuesLen=100560
...
```

输出示例（UV 保留版无不一致）：

```text
[SUMMARY] meshes=13 with_uv=13 faceVarying_uv=13 mismatches=0
```

说明：
- 面角点总数为 `sum(faceVertexCounts)`；`faceVarying` 模式需与之对齐（使用 `indices` 时校验 indices 长度）。
- `--limit` 控制打印的不一致条目上限。
- 常见不一致来自“只删几何未同步裁剪 UV（values 仍为旧长度）”。

## 材质检查（inspect）

用于**只读**分析某个 Material 在 MDL 或 UsdPreviewSurface 模式下的着色网络：

```
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect /abs/path/to/scene.usd usdpreview /Looks/Mat01
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect /abs/path/to/scene.usd mdl /Looks/Mat01
```

示例（仓库自带演示文件）：
```
cd /opt/my_dev/ConvertAsset
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect examples/inspect_demo.usda usdpreview /Looks_PreviewMat
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect examples/inspect_demo.usda mdl /Looks_Mat
```

更多细节见：`docs/inspect_material.md`

## 导出 MDL 材质为独立材质球 USD（含贴图连接）

该命令将遍历 MDL 材质并为每个材质创建一个独立的 UsdPreviewSurface 材质 USD 文件。

```
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py export-mdl-materials \
	/abs/path/to/scene.usd \
	--out-dir-name mdl_materials \
	--placement authoring \  # 将材质球写到“材质定义所在的最小子文件”的同目录（默认）
	# --placement root      # 将材质球统一写到“场景顶层文件”的同目录
	# --no-external         # 仅导出根层作者的材质，忽略外部引用
	# --binary              # 可选，写 .usd（默认 .usda）
```

导出结果示例：
- 输入：`/data/scene.usd`
- 输出：`/data/mdl_materials/<MaterialName>.usda`

更多细节见：`docs/export_mdl_materials/`（入口：README.md；索引：INDEX.md）

注意：
- 默认 `--placement authoring` 会把每个材质球写到该材质“作者层”（通常是最小子 USD）的同级目录下的 `--out-dir-name` 子目录中，因此不会和场景顶层 USD 放在同一个目录；这正是避免混放的推荐方式。
- 若你希望统一输出在顶层 USD 目录，可切换 `--placement root`。
- `--no-external` 可用于只导出根层拥有/定义的材质。
- 导出过程会自动搭建预览网络并尽可能复用/解析 MDL 贴图路径（BaseColor / Roughness / Metallic / Normal）。

## GLB 导出 (export-glb / usd-to-glb)

将 USD 资产转换为 GLB (glTF 2.0 Binary) 格式。支持两种模式：

**1. 直接导出 (`export-glb`)**
适用于已经去除了 MDL 的文件：
```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py export-glb \
	"/abs/path/to/scene_noMDL.usd" \
	--out "/abs/path/to/output.glb"
```

**2. 一站式管道 (`usd-to-glb`)**
适用于原始 MDL 资产，自动处理材质转换并清理中间文件：
```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py usd-to-glb \
	"/abs/path/to/scene.usd" \
	--out "/abs/path/to/output.glb"
```

**关键特性**：
- **FaceVarying UV 支持**：自动检测并处理 USD 的 FaceVarying UV 拓扑，通过顶点分裂（Mesh Flattening）确保在 glTF 中正确显示纹理，解决 UV 错乱或丢失问题。
- **稳健的纹理提取**：智能解析 UsdPreviewSurface 网络，支持嵌套连接、直接 Prim 引用以及 `info:id="UsdUVTexture"` 等多种 USD 变体，确保 BaseColor、Normal、Metallic 等贴图正确链接。
- **自动坐标系转换**：处理 Z-up 到 Y-up 的转换（如果需要）。

## 缩略图渲染（thumbnails）

使用 Isaac Sim 无头渲染，为场景中的实例 Mesh 生成带背景的多视角缩略图（按实例名分文件夹保存）。

基本用法（默认输出到 `<usd目录>/thumbnails/multi_views_with_bg`）：

```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails /abs/path/to/scene.usd
```

常用参数：

- `--out` 指定输出目录
- `--instance-scope` 实例所在作用域，默认 `scene/Instances`（等价于 `/World/scene/Instances`）
- `--width` / `--height` 分辨率（默认 600x450）
- `--views` 视角数量（偶数，默认 6，上/下半球各一半）
- `--warmup-steps` / `--render-steps` 预热与渲染步数（默认 1000 / 8）
- `--focal-mm` 焦距（默认 9.0）
- `--bbox-threshold` 2D 紧/松包围框面积比阈值（默认 0.8，低于阈值不保存）
- `--no-bbox-draw` 不在图片上绘制框
- `--skip-model-filter` 跳过基于 models 目录的过滤（默认跳过）

输出结构：`<out>/<PrimName>/<PrimName>_with_bg_<index>.png`

注意：必须在 Omniverse Isaac Sim 的 Python 环境中运行（`SimulationApp`）。环境与常见问题请参见：`docs/thumbnails/`。

## 配置

修改 `convert_asset/no_mdl/config.py` 中的参数，例如：
- `SUFFIX`: 输出文件后缀，默认 `_noMDL`
- `ALLOW_OVERWRITE`: 是否允许覆盖已存在的输出
- `MATERIAL_ROOT_HINTS`: 材质所在的常见路径 hint
- 其它材质/贴图处理选项参见文件内注释

## Git 忽略

- `asset/` 目录不会纳入版本控制（见根目录 `.gitignore`）
- 常见 Python 临时文件与 IDE 目录也已忽略

## 许可证

内部项目（如需对外开源，请补充许可协议）。
