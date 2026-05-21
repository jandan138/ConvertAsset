# GRScenes Full Materialization And Closure Runner Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the full GRScenes no-MDL route from read-only evidence into a gated, materializable scratch dataset and a runner that consumes the full dependency closure report.

**Architecture:** Add a pure-Python full scratch materializer that consumes `full_nomdl_scratch_plan.json`, applies only scratch-side tree hardlinks/copies and scene-entry repairs, and writes a report outside source/scratch. Then extend `run_full_nomdl_multi_root.py` so dry-run/apply can consume `full_dependency_closure_report.json` as the authoritative closure gate before importing no-MDL code.

**Tech Stack:** Python standard library, pytest, existing GRScenes VLM evidence layout, ConvertAsset lazy no-MDL imports for apply only.

---

### Task 1: Full Scratch Materializer Tests

**Files:**
- Add: `tests/test_grscenes_vlm_full_scratch_materializer.py`

- [ ] **Step 1: Write failing tests**

Add tests with a tiny fake full plan:

```python
def test_materializer_dry_run_writes_nothing(tmp_path: Path) -> None:
    module = load_module()
    plan, paths = make_full_plan(tmp_path)
    report = module.materialize_full_scratch_plan(plan, dry_run=True)
    assert report["summary"]["planned_tree_action_count"] == 3
    assert report["summary"]["planned_repair_action_count"] == 2
    assert not paths["scratch_scene"].exists()
```

Also cover:

- import without `pxr`;
- source/scratch nesting rejection;
- destination path escaping scratch rejection;
- hardlink materialization of resource and scene trees;
- pointer-file repair into scratch-side relative symlinks without modifying source;
- idempotent second run;
- `copy` mode creates separate inodes;
- report output path cannot be inside source or scratch.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_scratch_materializer.py
```

Expected before implementation: failure because `materialize_full_nomdl_scratch.py` does not exist.

### Task 2: Full Scratch Materializer Implementation

**Files:**
- Add: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py`

- [ ] **Step 1: Implement pure-Python loaders and guards**

Implement:

```python
DEFAULT_PLAN = RAW_DIR / "full_nomdl_scratch_plan.json"
DEFAULT_OUTPUT = RAW_DIR / "full_nomdl_scratch_materialization_report.json"
COPY_MODES = ("hardlink", "copy")
TREE_ACTION_KINDS = {"resource_tree", "scene_dir"}
REPAIR_ACTION_KIND = "scene_entry_repair"
IGNORED_ACTION_KINDS = {"convert_no_mdl"}
```

Validate:

- `plan["status"] == "planned_full_grscenes_nomdl_scratch"`;
- `scratch_root` is not inside `source_root`;
- `source_root` is not inside `scratch_root`;
- tree `src` is inside source and tree `dst` is inside scratch;
- repair `dst` is inside scratch and relative `target_text` resolves inside scratch;
- report `--out` is outside source and scratch.

- [ ] **Step 2: Implement tree materialization**

For `resource_tree` and `scene_dir` actions:

- `dry_run=True`: record `planned`;
- missing source: raise `FileNotFoundError`;
- existing destination symlink: reject;
- existing destination directory: validate with a tree manifest;
- new destination: `shutil.copytree(..., symlinks=True, copy_function=os.link)` in hardlink mode, or `shutil.copy2` in copy mode.

For scene dirs, ignore `repairable_entry_names` such as `models` and `Materials` when validating existing repaired trees.

- [ ] **Step 3: Implement scene-entry repairs**

For each `scene_entry_repair` action:

- if expected symlink already exists, return `exists`;
- if destination is the copied source pointer file and matches the source entry, unlink scratch destination only;
- create a relative symlink using `target_text`;
- reject mismatched existing files so user scratch edits are not silently overwritten.

- [ ] **Step 4: Implement CLI**

Run dry by default:

```bash
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py
```

Run real materialization only with:

```bash
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py --apply
```

The report must include `dry_run`, per-action results, and summary counts for planned/created/exists/repair statuses plus top-level scratch input existence.

### Task 3: Runner Closure-Report Consumption Tests

**Files:**
- Modify: `tests/test_grscenes_vlm_full_nomdl_runner.py`

- [ ] **Step 1: Write failing tests**

Add tests that pass both a scratch plan and closure report:

```python
report = module.build_multi_root_run_report(plan, closure_report=closure)
assert "whole_scene_dependency_closure_not_scanned" not in report["safety"]["remaining_apply_blockers"]
assert "recursive_nomdl_output_collision_scan_missing" not in report["safety"]["remaining_apply_blockers"]
assert "single_process_multi_root_runner_closure_report_not_consumed" in report["safety"]["satisfied_apply_blockers"]
```

Also cover rejection when closure `source_root`, `scratch_root`, or top-level expected output counts do not match the plan.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_runner.py
```

Expected before implementation: failure because `build_multi_root_run_report()` has no closure-report parameter.

### Task 4: Runner Closure-Report Implementation

**Files:**
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py`

- [ ] **Step 1: Add closure-report validation**

Add optional `closure_report` support that requires:

- `status == "planned_full_grscenes_dependency_closure"`;
- same `source_root` and `scratch_root`;
- `scan_truncated=false`;
- missing/outside/output collision counts are zero;
- `expected_top_output_count == len(selected jobs)` for full runs;
- closure jobs match selected `scratch_input_usd` and `expected_top_output_usd`.

- [ ] **Step 2: Recompute blockers from closure gate**

When valid closure is supplied, satisfy:

- `whole_scene_dependency_closure_not_scanned`;
- `recursive_nomdl_output_collision_scan_missing`;
- `single_process_multi_root_runner_closure_report_not_consumed`.

Keep:

- `scratch_cleanliness_not_verified` until explicit scratch cleanliness evidence exists;
- `scratch_root_missing` and `scratch_inputs_missing` until filesystem checks pass;
- source/top-output collision blockers if runner-level checks find them.

- [ ] **Step 3: Add CLI flag**

Add:

```bash
--closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json
```

The dry-run path must still import no `pxr` and no `convert_asset.no_mdl`.

### Task 5: Evidence, Docs, Review, Verification

**Files:**
- Add: `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json`
- Modify: `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json`
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- Modify: `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- Add: `docs/records/2026-05-21-grscenes-full-materialization-and-closure-runner.md`

- [ ] **Step 1: Generate dry-run materialization report**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py
```

Expected: `dry_run=true`, no scratch writes, all tree and repair actions planned.

- [ ] **Step 2: Generate closure-aware runner report**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py --closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json
```

Expected: closure scan blockers satisfied; scratch blockers still remain until real materialization and cleanliness verification.

- [ ] **Step 3: Request multi-agent review**

Ask reviewers to check source-pollution safety, closure-gate semantics, idempotency, and whether docs overclaim real conversion.

- [ ] **Step 4: Verify**

Run:

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 python -m py_compile paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_scratch_materializer.py tests/test_grscenes_vlm_full_nomdl_runner.py tests/test_grscenes_vlm_full_dependency_closure.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

- [ ] **Step 5: Commit and push**

Commit once dry-run evidence and review are clean.
