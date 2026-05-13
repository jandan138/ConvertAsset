# ConvertAsset Genesis-Style Documentation Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize ConvertAsset documentation into a Genesis-LLM-style structure while preserving all existing technical knowledge.

**Architecture:** Keep documentation-only changes in one integration stream because nearly every file has link overlap. Move current docs into `docs/design/`, `docs/operations/`, `docs/records/`, and `docs/reference/`; move superseded or paper-specific material into `archive/docs/`; update root entry points to explain the new structure.

**Tech Stack:** Markdown, Git file moves, shell verification, lightweight Python link checker.

---

## File Structure

Create or modify:

- `docs/index.md`: canonical docs entry point.
- `docs/README.md`: compatibility pointer to `docs/index.md`.
- `docs/setup.md`: Isaac Sim and optional native backend setup summary.
- `docs/design/`: architecture and implementation deep dives.
- `docs/operations/`: runbooks, CLI usage, troubleshooting.
- `docs/records/`: dated change logs and project records.
- `docs/reference/`: USD and material background.
- `archive/README.md`: archive navigation.
- `archive/docs/legacy/`: stale legacy indexes and superseded docs.
- `archive/docs/paper/`: paper/submission records that are not current ConvertAsset engineering docs.
- `README.md`: concise project landing page.
- `CLAUDE.md`: update documentation paths and rules.
- `AGENTS.md`: update documentation paths and rules.

Do not modify source files under `convert_asset/`, `native/`, `scripts/`, or tests.

## Task 1: Prepare Target Directories

**Files:**
- Create: `archive/README.md`
- Create dirs: `docs/design/`, `docs/operations/`, `docs/records/`, `docs/reference/`, `archive/docs/legacy/`, `archive/docs/paper/`

- [ ] **Step 1: Create directories**

Run:

```bash
mkdir -p docs/design docs/operations docs/records docs/reference archive/docs/legacy archive/docs/paper
```

Expected: command exits 0.

- [ ] **Step 2: Confirm no source files are staged**

Run:

```bash
git status --short --branch
```

Expected: only documentation or untracked directory changes appear.

## Task 2: Move Current Design Documents

**Files:**
- Move current architecture and implementation docs into `docs/design/`
- Move stale module indexes into `archive/docs/legacy/`

- [ ] **Step 1: Move architecture docs**

Run:

```bash
git mv docs/architecture/design.md docs/design/architecture-design.md
git mv docs/architecture/flow.md docs/design/architecture-flow.md
git mv docs/architecture/modules.md docs/design/architecture-modules.md
git mv docs/architecture/callstack.md docs/design/architecture-callstack.md
git mv docs/architecture/processor_details.md docs/design/no-mdl-processor-details.md
git mv docs/architecture/orbit_camera_capture.md docs/design/orbit-camera-capture.md
git mv docs/architecture/orbit_camera_capture_zh.md docs/design/orbit-camera-capture-zh.md
git mv docs/architecture/README.md archive/docs/legacy/architecture-readme.md
```

Expected: files are renamed and `docs/architecture/` has no remaining Markdown except files moved in later steps.

- [ ] **Step 2: Move no-MDL design docs**

Run:

```bash
git mv docs/no_mdl/materials_details.md docs/design/no-mdl-materials.md
git mv docs/no_mdl/references_details.md docs/design/no-mdl-references.md
git mv docs/no_mdl/texture_path_handling.md docs/design/no-mdl-texture-path-handling.md
git mv docs/no_mdl/feature_specs/texture_path_preservation.md docs/design/no-mdl-texture-path-preservation.md
git mv docs/no_mdl/README.md archive/docs/legacy/no-mdl-readme.md
```

Expected: no no-MDL technical detail is lost.

- [ ] **Step 3: Move GLB design docs**

Run:

```bash
git mv docs/glb/architecture.md docs/design/glb-architecture.md
git mv docs/glb/architecture_zh.md docs/design/glb-architecture-zh.md
git mv docs/glb/code_walkthrough.md docs/design/glb-code-walkthrough.md
git mv docs/glb/code_walkthrough_zh.md docs/design/glb-code-walkthrough-zh.md
```

Expected: GLB architecture and walkthroughs are first-class design docs.

- [ ] **Step 4: Move mesh and native backend design docs**

Run:

```bash
git mv docs/mesh/overview.md docs/design/mesh-overview.md
git mv docs/mesh/algorithm_qem.md docs/design/mesh-qem-algorithm.md
git mv docs/native_meshqem/README.md docs/design/native-meshqem.md
git mv docs/native_meshqem/algorithm_details.md docs/design/native-meshqem-algorithm.md
git mv docs/mesh/legacy archive/docs/legacy/mesh
git mv docs/mesh/README.md archive/docs/legacy/mesh-readme.md
```

Expected: current algorithm docs are active; superseded mesh docs are archived.

- [ ] **Step 5: Move export-mdl-materials and camera design docs**

Run:

```bash
git mv docs/export_mdl_materials/export_mdl_materials_overview.md docs/design/export-mdl-materials-overview.md
git mv docs/export_mdl_materials/export_mdl_materials_code_walkthrough.md docs/design/export-mdl-materials-code-walkthrough.md
git mv docs/export_mdl_materials/export_mdl_materials_line_by_line.md docs/design/export-mdl-materials-line-by-line.md
git mv docs/architecture/ai_material_analysis.md docs/reference/ai-material-analysis.md
```

Expected: implementation-heavy docs are active and conceptual analysis is in reference.

## Task 3: Move Operations And Reference Documents

**Files:**
- Move runbooks and troubleshooting into `docs/operations/`
- Move educational background into `docs/reference/`

- [ ] **Step 1: Move GLB and mesh operations docs**

Run:

```bash
git mv docs/glb/README.md docs/operations/glb-export.md
git mv docs/glb/README_zh.md docs/operations/glb-export-zh.md
git mv docs/mesh/cli_usage.md docs/operations/mesh-cli-usage.md
git mv docs/mesh/performance_and_limits.md docs/operations/mesh-performance-and-limits.md
git mv docs/mesh/face_counting.md docs/operations/mesh-face-counting.md
git mv docs/mesh/roadmap.md docs/records/mesh-roadmap.md
git mv docs/native_meshqem/python_calls_cpp_tutorial.md docs/operations/native-meshqem-python-calls-cpp.md
git mv docs/native_meshqem/usage_and_integration.md docs/operations/native-meshqem-usage.md
```

Expected: executable and tuning docs are operations; roadmap is a record.

- [ ] **Step 2: Move export-mdl-materials operations docs**

Run:

```bash
git mv docs/export_mdl_materials/README.md docs/operations/export-mdl-materials.md
git mv docs/export_mdl_materials/export_mdl_materials_usage.md docs/operations/export-mdl-materials-usage.md
git mv docs/export_mdl_materials/export_mdl_materials_gotchas.md docs/operations/export-mdl-materials-troubleshooting.md
git mv docs/export_mdl_materials/INDEX.md archive/docs/legacy/export-mdl-materials-index.md
```

Expected: user-facing export docs are operations; old index is archived.

- [ ] **Step 3: Move thumbnails, tools, and troubleshooting**

Run:

```bash
git mv docs/thumbnails/README.md docs/operations/thumbnails.md
git mv docs/thumbnails/environment.md docs/operations/thumbnails-environment.md
git mv docs/thumbnails/usage.md docs/operations/thumbnails-usage.md
git mv docs/thumbnails/troubleshooting.md docs/operations/thumbnails-troubleshooting.md
git mv docs/tools/README.md docs/operations/tools.md
git mv docs/tools/inspect_material.md docs/operations/inspect-material.md
git mv docs/tools/isaac_python_wrapper.md docs/operations/isaac-python-wrapper.md
git mv docs/troubleshooting/README.md docs/operations/troubleshooting.md
git mv docs/troubleshooting/no_materials_preview.md docs/operations/troubleshooting-no-materials-preview.md
git mv docs/troubleshooting/no_mdl_failure_analysis.md docs/operations/troubleshooting-no-mdl-failure-analysis.md
git mv docs/troubleshooting/orbit_camera_capture_pitfalls.md docs/operations/troubleshooting-orbit-camera-capture-pitfalls.md
git mv docs/architecture/orbit_cli_camera_pose.md docs/operations/orbit-cli-camera-pose.md
```

Expected: active runbooks and troubleshooting guides are under operations.

- [ ] **Step 4: Move agent operations docs**

Run:

```bash
git mv docs/agent-team-playbook.md docs/operations/agent-team-playbook.md
git mv docs/codex-agent-playbook.md docs/operations/codex-agent-playbook.md
```

Expected: agent docs remain available in operations.

- [ ] **Step 5: Move USD reference docs**

Run:

```bash
git mv docs/usd_knowledge/README.md docs/reference/usd-knowledge.md
git mv docs/usd_knowledge/listop_and_composition_kinds.md docs/reference/usd-listop-and-composition-kinds.md
git mv docs/usd_knowledge/material_basics.md docs/reference/usd-material-basics.md
git mv docs/usd_knowledge/materials_texturing_mdl_for_beginners.md docs/reference/mdl-materials-texturing-for-beginners.md
git mv docs/usd_knowledge/roots_refs_prims.md docs/reference/usd-roots-refs-prims.md
git mv docs/usd_knowledge/shading_outputs_token_switch.md docs/reference/usd-shading-outputs-token-switch.md
```

Expected: USD learning docs are under reference.

## Task 4: Move Records And Archive Paper Material

**Files:**
- Move engineering records into `docs/records/`
- Move paper/submission records into `archive/docs/paper/`

- [ ] **Step 1: Move engineering records**

Run:

```bash
git mv docs/changes/README.md docs/records/README.md
git mv docs/changes/2026-01-06_glb_refactor.md docs/records/2026-01-06-glb-refactor.md
git mv docs/changes/2026-03-06_codex_agent_system.md docs/records/2026-03-06-codex-agent-system.md
git mv docs/changes/2026-03-09_agent_team_diagnosis.md docs/records/2026-03-09-agent-team-diagnosis.md
git mv docs/changes/2026-03-17_glb_hierarchy_preservation_implementation.md docs/records/2026-03-17-glb-hierarchy-preservation-implementation.md
git mv docs/changes/2026-03-17_usd_to_glb_implementation_survey.md docs/records/2026-03-17-usd-to-glb-implementation-survey.md
git mv docs/changes/no_mdl_diagnostics_changes.md docs/records/no-mdl-diagnostics-changes.md
git mv docs/changes/no_mdl_strict_pass_and_audit.md docs/records/no-mdl-strict-pass-and-audit.md
git mv docs/changes/orbit_camera_headless.md docs/records/orbit-camera-headless.md
git mv docs/changes/history/2026_01_06_glb_export.md docs/records/2026-01-06-glb-export-history.md
git mv docs/changes/history/no_mdl_dev_changes.md docs/records/no-mdl-dev-changes.md
```

Expected: engineering history is active under records.

- [ ] **Step 2: Archive paper and submission records**

Run:

```bash
git mv docs/changes/2026-03-06_autofigure_edit_research.md archive/docs/paper/2026-03-06-autofigure-edit-research.md
git mv docs/changes/2026-03-06_methodology_pipeline_figure.md archive/docs/paper/2026-03-06-methodology-pipeline-figure.md
git mv docs/changes/2026-03-06_paper_figure_asset_placement.md archive/docs/paper/2026-03-06-paper-figure-asset-placement.md
git mv docs/changes/2026-03-06_syndata4cv_submission_package.md archive/docs/paper/2026-03-06-syndata4cv-submission-package.md
git mv docs/changes/2026-03-06_syndata4cv_submission_readiness.md archive/docs/paper/2026-03-06-syndata4cv-submission-readiness.md
git mv docs/changes/2026-03-09_autofigure_methodology_pipeline_integration.md archive/docs/paper/2026-03-09-autofigure-methodology-pipeline-integration.md
git mv docs/changes/2026-03-09_grscene_startup_benchmark.md archive/docs/paper/2026-03-09-grscene-startup-benchmark.md
git mv docs/changes/2026-03-09_perf_benchmark_scope_reframe.md archive/docs/paper/2026-03-09-perf-benchmark-scope-reframe.md
git mv docs/changes/2026-03-09_remove_detection_experiment.md archive/docs/paper/2026-03-09-remove-detection-experiment.md
git mv docs/changes/2026-03-09_submission_readiness_recheck.md archive/docs/paper/2026-03-09-submission-readiness-recheck.md
git mv docs/changes/2026-03-09_submission_readiness_review.md archive/docs/paper/2026-03-09-submission-readiness-review.md
```

Expected: paper/submission history is preserved but no longer first-class engineering navigation.

## Task 5: Rewrite Entry Points And Indexes

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`
- Create/modify: `docs/index.md`
- Modify: `docs/README.md`
- Create: `docs/setup.md`
- Create: `archive/README.md`

- [ ] **Step 1: Write `docs/index.md`**

Create a concise Chinese-first docs index with:

```markdown
# ConvertAsset 文档

> 最后更新: 2026-05-13

## 快速导航

- `docs/design/` - 架构、模块职责、算法与实现深挖
- `docs/operations/` - 运行环境、CLI、构建、排障与 agent 协作
- `docs/records/` - 变更日志、实现记录、审计与路线记录
- `docs/reference/` - USD、UsdShade、MDL 与材质背景知识
- `archive/` - 旧索引、legacy 文档、论文/提交相关历史材料

## 项目概述

ConvertAsset 是面向 NVIDIA Isaac Sim / USD 资产的转换与优化工具集，核心能力包括 no-MDL 转换、mesh 简化、USD 到 GLB 导出、缩略图渲染、材质检查与 MDL 材质导出。
```

Expected: active documentation has a Genesis-style root index.

- [ ] **Step 2: Replace `docs/README.md` with compatibility pointer**

Write:

```markdown
# ConvertAsset Documentation

Canonical documentation now starts at `docs/index.md`.
```

Expected: old docs entry remains usable.

- [ ] **Step 3: Create lightweight directory indexes**

Create `docs/design/README.md`, `docs/operations/README.md`,
`docs/reference/README.md`, and update `docs/records/README.md` with concise
file lists for their directories.

Expected: directory links from `docs/index.md` resolve to useful navigation.

- [ ] **Step 4: Rewrite `README.md`**

Use Genesis-LLM landing page shape:

```markdown
# ConvertAsset

> USD asset conversion and optimization toolkit for NVIDIA Isaac Sim

## 概述

ConvertAsset converts MDL-heavy USD assets into portable UsdPreviewSurface assets,
simplifies triangle meshes, exports GLB, and supports thumbnail and material
inspection workflows.
```

Then include a directory table, quick start commands, core command table, and
`docs/index.md` pointer.

Expected: root README is concise and no longer carries long native backend details.

- [ ] **Step 5: Create `docs/setup.md`**

Summarize Isaac Sim Python setup, `ISAAC_SIM_ROOT`, lazy `pxr` constraint, and
native meshqem build pointer to `docs/operations/native-meshqem-usage.md`.

Expected: setup information has a stable active path.

- [ ] **Step 6: Create `archive/README.md`**

Document archive purpose and subdirectories:

```markdown
# Archive

Historical documentation retained for reference. Nothing here is required for
the primary ConvertAsset user workflow.

- `docs/legacy/` - superseded indexes and legacy mesh docs
- `docs/paper/` - paper/submission process records
```

Expected: archived docs are discoverable.

- [ ] **Step 7: Update `CLAUDE.md` and `AGENTS.md`**

Replace old documentation path descriptions with the new model:

```text
docs/design/      architecture and implementation design
docs/operations/  setup, runbooks, CLI usage, troubleshooting, agent docs
docs/records/     dated change logs and engineering records
docs/reference/   USD and material background
archive/          retained historical material
```

Expected: agent instructions refer to the current docs structure.

## Task 6: Repair Internal Links And Remove Empty Directories

**Files:**
- Modify Markdown files under `docs/`
- Remove empty old directories after successful moves

- [ ] **Step 1: Search active docs for old path references**

Run:

```bash
grep -RInE 'docs/(architecture|changes|glb|mesh|native_meshqem|no_mdl|export_mdl_materials|thumbnails|tools|troubleshooting|usd_knowledge)/|\\.\\./(architecture|changes|glb|mesh|native_meshqem|no_mdl|export_mdl_materials|thumbnails|tools|troubleshooting|usd_knowledge)/' README.md CLAUDE.md AGENTS.md docs || true
```

Expected: any matches are intentionally historical or must be updated.

- [ ] **Step 2: Update active links**

Use targeted edits for links in `docs/design/`, `docs/operations/`,
`docs/reference/`, `docs/records/`, `README.md`, `CLAUDE.md`, and `AGENTS.md`.
Prefer relative links to the new canonical paths.

Expected: first-class navigation does not point at removed directories.

- [ ] **Step 3: Remove empty old directories**

Run:

```bash
find docs -type d -empty -delete
```

Expected: old empty topic directories disappear.

## Task 7: Verify And Review

**Files:**
- No planned edits unless verification finds a problem.

- [ ] **Step 1: Verify Markdown path coverage**

Run:

```bash
python - <<'PY'
from pathlib import Path
import re

roots = [Path('README.md'), Path('CLAUDE.md'), Path('AGENTS.md')]
roots += list(Path('docs').rglob('*.md'))
roots += list(Path('archive').rglob('*.md'))
link_re = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
missing = []
for path in roots:
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8')
    for raw in link_re.findall(text):
        target = raw.split('#', 1)[0].strip()
        if not target or '://' in target or target.startswith('mailto:') or target.startswith('#'):
            continue
        target_path = (path.parent / target).resolve()
        if not target_path.exists():
            missing.append((str(path), raw))
if missing:
    for path, raw in missing:
        print(f'{path}: missing {raw}')
    raise SystemExit(1)
print('all local markdown links resolve')
PY
```

Expected: `all local markdown links resolve`.

- [ ] **Step 2: Verify no source files changed**

Run:

```bash
git diff --name-only | grep -Ev '^(README.md|CLAUDE.md|AGENTS.md|docs/|archive/)' || true
```

Expected: no output.

- [ ] **Step 3: Verify repository whitespace hygiene**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 4: Request read-only review**

Dispatch one explorer/reviewer with this brief:

```text
Review the documentation-only refactor. Check whether active docs follow the
Genesis-style taxonomy, all first-class docs are discoverable, archive choices
are reasonable, and local Markdown links resolve. Do not modify files. Return
findings ordered by severity.
```

Expected: reviewer findings are either fixed or explicitly rejected with
technical reasoning.

- [ ] **Step 5: Commit migration**

Run:

```bash
git status --short
git add README.md CLAUDE.md AGENTS.md docs archive
git commit -m "docs: reorganize documentation in genesis style"
```

Expected: commit succeeds after verification and review.
