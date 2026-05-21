# GRScenes Full Dependency Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only full-scene dependency/output closure report for the 99-scene GRScenes no-MDL route.

**Architecture:** Create a companion planner that consumes `full_nomdl_scratch_plan.json`, scans authored USD composition dependencies with a lazy PXR/Sdf backend, maps source dependencies into the planned scratch tree, computes the recursive `_noMDL` write set, and reports missing/outside dependencies plus output collisions. It must not copy, hardlink, convert, render, or write under source/scratch asset roots.

**Tech Stack:** Python standard library for import/tests, optional lazy `pxr.Sdf` scan backend for real GRScenes evidence, pytest, existing evidence layout.

---

### Task 1: Closure Tests

**Files:**
- Add: `tests/test_grscenes_vlm_full_dependency_closure.py`

- [x] **Step 1: Write failing tests**

Cover import without `pxr`, split-level `models`/`Materials` composition-arc
recovery, recursive USD write-set mapping, missing/outside dependency blockers,
shared dependency dedupe, base sidecar collision detection, timestamped sidecar
collision detection, recursive scratch-input completeness, and report output
path safety.

- [x] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_dependency_closure.py
```

Expected before implementation: failures because
`plan_full_dependency_closure.py` does not exist.

### Task 2: Read-Only Full Closure Planner

**Files:**
- Add: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_dependency_closure.py`

- [x] **Step 1: Implement pure report core**

Accept injected dependency records for tests. Validate roots and job paths,
resolve dependencies inside source root, recover scene-local `models/...` and
`Materials/...` composition dependencies to split-level resource roots, and map
reachable USD dependencies to scratch paths.

- [x] **Step 2: Implement lazy Sdf backend**

Use lazy `from pxr import Sdf` only when the CLI backend requires it. Scan
authored composition asset dependencies without opening a composed Stage or
mutating assets. Do not claim shader/texture attribute closure from this
backend; material-file closure remains separate evidence unless those files are
surfaced as composition arcs.

- [x] **Step 3: Implement recursive no-MDL output collision scan**

Compute `<stem>_noMDL<ext>` for every reachable planned scratch USD, detect
existing base outputs, timestamped sibling outputs, and duplicate planned
outputs. Count missing scratch inputs for both top-level roots and recursive
dependencies. Mark `whole_scene_dependency_closure_not_scanned` and
`recursive_nomdl_output_collision_scan_missing` as satisfied only when the
closure scan is untruncated; keep concrete blockers when missing dependencies,
outside refs, collisions, truncation, or scratch materialization gaps remain.

- [x] **Step 4: Verify GREEN**

Run the targeted closure tests without requiring Isaac/PXR.

### Task 3: Real Report And Documentation

**Files:**
- Add: `paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json`
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- Modify: `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- Add: `docs/records/2026-05-21-grscenes-full-dependency-closure.md`
- Modify: `docs/records/README.md`
- Modify: `docs/superpowers/README.md`

- [x] **Step 1: Generate real read-only report**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_dependency_closure.py
```

Expected: JSON report for all 99 planned raw jobs. The report may satisfy the
two scan-missing blockers only if the scan is untruncated, and it must not claim
conversion readiness while top-level or recursive scratch inputs are still
missing.

- [x] **Step 2: Document the story gate**

Record that this is scan evidence only. The next gate remains full scratch
materialization plus runner consumption of the closure report.

### Task 4: Review, Verification, Commit

- [x] **Step 1: Request multi-agent review**

Ask reviewers to check dependency semantics, output-collision semantics,
overclaim risk, and whether the report is understandable in the ACL experiment
story.

- [x] **Step 2: Run verification**

Run py_compile, targeted new tests, existing full no-MDL planner/runner tests,
full pytest, JSON invariant checks, and diff checks.

- [x] **Step 3: Commit and push**

Commit the closure planner, report, tests, and documentation, then push to
`origin/main`.
