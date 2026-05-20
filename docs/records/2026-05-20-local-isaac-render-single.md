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
  - 支持 `view` 命名、MDL search path、HDRI 透明背景合成、bbox fallback、cleanup。
  - bbox fallback 吸收 `render-usd` 后期修复：authored extent 过大或 authored/mesh 中心偏移时改用 mesh/boundable bbox，并忽略不可见或非 default purpose 的辅助几何。
  - HDRI 查找优先从 `ISAAC_SIM_ROOT`、`isaacsim.__file__` 祖先目录和 `/isaac-sim` 下的 `extscache` 定位 `photo_studio_01_4k.hdr`。
- `tests/test_render_single.py`
  - 固化 CLI import-clean 回归；
  - 固化 missing thumbnail input 不应加载 runtime 模块；
  - 固化 `render.single` import-clean 和 `view` 输出命名；
  - 固化 `SimulationApp` 启动失败时返回 `3`，避免非 `RuntimeError` 直接冒泡到 CLI。
  - 固化 `backgroundZeroAlpha` 设置、可配置背景色、HDRI 路径发现、bbox 中心偏移 fallback、visibility/purpose/boundable bbox 边界。

## 验证

单元与静态验证：

```bash
python -m pytest tests/test_render_single.py -q
python -m py_compile convert_asset/cli.py convert_asset/render/single.py
python main.py render-single --help
```

本地 Isaac 出图 smoke test：

```bash
rm -rf /tmp/convertasset_render_single_hdri_smoke3
./scripts/isaac_python.sh ./main.py render-single \
  /cpfs/user/zhuzihou/dev/ConvertAsset/assets/usd/chestofdrawers_nomdl/chestofdrawers_0011/instance.usd \
  --out /tmp/convertasset_render_single_hdri_smoke3 \
  --naming-style view \
  --width 256 \
  --height 256 \
  --warmup-steps 100 \
  --render-steps 8 \
  --background-color 40,40,40 \
  --overwrite
```

输出：

```text
/tmp/convertasset_render_single_hdri_smoke3/instance/front.png
/tmp/convertasset_render_single_hdri_smoke3/instance/left.png
/tmp/convertasset_render_single_hdri_smoke3/instance/back.png
/tmp/convertasset_render_single_hdri_smoke3/instance/right.png
```

图片尺寸均为 `256x256`，文件大小约 `14KB-23KB`。四角背景像素 mode/median 均为 `RGB(40,40,40)`，说明 HDRI 光照和透明背景合成已经生效。

额外复核：

- `python - <<'PY' ... _find_builtin_hdri() ... PY` 返回 `/isaac-sim/extscache/omni.kit.widget.material_preview-1.0.16/data/photo_studio_01_4k.hdr`；
- `front/left/back/right` 四图均非空；
- 常见 headless 警告、Isaac deprecated namespace 警告和该资产的 corrupted normal primvar 警告仍为非致命。

独立代码/文档复核结论：应迁移 `render-usd` 的 HDRI + `backgroundZeroAlpha` + 深灰背景合成、无限 camera distance 上限、bbox extent/center-offset fallback；不应迁移 conda/DLC/batch overwrite 流程或场景内 with-bg 六视图逻辑。

独立视觉审阅结论：整体 `WARN`。四视图目标均可见、无裁切，深灰背景有帮助且不抢画面；但默认 `35` 度 elevation 对该抽屉柜资产偏俯视，物体读作“盒体/柜体”多于明确抽屉正面。右视图 `PASS`，后续论文/benchmark 图建议保留深灰背景，并使用更低 elevation 或三分之四 front view 让木质正面和抽屉结构更清楚。

代码审阅结论：未发现 import-order 阻塞问题；审阅指出 `SimulationApp` 构造阶段异常处理不完整，已通过回归测试修复。

## 后续

- 将 `render-single` 接到 ACL/VLM render manifest runner；
- 对 before/after material condition 使用相同 camera seed 和 output naming；
- 如需场景内某 prim 的精确位置拍照，应在单独命令中读取场景 prim path 并把相机 stage authoring 与渲染进程隔离。
