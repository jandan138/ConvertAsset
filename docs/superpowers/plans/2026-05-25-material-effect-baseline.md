# Material-Effect Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an auditable ConvertAsset vs NVIDIA baseline experiment grouped by material effects.

**Architecture:** Keep generated metadata in the repo and heavy scratch/renders under the normalized external research root. Reuse the existing GRScenes material closure and stress manifests for real-scene samples, then add official/sample assets only for effect bins that GRScenes does not cover.

**Tech Stack:** Python stdlib JSON/CSV, pytest, Isaac Sim Kit `SimulationApp`, NVIDIA `omni.kit.asset_converter`, existing ConvertAsset no-MDL outputs.

---

### Task 1: Effect Sample Manifest

**Files:**
- Create: `tests/test_material_effect_baseline_manifest.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_sample_manifest.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/effect_sample_manifest.json`
- Modify: `paper/shared/evidence/results_manifest.yaml`

- [x] **Step 1: Write failing tests**

```bash
python -m pytest -q tests/test_material_effect_baseline_manifest.py
```

Expected before implementation: tests fail because
`build_effect_sample_manifest.py` does not exist.

- [x] **Step 2: Implement effect detection and manifest generation**

Implement `detect_material_effects()` so `opacity: 1.f` is not treated as an
opacity/transparency effect, and implement `build_effect_sample_manifest()` so
selected stress pairs are linked to material closure models by `target_prim_path`.

- [x] **Step 3: Verify tests pass**

```bash
python -m pytest -q tests/test_material_effect_baseline_manifest.py
```

Expected: `3 passed`.

- [x] **Step 4: Generate the real manifest**

```bash
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_sample_manifest.py
```

Expected: writes `paper/shared/evidence/raw/material_effect_baseline/effect_sample_manifest.json`.

### Task 2: NVIDIA Baseline Smoke

**Files:**
- Create: `tests/test_material_effect_baseline_nvidia_smoke.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_asset_converter_smoke.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/nvidia_baseline_smoke_manifest.json`

- [x] **Step 1: Write failing tests for smoke manifest shape**

Test that the smoke manifest records `context_flags`, `input_usd`,
`output_usd`, `conversion_success`, `stage_opened`, `preview_surface_count`,
`active_mdl_shader_count`, and `claimable_as_baseline`.

- [x] **Step 2: Implement the Kit-mode smoke runner**

Use `SimulationApp({"headless": True})`, enable `omni.kit.asset_converter`,
run a tiny USD through `AssetConverterContext(export_preview_surface=True)`,
and write the manifest even on failure. The implementation also writes a
checkpoint manifest before `SimulationApp.close()` so Kit shutdown cannot drop
the audit record after successful conversions.

- [x] **Step 3: Verify smoke output**

```bash
python -m pytest -q tests/test_material_effect_baseline_nvidia_smoke.py
timeout 180 ./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_asset_converter_smoke.py
```

Actual: tests pass, and the smoke manifest records
`ready_for_sample_baseline=true` with two claimable USD baseline candidates:
`usd_to_usd_preview` and `usd_to_usd_bake_flag`.

### Task 3: Baseline Conversion Manifest

**Files:**
- Create: `tests/test_material_effect_baseline_conversion_manifest.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/baseline_conversion_manifest.json`

- [ ] **Step 1: Write failing tests**

Test that each sample has `original_MDL`, `existing_noMDL`, and
`nvidia_asset_converter_preview_or_bake` condition records with status,
hash/provenance, residual MDL counts, and PreviewSurface counts.

- [ ] **Step 2: Implement manifest builder**

Read `effect_sample_manifest.json` and the NVIDIA smoke result. Emit planned
or completed conversion records without claiming success for missing NVIDIA
outputs.

- [ ] **Step 3: Verify**

```bash
python -m pytest -q tests/test_material_effect_baseline_conversion_manifest.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py
```

Expected: manifest exists and refuses broad claims until all selected outputs
exist and pass static gates.

### Task 4: Effect Tables and Qualitative Cases

**Files:**
- Create: `tests/test_material_effect_baseline_tables.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py`
- Create: `paper/shared/tables/material_effect_baseline_summary.csv`
- Create: `paper/shared/tables/tab_material_effect_baseline_summary.tex`

- [ ] **Step 1: Write failing tests**

Test effect-group aggregation over a synthetic conversion manifest, including
missing NVIDIA rows and selected failure cases.

- [ ] **Step 2: Implement table builder**

Aggregate by effect bin, target category, baseline condition, conversion status,
and claim gate. Emit selected qualitative case IDs but do not copy large media.

- [ ] **Step 3: Verify**

```bash
python -m pytest -q tests/test_material_effect_baseline_tables.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py
```

Expected: CSV and LaTeX table exist and are registered in the paper manifest.
