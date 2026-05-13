# ConvertAsset Genesis-Style Documentation Refactor Design

Date: 2026-05-13

## Goal

Refactor ConvertAsset documentation into the same operating shape used by
`/cpfs/user/zhuzihou/dev/genesis-llm`, while preserving the full accumulated
knowledge in this repository.

The migration scope includes:

- `docs/`
- root `README.md`
- root `CLAUDE.md`
- root `AGENTS.md`

The preferred strategy is full retention with layered visibility: current
maintainer-facing documentation stays first-class, historical or superseded
material moves to archive, and no useful technical knowledge is deleted.

## Source And Target Models

ConvertAsset currently uses module/topic directories:

- `docs/architecture/`
- `docs/no_mdl/`
- `docs/glb/`
- `docs/mesh/`
- `docs/native_meshqem/`
- `docs/export_mdl_materials/`
- `docs/thumbnails/`
- `docs/tools/`
- `docs/troubleshooting/`
- `docs/usd_knowledge/`
- `docs/changes/`

Genesis-LLM uses a smaller purpose-based structure:

- `docs/index.md`
- `docs/design/`
- `docs/operations/`
- `docs/records/`
- `docs/reference/`
- root `archive/`

ConvertAsset should adopt that purpose-based structure without forcing every
legacy module document into one large merged document.

## Target Directory Layout

```text
README.md
CLAUDE.md
AGENTS.md
archive/
  README.md
  docs/
    legacy/
    paper/
docs/
  index.md
  setup.md
  design/
  operations/
  records/
  reference/
  superpowers/
    specs/
    plans/
```

`docs/README.md` may be kept as a compatibility alias to `docs/index.md`, but
the canonical entry should be `docs/index.md`.

## Classification Rules

### `docs/design/`

Use for current architecture, module design, and implementation deep dives that
define how ConvertAsset works.

Expected content:

- no-MDL pipeline design and details
- GLB exporter architecture and walkthroughs
- mesh and native meshqem algorithms
- thumbnail/orbit camera design
- export-mdl-materials design
- top-level system architecture summaries

### `docs/operations/`

Use for executable runbooks, setup, commands, wrappers, and troubleshooting that
operators need while running the tool.

Expected content:

- Isaac Sim Python wrapper usage
- CLI usage for no-mdl, GLB, mesh, thumbnails, inspect, uv-audit, export-mdl-materials
- build instructions for native meshqem
- troubleshooting guides
- environment constraints

### `docs/records/`

Use for dated factual history, implementation notes, audits, benchmark notes,
and change logs. This replaces `docs/changes/` as the canonical location.

Expected content:

- all current `docs/changes/*.md`
- old `docs/changes/history/*.md`
- run-backed notes such as GLB hierarchy preservation and orbit camera headless notes

### `docs/reference/`

Use for educational or background material that is useful but not a runbook or
current design contract.

Expected content:

- USD knowledge base
- USD material and shading primers
- MDL material texturing background
- AI/material representation analysis when used as conceptual background

### `archive/`

Use for material retained for history but not presented as active project
documentation.

Expected content:

- legacy mesh documents superseded by current mesh docs
- paper/submission-related records that are not part of ConvertAsset's current
  engineering docs
- stale generated indexes that point to pre-refactor paths

Archive files should remain discoverable from `archive/README.md`.

## File Mapping Principles

Use clear, stable filenames rather than preserving every old subdirectory name.
When multiple files are naturally related, prefix with the feature name:

- `docs/design/no-mdl-pipeline.md`
- `docs/design/no-mdl-materials.md`
- `docs/design/no-mdl-references.md`
- `docs/design/glb-exporter.md`
- `docs/design/glb-code-walkthrough.md`
- `docs/design/mesh-qem.md`
- `docs/operations/mesh-simplify.md`
- `docs/operations/isaac-python-wrapper.md`
- `docs/reference/usd-material-basics.md`
- `docs/records/2026-03-17-glb-hierarchy-preservation.md`

Avoid deleting content during the first migration pass. If a document is
duplicative, move it into archive or leave it as a clearly labeled compatibility
redirect.

## Root Document Changes

### `README.md`

Rewrite as a concise project landing page in the Genesis-LLM style:

- one-sentence purpose
- overview
- directory structure table
- quick start using `./scripts/isaac_python.sh`
- core commands
- documentation pointer to `docs/index.md`

Keep practical examples, but move long backend build details into
`docs/operations/`.

### `CLAUDE.md`

Keep as the authoritative agent/project instruction file. Update only the docs
section and paths so it refers to the new structure:

- `docs/design/`
- `docs/operations/`
- `docs/records/`
- `docs/reference/`
- `archive/`

Preserve existing architecture, lazy `pxr` import constraint, command examples,
and documentation rule.

### `AGENTS.md`

Keep the team lead protocol and playbook mapping. Update project context and
documentation rule references to the new docs structure. Do not remove the
distinction between `.claude/` and `.codex/`.

## Link And Compatibility Strategy

The migration should update internal links to point at canonical new paths.

Compatibility aliases are allowed when a path is likely to be referenced by
older agents or user notes:

- `docs/README.md` -> `docs/index.md`
- old high-level module `README.md` files may become short pointers if keeping
  them is cheaper than updating all historical references

For records and archive material, links to pre-refactor paths may remain if they
are quoted as historical facts, but active navigation should use new paths.

## Verification Strategy

The refactor changes documentation only. Verification should therefore focus on
repository hygiene and link integrity:

- `git status --short --branch`
- `find docs archive -type f -name '*.md' | sort`
- check for unresolved old active links such as `docs/changes/` and
  `docs/architecture/` from first-class docs
- check Markdown files for placeholder strings like `TBD` or broken path
  references introduced by the migration
- run a lightweight script that extracts relative Markdown links from `README.md`,
  `CLAUDE.md`, `AGENTS.md`, and `docs/**/*.md`, then verifies local file targets
  exist

No Isaac Sim runtime test is required because no source behavior changes.

## Multi-Agent Review Plan

Use agents for read-only review and focused critique rather than parallel writes:

- one explorer maps existing docs to the target taxonomy
- the lead writes and applies the migration
- one reviewer checks link integrity, missing first-class docs, and archive
  classification after the migration

Avoid multiple writing agents touching `docs/` in parallel because this task has
high write-scope overlap.

## Acceptance Criteria

- `docs/index.md` is the canonical documentation entry.
- The active docs tree follows `design/`, `operations/`, `records/`,
  `reference/`, and `superpowers/`.
- Historical material is preserved under `archive/` or `docs/records/`.
- `README.md`, `CLAUDE.md`, and `AGENTS.md` point to the new documentation model.
- Internal first-class links resolve.
- No source code files are modified.
- Verification commands are recorded in the final handoff.
