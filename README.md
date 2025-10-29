# ConvertAsset

本项目用于将包含 MDL 材质的 USD 资产批量转换为基于 `UsdPreviewSurface` 的无 MDL 版本，保留引用/载荷/variants/clips，不做 flatten，并在原始目录旁生成 `*_noMDL.usd` 文件。

## 运行

推荐使用新的入口：

```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py "/abs/path/to/top.usd"
```

也可以显式指定子命令：

```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py no-mdl "/abs/path/to/top.usd"
# 仅输出 *_noMDL.usd（不写旁路的 summary/audit 文件）
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py no-mdl "/abs/path/to/top.usd" --only-new-usd
```

仍可使用旧脚本：

```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/scripts/usd_make_preview_copies.py "/abs/path/to/top.usd"
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
