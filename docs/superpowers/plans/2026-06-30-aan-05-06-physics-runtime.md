# AAN-05/06 Physics and Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AAN-05 static physics/articulation closure and AAN-06 Isaac 4.1 runtime smoke evidence to `normalize-asset`.

**Architecture:** Preserve the existing AAN-03/AAN-04 gate chain. `physics_checks.py` performs pxr-only static inspection of the packaged USD, while `runtime_smoke.py` owns the optional Isaac headless subprocess and writes machine-readable evidence. Static runs end at AAN-05; AAN-06 runs only when `runtime` is requested in `--gates`.

**Tech Stack:** Python stdlib, lazy `pxr` imports, optional Isaac Sim 4.1 headless subprocess through `scripts/isaac_python.sh`, pytest.

---

### Task 1: AAN-05 Static Physics Tests

**Files:**
- Modify: `tests/test_asset_application_normalizer_cli.py`

- [ ] **Step 1: Write the failing authored-physics test**

Add a test that builds a USDA asset with `PhysicsArticulationRootAPI`, `PhysicsRigidBodyAPI`, `PhysicsCollisionAPI`, `PhysicsMassAPI`, and one `PhysicsRevoluteJoint`. Run `normalize-asset` without `--dry-run`; expect milestone `AAN-05-physics-static`, a pass AAN-05 gate, one authored rigid body, one authored collision, one authored mass record, one articulation root, and one joint with axis/limits.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_writes_physics_static_closure_for_authored_articulation -q
```

Expected: fail because AAN-05 manifest fields and milestone do not exist yet.

- [ ] **Step 3: Write the failing missing-articulation blocker test**

Add a test that normalizes an `asset_class=articulated` USD with no articulation root or joint. Expect return code `5`, AAN-05 gate `blocked`, and blocker id `aan05_block_missing_articulation`.

- [ ] **Step 4: Verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_articulated_asset_without_articulation_facts -q
```

Expected: fail because current pipeline stops at AAN-04 and passes the empty asset.

### Task 2: AAN-05 Static Physics Implementation

**Files:**
- Modify: `convert_asset/asset_application_normalizer/model.py`
- Create: `convert_asset/asset_application_normalizer/physics_checks.py`
- Modify: `convert_asset/asset_application_normalizer/evidence_manifest.py`
- Modify: `convert_asset/asset_application_normalizer/pipeline.py`

- [ ] **Step 1: Add milestone constant**

Add:

```python
MILESTONE_AAN05 = "AAN-05-physics-static"
```

- [ ] **Step 2: Implement `PhysicsCheckResult` and not-run result**

Create a dataclass with `overall_status`, `return_code`, `physics_closure`, `articulation_closure`, `static_physics_report`, `static_articulation_report`, `stage_gate`, and `blocked_reasons`. Add `build_not_run_physics_checks(reason)`.

- [ ] **Step 3: Implement package static inspection**

Open `TargetPackageLayout.root_usd` with lazy `from pxr import Usd, UsdGeom, UsdPhysics`. Traverse prims and collect:

```python
rigid_bodies = prims with PhysicsRigidBodyAPI
collisions = prims with PhysicsCollisionAPI
mass_records = prims with PhysicsMassAPI attrs
articulation_roots = prims with PhysicsArticulationRootAPI
joints = prims whose type name starts with "Physics" and ends with "Joint"
```

Every authored value record must include `value_source: "authored"` and owning layer where available.

- [ ] **Step 4: Implement blockers**

Block when stage open fails, required prim paths are absent, an `articulated` asset has no articulation root or no joints, or a joint is missing required axis/lower/upper values. Do not block missing drive on externally manipulated assets; record it as `drive_status: "not_authored"`.

- [ ] **Step 5: Wire pipeline and manifest**

Run AAN-05 only after AAN-04 passes. If AAN-03/AAN-04 blocked, append an AAN-05 `not_run` gate. Add `physics_closure`, `articulation_closure`, `static_physics_report`, and `static_articulation_report` parameters to `build_manifest`.

- [ ] **Step 6: Verify GREEN**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_writes_physics_static_closure_for_authored_articulation tests/test_asset_application_normalizer_cli.py::test_normalize_asset_blocks_articulated_asset_without_articulation_facts -q
```

Expected: both pass.

### Task 3: AAN-06 Runtime Smoke Contract Tests

**Files:**
- Modify: `tests/test_asset_application_normalizer_cli.py`

- [ ] **Step 1: Write runtime-gate integration test with fake smoke result**

Call `normalize_asset()` directly with `gates=["static", "runtime"]`, monkeypatch `pipeline.build_runtime_smoke` to return a pass `RuntimeSmokeResult`, and assert milestone `AAN-06-runtime-smoke`, a pass AAN-06 gate, and populated `runtime_evidence.render_readback`.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_runtime_gate_records_smoke_evidence_when_requested -q
```

Expected: fail because the runtime result type and AAN-06 pipeline hook do not exist.

### Task 4: AAN-06 Runtime Smoke Implementation

**Files:**
- Modify: `convert_asset/asset_application_normalizer/model.py`
- Create: `convert_asset/asset_application_normalizer/runtime_smoke.py`
- Modify: `convert_asset/asset_application_normalizer/evidence_manifest.py`
- Modify: `convert_asset/asset_application_normalizer/pipeline.py`

- [ ] **Step 1: Add milestone constant**

Add:

```python
MILESTONE_AAN06 = "AAN-06-runtime-smoke"
```

- [ ] **Step 2: Implement result type and not-run result**

Create `RuntimeSmokeResult` with `overall_status`, `return_code`, `runtime_evidence`, `stage_gate`, and `blocked_reasons`. Add `build_not_run_runtime_smoke(reason)`.

- [ ] **Step 3: Implement subprocess contract**

When requested, run:

```bash
./scripts/isaac_python.sh -m convert_asset.asset_application_normalizer.runtime_smoke --worker --root-usd <package>/asset.usd --required-prim <path> --report-out <package>/evidence/runtime_smoke/report.json --render-out <package>/evidence/runtime_smoke/render.png
```

Capture stdout/stderr under `package/evidence/runtime_smoke/`, use a timeout, and write command contract into `runtime_evidence.commands.runtime_smoke_001`.

- [ ] **Step 4: Implement worker**

Inside the worker, lazy-import `isaacsim.SimulationApp`, `omni`, `World`, `Camera`, `pxr`, `numpy`, and `cv2`. Perform cold stage open, required prim existence checks, one render readback with mean RGB / non-background ratio / bbox ratio / SHA-256, finite step smoke, reset smoke, and JSON report emission.

- [ ] **Step 5: Wire pipeline**

If `runtime` is absent from request gates, append AAN-06 `not_run` evidence and keep final milestone AAN-05. If `runtime` is present and AAN-05 passes, run AAN-06 and use its status/return code. If AAN-05 blocks, AAN-06 must be `not_run`.

- [ ] **Step 6: Verify GREEN**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_runtime_gate_records_smoke_evidence_when_requested -q
```

Expected: pass without launching Isaac because the smoke builder is monkeypatched.

### Task 5: Regression, Evidence, and Docs

**Files:**
- Modify: `docs/design/asset-application-normalizer.md` if implementation clarifies schema fields.
- Create: `docs/records/2026-06-30-aan-05-06-physics-runtime.md`
- Create/update: `docs/records/evidence/2026-06-30-aan-05-06-dryingbox-physics-runtime/`

- [ ] **Step 1: Run focused regression**

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports -q
```

- [ ] **Step 2: Run DryingBox static evidence**

Use the previous DryingBox overlay source and required prim, with `--gates static`, to produce AAN-05 evidence.

- [ ] **Step 3: Run DryingBox runtime evidence if the existing Isaac 4.1 environment starts cleanly**

Use the same source with `--gates static,runtime`. If runtime fails, keep the manifest blocked with logs instead of claiming runtime pass.

- [ ] **Step 4: Run integrity checks**

```bash
python -m py_compile convert_asset/asset_application_normalizer/*.py
git diff --check
git status --short
```

- [ ] **Step 5: Commit**

```bash
git add convert_asset/asset_application_normalizer tests/test_asset_application_normalizer_cli.py docs/superpowers/plans/2026-06-30-aan-05-06-physics-runtime.md docs/records docs/design/asset-application-normalizer.md
git commit -m "feat(aan): add physics and runtime smoke gates"
```
