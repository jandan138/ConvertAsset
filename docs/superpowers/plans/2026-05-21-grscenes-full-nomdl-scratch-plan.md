# GRScenes Full no-MDL Scratch Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only planner for full GRScenes no-MDL scratch preparation so the source dataset is never converted in place.

**Architecture:** The planner inventories all `zzh-grscenes` GRScenes-100 scene directories, plans scratch-side scene/resource materialization, and emits guarded no-MDL conversion jobs. It does not copy, hardlink, convert, render, or open USD stages; it defaults to `safe_to_apply=false` until a later runner proves whole-scene dependency closure and no-MDL output collision handling.

**Tech Stack:** Python standard library, pytest, existing GRScenes VLM evidence layout.

---

### Task 1: Planner Tests

**Files:**
- Add: `tests/test_grscenes_vlm_full_nomdl_scratch_plan.py`

- [x] **Step 1: Write failing tests**

Cover import without `pxr`, source/scratch path safety, full scene inventory,
scene-local pointer/symlink handling, resource-tree actions, no-MDL command
generation with `--only-new-usd`, existing source sidecar detection, and guarded
`safe_to_apply=false` semantics.

- [x] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_scratch_plan.py
```

Expected before implementation: failures because
`plan_full_nomdl_scratch.py` does not exist.

### Task 2: Read-Only Full Planner

**Files:**
- Add: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_nomdl_scratch.py`

- [x] **Step 1: Implement pure-Python inventory**

Scan only bounded GRScenes-100 scene directories under:

```text
scenes/GRScenes-100/home_scenes/scenes/*_usd
scenes/GRScenes-100/commercial_scenes/scenes/*_usd
```

Default planned no-MDL input is `start_result_raw.usd`; support explicit variant
lists for later `navigation` and `interaction` expansion.

- [x] **Step 2: Implement action and conversion-job schema**

Emit:

- `scene_dir` scratch materialization actions.
- split-level `models` and `Materials` `resource_tree` actions.
- scratch-side `scene_entry_repair` actions for pointer-file scene entries.
- `convert_no_mdl` jobs that run against scratch inputs with `--only-new-usd`.

- [x] **Step 3: Implement safety gates**

Reject source/scratch nesting, detect existing source `_noMDL` sidecars for
planned source USDs, record that CLI per-scene conversion can duplicate
recursive dependency sidecars, and keep `safe_to_apply=false` until a later
single-process multi-root runner and dependency closure are implemented.

- [x] **Step 4: Verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_scratch_plan.py
```

Expected after implementation: all full planner tests pass.

### Task 3: Real Plan Artifact And Documentation

**Files:**
- Add: `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_plan.json`
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- Modify: `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- Add: `docs/records/2026-05-21-grscenes-full-nomdl-scratch-plan.md`
- Modify: `docs/records/README.md`
- Modify: `docs/superpowers/README.md`

- [x] **Step 1: Generate the real read-only plan**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_nomdl_scratch.py
```

Expected: JSON plan for 99 GRScenes-100 `start_result_raw.usd` inputs under a
scratch root outside `/cpfs/user/zhuzihou/assets/zzh-grscenes`, with
`planner_only=true` and `safe_to_apply=false`.

- [x] **Step 2: Document the route decision**

Record the plain-language status: full scratch no-MDL is possible in principle,
but should proceed through a guarded planner, then a dedicated single-process
runner, not direct in-place conversion and not naive per-scene CLI loops.

### Task 4: Review, Verification, Commit

- [x] **Step 1: Request multi-agent review**

Ask reviewers to check path safety, overclaim risk, storage assumptions, and
whether the schema makes the next runner implementable.

- [x] **Step 1a: Fix review findings**

Fixes applied:

- reject report `--out` paths under source or scratch roots;
- add structured `argv` fields to preview conversion jobs;
- update tests to use path-relative checks instead of substring checks;
- clarify route-planner vs task/render manifest schemas in raw docs;
- correct the full planner test count in the record.

- [x] **Step 2: Run verification**

Run py_compile, targeted tests, full pytest, and JSON invariant checks.

- [x] **Step 3: Commit and push**

Commit the planner, test, plan artifact, and documentation, then push to
`origin/main`.
