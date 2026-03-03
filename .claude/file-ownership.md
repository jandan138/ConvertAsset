# 文件归属表（File Ownership Map）

> 本文件供 Agent Teams 使用：team lead 依此分配任务，version-commit-agent 依此规划合并顺序。
> **同一文件在一次 Agent Teams 会话中只能由一个 agent 修改**；若多个 agent 需触及同一文件，应串行而非并行。

## 代码模块归属

| 路径 | 负责 Agent | 说明 |
|---|---|---|
| `convert_asset/no_mdl/` | feature-implementer, code-refactorer | MDL 转换核心：processor、materials、references、config |
| `convert_asset/glb/` | feature-implementer, code-refactorer | GLB 导出管道：converter、usd_mesh、usd_material、writer |
| `convert_asset/mesh/` | feature-implementer, code-refactorer | 网格简化：simplify、backend_cpp、backend_cpp_impl |
| `convert_asset/camera/` | feature-implementer | 缩略图摄像机：fit、orbit |
| `convert_asset/cli.py` | feature-implementer | 新增子命令必须经此文件；高冲突风险，多功能时串行处理 |
| `convert_asset/export_mdl_materials.py` | feature-implementer, code-refactorer | MDL 材质导出 |
| `convert_asset/thumbnail.py` | feature-implementer | 缩略图生成管道 |
| `convert_asset/inspect_material.py` | feature-implementer, bug-fixer | 材质检查工具 |
| `native/meshqem/` | feature-implementer | C++ QEM backend（需重新编译） |

## 文档归属

| 路径 | 负责 Agent | 说明 |
|---|---|---|
| `docs/` | docs-writer | 所有文档；其他 agent 只读，不直接修改 |
| `CLAUDE.md` | team lead / 手动 | 项目级指令；需人工审核，不由 agent 自动修改 |

## 测试与验证

| 路径 | 负责 Agent | 说明 |
|---|---|---|
| `tests/` | isaac-sim-headless-tester | 验证脚本；tester 负责新建和维护 |

## 基础设施（仅 team lead 或手动操作）

| 路径 | 负责 Agent | 说明 |
|---|---|---|
| `.claude/agents/` | team lead / 手动 | Agent 定义；不由代码类 agent 修改 |
| `.claude/file-ownership.md` | team lead / 手动 | 本文件；需人工维护 |
| `.gitignore` | team lead / 手动 | 需人工审核 |
| `scripts/` | team lead / 手动 | Isaac Sim 启动脚本；慎改 |

## 高冲突风险文件

以下文件被多个模块依赖，在 Agent Teams 并行时需特别注意：

| 文件 | 风险原因 | 推荐处理方式 |
|---|---|---|
| `convert_asset/cli.py` | 所有新子命令均在此注册 | 多功能时串行，或由 team lead 统一处理 |
| `convert_asset/no_mdl/config.py` | 全局配置，各模块都引用 | 同一 team 只允许一个 agent 修改 |
| `convert_asset/no_mdl/path_utils.py` | 工具函数，被多个模块 import | 同上 |

## 规则摘要

1. **并行安全**：各 agent 改动不重叠的路径（如 feature-implementer A 改 `glb/`，B 改 `mesh/`）
2. **并行危险**：两个 agent 都需要改同一个文件
3. **合并顺序**：version-commit-agent 应先合并改动范围最小、最独立的分支
4. **超范围警告**：若 agent 的改动超出本表所列范围，version-commit-agent 须在合并前报告 team lead
