# 2026-05-20 Local Isaac Render-Single

## 背景

调研发现 `/cpfs/shared/simulation/zhuzihou/dev/render-usd` 的 `single` 能出图，但依赖它自己的 conda 环境；默认系统 Python 下无法导入 `isaacsim`。本仓库需要吸收其稳定出图经验，但运行路径应统一回到：

```bash
./scripts/isaac_python.sh ./main.py <subcommand>
```

## 根因

原 `convert_asset/cli.py` 顶层导入会提前加载 `pxr`：

- `from .no_mdl.path_utils import _to_posix` 会先执行 `no_mdl/__init__.py`，进而导入带 top-level `pxr` 的 no-MDL 模块；
- `from .mesh.faces import count_mesh_faces` 也会导入 `pxr`。

这会污染 `thumbnails` / 后续 Isaac 渲染命令的启动顺序：`SimulationApp` 创建前已经加载 USD 绑定，容易触发 Isaac runtime 崩溃或异常。

## 变更

- `convert_asset/cli.py`
  - 内联 `_to_posix()`，避免通过 `no_mdl` package 导入工具函数；
  - 将 `count_mesh_faces` 移到 `mesh-faces` 分支内 lazy import；
  - 新增 `render-single` 子命令。
- `convert_asset/render/single.py`
  - 新增 import-clean 的本地 Isaac 单资产渲染模块；
  - Runtime 内部先创建 `SimulationApp`，再导入 `omni` / `pxr` / sensor / `cv2`；
  - 输出规划逻辑可在普通 Python 下测试；
  - 支持 `view` 命名、MDL search path、bbox fallback、cleanup。
- `tests/test_render_single.py`
  - 固化 CLI import-clean 回归；
  - 固化 missing thumbnail input 不应加载 runtime 模块；
  - 固化 `render.single` import-clean 和 `view` 输出命名；
  - 固化 `SimulationApp` 启动失败时返回 `3`，避免非 `RuntimeError` 直接冒泡到 CLI。

## 验证

单元与静态验证：

```bash
python -m pytest tests/test_render_single.py -q
python -m py_compile convert_asset/cli.py convert_asset/render/single.py
python main.py render-single --help
```

本地 Isaac 出图 smoke test：

```bash
rm -rf /tmp/convertasset_render_single_smoke
./scripts/isaac_python.sh ./main.py render-single \
  /cpfs/user/zhuzihou/dev/ConvertAsset/assets/usd/chestofdrawers_nomdl/chestofdrawers_0011/instance.usd \
  --out /tmp/convertasset_render_single_smoke \
  --naming-style view \
  --width 256 \
  --height 256 \
  --warmup-steps 100 \
  --render-steps 8 \
  --overwrite
```

输出：

```text
/tmp/convertasset_render_single_smoke/instance/front.png
/tmp/convertasset_render_single_smoke/instance/left.png
/tmp/convertasset_render_single_smoke/instance/back.png
/tmp/convertasset_render_single_smoke/instance/right.png
```

图片尺寸均为 `256x256`，文件大小约 `12KB-20KB`。`front.png` 人眼检查能看到浅色柜体和顶部旋钮，取景可用于 smoke test。

独立视觉审阅结论：整体 `WARN`。四视角均能看到目标柜类资产，适合验证本地 Isaac 渲染链路；但浅色材质和白灰背景对比偏低，当前相机角度偏俯视，作为论文实验图时建议降低视角并使用更深的中性背景。

代码审阅结论：未发现 import-order 阻塞问题；审阅指出 `SimulationApp` 构造阶段异常处理不完整，已通过回归测试修复。

## 后续

- 将 `render-single` 接到 ACL/VLM render manifest runner；
- 对 before/after material condition 使用相同 camera seed 和 output naming；
- 如需场景内某 prim 的精确位置拍照，应在单独命令中读取场景 prim path 并把相机 stage authoring 与渲染进程隔离。
