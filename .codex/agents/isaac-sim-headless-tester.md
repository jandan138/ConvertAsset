# isaac-sim-headless-tester

## Mirror

- Canonical role spec: `.claude/agents/isaac-sim-headless-tester.md`

## Codex Mapping

- Built-in agent type: `default`
- Writes: temporary validation scripts only, unless team lead explicitly assigns a persistent file
- Parallel-safe when: yes
- Memory: `.codex/agent-memory/isaac-sim-headless-tester/MEMORY.md`

## Use When

- 需要用 `pxr` 或 headless Isaac 环境验证 USD 读写、脚本执行、批量加载
- 不需要完整 GUI / RTX / `omni.*` 运行时

## Must Read

- `CLAUDE.md`
- `.codex/agent-memory/isaac-sim-headless-tester/MEMORY.md`
- `.claude/agents/isaac-sim-headless-tester.md`
- target asset/script paths

## Dispatch Contract

- 优先用 `./scripts/isaac_python.sh`
- 捕获完整 stdout/stderr
- 给出明确的通过/失败判断

## Return To Lead

- tested targets
- commands run
- pass/fail result
- key logs or warnings
- next debugging steps if needed
