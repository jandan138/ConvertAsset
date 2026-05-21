# GRScenes Full no-MDL Multi-Root Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a guarded single-process no-MDL runner report for the full GRScenes scratch route without converting assets by default.

**Architecture:** Add a pure-Python report builder that consumes `full_nomdl_scratch_plan.json`, validates source/scratch/job paths, scans top-level output collisions, and emits a run-readiness report. The actual apply path exists only as a gated function that would reuse one `Processor` instance, but it refuses to run while dependency closure, scratch inputs, and collision blockers remain.

**Tech Stack:** Python standard library, pytest, existing GRScenes VLM evidence layout, lazy `convert_asset.no_mdl.processor` import only after apply gates pass.

---

### Task 1: Runner Tests

**Files:**
- Add: `tests/test_grscenes_vlm_full_nomdl_runner.py`

- [x] **Step 1: Write failing tests**

Cover import without `pxr`, run-readiness report generation, single-process
strategy metadata, top-level expected-output collision detection, timestamped
top-output detection, path-safety rejection for jobs and `--out`, and apply
refusal before importing no-MDL when blockers remain.

- [x] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_runner.py
```

Expected before implementation: failures because
`run_full_nomdl_multi_root.py` does not exist.

### Task 2: Guarded Runner Report

**Files:**
- Add: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py`

- [x] **Step 1: Implement plan loading and validation**

Validate schema/status, root nesting, conversion jobs, source paths, scratch
input paths, expected output paths, and output report location. Do not import
`pxr` or no-MDL modules on the report path.

- [x] **Step 2: Implement collision and readiness summary**

Scan only the planned top-level output locations:

- existing expected top outputs;
- timestamped siblings like `<stem>_noMDL_*.usd`;
- duplicate planned top outputs;
- missing scratch input USDs.

Mark `single_process_multi_root_runner_missing` as satisfied by this runner,
but keep remaining blockers such as dependency closure, recursive output
collision scan, scratch cleanliness, and missing scratch inputs.

- [x] **Step 3: Implement gated apply function**

If `--apply` is passed, rebuild the report and refuse unless
`apply_ready=true`. Only after that gate passes, lazily import
`convert_asset.no_mdl.processor`, set `RUNTIME_ONLY_NEW_USD=True`, create one
`Processor`, and call `process()` for each planned scratch input so
`Processor.done` is shared across roots.

- [x] **Step 4: Verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_runner.py
```

Expected after implementation: all runner tests pass without Isaac/pxr.

### Task 3: Real Dry-Run Report And Documentation

**Files:**
- Add: `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json`
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- Modify: `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- Add: `docs/records/2026-05-21-grscenes-full-nomdl-multi-root-runner.md`
- Modify: `docs/records/README.md`
- Modify: `docs/superpowers/README.md`

- [x] **Step 1: Generate the real dry-run report**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py
```

Expected: JSON report for the 99 planned raw jobs, with `dry_run=true`,
`apply_ready=false`, `single_process_multi_root_runner_missing` satisfied, and
remaining blockers documented.

- [x] **Step 2: Document the next gate**

Record that this is the runner safety shell, not converted-scene evidence. The
next gate remains dependency closure plus scratch materialization/collision
validation.

### Task 4: Review, Verification, Commit

- [x] **Step 1: Request multi-agent review**

Ask reviewers to check apply safety, lazy import behavior, overclaim risk, and
whether the report meaning is understandable in the ACL experiment story.

- [x] **Step 2: Run verification**

Run py_compile, targeted runner tests, full GRScenes planner/materializer tests,
full pytest, JSON invariant checks, and diff checks.

- [x] **Step 3: Commit and push**

Commit the runner, report, tests, and documentation, then push to `origin/main`.
