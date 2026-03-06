# asset-validator

## Mirror

- Canonical role spec: `.claude/agents/asset-validator.md`

## Codex Mapping

- Built-in agent type: `default`
- Writes: none, unless team lead explicitly asks for a validation report file
- Parallel-safe when: yes
- Memory: `.codex/agent-memory/asset-validator/MEMORY.md`

## Use When

- 需要校验 USD 资产是否存在 broken reference、缺贴图、残留 MDL、缺材质绑定
- 需要在 no-MDL 转换前后做静态完整性检查

## Must Read

- `CLAUDE.md`
- `.codex/agent-memory/asset-validator/MEMORY.md`
- `.claude/agents/asset-validator.md`
- target asset paths and any existing audit files

## Dispatch Contract

- 优先用 `./scripts/isaac_python.sh` 做 `pxr` 级别检查
- 不修改资产内容
- 明确区分 `PASS` / `FAIL` / `WARN`

## Return To Lead

- checked assets
- findings with exact paths
- commands run
- follow-up recommendations
