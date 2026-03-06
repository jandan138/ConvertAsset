# feature-implementer

## Mirror

- Canonical role spec: `.claude/agents/feature-implementer.md`

## Codex Mapping

- Built-in agent type: `worker`
- Writes: the exact implementation scope assigned by team lead
- Parallel-safe when: write scope is disjoint
- Memory: `.codex/agent-memory/feature-implementer/MEMORY.md`

## Use When

- 需要把需求、设计稿、ticket 落成代码
- 需要新增 CLI 子命令、模块、后端或 pipeline 步骤

## Must Read

- `CLAUDE.md`
- `.codex/file-ownership.md`
- `.codex/agent-memory/feature-implementer/MEMORY.md`
- `.claude/agents/feature-implementer.md`
- relevant docs and source files

## Dispatch Contract

- 明确拥有的文件/目录
- 明确提醒不要回滚他人改动
- 在 forked workspace 内完成实现，并返回改动文件列表
- 若行为有变化，返回 docs handoff

## Return To Lead

- implementation summary
- changed files
- validation commands and results
- open risks
- documentation handoff
