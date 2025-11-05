# 使用指南（usage）

## 基本命令

在 Isaac Sim 的 Python 环境中执行（必须）：

```bash
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails /abs/path/to/scene.usd
```

- 默认输出：`<usd目录>/thumbnails/multi_views_with_bg`
- 默认参数：宽 600、高 450、视角 6（偶数，上/下半球均分）、预热 1000 步、渲染 8 步、焦距 9.0mm、bbox 阈值 0.8、绘制 bbox、跳过 models 目录过滤

## 常用参数

```bash
# 自定义输出目录、分辨率、视角数量
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails \
  /abs/path/to/scene.usd \
  --out /abs/path/to/out \
  --width 800 --height 600 \
  --views 8

# 控制预热与渲染步数（越大越稳定，但更慢）
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails \
  /abs/path/to/scene.usd \
  --warmup-steps 200 --render-steps 4

# 设置实例作用域（相对于 /World 或给绝对路径）
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails \
  /abs/path/to/scene.usd \
  --instance-scope scene/Instances

# 关闭 bbox 绘制或调低阈值
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails \
  /abs/path/to/scene.usd \
  --no-bbox-draw --bbox-threshold 0.7

# 尝试开启基于 models 目录的过滤（默认跳过）
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails \
  /abs/path/to/scene.usd \
  --skip-model-filter
```

- `--instance-scope`：例如 `scene/Instances`（最终解析为 `/World/scene/Instances`），也可直接写绝对路径 `/World/Root/Inst`
- `--views`：必须为偶数，工具会将其一分为二（上/下半球）；若传入奇数会自动 +1
- 输出结构：`<out>/<PrimName>/<PrimName>_with_bg_<index>.png`

## 适配建议

- 视角数量与 bbox 阈值可按数据特性调整；如果上半球视角普遍丢检，可能是实例高度/遮挡问题，可放宽阈值或增大渲染步数
- 预热步数较大（默认 1000）主要为了稳定曝光/光照；在快速迭代时可临时调小以加快调试
- 输出目录建议放在与源 USD 同级，以便关联检查与数据打包
