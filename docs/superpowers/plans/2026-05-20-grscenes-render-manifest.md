# GRScenes Render Manifest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the next ACL/VLM gate that turns resolved GRScenes targets into paired original/no-MDL render plans with deterministic camera poses and output paths.

**Architecture:** Add a pure-Python manifest generator beside the existing source and target manifest scripts. It consumes `target_manifest.json`, collapses duplicate episode records into unique spatial targets, creates target-centered camera views, emits original/converted render jobs with identical camera metadata, and writes `render_manifest.json` without opening USD stages or mutating datasets.

**Tech Stack:** Python stdlib JSON/path/hash helpers, pytest for pure helper tests, existing GRScenes evidence docs and raw manifest taxonomy.

---

### Task 1: Render Manifest Tests

**Files:**
- Create: `tests/test_grscenes_vlm_render_manifest.py`
- Create: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py`

- [ ] **Step 1: Write failing tests**

Cover:
- the module imports without `pxr`;
- duplicate episode records collapse to one unique render target with both episode IDs preserved;
- one target with two views produces two render pairs and four render jobs;
- original and converted jobs share the same camera pose and differ only by material condition/USD/output path;
- `--require-converted` style validation can detect missing converted USDs.

- [ ] **Step 2: Run RED**

Run:

```bash
python -m pytest tests/test_grscenes_vlm_render_manifest.py -q
```

Expected: FAIL because the generator does not exist yet.

### Task 2: Pure Generator

**Files:**
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py`
- Modify: `tests/test_grscenes_vlm_render_manifest.py`

- [ ] **Step 1: Implement pure helpers**

Implement JSON loading, source scene lookup, target keying, stable ID hashing, bbox center/size validation, deterministic camera pose creation, render output path creation, and missing-converted accounting. Do not import `pxr` or `omni`.

- [ ] **Step 2: Run GREEN**

Run:

```bash
python -m pytest tests/test_grscenes_vlm_render_manifest.py -q
```

Expected: PASS.

### Task 3: Manifest Artifact and Docs

**Files:**
- Create: `paper/shared/evidence/raw/grscene_vlm_grounding/render_manifest.json`
- Modify: `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/README.md`
- Modify: `paper/shared/evidence/raw/grscene_vlm_grounding/README.md`
- Modify: `paper/shared/evidence/results_manifest.yaml`
- Modify: `paper/venues/acl27/STATUS.md`
- Create: `docs/records/2026-05-20-grscenes-vlm-render-manifest.md`
- Modify: `docs/records/README.md`
- Modify: `docs/superpowers/README.md`

- [ ] **Step 1: Run generator**

Run:

```bash
python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py
```

Expected: `render_manifest.json` exists, summarizes 23 unique targets, 4 views per target, 92 paired views, and 184 condition jobs for the current selected pilot.

- [ ] **Step 2: Document the gate**

Record that this is still a render plan, not image output or VLM performance; converted jobs may be marked missing until no-MDL scratch conversion is materialized.

- [ ] **Step 3: Verify**

Run:

```bash
python -m pytest tests/test_grscenes_vlm_render_manifest.py tests/test_grscenes_vlm_target_resolver.py tests/test_grscenes_vlm_manifest.py tests/test_paper_layout.py -q
python -m py_compile paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py
git diff --check
```

Expected: all commands pass.

### Task 4: Review, Commit, Push

**Files:** all changed files from Tasks 1-3.

- [ ] **Step 1: Request independent review**

Ask a fresh review agent to inspect schema completeness, provenance, duplicate-target handling, and docs consistency.

- [ ] **Step 2: Address findings**

Fix Critical/Important findings and rerun the relevant verification command.

- [ ] **Step 3: Commit and push**

Commit with:

```bash
git commit -m "feat(paper): plan grscenes vlm render pairs"
```

Push `main` and verify `origin/main` points at the new commit.
