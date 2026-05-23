# InternNav VLN Main-Result Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the reproducible batch, statistics, and video-manifest infrastructure needed to turn the InternNav/DualVLN smoke bridge into an ACL main-result benchmark.

**Architecture:** Extend the existing `07_internnav_vln_downstream` evidence package rather than creating a parallel experiment tree. Keep large InternNav logs and videos outside git, while committing small manifests, result summaries, tests, and paper status updates.

**Tech Stack:** Python stdlib, pytest, InternNav result JSON/LMDB outputs, GRScenes SN episode metadata, optional ffmpeg for final video composition.

---

### Task 1: Dynamic Batch Preparation

**Files:**
- Modify: `paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py`
- Modify: `tests/test_internnav_vln_downstream_prep.py`
- Update: `paper/shared/evidence/experiments/07_internnav_vln_downstream/README.md`

- [ ] **Step 1: Write failing tests**

Add tests that call `prepare_minipair(..., split_name="acl_main_050", max_episodes=2)` and assert:

```python
assert manifest["dataset"]["split"] == "acl_main_050"
assert "convertasset_grscene_sn_original_acl_main_050" in manifest["internnav_eval_commands"]["original"]
assert "convertasset_grscene_sn_modified_acl_main_050" in manifest["internnav_eval_commands"]["converted"]
assert manifest["internnav_eval_commands"]["expected_result_jsons"] == [
    "logs/convertasset_grscene_sn_original_acl_main_050/result.json",
    "logs/convertasset_grscene_sn_modified_acl_main_050/result.json",
]
```

- [ ] **Step 2: Run red test**

Run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py::test_prepare_minipair_uses_dynamic_task_names_for_acl_batch -q
```

Expected: fail because task names are still hard-coded to `mini`.

- [ ] **Step 3: Implement dynamic task naming**

Generate task names from `split_name` and condition. Use `modified` as the
generic paper-facing condition label while preserving no-MDL provenance in
`source.nomdl_work_root`.

- [ ] **Step 4: Run green tests**

Run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py -q
```

Expected: all tests pass.

### Task 2: Per-Episode Extraction Contract

**Files:**
- Create: `paper/shared/evidence/experiments/07_internnav_vln_downstream/extract_episode_metrics.py`
- Modify: `tests/test_internnav_vln_downstream_prep.py`
- Update: `paper/shared/evidence/experiments/07_internnav_vln_downstream/README.md`

- [ ] **Step 1: Write failing tests**

Add tests for a pure helper that converts InternNav LMDB records into committed
JSON-safe rows:

```python
row = module.record_to_episode_row(
    condition="original",
    path_key="scene_obj_0_0",
    record={
        "info": {"TL": 10.0, "NE": 1.0, "osr": 1.0, "success": 0.0, "spl": 0.0, "steps": 200},
        "finish_status": "fail",
        "fail_reason": "exceed_total_max_step",
    },
)
assert row["condition"] == "original"
assert row["metrics"]["TL"] == 10.0
assert row["failure_reason"] == "exceed_total_max_step"
```

- [ ] **Step 2: Run red test**

Run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py::test_extract_episode_metrics_normalizes_internnav_lmdb_record -q
```

Expected: fail because the script does not exist yet.

- [ ] **Step 3: Implement extractor**

Implement lazy imports for `lmdb` and `msgpack_numpy` inside the actual LMDB
read function so unit tests can run without InternNav runtime packages.

- [ ] **Step 4: Run green tests**

Run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py -q
```

Expected: all tests pass.

### Task 3: Paired Statistics Summary

**Files:**
- Create: `paper/shared/evidence/experiments/07_internnav_vln_downstream/analyze_paired_metrics.py`
- Modify: `tests/test_internnav_vln_downstream_prep.py`
- Update: `paper/shared/evidence/raw/internnav_vln_downstream/README.md`

- [ ] **Step 1: Write failing tests**

Add a synthetic paired metrics test with two episodes and assert mean deltas,
paired win/loss counts, and effect-size fields.

- [ ] **Step 2: Run red test**

Run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py::test_analyze_paired_metrics_computes_paper_summary -q
```

Expected: fail because the analyzer does not exist yet.

- [ ] **Step 3: Implement analyzer**

Use only stdlib statistics. Emit `schema_version`, `episode_count`,
`metrics`, `paired_deltas`, `paired_outcomes`, and `claim_gate`.

- [ ] **Step 4: Run green tests**

Run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py -q
```

Expected: all tests pass.

### Task 4: Video Case Manifest

**Files:**
- Create: `paper/shared/evidence/experiments/07_internnav_vln_downstream/select_video_cases.py`
- Modify: `tests/test_internnav_vln_downstream_prep.py`
- Update: `paper/shared/evidence/experiments/07_internnav_vln_downstream/README.md`

- [ ] **Step 1: Write failing tests**

Add tests that feed paired episode metrics into the selector and assert it
chooses bounded representative cases:

```python
assert manifest["storage_policy"]["metric_runs_keep_video_disabled"] is True
assert manifest["case_quota"]["max_cases"] == 8
assert {case["case_type"] for case in manifest["selected_cases"]}
```

- [ ] **Step 2: Run red test**

Run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py::test_select_video_cases_builds_storage_bounded_manifest -q
```

Expected: fail because the selector does not exist yet.

- [ ] **Step 3: Implement selector**

Select examples by paired outcome: both success with trajectory divergence,
original-only success, modified-only success, both failure with large `NE` or
`TL` delta, and representative neutral cases.

- [ ] **Step 4: Run green tests**

Run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py -q
```

Expected: all tests pass.

### Task 5: Documentation And ACL Paper Integration

**Files:**
- Modify: `docs/superpowers/README.md`
- Create or modify: `docs/records/2026-05-23-internnav-vln-main-result-roadmap.md`
- Modify: `paper/EXPERIMENT_CHECKLIST.md`
- Modify: `paper/venues/acl27/STATUS.md`
- Modify after real batch results exist: `paper/shared/sections/experiments.tex`
- Modify after real batch results exist: `paper/venues/acl27/sections/limitations.tex`

- [ ] **Step 1: Record the current roadmap**

Document that the main-result goal is active and that this iteration adds the
batch/stat/video infrastructure, not final benchmark results.

- [ ] **Step 2: Update status files**

Status must say that one-episode smoke is complete, batch main-result execution
is pending, and the next hard evidence gate is multi-episode paired metrics.

- [ ] **Step 3: Keep manuscript claims bounded**

Do not replace the current one-episode paragraph with a broad benchmark claim
until real multi-episode outputs exist and pass the claim gate.

### Task 6: Verification And Commit

**Files:**
- All files changed in Tasks 1-5

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/test_internnav_vln_downstream_prep.py -q
```

- [ ] **Step 2: Run script dry checks**

Run:

```bash
python paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py --max-episodes 2 --split-name acl_main_pilot --scene-id MV7J6NIKTKJZ2AABAAAAADY8_usd
```

- [ ] **Step 3: Run whitespace check**

Run:

```bash
git diff --check
```

- [ ] **Step 4: Commit and push**

Commit with:

```bash
git commit -m "feat(paper): scaffold InternNav VLN main-result benchmark"
```

Push to `main` after verification passes.
