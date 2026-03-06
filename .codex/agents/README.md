# Codex Agent Playbooks

本目录保存的是 **Codex 版角色适配层**，不是平台自动识别的 agent 注册表。

使用方式：

1. 主会话先读 `AGENTS.md`
2. 再读目标角色的 `.codex/agents/<name>.md`
3. 如需更细的项目语义，再补读对应的 `.claude/agents/<name>.md`
4. 按 playbook 指定的 `spawn_agent` 类型、读写边界、交付契约来下发任务

统一约定：

- `Built-in agent type` 是建议值，不是硬限制；若任务明显跨出该类型的舒适区，由主会话调整
- `worker` 一律要显式声明 write scope，并提醒其不要回滚他人改动
- 任何会影响行为的任务都要附带文档 handoff，供 `docs-writer` 跟进
- 任何 agent 在较大任务前都要先看自己的 `.codex/agent-memory/<name>/MEMORY.md`
- 对调研、验证、测试、论文写作等慢任务，主会话默认要更耐心等待；不要因为短时间静默就轻易 `interrupt`
