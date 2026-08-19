# isaac-sim-headless-tester Memory

只记录稳定的、项目级的、跨会话仍有价值的 headless 验证经验。

- 记录 `pxr` 检查套路、批量加载经验、常见报错原因
- 不记录单次运行日志

## 运行时环境（本机，2026-08 验证）

- `/isaac-sim` 是 4.5.0-rc，**不是** 4.1。需要 Isaac 4.1 指纹的资格/录制脚本必须用 conda 环境
  `/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python`（pip 版 isaacsim 4.1.0）。
- 该环境没有 `imageio_ffmpeg`，但有系统 `/usr/bin/ffmpeg`；mp4 用 PNG 帧 + ffmpeg 编码。
- 从 repo 根以 `python -m scripts.xxx` 方式跑脚本（无 `scripts/__init__.py`，靠 cwd 进 sys.path）。
- 跑 Isaac CLI 加 `-u`：Kit 在 C++ 层硬退出时 Python stdout 缓冲会丢，未缓冲才能看到 Traceback。

## Headless 录制 / 关节驱动（本机，2026-08 验证）

- `capture_viewport_to_file` 在本机 headless 不可用（GLFW 初始化失败，首帧空网格、后续黑帧）。
  已验证路径是 `omni.isaac.sensor.Camera` RGBA readback（`convert_asset/render/single.py` 的
  `_init_camera`/`_camera_rgba`/`_rgba_to_rgb`/`_save_rgb_png`，与 AAN runtime-smoke 同一机制）。
- sensor render product 滞后一拍：每帧摆好位姿后渲染两次再读 RGBA。
- Isaac 4.1 的单例 `Articulation` 没有 `set_joint_position_targets`；用 `articulation._articulation_view`。
- 不要调 `app.close()`（可能在证据落盘前杀掉解释器）；Kit teardown 可能在进程退出时段错误，
  CLI 写完证据后 `sys.stdout.flush()` + `os._exit(code)`（与 `runtime_smoke.py` 一致）。

## 物理落体 / 碰撞（本机，2026-08 验证）

- `physics:kinematicEnabled` 运行时切换可用：kinematic 摆位 → Set(False) 后刚体从静止自由落体。
- **静态碰撞圆盘半径 < ~15 mm 会被 PhysX 忽略**（实测 r=8.4/12 穿落、r=15/20/50 正常，
  contactOffset 覆盖无效）；小型杯底碰撞盘直接做到 r≥15 mm。
- 小物体落体用 1/240 s dt；~0.65 m/s 冲击在 r≥15 mm、4 mm 厚圆盘上无穿透（无需 CCD——
  CCD 与 kinematic 同设会被忽略）。
- 平面薄板上的"顶点距离"查不出几何（大平面只在边界有顶点）；量孔深/座位要走
  Möller–Trumbore raycast 打面，别数顶点。
- USDA `matrix4d` 文本存储的是有效变换的**转置**（Gf 打印即转置）：程序化写矩阵 prim 时
  先转置再写入，并用"回读组合"测试钉住（r10 杯孔碰撞踩过两次）。
- 给碰撞代理标 `visibility="invisible"` 会缩小包的**视觉 AABB**；benchtop 挂载合同按
  视觉 AABB 卡 `qualified_reset_geometry`，改 visible→invisible 后必须重测该几何再跑门。
- 接触矩阵 `get_contact_force_matrix` 形状 (1, n_filters, 3)：读 tube-lid 接触要选对
  filter 通道（本项目 [ROTOR, LID] → ch1 才是盖），读错通道会把"坐底接触"误判成盖碰。
