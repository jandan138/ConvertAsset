# Scene Target Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first-class single-scene target capture pipeline for GRScenes-style USD scenes.

**Architecture:** Add focused modules for target discovery, bbox extraction, pose planning, viewport rendering, and manifests. Keep `thumbnails` compatible and expose the new behavior through `target-list` and `target-capture`.

**Tech Stack:** Python 3.10, Isaac Sim Python, `pxr` lazy imports, `argparse`, `pytest`, JSON/JSONL manifests.

---

## File Structure

- Create `convert_asset/capture/__init__.py`: package marker and public exports.
- Create `convert_asset/capture/targets.py`: `TargetConfig`, `TargetSpec`, scope resolution, object/category/mesh target listing.
- Create `convert_asset/capture/manifest.py`: JSON-safe record conversion and manifest writers.
- Create `convert_asset/capture/pipeline.py`: `run_target_list` and `run_target_capture`.
- Create `convert_asset/camera/bounds.py`: lazy-pxr world bounds with finite bbox filtering.
- Create `convert_asset/camera/poses.py`: pure-Python orbit pose planning.
- Create `convert_asset/render/__init__.py`: package marker.
- Create `convert_asset/render/viewport.py`: lazy Isaac viewport capture session helpers.
- Create `convert_asset/datasets/__init__.py`: package marker.
- Create `convert_asset/datasets/grscenes.py`: `layout.usd` discovery helper for future dataset batching.
- Modify `convert_asset/cli.py`: add `target-list` and `target-capture` commands.
- Create `tests/capture/test_targets.py`: fast target discovery unit tests with fake prims.
- Create `tests/capture/test_poses_manifest.py`: pose and manifest unit tests.
- Create `docs/design/target-capture.md`: user-facing architecture document.
- Create `docs/operations/target-capture.md`: CLI runbook.
- Create `docs/records/2026-05-14-target-capture.md`: implementation record.
- Modify `docs/index.md`, `docs/design/README.md`, `docs/operations/README.md`, `docs/records/README.md`, and `docs/superpowers/README.md`: add navigation links.

## Task 1: Write Failing Unit Tests

**Files:**
- Create: `tests/capture/test_targets.py`
- Create: `tests/capture/test_poses_manifest.py`

- [ ] **Step 1: Add target discovery tests**

Create fake prim/stage helpers that implement the small subset used by
`targets.py`: `GetPath`, `GetName`, `GetTypeName`, `GetChildren`, `IsActive`,
`IsInstanceProxy`, `IsValid`, and `GetPrimAtPath`.

Tests:

```python
def test_auto_scope_prefers_direct_grscenes_furniture():
    stage = fake_grscenes_stage()
    assert resolve_target_scope(stage, "auto") == "/Root/Meshes/Furnitures"
```

```python
def test_object_level_lists_non_empty_model_roots_only():
    stage = fake_grscenes_stage()
    targets = list_scene_targets(stage, TargetConfig(target_scope="auto", target_level="object"))
    assert [t.category for t in targets] == ["chair", "table"]
    assert all(t.mesh_count > 0 for t in targets)
    assert all("/model_" in t.prim_path for t in targets)
```

```python
def test_mesh_level_returns_mesh_leaves():
    stage = fake_grscenes_stage()
    targets = list_scene_targets(stage, TargetConfig(target_scope="auto", target_level="mesh"))
    assert [t.level for t in targets] == ["mesh", "mesh", "mesh"]
```

- [ ] **Step 2: Add pose and manifest tests**

Tests:

```python
def test_plan_orbit_poses_returns_finite_positions():
    bounds = Bounds3D(min=(0, 0, 0), max=(2, 2, 2), center=(1, 1, 1), size=(2, 2, 2))
    poses = plan_orbit_poses(bounds, views=4)
    assert len(poses) == 4
    assert {p.view_index for p in poses} == {0, 1, 2, 3}
    assert all(math.isfinite(v) for p in poses for v in p.position)
```

```python
def test_manifest_writer_outputs_jsonl_records(tmp_path):
    record = CaptureRecord(...)
    path = tmp_path / "manifest.jsonl"
    append_capture_record(path, record)
    loaded = json.loads(path.read_text().strip())
    assert loaded["target_id"] == record.target.target_id
```

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
python -m pytest tests/capture -q
```

Expected: fails because the new modules do not exist.

## Task 2: Implement Target Discovery

**Files:**
- Create: `convert_asset/capture/__init__.py`
- Create: `convert_asset/capture/targets.py`

- [ ] **Step 1: Implement dataclasses**

Add `TargetConfig` and `TargetSpec` with fields used by the tests:
`target_scope`, `target_level`, `include_animation`, `prim_path`, `target_id`,
`name`, `category`, `level`, `mesh_count`, and `type_name`.

- [ ] **Step 2: Implement scope resolution**

Implement `resolve_target_scope(stage, requested_scope)` with this priority for
`auto`:

1. `/World/scene/Meshes/Furnitures`
2. `/Root/Meshes/Furnitures`
3. `/World/scene/Instances`
4. `/Root/Instances`
5. `/World/scene`
6. `/Root`

Explicit relative scopes are tried as `/World/<scope>`, `/<scope>`, and under
the default prim when the stage exposes one.

- [ ] **Step 3: Implement target listing**

Implement `list_scene_targets(stage, config)`:

- `object`: find non-empty `model_*` roots under category children; fall back to
  non-empty direct children when no `model_*` roots exist.
- `mesh`: recursively return mesh leaves under the scope.
- `category`: return direct non-empty category children.

Skip inactive prims, instance proxies, invalid prims, light prims, environment
paths, and empty object roots.

- [ ] **Step 4: Run target tests and verify GREEN**

Run:

```bash
python -m pytest tests/capture/test_targets.py -q
```

Expected: all target tests pass.

## Task 3: Implement Bounds, Poses, And Manifest

**Files:**
- Create: `convert_asset/camera/bounds.py`
- Create: `convert_asset/camera/poses.py`
- Create: `convert_asset/capture/manifest.py`

- [ ] **Step 1: Implement `Bounds3D` and bbox helpers**

`Bounds3D` stores `min`, `max`, `center`, `size`, and computed `diagonal`.
`compute_world_bounds(stage, prim_path)` imports `pxr` inside the function and
uses `UsdGeom.BBoxCache` with finite bbox validation.

- [ ] **Step 2: Implement orbit pose planning**

`plan_orbit_poses(bounds, views, distance_scale, start_azimuth_deg)` returns
`CameraPoseSpec` records with view index, azimuth, elevation, distance, position,
and target. The default splits views between positive and negative elevation.

- [ ] **Step 3: Implement manifest records**

Add `TargetRecord`, `CaptureRecord`, `write_targets_json`, and
`append_capture_record`. JSON output must contain only plain Python scalars,
lists, and dictionaries.

- [ ] **Step 4: Run pose and manifest tests**

Run:

```bash
python -m pytest tests/capture/test_poses_manifest.py -q
```

Expected: all pose and manifest tests pass.

## Task 4: Implement Pipelines And CLI

**Files:**
- Create: `convert_asset/capture/pipeline.py`
- Create: `convert_asset/render/__init__.py`
- Create: `convert_asset/render/viewport.py`
- Create: `convert_asset/datasets/__init__.py`
- Create: `convert_asset/datasets/grscenes.py`
- Modify: `convert_asset/cli.py`

- [ ] **Step 1: Implement `run_target_list`**

Open the stage with `pxr.Usd.Stage.Open`, list targets, compute bounds for each
target when possible, print a compact inventory, and write `targets.json` when
`--out` is provided.

- [ ] **Step 2: Implement viewport rendering helpers**

Move reusable logic from `scripts/render_with_viewport_capture.py` into
`convert_asset/render/viewport.py` with lazy Isaac imports:
`create_simulation_app`, `enable_viewport_extension`, `wait_frames`,
`open_stage`, `get_viewport`, and `capture_viewport_image`.

- [ ] **Step 3: Implement `run_target_capture`**

Start one app, open one stage, create one camera prim, plan views for each
target, capture images, and append one manifest record per planned view.

- [ ] **Step 4: Add CLI commands**

Add `target-list` and `target-capture` argparse subcommands. Keep `thumbnails`
unchanged.

- [ ] **Step 5: Run CLI help and compile checks**

Run:

```bash
python -m py_compile convert_asset/capture/targets.py convert_asset/capture/manifest.py convert_asset/capture/pipeline.py convert_asset/camera/bounds.py convert_asset/camera/poses.py convert_asset/render/viewport.py convert_asset/datasets/grscenes.py convert_asset/cli.py
```

Run:

```bash
python ./main.py --help
```

Expected: both commands exit 0 and the help includes `target-list` and
`target-capture`.

## Task 5: Document The Feature

**Files:**
- Create: `docs/design/target-capture.md`
- Create: `docs/operations/target-capture.md`
- Create: `docs/records/2026-05-14-target-capture.md`
- Modify: `docs/index.md`
- Modify: `docs/design/README.md`
- Modify: `docs/operations/README.md`
- Modify: `docs/records/README.md`
- Modify: `docs/superpowers/README.md`

- [ ] **Step 1: Write architecture doc**

Explain target levels, GRScenes defaults, module boundaries, and why object roots
are the default.

- [ ] **Step 2: Write operations doc**

Include `target-list` and `target-capture` command examples, smoke-test workflow,
output layout, and known rendering limits.

- [ ] **Step 3: Write implementation record**

Record the investigation, design decisions, changed files, validation commands,
baseline test caveat, and follow-up dataset batching work.

- [ ] **Step 4: Update indexes**

Add links to the new design, operations, record, and superpowers artifacts.

## Task 6: Verify, Review, Commit, Push

**Files:**
- All changed files.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/capture -q
```

Expected: all capture tests pass.

- [ ] **Step 2: Run compile checks**

Run:

```bash
python -m py_compile convert_asset/capture/targets.py convert_asset/capture/manifest.py convert_asset/capture/pipeline.py convert_asset/camera/bounds.py convert_asset/camera/poses.py convert_asset/render/viewport.py convert_asset/datasets/grscenes.py convert_asset/cli.py
```

Expected: exit 0.

- [ ] **Step 3: Run sample USD target inventory**

Run:

```bash
./scripts/isaac_python.sh ./main.py target-list /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100/home/MV7J6NIKTKJZ2AABAAAAADQ8_usd/layout.usd --target-level object --limit 5 --out /tmp/convertasset-targets.json
```

Expected: exit 0, prints object targets, and writes JSON.

- [ ] **Step 4: Request code review**

Dispatch a reviewer with the spec, plan, and git diff. Fix Critical and Important
findings before proceeding.

- [ ] **Step 5: Commit and push**

Run:

```bash
git status --short
git add convert_asset tests docs
git commit -m "feat: add scene target capture pipeline"
git push -u origin feature/target-capture
```

Expected: commit succeeds and branch is pushed.

