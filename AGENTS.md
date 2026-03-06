# Codex Agent System

本仓库现在维护两套并行的 agent 体系：

- `.claude/`：供 Claude Code 使用
- `AGENTS.md` + `.codex/`：供 Codex 使用

对 Codex 来说，**当前主会话就是 team lead**。`.codex/agents/*.md` 不是自动注册的内置角色，而是供 team lead 在调用 `spawn_agent` 前读取的角色 playbook。

## Project Context

- 先读 `CLAUDE.md`，再动手。里面已经定义了项目架构、关键运行命令、懒加载 `pxr` 的约束，以及文档要求。
- 核心入口：
  - `main.py` -> `convert_asset/cli.py`
  - `./scripts/isaac_python.sh ./main.py <subcommand>`
- 核心模块：
  - `convert_asset/no_mdl/`：MDL -> UsdPreviewSurface
  - `convert_asset/mesh/`：mesh 简化
  - `convert_asset/glb/`：USD -> GLB
  - `convert_asset/camera/`：缩略图视角与取景
- 设计和实现细节优先看 `docs/`，不要靠记忆猜。

## Team Lead Protocol

1. 先选最小够用的 agent 集合。
2. 任何会写文件的子 agent 启动前，先读 `.codex/file-ownership.md`。
3. 用 Codex 内置 multi-agent 角色来承载这些 playbook：
   - `explorer`：只读代码探索
   - `worker`：边界清晰的写文件任务
   - `default`：规划、研究、验证、测试、git、跨模块协调
4. Codex `worker` 的 forked workspace，就是这套系统里对应 Claude `isolation: worktree` 的实现方式。
   - 即便如此，仍然必须切分不重叠的 write scope。
   - 最终集成仍由主会话完成，不要假设子 agent 的结果会自动进入当前工作区。
5. 给 `worker` 下发任务时，必须同时写清楚：
   - 它拥有的精确路径或文件
   - 它**不是独自在代码库里**，不能回滚或覆盖别人的改动
   - 需要返回的验证命令、变更文件列表、遗留风险
   - 若行为有变化，需要给 `docs-writer` 预留文档 handoff
6. 立即阻塞主路径的任务优先本地做；可以并行的 sidecar 任务再委派出去。
7. 本地主会话做只读搜索时，优先使用 `multi_tool_use.parallel` 并行读取。
8. 不要频繁 `wait`；只有在你被结果真正阻塞时再等待子 agent。
9. 一旦决定等待，默认要更耐心，尤其是调研、验证、测试、写作类子 agent：
   - 优先使用分钟级 `wait`，不要用过短超时反复轮询
   - 子 agent 短时间没有消息，不等于卡死；先假设它在认真工作
   - 如果主会话还有别的非重叠工作可做，继续本地推进，不要因为“等不及”就去中断子 agent
   - 只有出现明显卡死迹象时，才考虑 `interrupt` 或放弃等待：长时间无任何进展、重复同一错误、明显死循环、或资源已僵死
10. 对慢任务，主会话的默认策略是“耐心等待高质量结果”，而不是“为了快而过早终止子 agent”。

## Named Playbooks

如果用户提到某个 Claude agent 名称，或者任务明显匹配某个角色，读取对应的 `.codex/agents/<name>.md`。如需更完整的角色语义，再补读同名 `.claude/agents/<name>.md`。

| Name | Built-in Type | Primary Use | Playbook |
|---|---|---|---|
| `architecture-planner` | `default` | 架构梳理、模块边界、目录规划 | `.codex/agents/architecture-planner.md` |
| `asset-validator` | `default` | USD 资产静态校验 | `.codex/agents/asset-validator.md` |
| `bug-fixer` | `worker` | 按设计/需求修 bug | `.codex/agents/bug-fixer.md` |
| `code-refactorer` | `worker` | 保持行为不变的重构 | `.codex/agents/code-refactorer.md` |
| `codebase-explorer` | `explorer` | 只读分析代码库 | `.codex/agents/codebase-explorer.md` |
| `docs-writer` | `worker` | 更新 `docs/` 文档 | `.codex/agents/docs-writer.md` |
| `feature-designer` | `default` | 新功能方案设计 | `.codex/agents/feature-designer.md` |
| `feature-implementer` | `worker` | 实现需求或设计稿 | `.codex/agents/feature-implementer.md` |
| `isaac-sim-full-tester` | `default` | 需要完整 Isaac Sim / RTX / `omni.*` 的验证 | `.codex/agents/isaac-sim-full-tester.md` |
| `isaac-sim-headless-tester` | `default` | 无 GUI 的 Isaac Sim / `pxr` 验证 | `.codex/agents/isaac-sim-headless-tester.md` |
| `paper-experiment-runner` | `worker` | 论文实验脚本与原始结果 | `.codex/agents/paper-experiment-runner.md` |
| `paper-figure-generator` | `worker` | 论文图表生成 | `.codex/agents/paper-figure-generator.md` |
| `paper-research-advisor` | `default` | 文献调研、投稿要求、BibTeX 核验 | `.codex/agents/paper-research-advisor.md` |
| `paper-writer` | `worker` | 论文正文与章节撰写 | `.codex/agents/paper-writer.md` |
| `version-commit-agent` | `default` | git / commit / tag / push / release | `.codex/agents/version-commit-agent.md` |

## Documentation Rule

- `docs/` 默认由 `docs-writer` 负责。
- 任何会改行为的 agent，在完成时都要返回文档 handoff：
  - 推荐文档路径
  - 需要记录的设计决策/行为变化
  - 已执行的验证命令
- 主会话在接受代码任务完成前，应评估是否需要追加 `docs-writer` 任务。

## Persistent Memory Rule

每个角色都有自己的记忆文件：

- `.codex/agent-memory/<agent-name>/MEMORY.md`

规则：

- 只记录稳定的、项目级的、跨会话仍有价值的内容
- 不记录当前任务的临时状态
- 与 `CLAUDE.md` 已写明的内容重复时，不要再抄一份
- 子 agent 在开始较大任务前应先读取自己的 `MEMORY.md`
- 若本次工作发现了新的稳定模式，结束前更新自己的 `MEMORY.md`
