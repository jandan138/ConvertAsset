# ConvertAsset

本项目用于将包含 MDL 材质的 USD 资产批量转换为基于 `UsdPreviewSurface` 的无 MDL 版本，保留引用/载荷/variants/clips，不做 flatten，并在原始目录旁生成 `*_noMDL.usd` 文件。

同时提供“带背景的多视角缩略图”生成功能，适用于根据场景内实例对象批量出图，作为检索/标注的可视化资产。

## 运行

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

也可以显式指定子命令：

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

### 新增：材质检查 (inspect)

用于**只读**分析某个 Material 在 MDL 或 UsdPreviewSurface 模式下的着色网络：

```
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect /abs/path/to/scene.usd usdpreview /Looks/Mat01
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect /abs/path/to/scene.usd mdl /Looks/Mat01
```

示例（仓库自带演示文件）：
```
cd /opt/my_dev/ConvertAsset
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect examples/inspect_demo.usda usdpreview /Looks_PreviewMat
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect examples/inspect_demo.usda mdl /Looks_Mat
```

更多细节见：`docs/inspect_material.md`

### 新增：导出本文件内的 MDL 材质为独立材质球 USD（含贴图连接）

该命令将遍历 MDL 材质并为每个材质创建一个独立的 UsdPreviewSurface 材质 USD 文件。

```
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py export-mdl-materials \
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

### 新增：缩略图渲染（thumbnails）

使用 Isaac Sim 无头渲染，为场景中的实例 Mesh 生成带背景的多视角缩略图（按实例名分文件夹保存）。

基本用法（默认输出到 `<usd目录>/thumbnails/multi_views_with_bg`）：

```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails /abs/path/to/scene.usd
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
