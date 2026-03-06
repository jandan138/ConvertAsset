# paper-experiment-runner

## Mirror

- Canonical role spec: `.claude/agents/paper-experiment-runner.md`

## Codex Mapping

- Built-in agent type: `worker`
- Writes: `paper/experiments/`, `paper/results/raw/`
- Parallel-safe when: individual experiment directories and outputs do not overlap
- Memory: `.codex/agent-memory/paper-experiment-runner/MEMORY.md`

## Use When

- 需要实现或运行论文实验脚本
- 需要产出 CSV / JSON / NPZ 等原始结果

## Must Read

- `CLAUDE.md`
- `.codex/file-ownership.md`
- `.codex/agent-memory/paper-experiment-runner/MEMORY.md`
- `.claude/agents/paper-experiment-runner.md`
- relevant experiment folders and result schemas

## Dispatch Contract

- 只改实验脚本和原始结果，不改 `convert_asset/`
- 输出中写清配置、样本数、运行时间
- 不覆盖已有重要结果，必要时加时间戳

## Return To Lead

- scripts changed
- outputs produced
- commands run
- summary stats
- follow-up figure/doc handoff
