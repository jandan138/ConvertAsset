# Agent Team Issues: Diagnosis Report

**Date**: 2026-03-09
**Status**: Root cause confirmed — API proxy issue, not Claude Code bug

## Executive Summary

Agent teams spawned via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` had two symptoms:
1. Team agents went idle without executing any tools (Bash, Edit, Write all silent)
2. Team agents did not respond to `shutdown_request`, making `TeamDelete` impossible

Both issues were caused by the **API proxy backend** (`ANTHROPIC_BASE_URL`), not by Claude Code's agent team implementation or permission configuration.

## Controlled Experiment

| Test | `team_name` | API pool | Bash | Write | Read | Shutdown | TeamDelete |
|------|-------------|----------|------|-------|------|----------|------------|
| Standalone agent (no team) | — | 旧号池 | ✅ | ✅ | ✅ | n/a | n/a |
| Team agent | `debug-test` | 旧号池 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Team agent | `api-test` | **新号池** | ✅ | ✅ | ✅ | ✅ | ✅ |

**Key observation**: Standalone agents (synchronous, no mailbox) worked on both API pools. Team agents (asynchronous, mailbox-dispatched) only worked after switching API pools.

## Root Cause

Team agents use a **mailbox-based async dispatch** mechanism (`backendType: "in-process"`). The agent's prompt and subsequent tool-use loop are delivered through this mailbox, not inline in the parent session's API call.

The old API proxy did not fully support this multi-turn mailbox dispatch pattern. Specifically:
- The agent process was spawned successfully (config.json shows correct member entries)
- The initial prompt was recorded in the team config
- But the **agent's tool execution loop never ran** — the agent went idle immediately without making any API calls of its own

This explains both symptoms:
1. **No tool execution**: The agent's prompt was never processed into tool calls
2. **No shutdown response**: `shutdown_request` is delivered via the same mailbox — if the agent can't process its initial prompt, it can't process subsequent messages either

## What Was NOT the Cause

The following were investigated and ruled out:

| Suspected cause | Finding |
|-----------------|---------|
| Permission configuration | ❌ Not the issue — `mode: "bypassPermissions"` was set, and standalone agents with the same permissions worked fine |
| `file-ownership.md` restrictions | ❌ Not enforced technically — these are conventions, not runtime constraints |
| Missing agent tool grants | ❌ `settings.local.json` has `Edit(*)`, `Write(*)`, `Bash(*)` all allowed |
| Hooks or rules blocking edits | ❌ No hooks configured, no `.claude/rules/` directory |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | ❌ Set to "1" in both pools; did not affect standalone agents |
| Team config missing fields | ❌ Config structure identical between working and non-working runs |

## Impact

During the paper submission readiness review session, 8+ team agents across 3 teams failed silently. All file edits had to be done by the team lead manually. Approximately 30 minutes were spent on failed agent dispatches before falling back to direct editing.

## Resolution

Switching to a different API proxy pool resolved both issues completely. No changes to Claude Code settings, permissions, or agent configuration were needed.

## Recommendations

1. **When using third-party API proxies**: Test team agent functionality with a simple write test before dispatching real work
2. **Diagnostic pattern**: If team agents go idle without output but standalone agents work, the issue is likely the API backend, not permissions
3. **Fallback strategy**: If team agents fail, use standalone agents (no `team_name`) with `run_in_background: true` for parallelism — these use synchronous dispatch and are more resilient to proxy issues
4. **Force cleanup**: When `TeamDelete` fails due to stuck agents, `rm -rf ~/.claude/teams/<name> ~/.claude/tasks/<name>` followed by `TeamDelete` works
