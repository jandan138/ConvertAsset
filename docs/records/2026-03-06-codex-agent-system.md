# 2026-03-06 Codex Agent System

## 背景

项目此前已有一套面向 Claude Code 的 `.claude/` agent 体系，但缺少一套与 Codex 内置 multi-agent 能力直接对接的配置层。

本次改动新增了一套 **Codex 原生入口 + 角色 playbook + ownership + memory** 的组合，使同一仓库可以同时支持 Claude 与 Codex 两种 agent 协作模式。

## 本次新增

### 1. 仓库级入口

- 新增 `AGENTS.md`
- 作用：
  - 定义 Codex 主会话就是 team lead
  - 规定如何读取 `.codex/agents/*.md`
  - 将角色映射到 Codex 内置 `explorer` / `worker` / `default`

### 2. Codex 角色定义目录

- 新增 `.codex/agents/`
- 为以下角色提供了 Codex 版调度适配层：
  - `architecture-planner`
  - `asset-validator`
  - `bug-fixer`
  - `code-refactorer`
  - `codebase-explorer`
  - `docs-writer`
  - `feature-designer`
  - `feature-implementer`
  - `isaac-sim-full-tester`
  - `isaac-sim-headless-tester`
  - `paper-experiment-runner`
  - `paper-figure-generator`
  - `paper-research-advisor`
  - `paper-writer`
  - `version-commit-agent`

这些文件没有试图复制 Claude 的 front matter 机制，而是保留角色名和语义，同时补充了：

- 推荐的 `spawn_agent` 类型
- 读写边界
- memory 路径
- 向主会话返回结果的契约

### 3. 文件归属与并行规则

- 新增 `.codex/file-ownership.md`
- 作用：
  - 指定不同 agent 的推荐 write scope
  - 明确高冲突文件
  - 说明 Codex `worker` forked workspace 只是 Claude worktree 的等价实现，不意味着可以忽略冲突

### 4. 持久化记忆

- 新增 `.codex/agent-memory/<agent>/MEMORY.md`
- 作用：
  - 为每个角色提供稳定的项目级经验沉淀位置
  - 约束只记录跨会话有价值的信息

### 5. 使用手册

- 新增 `docs/codex-agent-playbook.md`
- 说明 Claude 系统如何映射到 Codex，以及推荐的调度流程

## 设计取舍

### 没有直接复制 `.claude/settings.local.json`

原因：

- 那是 Claude 侧运行时配置
- Codex 当前主要依赖 `AGENTS.md` 和内置 multi-agent 工具，而不是 Claude 的本地设置文件格式

### 没有把所有角色都做成自动注册

原因：

- Codex 当前没有项目内“自动注册自定义 agent 名称”的同构机制
- 因此采用 “主会话读取 playbook 后再调度内置 agent 类型” 的方式更稳妥，也更贴近 Codex 的原生工具模型

### 新增“耐心等待子 agent”规则

原因：

- Codex multi-agent 在调研、测试、论文写作等任务上，本来就可能比普通代码编辑更慢
- 这些任务慢，不代表质量差；相反，过早中断常常会直接损伤结果质量
- 因此在 `AGENTS.md` 和 Codex playbook 中明确要求主会话默认更耐心等待，除非子 agent 明显卡死

## 验证

本次主要验证的是配置完整性，而不是业务逻辑：

- 检查 `AGENTS.md` 与 `.codex/` 目录已创建
- 检查角色 playbook 与 memory 路径一一对应
- 检查文档索引已加入新 playbook 入口

## 后续建议

1. 未来第一次实际使用某个 Codex 子 agent 后，把真实有效的经验写入对应 `MEMORY.md`
2. 若某个角色经常需要固定 prompt 片段，可以在对应 `.codex/agents/<name>.md` 中继续细化 dispatch 模板
3. 如果团队后续形成更稳定的 commit / docs 节奏，可继续补强 `version-commit-agent` 与 `docs-writer` 的协作规范
