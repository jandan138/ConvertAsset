# GRScenes Target Resolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn selected GRScenes VLM episode targets from manifest-only records into USD-resolved target prim records with world-space bounding boxes.

**Architecture:** Add one read-only experiment script beside the existing GRScenes VLM source-manifest script. The script loads `source_manifest.json`, opens each selected source USD with lazy `pxr` imports, matches episode `metadata_model_paths` against authored reference/payload asset paths, computes target world bboxes, and writes a separate `target_manifest.json` without mutating the benchmark source tree.

**Tech Stack:** Python stdlib for manifest handling, Isaac Sim `pxr` bindings for USD traversal and bbox computation, pytest for pure helper tests.

---

### Task 1: Pure Target-Resolution Helpers

**Files:**
- Create: `tests/test_grscenes_vlm_target_resolver.py`
- Create: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py`

- [x] **Step 1: Write failing helper tests**

Add tests that prove:
- `../../models/object/others/cabinet/hash/instance.usd` matches `models/object/others/cabinet/hash/instance.usd`.
- `object_instance_id` instance index selects the matching candidate deterministically.
- unresolved candidates get explicit `mapping_status` values instead of silent nulls.

- [x] **Step 2: Run RED**

Run: `python -m pytest tests/test_grscenes_vlm_target_resolver.py -q`

Expected: FAIL because `resolve_target_prims.py` does not exist yet.

- [x] **Step 3: Implement pure helpers**

Implement helper functions for path normalization, metadata path matching, candidate filtering, deterministic candidate selection, and record enrichment. Do not import `pxr` at module import time.

- [x] **Step 4: Run GREEN**

Run: `python -m pytest tests/test_grscenes_vlm_target_resolver.py -q`

Expected: PASS.

### Task 2: USD Stage Reader

**Files:**
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py`
- Test: `tests/test_grscenes_vlm_target_resolver.py`

- [x] **Step 1: Add test boundary**

Add a test asserting the module can be imported in normal Python without `pxr`.

- [x] **Step 2: Implement lazy pxr traversal**

Inside USD-only functions, import `pxr.Usd`, `pxr.UsdGeom`, and related modules. Traverse prims, collect authored references/payloads, compute world bbox via `UsdGeom.BBoxCache`, and return serializable prim records.

- [x] **Step 3: Run unit tests**

Run: `python -m pytest tests/test_grscenes_vlm_target_resolver.py -q`

Expected: PASS.

### Task 3: Manifest CLI and Real Smoke Run

**Files:**
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py`
- Create: `paper/shared/evidence/raw/grscene_vlm_grounding/target_manifest.json`

- [x] **Step 1: Implement CLI**

Add `--manifest`, `--out`, `--limit-scenes`, and `--fail-on-unresolved` arguments. Default input is the existing source manifest and default output is `paper/shared/evidence/raw/grscene_vlm_grounding/target_manifest.json`.

- [x] **Step 2: Run Isaac/pxr smoke**

Run: `./scripts/isaac_python.sh paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py --limit-scenes 1 --out /tmp/grscene_target_manifest_smoke.json`

Expected: script opens one selected source scene read-only and writes a JSON report.

- [x] **Step 3: Run full selected manifest**

Run: `./scripts/isaac_python.sh paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py`

Expected: target manifest exists with resolution summary and per-record mapping statuses.

### Task 4: Documentation and Review

**Files:**
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- Modify: `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- Create: `docs/records/2026-05-20-grscenes-target-resolver.md`
- Modify: `docs/records/README.md`
- Modify: `docs/superpowers/README.md`

- [x] **Step 1: Document behavior**

Record that the resolver is read-only against `/cpfs/user/zhuzihou/assets/zzh-grscenes`, writes only repo raw manifests, and produces no VLM performance claims.

- [x] **Step 2: Verify**

Run:
- `python -m pytest tests/test_grscenes_vlm_target_resolver.py tests/test_grscenes_vlm_manifest.py -q`
- `python -m py_compile paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py`
- `git diff --check`

- [ ] **Step 3: Review, commit, push**

Request agent review, address findings, then commit and push.
