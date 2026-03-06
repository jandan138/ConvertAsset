# docs-writer

## Mirror

- Canonical role spec: `.claude/agents/docs-writer.md`

## Codex Mapping

- Built-in agent type: `worker`
- Writes: `docs/`
- Parallel-safe when: doc files do not overlap
- Memory: `.codex/agent-memory/docs-writer/MEMORY.md`

## Use When

- 需要在 `docs/` 下新增或更新 Markdown 文档
- 代码或流程有变化，需要补 changes entry、feature spec、architecture note

## Must Read

- `CLAUDE.md`
- `.codex/file-ownership.md`
- `.codex/agent-memory/docs-writer/MEMORY.md`
- `.claude/agents/docs-writer.md`
- existing docs near the target path

## Dispatch Contract

- 不改源码
- 先读现有文档和相关代码，再写文档
- 保持语言、层次、文件命名与现有 `docs/` 一致

## Return To Lead

- created or updated doc paths
- what was documented
- follow-up doc suggestions
