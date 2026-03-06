# paper-figure-generator

## Mirror

- Canonical role spec: `.claude/agents/paper-figure-generator.md`

## Codex Mapping

- Built-in agent type: `worker`
- Writes: `paper/results/figures/`, and figure generation scripts when explicitly assigned
- Parallel-safe when: figure outputs do not overlap
- Memory: `.codex/agent-memory/paper-figure-generator/MEMORY.md`

## Use When

- 需要把实验原始结果转成论文图表
- 需要输出 PNG + PDF 的 publication-quality 图

## Must Read

- `CLAUDE.md`
- `.codex/file-ownership.md`
- `.codex/agent-memory/paper-figure-generator/MEMORY.md`
- `.claude/agents/paper-figure-generator.md`
- relevant raw results and existing figure styles

## Dispatch Contract

- 只读 `paper/results/raw/`
- 输出 PNG 和 PDF 两种格式
- 保持 A/B 颜色编码一致

## Return To Lead

- figure files produced
- scripts changed if any
- source data used
- style decisions
- follow-up writing handoff
