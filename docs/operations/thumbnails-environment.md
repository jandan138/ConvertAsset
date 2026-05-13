# 运行环境与依赖（environment）

本功能依赖 NVIDIA Omniverse Isaac Sim 的渲染/标注能力，必须在其 Python 环境中运行：

## 进入运行环境

```bash
# 使用 Isaac Sim 提供的 Python 入口（路径以你的安装为准）
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails /abs/path/to/scene.usd
```

> 不支持在系统自带 Python 中直接运行（因依赖 SimulationApp、omni.*、pxr 等组件）。

## Python 依赖

- numpy（建议 1.26.x 版本，以匹配 opencv 的 ABI）
- opencv-python（cv2）
- scipy（Rotation 用于相机姿态）
- tqdm（进度条）

Isaac Sim 的 Python 环境中通常已包含大部分依赖；若你遇到 `cv2` 与 `numpy` 的 ABI 不匹配（常见报错：`cv2.error: OpenCV loader: missing configuration file: ... requires numpy<2`），请将 numpy 降级到 1.26.x：

```bash
# 在 Isaac Sim Python 环境中执行（示例）
pip install --upgrade "numpy<2" tqdm natsort
```

## USD/资产路径

- 本工具不修改 USD 解析器配置；如果你的场景引用了相对路径，请在 Isaac Sim 的工作目录或环境变量中确保可解析到资源
- 若场景内引用的某些模型路径不存在（例如某些目录结构在当前数据集中缺失），USD 将输出大量 "Could not open asset @...@" 的警告，属于数据层面的缺失，不是工具本身错误

## 渲染器与性能

- 默认使用 PathTracing 渲染，图像质量较高，但速度更慢
- `--warmup-steps` 与 `--render-steps` 影响时长；大场景/大量实例可能运行数小时
- 多视角渲染会按视角数线性增长耗时；建议先用较小步数/分辨率做预跑
