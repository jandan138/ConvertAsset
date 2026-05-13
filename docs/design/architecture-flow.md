# 执行流程（Flow）

以下描述从命令行到输出 `_noMDL.usd` 的完整链路。

## 命令入口
- 运行：`/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py <top.usd>`
- `main.py` -> `convert_asset.cli.main(argv)`
- CLI 解析：默认子命令 `no-mdl`，传入源 USD 路径。

## Processor 处理流程
1. 加载顶层 Stage（不 flatten）。
2. `_collect_asset_paths(stage)` 收集：
   - subLayers（LayerStack）
   - references / payloads（通过 `prim.GetMetadata("references")` / `"payloads"` 读取 ListOp）
   - variants（遍历 variantSets，记录每个选项内的引用路径）
   - clips（`valueClips` 中的 assetPaths）
3. 为顶层计算输出文件：`_sibling_noMDL_path(top)`，复制/写出骨架。
4. 在顶层 Stage 上改写依赖指向 `_noMDL`：`_rewrite_assets_in_stage(stage, mapping)`。
5. 仅在顶层文件执行材质转换：`convert_and_strip_mdl_in_this_file_only(stage)`
   - 定位材质根（`MATERIAL_ROOT_HINTS`，找不到则全表扫描）
   - 将 MDL 节点替换为 `UsdPreviewSurface` 网络，连接贴图或常量
   - 移除所有 MDL 着色器与输出
6. 保存并校验：`verify_no_mdl(stage)` -> `noMDL=True`。
7. 递归处理子依赖：对收集到的每个子 USD 重复 1-6（去重与循环检测），从而在各自目录生成 `_noMDL`。
8. 打印 SUMMARY 映射与统计（materials processed X/Y）。

## 重要注意
- “仅在当前导出层转换”的策略保证：不修改下游文件的内容；每个文件在其自身导出时再转换。
- 兼容旧版 USD：读取 ListOp 用元数据；写入优先 API，失败回退 SetMetadata。
- 输出命名冲突：若不允许覆盖，则在文件名后追加时间戳。
