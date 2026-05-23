# InternNav VLN Downstream Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest reproducible InternNav/VL-LN downstream bridge for paired GRScenes original vs no-MDL navigation scenes.

**Architecture:** Keep ConvertAsset as the provenance and preparation layer, not the InternNav runtime. A pure-Python preparer converts GRScenes `sn_episodes.json` into InternNav-compatible `json.gz` episodes, creates external work-root `fixed.usd` scene links, and emits manifests/config stubs that can be consumed by the separate InternNav checkout.

**Tech Stack:** Python stdlib, pytest, GRScenes SN episodes, InternNav config conventions, Isaac Sim only for later no-MDL USD generation.

---

### Task 1: GRScenes SN To InternNav Mini Dataset Preparer

**Files:**
- Create: `paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py`
- Create: `tests/test_internnav_vln_downstream_prep.py`

- [ ] **Step 1: Write failing tests**

Test a synthetic GRScenes source root with one SN episode and paired navigation USDs. Assert the preparer writes `mini.json.gz`, creates `scene_data/original/<scene>/fixed.usd` and `scene_data/converted/<scene>/fixed.usd`, emits InternNav-style fields (`scan`, `start_position`, `start_rotation`, `reference_path`, `instruction`, `info.geodesic_distance`), and records source/conversion provenance.

- [ ] **Step 2: Run red test**

Run: `pytest tests/test_internnav_vln_downstream_prep.py -q`

Expected: FAIL because `prepare_minipair.py` does not exist yet.

- [ ] **Step 3: Implement minimal preparer**

Implement only stdlib code. Do not import `pxr`; do not copy scene payloads into the repository. Use symlinks by default under an external work root and fall back to lightweight file copy for tests.

- [ ] **Step 4: Run green test**

Run: `pytest tests/test_internnav_vln_downstream_prep.py -q`

Expected: PASS.

### Task 2: Real GRScenes Pair Smoke Preparation

**Files:**
- Runtime output only under `/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523`
- Repo output: `paper/shared/evidence/raw/internnav_vln_downstream/prep_manifest.json`

- [ ] **Step 1: Check selected scene has original navigation USD**

Run exact path checks against `/cpfs/user/zhuzihou/assets/zzh-grscenes`; do not do a wide filesystem scan.

- [ ] **Step 2: If no-MDL navigation USD is missing, convert only the selected scratch scene**

Run: `./scripts/isaac_python.sh ./main.py no-mdl /cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes/scenes/<scene_id>/start_result_navigation.usd`

- [ ] **Step 3: Generate the mini-pair work root**

Run the preparer with `--max-episodes 1`, source root `/cpfs/user/zhuzihou/assets/zzh-grscenes`, no-MDL root `/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521`, and work root `/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523`.

### Task 3: InternNav Runbook And Paper Status

**Files:**
- Create: `docs/records/2026-05-23-internnav-vln-downstream-prep.md`
- Modify: `docs/records/README.md`
- Optionally modify: `paper/venues/acl27/STATUS.md`

- [ ] **Step 1: Document the current story state**

Explain that this step prepares paired downstream inputs and run configs, while true SR/SPL still needs InternUtopia, model weights, and full InternNav dependency setup.

- [ ] **Step 2: Record exact commands and blockers**

Include the generated work root, manifest path, eval command template, missing dependencies, and the source-asset safety rule.

### Task 4: Verification And Commit

**Files:**
- All files changed in Tasks 1-3

- [ ] **Step 1: Run focused tests**

Run: `pytest tests/test_internnav_vln_downstream_prep.py -q`

- [ ] **Step 2: Run script smoke**

Run: `python paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py --max-episodes 1`

- [ ] **Step 3: Commit and push**

Commit the repo changes. Push using SSH or the scoped GitHub proxy workflow if HTTPS transport fails.
