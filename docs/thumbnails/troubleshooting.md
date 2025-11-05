# 常见问题排查（troubleshooting）

## 1. `cv2` 与 `numpy` 的 ABI 不匹配

症状：
- ImportError 或运行时报错，提示 OpenCV loader 缺少配置、或者需要更低版本的 numpy

处理：
```bash
# 在 Isaac Sim Python 环境内执行
pip install --upgrade "numpy<2"
```
如仍有问题，确认 `opencv-python` 安装在相同环境内。

## 2. USD 引用资源缺失（Could not open asset）

症状：
- 渲染时不断出现 `Could not open asset @...@` 警告

说明：
- 这是被引用资产路径在当前数据集不存在（目录结构不匹配或软链指向错误）导致；可用 USDView 或自查目录结构确认
- 工具会跳过无法实际加载到 Mesh 的实例，导致可用实例数量减少

## 3. 渲染似乎“卡住”很久

现象：
- 前期长时间无图像输出

原因：
- 默认预热步数较大（1000），用于稳定曝光/光照；此外 PathTracing 本身较慢

建议：
- 调低 `--warmup-steps` 与 `--render-steps` 做快速试跑；改回默认值做正式批量

## 4. 没有检测到 2D bbox，导致不保存图片

原因：
- 目标过小/被遮挡/视角太偏，紧/松框面积比低于阈值

处理：
- 降低 `--bbox-threshold`（如 0.7），或增大 `--render-steps`；必要时提高分辨率或增加视角数

## 5. 退出/资源释放

说明：
- 工具内部会在流程结束后调用 `simulation_app.close()`；若在交互式会话中中断，可能需要手动重启会话

## 6. 作用域（instance-scope）找不到实例

现象：
- 输出为空或数量明显不对

处理：
- 确认 `--instance-scope` 实际存在，例如 `scene/Instances` 等价于 `/World/scene/Instances`；也可直接传绝对路径 `/World/...`
