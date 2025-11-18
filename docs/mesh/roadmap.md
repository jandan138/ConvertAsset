# 路线图（Roadmap，UV-aware 版本）

本小节描述基于 UV-aware C++ QEM 后端后的后续改进方向。

## 已完成

- Python 参考实现 `qem_simplify_ex`，支持 face‑varying UV 的携带；
- C++ QEM 内核扩展 `Mesh::face_uvs`，在压缩阶段同步保持 per-face UV triplets；
- pybind11 模块 `meshqem_py`，允许 Python 在内存中调用 C++ 并传递 UV；
- CLI 支持 `--backend cpp-uv`，用于启用 UV-aware C++ 后端；
- 文档与 README 更新，覆盖环境配置和使用示例。

## 规划中的功能

- 更细粒度的性能基准：
  - 针对不同面数区间（10k / 100k / 1M）比较 `py` / `cpp` / `cpp-uv`；
  - 分析 I/O（OBJ 写读）与纯内存路径的开销差异。

- UV 质量评估工具：
  - 在简化前后对比 UV 拉伸/折叠情况（目前仅保证拓扑上一致）；
  - 支持对选定 Mesh 进行可视化检查（例如输出 UV heatmap 或统计指标）。

- 更丰富的 C++ 选项暴露：
  - 通过 pybind11 暴露更多 `SimplifyOptions` 字段，如边界保护、法线约束等（若在 C++ 内核中实现）；
  - 提供更高层的“质量预设”（quality presets），如 `fast` / `balanced` / `high-quality`。

- 与 `uv-audit` 的联动：
  - 在 `cpp-uv` 路径处理前后自动调用 UV 体检，形成一份报告；
  - 提供“只对通过 UV 体检的 Mesh 执行 C++ 简化”的选项。

## 兼容性与迁移建议

- 旧文档与仅 Python 后端相关内容已移动到 `docs/mesh/legacy/` 下，作为参考存档；
- 现有调用方无需改动即可继续使用 `--backend py`；
- 推荐对性能敏感、且 UV 质量可接受“只删面”的场景逐步迁移到 `--backend cpp-uv`，在必要时用 `--backend cpp` 或纯 Python 进行对比验证。
