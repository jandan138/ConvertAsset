# 命令行用法（Python 后端）

统计面数：
```
python -m convert_asset.cli mesh-faces <stage.usd>
```

按目标总面数进行规划（只计算建议 ratio，不真正减面）：
```
python -m convert_asset.cli mesh-simplify <stage.usd> --target-faces 80000
```

用 Python 后端执行减面（写回并导出）：
```
python -m convert_asset.cli mesh-simplify <stage.usd> \
  --ratio 0.5 --apply --out <out.usd> \
  --progress --progress-interval-collapses 10000 --time-limit 120
```

Isaac 环境示例（带 USD 路径与进度）：
```
PYTHONPATH=/opt/my_dev/ConvertAsset:$PYTHONPATH \
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py \
  mesh-simplify /path/to/scene.usd \
  --backend py --ratio 0.8 --apply --out /tmp/scene_simplified.usd \
  --time-limit 30 --progress
```

参数说明：
- `--ratio r` 目标面数比率 (0..1]；若同时给出 `--target-faces`，会先计算建议 ratio；
- `--apply` 将结果写回 Stage，并导出到 `--out`；
- `--out` 输出 USD 路径（当 `--apply` 时必填）；
- `--progress` 展示周期性进度；频率通过 `--progress-interval-collapses` 指定（单位：坍塌次数）；
- `--time-limit` 单网格的时间上限（秒）；
- `--backend {py,cpp}` 选择后端。若选择 cpp，请参考 `../native_meshqem/` 文档。
