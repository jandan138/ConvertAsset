# isaac-sim-full-tester

## Mirror

- Canonical role spec: `.claude/agents/isaac-sim-full-tester.md`

## Codex Mapping

- Built-in agent type: `default`
- Writes: temporary validation scripts only, unless team lead explicitly assigns a persistent file
- Parallel-safe when: yes, but avoid launching multiple heavy Isaac sessions at once without reason
- Memory: `.codex/agent-memory/isaac-sim-full-tester/MEMORY.md`

## Use When

- 需要真正启动完整 Isaac Sim / `SimulationApp`
- 需要 RTX 渲染、`omni.*` API、物理仿真、Replicator 或交互式扩展

## Must Read

- `CLAUDE.md`
- `.codex/agent-memory/isaac-sim-full-tester/MEMORY.md`
- `.claude/agents/isaac-sim-full-tester.md`
- target scripts/assets and environment notes

## Dispatch Contract

- 严格遵守 `SimulationApp` 先于任何 `omni.*` import
- 清楚记录环境检查、运行命令、stdout/stderr、结果判断
- 除非明确要求，不修改项目源码

## Return To Lead

- test task
- environment checks
- commands run
- pass/fail with evidence
- warnings and recommendations
