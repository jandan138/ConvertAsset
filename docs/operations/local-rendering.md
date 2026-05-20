# 本地 Isaac 单资产渲染

`render-single` 是 ConvertAsset 内置的轻量出图入口，用本仓库的 Isaac Sim Python wrapper 直接启动本地 `/isaac-sim`，不依赖 `/cpfs/shared/simulation/zhuzihou/dev/render-usd` 的独立 conda/py 环境。

## 适用场景

- 单个 USD 资产的四视角 smoke test；
- no-MDL 前后材质/纹理对比的原始图生成；
- ACL/VLM 实验中需要先验证某个资产能不能稳定出图；
- 后续 `render-manifest` 批处理的底层 worker。

它不是 `thumbnails` 的替代品。`thumbnails` 面向“场景内每个实例逐个找 prim 并带背景拍照”；`render-single` 面向“给一个 USD 文件整体绕圈拍几张标准物体图”。

## 快速开始

```bash
./scripts/isaac_python.sh ./main.py render-single \
  /path/to/asset.usd \
  --out /tmp/asset_renders \
  --naming-style view \
  --overwrite
```

默认会生成 4 张图：

```text
/tmp/asset_renders/<asset-stem>/front.png
/tmp/asset_renders/<asset-stem>/left.png
/tmp/asset_renders/<asset-stem>/back.png
/tmp/asset_renders/<asset-stem>/right.png
```

常用参数：

- `--width` / `--height`：输出分辨率，默认 `512x512`；
- `--views`：视角数，默认 `4`；
- `--naming-style view`：当 `--views 4` 时写出 `front/left/back/right.png`；
- `--warmup-steps` / `--render-steps`：传感器帧预热与渲染步数，默认 `100/8`；
- `--renderer`：默认 `PathTracing`；
- `--mdl-path`：补充 MDL 搜索目录，可重复指定，也会读取 `MDL_SYSTEM_PATH`。

## 迁移自 render-usd 的做法

保留的经验：

- `SimulationApp` 必须先启动，再导入 `omni` / `pxr` / Isaac sensor 模块；
- 一个 CLI 进程内只启动一个 Isaac app；
- 加载资产到固定 `/World/Show`，结束时删除 prim、reset world、释放相机资源；
- 用 USD bbox 加 mesh point fallback，避免极端 authored extent 把相机推得太远；
- `view` 命名兼容 `front/left/back/right`；
- 使用灰白背景和 alpha composite，保证透明区域不变成黑底。

没有迁移的部分：

- render-usd 的 conda/DLC bootstrap；
- GRScenes 专用硬编码路径和目录扫描；
- 大批量 chunk 调度；
- 场景内实例级 bbox 过滤逻辑。

## 已知注意点

- `--warmup-steps 1 --render-steps 1` 可能拿不到相机帧；实际 smoke test 建议使用默认 `100/8`。
- Headless 环境中 `GLFW initialization failed`、音频设备告警、Isaac 4.5 旧 namespace deprecation warning 通常不影响 PNG 输出。
- 资产本身如果有 corrupted normal primvar，Isaac 可能打印 mesh 警告；只要 PNG 非空且视觉审阅可用，先按资产质量问题记录。
