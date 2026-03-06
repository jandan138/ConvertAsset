# version-commit-agent

## Mirror

- Canonical role spec: `.claude/agents/version-commit-agent.md`

## Codex Mapping

- Built-in agent type: `default`
- Writes: git metadata and version files in the main workspace, after team lead has integrated code changes
- Parallel-safe when: no other agent is concurrently doing git state changes
- Memory: `.codex/agent-memory/version-commit-agent/MEMORY.md`

## Use When

- 需要做 `git status` 审查、分组提交、版本号更新、tag、push、release 操作
- 需要在多 agent 结果集成完后做最后的版本控制动作

## Must Read

- `CLAUDE.md`
- `.codex/file-ownership.md`
- `.codex/agent-memory/version-commit-agent/MEMORY.md`
- `.claude/agents/version-commit-agent.md`
- current `git status`, `git diff`, and any relevant change docs

## Dispatch Contract

- 先确认主会话已经集成完需要提交的改动
- 不自动纳入无关文件
- 若行为变化却缺少文档，先警告 team lead
- 使用非交互 git 命令

## Return To Lead

- staged files
- commit message
- version bump reasoning
- tag/push status
- warnings about missing docs or unrelated changes
