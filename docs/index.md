# ConvertAsset 文档

> 最后更新: 2026-05-13

## 快速导航

- **[设计文档](design/README.md)** - 架构、模块职责、算法与实现深挖
- **[运维文档](operations/README.md)** - 运行环境、CLI、构建、排障与 agent 协作
- **[Setup](setup.md)** - Isaac Sim Python 与可选 native backend 环境说明
- **[过程记录](records/README.md)** - 变更日志、实现记录、审计与路线记录
- **[参考资料](reference/README.md)** - USD、UsdShade、MDL 与材质背景知识
- **[Superpowers 内部流程](superpowers/README.md)** - 本次设计/计划流程产物
- **[归档材料](../archive/README.md)** - 旧索引、legacy 文档、论文/提交相关历史材料

## 项目概述

ConvertAsset 是面向 NVIDIA Isaac Sim / USD 资产的转换与优化工具集。核心能力包括 no-MDL 转换、mesh 简化、USD 到 GLB 导出、缩略图渲染、材质检查与 MDL 材质导出。

所有需要 `pxr` 的命令都应通过 Isaac Sim Python 环境运行：

```bash
./scripts/isaac_python.sh ./main.py <subcommand> [args]
```

## 当前主线

- no-MDL：保留 composition，不 flatten，递归生成 `*_noMDL.usd`；
- mesh：Python QEM 为默认实现，C++ / `cpp-uv` 为可选加速路径；
- GLB：纯 Python 导出，支持 face-varying UV flattening 与 PBR 贴图；
- camera/thumbnails：为资产缩略图提供 orbit camera framing；
- docs：采用 Genesis-LLM 风格的 purpose-based taxonomy。

## 结构说明

主导航遵循 `design/`、`operations/`、`records/`、`reference/`、`archive/` 的用途分类。
`docs/superpowers/` 是内部流程例外，用于保存 superpowers 设计与执行计划证据，不作为用户功能文档分类。
