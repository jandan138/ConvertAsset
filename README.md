# ConvertAsset

> USD asset conversion and optimization toolkit for NVIDIA Isaac Sim

## 概述

ConvertAsset 面向 Isaac Sim / USD 资产处理，提供一组轻量、可组合的转换与优化工具：

- 将 MDL 材质转换为 `UsdPreviewSurface`，生成可移植的 `*_noMDL.usd`；
- 简化三角网格，支持 Python QEM 与可选 C++/pybind11 后端；
- 将 USD 资产导出为 GLB；
- 渲染缩略图、检查材质网络、导出独立 MDL 材质球；
- 保留 USD composition 结构，不默认 flatten 引用、payload、variant 或 clip。

## 目录结构

| 目录 | 用途 |
|---|---|
| `convert_asset/` | Python 源码 |
| `native/meshqem/` | 可选 C++ QEM 后端 |
| `scripts/` | Isaac Sim Python wrapper 和辅助脚本 |
| `examples/` | 小型示例资产 |
| `docs/` | 设计、运维、记录和参考文档 |
| `archive/` | 旧索引、legacy 文档和非当前工程主线历史材料 |

## 快速开始

所有需要 `pxr` 的命令都应通过 Isaac Sim Python 环境运行。推荐入口是仓库内 wrapper：

```bash
./scripts/isaac_python.sh ./main.py <subcommand> [args]
```

常用命令：

```bash
# no-MDL 转换
./scripts/isaac_python.sh ./main.py no-mdl /abs/path/to/scene.usd

# 一站式 USD -> GLB
./scripts/isaac_python.sh ./main.py usd-to-glb /abs/path/to/scene.usd --out /abs/path/to/scene.glb

# Mesh 简化
./scripts/isaac_python.sh ./main.py mesh-simplify /abs/path/to/scene.usd \
  --backend py --ratio 0.5 --apply --out /abs/path/to/scene_simplified.usd

# 材质检查
./scripts/isaac_python.sh ./main.py inspect /abs/path/to/scene.usd usdpreview /Looks/MaterialName

# 面数统计
./scripts/isaac_python.sh ./main.py mesh-faces /abs/path/to/scene.usd
```

如果 wrapper 无法自动定位 Isaac Sim，请设置：

```bash
export ISAAC_SIM_ROOT=/abs/path/to/isaac-sim
```

## 核心命令

| 命令 | 用途 |
|---|---|
| `no-mdl` | 递归生成无 MDL 的 `*_noMDL.usd` 资产 |
| `mesh-simplify` | 简化 USD Mesh，支持 `py`、`cpp`、`cpp-uv` 后端 |
| `mesh-faces` | 统计 USD Mesh 面数 |
| `export-glb` | 将已准备好的 USD 导出为 GLB |
| `usd-to-glb` | 执行 no-MDL -> GLB 的一站式管线 |
| `inspect` | 只读检查 MDL 或 UsdPreviewSurface 材质网络 |
| `export-mdl-materials` | 将场景中的 MDL 材质导出为独立材质球 USD |
| `thumbnails` | 批量渲染带背景的资产缩略图 |

## 文档

详见 [docs/index.md](docs/index.md)。

入口建议：

- [Setup](docs/setup.md)
- [运维文档](docs/operations/README.md)
- [设计文档](docs/design/README.md)
- [过程记录](docs/records/README.md)
- [参考资料](docs/reference/README.md)

## Agent 入口

- [CLAUDE.md](CLAUDE.md) 是 Claude Code / 项目架构约束入口。
- [AGENTS.md](AGENTS.md) 是 Codex team lead 和 multi-agent 协作入口。
