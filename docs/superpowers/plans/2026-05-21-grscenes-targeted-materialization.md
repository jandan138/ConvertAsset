# GRScenes Targeted Materialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize the current ACL/VLM GRScenes target closure into scratch without mirroring full split-level `models/` or `Materials/`.

**Architecture:** Add a pure-Python materializer that consumes `reference_closure_plan.json` and `material_dependency_closure_plan.json`, builds a file-level action plan, and defaults to dry-run. It copies only selected scene directories, selected model roots, selected material files, and scratch-side symlink repairs.

**Tech Stack:** Python standard library, pytest, existing GRScenes VLM planning JSONs.

---

### Task 1: Targeted Materializer Tests

**Files:**
- Add: `tests/test_grscenes_vlm_targeted_materialization.py`

- [x] **Step 1: Write failing tests**

Cover lazy import without `pxr`, file-level material actions, scene-local
`models`/`Materials` entry repairs, model-root `Materials` repairs, dry-run
non-mutation, hardlink/copy behavior, and path-safety rejection.

- [x] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_targeted_materialization.py
```

Expected before implementation: failures because
`materialize_targeted_closure.py` does not exist.

### Task 2: Targeted Materializer

**Files:**
- Add: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_targeted_closure.py`

- [x] **Step 1: Implement plan builder**

Build actions from the two closure plans:

- `scene_dir` for the 5 selected scene directories.
- `target_model_root` for the 23 selected model roots.
- `material_asset_file` for the 68 selected split-level material files.
- `scene_entry_repair` for each selected scene's `models` and `Materials`
  pointer files.
- `model_materials_entry_repair` from the 9 material closure repair actions.

- [x] **Step 2: Implement dry-run/apply executor**

Default to dry-run. Require `--apply` for writes. Use hardlinks by default for
files, preserve symlinks in copied trees, and replace only scratch-side pointer
files with relative symlinks.

- [x] **Step 3: Verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_targeted_materialization.py
```

Expected after implementation: all targeted materialization tests pass.

### Task 3: Dry-Run Report And Documentation

**Files:**
- Add: `paper/shared/evidence/raw/grscene_vlm_grounding/targeted_materialization_report.json`
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- Modify: `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- Add: `docs/records/2026-05-21-grscenes-targeted-materialization.md`
- Modify: `docs/records/README.md`
- Modify: `docs/superpowers/README.md`

- [x] **Step 1: Generate dry-run report**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_targeted_closure.py
```

Expected: a JSON report with `dry_run=true`, 115 planned actions, and zero
asset writes.

- [x] **Step 2: Document current status**

Record that this closes the target-object scratch subset but does not yet make
whole-scene no-MDL conversion ready. Scene-level dependencies and unselected
model references still need a broader scene dependency decision.

### Task 4: Review, Verification, Commit

- [x] **Step 1: Request code review**

Ask a read-only reviewer to check path safety, dry-run behavior, and whether
the report overclaims conversion readiness.

- [x] **Step 1a: Fix code-review findings**

Add regression tests and implementation guards for:

- projected copied-tree symlink targets escaping scratch;
- incomplete existing scratch trees;
- same-size stale material files;
- action destination escape;
- repair target escape;
- dry-run report timestamp naming.

- [x] **Step 2: Run verification**

Run targeted tests, full pytest, py_compile, JSON invariant checks, and diff
checks.

- [x] **Step 3: Commit and push**

Commit the implementation, tests, report, and documentation, then push to
`origin/main`.
