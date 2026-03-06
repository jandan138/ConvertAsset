# paper-research-advisor

## Mirror

- Canonical role spec: `.claude/agents/paper-research-advisor.md`

## Codex Mapping

- Built-in agent type: `default`
- Writes: `paper/references/` when explicitly asked; otherwise may stay read-only
- Parallel-safe when: yes, but serialize edits to `references.bib`
- Memory: `.codex/agent-memory/paper-research-advisor/MEMORY.md`

## Use When

- 需要在线查论文、核验引用、查询投稿要求、整理 BibTeX
- 需要确保引用真实存在，避免 hallucinated references

## Must Read

- `CLAUDE.md`
- `.codex/file-ownership.md`
- `.codex/agent-memory/paper-research-advisor/MEMORY.md`
- `.claude/agents/paper-research-advisor.md`
- relevant files under `paper/references/`

## Dispatch Contract

- 需要联网时必须查最新来源
- 对每条引用明确标记 `VERIFIED` 或 `UNVERIFIED`
- 若写 `paper/references/`，避免和其他 agent 并行改同一文件

## Return To Lead

- sources checked
- verified and unverified references
- updated files if any
- venue requirement summary if applicable
