# Codex Multi-Agent File Ownership Map

> 本表供 Codex 主会话在分配 `worker` 任务前使用。
> **同一文件在一次 multi-agent 会话中只能由一个写入型 agent 拥有。**
> 若多个 agent 需要触及同一文件，必须串行，不要并行。

## 代码模块归属

| 路径 | 推荐 Agent | 说明 |
|---|---|---|
| `convert_asset/no_mdl/` | `feature-implementer`, `code-refactorer`, `bug-fixer` | MDL 转换核心：processor、materials、references、config |
| `convert_asset/glb/` | `feature-implementer`, `code-refactorer`, `bug-fixer` | GLB 导出管道 |
| `convert_asset/mesh/` | `feature-implementer`, `code-refactorer`, `bug-fixer` | 网格简化与 C++ backend |
| `convert_asset/camera/` | `feature-implementer`, `bug-fixer` | 缩略图摄像机与取景 |
| `convert_asset/cli.py` | `feature-implementer`, `bug-fixer` | 子命令注册入口，高冲突文件 |
| `convert_asset/export_mdl_materials.py` | `feature-implementer`, `code-refactorer` | MDL 材质导出 |
| `convert_asset/thumbnail.py` | `feature-implementer`, `bug-fixer` | 缩略图生成管线 |
| `convert_asset/inspect_material.py` | `feature-implementer`, `bug-fixer` | 材质检查工具 |
| `native/meshqem/` | `feature-implementer`, `code-refactorer` | C++ QEM backend |
| `main.py` | `feature-implementer`, `bug-fixer` | 入口，通常只做轻量接线 |

## 文档归属

| 路径 | 推荐 Agent | 说明 |
|---|---|---|
| `docs/` | `docs-writer` | 项目文档与变更记录 |
| `paper/references/` | `paper-research-advisor` | 文献、BibTeX、核查报告 |
| `paper/writing/` | `paper-writer` | 论文章节 |

## 测试与验证归属

| 路径 | 推荐 Agent | 说明 |
|---|---|---|
| `tests/` | `isaac-sim-headless-tester` | 若后续补测试目录，优先由 tester 维护 |
| `paper/experiments/` | `paper-experiment-runner` | 论文实验脚本 |
| `paper/results/raw/` | `paper-experiment-runner` | 原始数据输出，只写不删 |
| `paper/results/figures/` | `paper-figure-generator` | 图表输出，只读 raw/，只写 figures/ |

## 基础设施归属

| 路径 | 推荐 Agent | 说明 |
|---|---|---|
| `AGENTS.md` | team lead / 手动 | Codex 项目级指令 |
| `.codex/agents/` | team lead / 手动 | Codex 角色定义 |
| `.codex/file-ownership.md` | team lead / 手动 | 本文件 |
| `.codex/agent-memory/` | 对应 agent / team lead | 共享持久化记忆 |
| `.claude/` | team lead / 手动 | Claude 侧系统，默认不要自动改 |
| `.gitignore` | team lead / 手动 | 需人工审核 |
| `scripts/` | team lead / 手动 | Isaac Sim 启动/渲染脚本，慎改 |

## 高冲突风险文件

| 文件 | 风险原因 | 推荐处理方式 |
|---|---|---|
| `convert_asset/cli.py` | 几乎所有新功能都可能接入这里 | 串行处理，或由主会话统一集成 |
| `convert_asset/no_mdl/config.py` | 全局配置，被多个模块依赖 | 同轮只允许一个 writer 修改 |
| `convert_asset/no_mdl/path_utils.py` | 被多个 no_mdl 模块复用 | 同轮只允许一个 writer 修改 |
| `paper/references/references.bib` | 多个文献任务都可能触及 | 文献相关任务串行 |

## 并行规则摘要

1. 读任务可以并行：`explorer`、研究、校验、只读检查
2. 写任务仅在 write scope 不重叠时并行
3. `worker` 的 forked workspace 不是免冲突许可证；主会话集成时仍要按范围检查
4. 若子 agent 的改动超出本表所述范围，主会话必须先审查，再决定是否集成
