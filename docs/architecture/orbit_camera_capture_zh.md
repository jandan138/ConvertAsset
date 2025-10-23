# 轨道相机抓取架构

## 概览
本文档说明如何在无界面（headless）环境下执行轨道相机抓取流程，用于生成室内参考渲染。该方案整合了两套工具：

1. `convert_asset.cli camera-orbit`：当源场景没有相机动画时，合成带有时间采样变换的 `UsdGeom.Camera`。
2. `scripts/render_with_viewport_capture.py`：在 Isaac Sim 中打开导出的场景，绑定指定相机到视口，驱动时间线并将每帧图像写入磁盘。

整个链路完全运行在 headless 模式下，并针对只实现了部分 USD 时间码接口的场景做了兼容处理。

## 主要组件
- **轨道相机生成（`convert_asset/camera/orbit.py`）**：计算兜底（fallback）内参与相机绕物旋转位置，写出带整数时间码的动画片段。CLI 包装（`convert_asset/cli.py`）暴露距离缩放、最小距离、视场、帧数等参数。
- **Headless 渲染器（`scripts/render_with_viewport_capture.py`）**：启动 `SimulationApp`，确保启用视口扩展，通过 `omni.usd.get_context()` 加载场景并负责抓图流程。
- **时间线桥接**：使用 `omni.timeline.get_timeline_interface()` 把作者的时间码转换为秒，让 RTX 渲染器准确采样每一帧的相机变换。

## 执行流程
1. **导出轨道相机**：
   ```bash
   /isaac-sim/python.sh -m convert_asset.cli camera-orbit \
     --usd /path/to/source.usd \
     --output /path/to/orbit_camera.usd \
     --camera-path /World/OrbitCam \
     --frames 10 \
     --fallback-horizontal-fov 68 \
     --fallback-aspect-ratio 1.7777778 \
     --fallback-distance-scale 1.2 \
     --fallback-min-distance 0.8
   ```
   - 读取原始场景，计算几何包围球，生成 `/World/OrbitCam` 并在帧 `0..frames-1` 上写出 `xformOp:transform` 时间采样。
   - 同步写出场景元数据（如 `timeCodesPerSecond`），方便渲染流程沿用作者定义的时间节奏。

2. **Headless 抓取**：
   ```bash
   /isaac-sim/python.sh scripts/render_with_viewport_capture.py \
     --usd-path /path/to/orbit_camera.usd \
     --camera /World/OrbitCam \
     --output-dir /path/to/images \
     --prefix orbit_cli \
     --ext png \
     --headless
   ```
   - 以 `headless=True` 和 `RayTracedLighting` 预设创建 `SimulationApp`。
   - 若运行环境未启用 UI 扩展，自动打开 `omni.kit.viewport`。
   - 通过 USD 上下文打开场景，在持续调用 `_wait_frames` 的同时等待异步加载结束。
   - 解析场景的起止帧（缺失 `HasStartTimeCode` 等接口时回退到 `0`）。
   - 配置视口分辨率并绑定 CLI 指定的相机 prim。

3. **逐帧推进**：
   - 获取全局时间线接口，依次调用：
     - `timeline.set_time_codes_per_second(stage.GetTimeCodesPerSecond())` 保持与场景一致的时间单位。
     - `timeline.time_code_to_time(code)` 将整数帧映射为 SimulationApp 的秒。
     - `timeline.set_current_time(...)` 依次设置当前采样时间。
   - 当环境支持时，通过 `usd_context.set_timeline(...)` 将 USD 上下文和活跃时间线绑定，保证二者同步。
   - 在每次抓取前等待若干模拟帧（`--wait-frames`），让渲染器收敛。

4. **输出图像**：
   - 调用 `omni.kit.viewport.utility.capture_viewport_to_file`，按照指定前缀与零填充序号写出 PNG。
   - 每帧日志都会记录绝对路径及对应的时间码，方便追溯。

## 关键实现细节
- **时间码兼容**：部分 USD 封装只提供 `GetStartTimeCode`，没有 `HasStartTimeCode`。`_maybe_stage_timecode` 为所有调用加了保护，缺失时回退到 `0.0`，确保循环稳定。
- **时间线同步**：Isaac Sim 4.5 不支持直接调用 `usd_context.set_time_code`。通过时间线 API 转换时间码，可确保变换、材质等动画属性被正确解析。
- **视口获取**：Headless 会话不保证存在视口实例。`_get_viewport` 先尝试现代视口接口，再退回 legacy 接口，确保始终有渲染目标。
- **加载等待**：场景加载与扩展切换是异步的。脚本在轮询 `ctx.is_stage_loading()`、`ctx.is_standby()` 时持续执行 `_wait_frames`，直到场景完全就绪。

## 典型故障与规避措施
- **缺少视口扩展**：脚本会自动启用 `omni.kit.viewport`。若扩展仓库不可用，会在抓取前输出错误。
- **帧画面静止**：以往由于时间线单位不匹配导致。改用时间线驱动后，可按 `timeCodesPerSecond` 正确推进。
- **Primvar 警告 / 资源缺失**：这些告警源自作者环境的 USD 资产，抓取脚本会原样透出，供独立排查。

## 验证清单
- 手动查看若干输出帧（例如 0000、0003、0006、0009）以确认轨道覆盖期望角度。
- 远程环境可用文件大小差异作为相机运动的快速凭证。
- 在 `docs/changes/orbit_camera_headless.md` 保留导出与抓取命令，确保流程可复现。

## 后续优化方向
- 通过 CLI 参数化渲染质量或降噪选项。
- 将“轨道导出 + headless 抓取”打包成自动化脚本或 CI 任务。
- 引入结构相似度等指标，对比抓取结果与基线图片，构建回归测试。
