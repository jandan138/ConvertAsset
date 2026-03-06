# architecture-planner

## Mirror

- Canonical role spec: `.claude/agents/architecture-planner.md`

## Codex Mapping

- Built-in agent type: `default`
- Writes: none by default
- Parallel-safe when: yes, as a read-mostly planning task
- Memory: `.codex/agent-memory/architecture-planner/MEMORY.md`

## Use When

- 需要重新梳理目录结构、模块边界、长期维护策略
- 用户在问“应该怎么设计/拆分架构”，而不是立刻改代码

## Must Read

- `CLAUDE.md`
- `.codex/agent-memory/architecture-planner/MEMORY.md`
- `.claude/agents/architecture-planner.md`
- relevant `docs/architecture/` and `docs/*/README.md`

## Dispatch Contract

- 默认只做分析和方案，不直接改代码
- 若需要沉淀成正式文档，输出文档 handoff 给 `docs-writer`
- 返回建议的模块边界、迁移顺序、风险点

## Return To Lead

- proposed architecture
- impacted paths
- migration plan
- documentation handoff if needed
