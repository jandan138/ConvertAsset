# AAN-07 Benchmark Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `AAN-07-benchmark-contract`, which writes and validates EBench task handoff files for normalized packages.

**Architecture:** Keep AAN-07 as a narrow post-static/post-runtime gate in `convert_asset/asset_application_normalizer/`. A new `benchmark_contract.py` module will load a JSON or simple YAML task contract, validate required semantic prim roles against the packaged stage, write `task/task_config.yaml`, `task/required_prims.yaml`, and `task/evaluator.yaml`, and return manifest evidence. The pipeline will run it only when `benchmark` appears in `--gates`.

**Tech Stack:** Python standard library, existing AAN model/layout/manifest patterns, lazy `pxr` imports inside functions, pytest.

---

## File Structure

- Create `convert_asset/asset_application_normalizer/benchmark_contract.py`
  - Owns task contract loading, validation, file writing, and AAN-07 result records.
- Modify `convert_asset/asset_application_normalizer/model.py`
  - Add `MILESTONE_AAN07 = "AAN-07-benchmark-contract"`.
- Modify `convert_asset/asset_application_normalizer/evidence_manifest.py`
  - Add benchmark contract fields and command stage mapping.
- Modify `convert_asset/asset_application_normalizer/pipeline.py`
  - Run AAN-07 after AAN-05 or AAN-06 when `benchmark` gate is requested.
- Modify `tests/test_asset_application_normalizer_cli.py`
  - Add failing tests first for pass and blocked AAN-07 cases.
- Modify docs after implementation:
  - `docs/design/asset-application-normalizer.md`
  - `docs/records/2026-06-30-aan-07-benchmark-contract.md`
  - `docs/records/README.md`

## Task 1: Add AAN-07 RED Tests

**Files:**
- Modify: `tests/test_asset_application_normalizer_cli.py`

- [ ] **Step 1: Write failing pass test**

Add a test named `test_normalize_asset_benchmark_gate_writes_ebench_task_contract` that:

```python
contract = {
    "task_config": {
        "task_id": "Lift2.DryingBox",
        "benchmark": "ebench-lift2",
        "asset_id": "DryingBox",
    },
    "required_prims": {
        "asset_root": "/World/DryingBox",
        "manipulated_body": "/World/DryingBox/Body",
        "collision_root": "/World/DryingBox/Body",
        "articulation_root": "/World/DryingBox",
        "spawn_anchor": "/World/DryingBox",
        "goal_target": "/World/DryingBox/Goal",
    },
    "evaluator": {
        "entrypoint": "ebench.evaluators.lift2:DryingBoxEvaluator",
        "metric": "door_open_success",
    },
}
```

It should write a small articulated USD with `/World/DryingBox`, `/World/DryingBox/Body`, and `/World/DryingBox/Goal`, run with `--contract <contract.json> --gates static,benchmark`, then assert:

```python
assert code == 0
assert (out_dir / "task" / "task_config.yaml").exists()
assert (out_dir / "task" / "required_prims.yaml").exists()
assert (out_dir / "task" / "evaluator.yaml").exists()
assert manifest["milestone"] == "AAN-07-benchmark-contract"
assert manifest["stage_gates"][-1]["check_id"] == "AAN-07-benchmark-contract"
assert manifest["benchmark_contract"]["status"] == "pass"
assert manifest["benchmark_contract"]["task_files"]["task_config"] == "task/task_config.yaml"
assert "EBench task readiness is achieved." in manifest["claims_allowed"]
assert "EBench task readiness is achieved." not in manifest["claims_forbidden"]
```

- [ ] **Step 2: Write failing blocked test**

Add a test named `test_normalize_asset_benchmark_gate_blocks_without_evaluator_entrypoint` that uses a contract missing `evaluator.entrypoint` and asserts:

```python
assert code == 5
assert manifest["milestone"] == "AAN-07-benchmark-contract"
assert manifest["overall_status"] == "blocked"
assert manifest["stage_gates"][-1]["status"] == "blocked"
assert manifest["benchmark_contract"]["status"] == "blocked"
assert "aan07_block_missing_evaluator_entrypoint" in blocker_ids
assert not (out_dir / "task" / "evaluator.yaml").exists()
assert "EBench task readiness is achieved." in manifest["claims_forbidden"]
```

- [ ] **Step 3: Run RED tests**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_benchmark_gate_writes_ebench_task_contract tests/test_asset_application_normalizer_cli.py::test_normalize_asset_benchmark_gate_blocks_without_evaluator_entrypoint -q
```

Expected: both fail because AAN-07 does not exist yet.

## Task 2: Implement Benchmark Contract Module

**Files:**
- Create: `convert_asset/asset_application_normalizer/benchmark_contract.py`
- Modify: `convert_asset/asset_application_normalizer/model.py`

- [ ] **Step 1: Add milestone constant**

Add:

```python
MILESTONE_AAN07 = "AAN-07-benchmark-contract"
```

- [ ] **Step 2: Implement module result and not-run helper**

Create `BenchmarkContractResult` with:

```python
overall_status: str
return_code: int
benchmark_contract: dict[str, Any]
task_contract_report: dict[str, Any]
stage_gate: dict[str, Any]
blocked_reasons: list[dict[str, Any]]
```

Add `build_not_run_benchmark_contract(reason: str)` returning status `not_run`, return code `0`, and AAN-07 stage gate `not_run`.

- [ ] **Step 3: Implement contract loading**

Implement `load_contract(path: Path) -> dict[str, Any]`.

Rules:
- `.json` uses `json.loads`.
- YAML uses a tiny repository-local parser only for simple maps, strings, numbers, booleans, and nested dictionaries.
- Invalid or missing contract produces a blocking AAN-07 result, not a traceback.

- [ ] **Step 4: Implement validation**

`build_benchmark_contract(layout, request)` must require:

```python
task_config.task_id
task_config.benchmark
task_config.asset_id
required_prims.asset_root
required_prims.manipulated_body
required_prims.collision_root
required_prims.spawn_anchor
required_prims.goal_target
evaluator.entrypoint
evaluator.metric
```

For `request.asset_class == "articulated"`, also require `required_prims.articulation_root`; for rigid/auto without articulation, allow `"N/A"` or `None`.

Every non-`N/A` required prim must exist in `layout.root_usd`, checked with lazy `pxr.Usd`.

- [ ] **Step 5: Write task files only on pass**

When all checks pass, write:

```text
task/task_config.yaml
task/required_prims.yaml
task/evaluator.yaml
```

Use deterministic YAML output with primitive keys sorted by insertion order. Do not write partial task files on blocked contracts.

- [ ] **Step 6: Run GREEN focused tests**

Run the two AAN-07 tests from Task 1. Expected: both pass.

## Task 3: Integrate AAN-07 Into Pipeline And Manifest

**Files:**
- Modify: `convert_asset/asset_application_normalizer/evidence_manifest.py`
- Modify: `convert_asset/asset_application_normalizer/pipeline.py`

- [ ] **Step 1: Extend manifest builder**

Add optional fields:

```python
benchmark_contract: dict[str, Any] | None = None
task_contract_report: dict[str, Any] | None = None
```

Manifest should include:

```python
"benchmark_contract": benchmark_contract or {},
```

And include `task_contract_report` when provided.

- [ ] **Step 2: Extend command stage mapping**

Map `MILESTONE_AAN07` to `benchmark_contract`.

- [ ] **Step 3: Pipeline gate order**

In `normalize_asset`, compute:

```python
runtime_requested = "runtime" in set(request.gates)
benchmark_requested = "benchmark" in set(request.gates)
```

Run AAN-07 if:

```python
benchmark_requested and physics passed and (not runtime_requested or runtime passed)
```

Otherwise return `not_run` AAN-07 with a clear reason.

- [ ] **Step 4: Return code and milestone**

If benchmark is requested, final milestone is `MILESTONE_AAN07`. Return code includes benchmark return code. Overall status is benchmark status when it runs or blocks.

- [ ] **Step 5: Claims**

Add allowed claim only when AAN-07 passes:

```python
"EBench task readiness is achieved."
"AAN-07 wrote EBench task_config, required_prims, and evaluator entrypoint files."
```

Keep forbidden claim when AAN-07 is not pass.

- [ ] **Step 6: Run full focused tests**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py -q
```

Expected: all pass.

## Task 4: Real DryingBox AAN-07 Evidence And Docs

**Files:**
- Create: `docs/records/2026-06-30-aan-07-benchmark-contract.md`
- Modify: `docs/records/README.md`
- Modify: `docs/design/asset-application-normalizer.md`
- Add evidence under: `docs/records/evidence/2026-06-30-aan-07-dryingbox-benchmark-contract/`

- [ ] **Step 1: Create DryingBox contract JSON**

Use the real DryingBox required root from AAN-05/06:

```text
/World/labutopia_level1_poc/obj_obj_DryingBox_01
```

Use conservative evaluator metadata:

```json
{
  "entrypoint": "ebench.evaluators.lift2:DryingBoxEvaluator",
  "metric": "door_state_success"
}
```

- [ ] **Step 2: Run real AAN-07 command**

Run with:

```bash
./scripts/isaac_python.sh ./main.py normalize-asset <lab_001 scene.usda> \
  --out /tmp/aan07_real_packages/overlay_level1_poc_dryingbox_01_benchmark \
  --asset-id DryingBox_01_overlay \
  --asset-class articulated \
  --source-runtime isaac51 \
  --target-runtime isaac41 \
  --target-benchmark ebench-lift2 \
  --task-id Lift2.DryingBox \
  --contract /tmp/aan07_real_packages/dryingbox_contract.json \
  --required-prim /World/labutopia_level1_poc/obj_obj_DryingBox_01 \
  --gates static,benchmark \
  --evidence-out /tmp/aan07_real_packages/overlay_level1_poc_dryingbox_01_benchmark/manifest.json
```

Expected: AAN-07 pass.

- [ ] **Step 3: Copy evidence**

Copy manifest and task files to:

```text
docs/records/evidence/2026-06-30-aan-07-dryingbox-benchmark-contract/
```

- [ ] **Step 4: Update docs**

Record:
- code changes
- DryingBox AAN-07 evidence
- task files written
- claim boundary: EBench task contract is ready for adapter consumption, not official leaderboard comparability

## Task 5: Final Verification And Commit

**Files:**
- All modified files.

- [ ] **Step 1: Run verification**

Run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports -q
python -m py_compile convert_asset/asset_application_normalizer/*.py
git diff --check
```

Expected: all pass.

- [ ] **Step 2: Inspect status**

Run:

```bash
git status --short
```

Expected: only AAN-07 implementation, tests, docs, and evidence files.

- [ ] **Step 3: Commit**

Run:

```bash
git add convert_asset/asset_application_normalizer tests/test_asset_application_normalizer_cli.py docs/design/asset-application-normalizer.md docs/records/README.md docs/records/2026-06-30-aan-07-benchmark-contract.md docs/records/evidence/2026-06-30-aan-07-dryingbox-benchmark-contract docs/superpowers/plans/2026-06-30-aan-07-benchmark-contract.md
git commit -m "feat(aan): add benchmark contract gate"
```

## Self-Review

- Spec coverage: AAN-07 deliverables, pass criteria, blocked criteria, manifest entrypoints, claims, and DryingBox evidence are covered.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: `benchmark_contract`, `task_contract_report`, `MILESTONE_AAN07`, and stage gate names are consistent across tasks.
