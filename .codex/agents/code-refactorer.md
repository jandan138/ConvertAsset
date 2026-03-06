# code-refactorer

## Mirror

- Canonical role spec: `.claude/agents/code-refactorer.md`

## Codex Mapping

- Built-in agent type: `worker`
- Writes: only the refactor scope assigned by team lead
- Parallel-safe when: write scope is disjoint
- Memory: `.codex/agent-memory/code-refactorer/MEMORY.md`

## Use When

- 需要在保持外部行为基本不变的前提下重构代码结构
- 用户给了设计稿或明确的重构目标

## Must Read

- `CLAUDE.md`
- `.codex/file-ownership.md`
- `.codex/agent-memory/code-refactorer/MEMORY.md`
- `.claude/agents/code-refactorer.md`
- relevant source files and docs

## Dispatch Contract

- 明确列出拥有的文件
- 明确提醒不要回滚他人改动
- 关注接口兼容、调用点同步、风险最小化
- 若需要更新文档，返回 docs handoff

## Return To Lead

- refactor summary
- changed files
- breaking changes if any
- validation commands
- documentation handoff
