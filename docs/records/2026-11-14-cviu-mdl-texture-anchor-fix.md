# CVIU MDL 纹理路径基准修复

## 修复与证据

MDL 回退解析中的纹理原先按 USD 属性层目录解析；改为按实际 MDL 文件所在目录
解析。直接 USD pin 路径逻辑保持原样。未修改源数据和历史转换文件。

tests/test_mdl_texture_anchor.py 使用真实 USD，覆盖 MDL 子目录相对纹理、绝对纹理
及错误目录同名冲突。命令：

```bash
PYTHONPATH=. ./scripts/isaac_python.sh tests/test_mdl_texture_anchor.py
python -m pytest -q tests/test_cviu_inventory.py tests/test_grscenes_vlm_full_scratch_materializer.py
```

结果：USD 回归 1 test（两种路径 subcase）通过；已有基础测试 16 passed。

## 真实资产重转

独立副本位于 assets/convertasset_research/experiments/cviu/recovery_20261114/cabinet_probe。
原始 instance.usd 复制自 commercial pilot 中柜子 59d6ea5ff2e0102cf8b08f8e44f1412c，
Materials 只读链接到已有材质库。用 main.py no-mdl 重新转换。

原始与新转换各 20 meshes；点、面拓扑、世界变换摘要一致；二者依赖未解析数均为 0。
机器记录：[cabinet_probe.json](../../paper/shared/evidence/raw/cviu_diagnostics/recovery_20261114/cabinet_probe.json)。
这只证明该资产路径修复和静态几何一致，不能替代完整场景验证。

## 未完成

三场景副本完整恢复、转换的全覆盖检查、独立缓存的渲染调度、配对 RGB 视觉验收仍待完成。
首次 cabinet original 远端渲染使用 GPU 0、120 秒超时，结果另见同目录 render_attempt.json。
不把 GUI/CUDA 警告单独作为驱动故障诊断，也不重启主机或终止无关进程。

渲染结论：120 秒超时，退出码 124，未生成 PNG；停留在 app ready，尚未确认场景捕获。
