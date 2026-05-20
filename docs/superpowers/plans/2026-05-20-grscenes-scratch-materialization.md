# GRScenes Scratch Materialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe, auditable scratch materialization step for the ACL/VLM GRScenes pilot so no-MDL conversion can run outside the immutable benchmark source tree.

**Architecture:** Add one pure-Python experiment script beside the existing GRScenes VLM manifest scripts. It reads `source_manifest.json`, validates benchmark/scratch safety boundaries, mirrors selected scene folders plus split-level `models` and `Materials` resources into scratch using hardlinks by default, and writes a materialization report with conversion commands. The script does not import `pxr`, does not run Isaac Sim by default, and does not mutate `/cpfs/user/zhuzihou/assets/zzh-grscenes`.

**Tech Stack:** Python standard library (`argparse`, `json`, `os`, `shutil`, `pathlib`), pytest, existing `paper/shared/evidence/experiments/06_grscenes_vlm_grounding` manifests.

---

### Task 1: Scratch Materializer Script

**Files:**
- Create: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py`
- Test: `tests/test_grscenes_vlm_materialize_scratch.py`

- [ ] **Step 1: Write failing import and safety tests**

Add tests that load the new script with `importlib`, assert it imports without `pxr`, and assert `build_materialization_plan()` raises when the manifest scratch root is inside the source root.

Run: `python -m pytest tests/test_grscenes_vlm_materialize_scratch.py -q`

Expected: FAIL because `materialize_scratch.py` does not exist.

- [ ] **Step 2: Implement manifest loading and safety validation**

Create `materialize_scratch.py` with:
- `DEFAULT_INPUT` pointing to `source_manifest.json`.
- `DEFAULT_OUTPUT` pointing to `scratch_materialization_report.json`.
- `_is_relative_to(path, parent)`.
- `validate_manifest_safety(manifest)`.
- `selected_scenes(manifest, limit_scenes=None)`.
- `build_materialization_plan(manifest, limit_scenes=None, copy_mode="hardlink")`.

Safety rules:
- `scratch_root` must not be under `benchmark_source_dataset.local_root`.
- `source_root` must not be under `scratch_root`.
- Every `scene_dir` and `source_usd` must be under source root.
- Every `scratch_scene_root` and `converted_usd` must be under scratch root.
- Every derived resource-tree action must keep `src` under source root and
  `dst` under scratch root.
- Existing symlink destinations are rejected because they can route no-MDL
  sidecars back into the immutable source tree.

- [ ] **Step 3: Write failing action-plan tests**

Add tests that build a tiny fake source tree with:
- `scenes/GRScenes-100/home_scenes/scenes/scene_a_usd/start_result_raw.usd`
- `scenes/GRScenes-100/home_scenes/scenes/scene_a_usd/models` containing `../../models`
- `scenes/GRScenes-100/home_scenes/scenes/scene_a_usd/Materials` containing `../../Materials`
- split-level `models/` and `Materials/`

Assert the plan contains:
- one `resource_tree` action for `home_scenes/models`;
- one `resource_tree` action for `home_scenes/Materials`;
- one `scene_dir` action for `scene_a_usd`;
- one conversion command pointing at scratch `start_result_raw.usd`;
- no destination path under source root.

Run: `python -m pytest tests/test_grscenes_vlm_materialize_scratch.py -q`

Expected: FAIL until the plan builder emits these actions.

- [ ] **Step 4: Implement action planning**

Implement:
- `split_root_for_scene(scene_dir)` by using `scene_dir.parent.parent`.
- resource actions for `models` and `Materials`, de-duplicated per split root.
- scene actions for each selected scene.
- report summary fields: `scene_count`, `resource_tree_count`, `copy_mode`, `dry_run`, `conversion_command_count`.

- [ ] **Step 5: Write failing hardlink materialization tests**

Add tests that call `materialize_from_plan(plan, dry_run=False)` on the tiny fake source tree and assert:
- destination files exist in scratch;
- hardlinked files share inode with source when `copy_mode="hardlink"`;
- top-level scratch destinations are not symlinks;
- GRScenes asset-internal relative symlinks are preserved and resolve inside
  scratch;
- a second run marks existing destinations as `exists` instead of deleting them.

Run: `python -m pytest tests/test_grscenes_vlm_materialize_scratch.py -q`

Expected: FAIL until materialization is implemented.

- [ ] **Step 6: Implement materialization**

Implement:
- `_copy_tree(src, dst, copy_mode)` using `shutil.copytree(..., copy_function=...)`.
- hardlink copy function using `os.link(src, dst)`; do not silently fall back to
  `shutil.copy2`, because that would make the provenance report misleading and
  may unexpectedly duplicate large resource trees.
- existing destination behavior: skip and report `exists`.
- `materialize_from_plan(plan, dry_run=True)` that records planned actions without filesystem writes.

- [ ] **Step 7: Add CLI and report writing**

Add CLI:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py \
  --source-manifest paper/shared/evidence/raw/grscene_vlm_grounding/source_manifest.json \
  --out paper/shared/evidence/raw/grscene_vlm_grounding/scratch_materialization_report.json \
  --limit-scenes 1 \
  --dry-run
```

Options:
- `--copy-mode hardlink|copy`, default `hardlink`.
- `--limit-scenes N`.
- `--dry-run`, default false in library but available in CLI.
- `--execute` is not needed; absence of `--dry-run` performs materialization.

- [ ] **Step 8: Run focused verification**

Run:
- `python -m pytest tests/test_grscenes_vlm_materialize_scratch.py -q`
- `python -m py_compile paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py`
- `python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py --limit-scenes 1 --dry-run --out /tmp/grscenes_scratch_materialization_report.json`

Expected:
- tests pass;
- py_compile passes;
- dry-run report is written outside the benchmark source tree.

### Task 2: Documentation and Manifest Workflow Wiring

**Files:**
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- Modify: `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- Modify: `docs/records/2026-05-20-grscenes-vlm-render-manifest.md`
- Create: `docs/records/2026-05-20-grscenes-scratch-materialization.md`

- [ ] **Step 1: Document the new gate**

Explain that scratch materialization sits between `source_manifest.json` and no-MDL conversion:

```text
source_manifest -> materialize_scratch -> no-mdl conversion in scratch -> prepare_render_manifest --require-converted
```

State clearly that `hardlink` is the default to avoid duplicating 19G+ shared materials, and that no-MDL must not rewrite existing source files.

- [ ] **Step 2: Add commands**

Add dry-run and execution commands:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py --limit-scenes 1 --dry-run
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py --limit-scenes 1
./scripts/isaac_python.sh ./main.py no-mdl /cpfs/user/zhuzihou/assets/acl27_grscenes_vlm_nomdl_work_20260520/scenes/GRScenes-100/home_scenes/scenes/<scene_id>/start_result_raw.usd
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py --require-converted
```

- [ ] **Step 3: Run doc-adjacent checks**

Run:
- `git diff --check`
- `python -m pytest tests/test_grscenes_vlm_materialize_scratch.py tests/test_grscenes_vlm_render_manifest.py -q`

Expected: no whitespace errors; both experiment-script test files pass.
