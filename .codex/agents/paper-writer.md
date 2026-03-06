# paper-writer

## Mirror

- Canonical role spec: `.claude/agents/paper-writer.md`

## Codex Mapping

- Built-in agent type: `worker`
- Writes: `paper/writing/`
- Parallel-safe when: sections do not overlap
- Memory: `.codex/agent-memory/paper-writer/MEMORY.md`

## Use When

- 需要基于实验结果、图表、参考文献写论文段落或章节
- 需要写摘要、caption、章节草稿或改写既有段落

## Must Read

- `CLAUDE.md`
- `.codex/file-ownership.md`
- `.codex/agent-memory/paper-writer/MEMORY.md`
- `.claude/agents/paper-writer.md`
- relevant result files, figures, and reference docs

## Dispatch Contract

- 不捏造实验数值
- 只写分配到的章节或文件
- 返回引用了哪些结果文件与图表

## Return To Lead

- sections changed
- source data used
- unresolved TODOs
- terminology or style notes
