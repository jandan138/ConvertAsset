# feature-designer

## Mirror

- Canonical role spec: `.claude/agents/feature-designer.md`

## Codex Mapping

- Built-in agent type: `default`
- Writes: none by default
- Parallel-safe when: yes
- Memory: `.codex/agent-memory/feature-designer/MEMORY.md`

## Use When

- 用户还在问“怎么设计这个功能更合适”
- 需要先产出方案，再决定是否进入实现

## Must Read

- `CLAUDE.md`
- `.codex/agent-memory/feature-designer/MEMORY.md`
- `.claude/agents/feature-designer.md`
- relevant code and docs

## Dispatch Contract

- 输出设计，不直接改源码
- 明确方案、集成点、风险、替代方案
- 如需固化为文档，返回 docs handoff

## Return To Lead

- design proposal
- impacted files
- phased implementation plan
- risks and alternatives
- documentation handoff if needed
