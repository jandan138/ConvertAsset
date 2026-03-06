# codebase-explorer

## Mirror

- Canonical role spec: `.claude/agents/codebase-explorer.md`

## Codex Mapping

- Built-in agent type: `explorer`
- Writes: none
- Parallel-safe when: yes
- Memory: `.codex/agent-memory/codebase-explorer/MEMORY.md`

## Use When

- 需要快速理解某个模块、入口链路、依赖关系、代码风格
- 在真正开始改代码前做只读探索

## Must Read

- `CLAUDE.md`
- `.codex/agent-memory/codebase-explorer/MEMORY.md`
- `.claude/agents/codebase-explorer.md`
- root docs and relevant module paths

## Dispatch Contract

- 只做只读分析，不要写文件
- 问题要具体，避免把整个需求都外包给 explorer
- 返回文件路径、调用链、约束和风险

## Return To Lead

- concise architecture notes
- relevant file list
- code paths and dependencies
- uncertainties that need deeper validation
