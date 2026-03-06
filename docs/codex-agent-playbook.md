# Codex Multi-Agent Playbook

## 目的

本文档说明本仓库的 **Codex 版 agent 系统** 如何工作，以及它如何与现有 `.claude/` 系统对应。

这套系统的目标不是复制 Claude Code 的运行时机制，而是把同样的团队分工、文件归属、记忆沉淀和文档习惯，映射到 Codex 已开启的内置 multi-agent 能力上。

## 核心设计

Codex 侧采用三层结构：

1. `AGENTS.md`
   - 仓库级入口
   - 告诉主 Codex 会话如何读取和调度角色 playbook
2. `.codex/`
   - 保存 Codex 专用的 agent playbook、文件归属表、持久化记忆
3. `.claude/`
   - 继续保留 Claude 侧原始角色语义，作为更详细的镜像参考

换句话说：

- `.claude/agents/*.md` 是“原始角色说明书”
- `.codex/agents/*.md` 是“Codex 调度适配层”

## Claude 到 Codex 的映射

| Claude 概念 | Codex 对应实现 |
|---|---|
| 主 Claude session 是 team lead | 当前主 Codex 会话就是 team lead |
| `.claude/agents/*.md` | `AGENTS.md` + `.codex/agents/*.md` |
| `isolation: worktree` | `worker` 的 forked workspace + 显式 write scope |
| `TaskCreate` / `SendMessage` / `TaskList` | `spawn_agent` / `send_input` / `wait` |
| `.claude/file-ownership.md` | `.codex/file-ownership.md` |
| `.claude/agent-memory/<agent>/` | `.codex/agent-memory/<agent>/` |

最重要的差异有两点：

1. Codex 没有自动注册自定义 agent 名称
   - 所以必须由 `AGENTS.md` 和 `.codex/agents/*.md` 来约束主会话如何调度
2. Codex 子 agent 的改动不会自动进入当前工作区
   - 主会话要负责审阅和集成
   - 因此文件归属和并行边界依然关键

## 目录结构

```text
AGENTS.md
.codex/
├── agents/
│   ├── README.md
│   ├── architecture-planner.md
│   ├── bug-fixer.md
│   ├── feature-implementer.md
│   └── ...
├── agent-memory/
│   ├── bug-fixer/MEMORY.md
│   ├── docs-writer/MEMORY.md
│   └── ...
└── file-ownership.md
```

## 调度规则

### 1. 先决定是否真的需要委派

- 立即阻塞主路径的工作，优先主会话本地完成
- 适合并行的 sidecar 任务，再交给子 agent

### 2. 正确选择内置 agent 类型

| 内置类型 | 适用场景 |
|---|---|
| `explorer` | 只读代码探索、回答明确的代码库问题 |
| `worker` | 边界清晰的写文件任务 |
| `default` | 架构规划、研究、测试、git、综合验证 |

### 3. `worker` 必须显式写清 scope

给 `worker` 下发任务时，至少要写清：

- 它拥有的文件或目录
- 它不是独自在代码库里，不能回滚他人改动
- 需要执行哪些验证
- 需要返回哪些文件、测试结果、风险
- 如果行为变化了，要给 `docs-writer` 留什么 handoff

### 4. 并行前先看 ownership

在任何写任务前先读：

- `.codex/file-ownership.md`

基本规则：

- 同一文件同一轮只能归一个 writer
- `convert_asset/cli.py`、`convert_asset/no_mdl/config.py`、`paper/references/references.bib` 属于高冲突文件
- 并行只发生在 write scope 明确不重叠时

### 5. 等待策略要保守而耐心

这是这套 Codex 系统里的硬规则：

- 对调研、测试、论文写作、图表生成、实验运行这类慢任务，默认使用更长的等待窗口
- 不要因为子 agent 一两次没有立刻回消息，就把它视为失败
- 如果主会话还有别的事情能做，先继续本地工作，而不是提前打断子 agent
- 只有在出现明显卡死信号时，才考虑中断：
  - 长时间无任何进展
  - 重复同一报错或同一日志
  - 明显死循环
  - 资源或进程已经僵死

简化成一句话就是：**宁可多等一会换取高质量结果，也不要为了“显得快”而过早终止子 agent。**

## 文档约束

本项目延续 Claude 侧“做事必须留文档”的原则，但对 Codex 做了更清晰的落地：

- `docs/` 默认由 `docs-writer` 负责
- 其他 agent 如果造成行为变化，完成时必须交回一个文档 handoff
- handoff 至少应包含：
  - 推荐文档路径
  - 需要记录的行为变化
  - 已执行的验证命令
  - 仍未覆盖的边界条件

## 持久化记忆约束

每个角色都有：

- `.codex/agent-memory/<agent>/MEMORY.md`

使用规则：

- 开始较大任务前先读自己的 `MEMORY.md`
- 结束时只写入稳定经验，不写任务过程日志
- 如果内容已在 `CLAUDE.md` 里明确，就不要再复制一遍

## 推荐工作流

### 场景一：先探索，再实现，再补文档

1. 主会话本地读 `CLAUDE.md`
2. `codebase-explorer` 只读梳理相关模块
3. `feature-implementer` 或 `bug-fixer` 实现改动
4. `docs-writer` 更新 `docs/changes/` 或相关模块文档
5. `version-commit-agent` 处理 git 提交

### 场景二：论文链路

1. `paper-research-advisor` 查资料、核引文
2. `paper-experiment-runner` 产出原始结果
3. `paper-figure-generator` 生成图
4. `paper-writer` 写章节

## 与现有 `.claude/` 系统的关系

这不是替换，而是并存：

- Claude 继续使用 `.claude/`
- Codex 使用 `AGENTS.md` + `.codex/`
- 两边角色名保持一致，方便团队在不同工具间切换
- 如果未来某个角色要升级，优先更新 `.codex/agents/<name>.md` 的调度契约；若角色语义本身变了，再同步回 `.claude/agents/<name>.md`

## 建议

- 对读任务，积极并行
- 对写任务，保守切 scope
- 对 Git 操作，最后串行
- 对子 agent，默认耐心等待，除非真的卡死
- 对经验沉淀，少写但写准
