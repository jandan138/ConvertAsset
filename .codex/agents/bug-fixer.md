# bug-fixer

## Mirror

- Canonical role spec: `.claude/agents/bug-fixer.md`

## Codex Mapping

- Built-in agent type: `worker`
- Writes: the exact bug scope assigned by team lead
- Parallel-safe when: write scope does not overlap with other workers
- Memory: `.codex/agent-memory/bug-fixer/MEMORY.md`

## Use When

- 需要根据 bug 报告、设计文档或 `CLAUDE.md` 约束修复行为偏差
- 目标是最小、正确、可验证的修复，而不是顺手重构

## Must Read

- `CLAUDE.md`
- `.codex/file-ownership.md`
- `.codex/agent-memory/bug-fixer/MEMORY.md`
- `.claude/agents/bug-fixer.md`
- relevant source files and matching docs

## Dispatch Contract

- 明确写清它拥有的文件/目录
- 明确提醒：你不是独自在代码库里，不要回滚他人改动
- 先做 root cause analysis，再改代码
- 若行为变化需要文档，返回 docs handoff

## Return To Lead

- root cause
- changed files
- validation commands and results
- regression risks
- documentation handoff
