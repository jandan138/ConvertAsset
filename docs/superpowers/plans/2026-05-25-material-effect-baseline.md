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

- [x] **Step 1: Write failing tests**

Test that each sample has `original_MDL`, `existing_noMDL`, and
`nvidia_asset_converter_preview_or_bake` condition records with status,
hash/provenance, residual MDL counts, and PreviewSurface counts.

- [x] **Step 2: Implement manifest builder**

Read `effect_sample_manifest.json` and the NVIDIA smoke result. Emit planned
or completed conversion records without claiming success for missing NVIDIA
outputs. The builder prefers the scratch-materialized original USD, not the raw
source path, so stage inspection uses dependency-complete inputs and avoids
under-counting shaders from unresolved relative references.

- [x] **Step 3: Verify**

```bash
python -m pytest -q tests/test_material_effect_baseline_conversion_manifest.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py
```

Actual: manifest exists and refuses broad claims. It records 30/30 available
`original_MDL`, 30/30 available `existing_noMDL`, and after Task 5, 30/30
available NVIDIA rows.

### Task 4: Effect Tables and Qualitative Cases

**Files:**
- Create: `tests/test_material_effect_baseline_tables.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py`
- Create: `paper/shared/tables/material_effect_baseline_summary.csv`
- Create: `paper/shared/tables/tab_material_effect_baseline_summary.tex`

- [x] **Step 1: Write failing tests**

Test effect-group aggregation over a synthetic conversion manifest, including
missing NVIDIA rows and selected failure cases.

- [x] **Step 2: Implement table builder**

Aggregate by effect bin, target category, baseline condition, conversion status,
and claim gate. Emit selected qualitative case IDs but do not copy large media.

- [x] **Step 3: Verify**

```bash
python -m pytest -q tests/test_material_effect_baseline_tables.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py
```

Actual: CSV and LaTeX table exist, include zero-sample rows for `clearcoat` and
`procedural_texture`, and are registered in the paper manifest. The case
manifest currently records 0 static-gate follow-up cases after Task 5.

### Task 5: Sample-Level NVIDIA Conversion

**Files:**
- Create: `tests/test_material_effect_baseline_nvidia_samples.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_sample_conversions.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/nvidia_sample_conversion_manifest.json`
- Modify: `paper/shared/evidence/raw/material_effect_baseline/baseline_conversion_manifest.json`
- Modify: `paper/shared/tables/material_effect_baseline_summary.csv`
- Modify: `paper/shared/evidence/raw/material_effect_baseline/effect_failure_case_manifest.json`

- [x] **Step 1: Write failing tests**

Test that the runner deduplicates 30 sample rows into unique source-scene jobs,
skips existing outputs unless forced, and writes an auditable conversion
manifest.

- [x] **Step 2: Implement and run sample conversions**

Run the smoke-validated `usd_to_usd_preview` route over the five unique selected
source scenes. Store large NVIDIA USD outputs under the external normalized
research root, not in the repo.

- [x] **Step 3: Regenerate manifests and tables**

Regenerate `baseline_conversion_manifest.json` and
`material_effect_baseline_summary.csv` after conversion.

Actual: NVIDIA sample conversion records `scene_job_count=5`,
`successful_scene_count=5`, and `output_exists_count=5`; baseline conversion
records 30/30 available original/noMDL/NVIDIA condition rows. The remaining
blocker is missing `clearcoat` and `procedural_texture` coverage, plus paired
render/qualitative comparison.

### Task 6: Paired Qualitative Render Manifest

**Files:**
- Create: `tests/test_material_effect_baseline_qualitative.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/build_qualitative_render_manifest.py`
- Create: `paper/shared/figures/gen_material_effect_qualitative.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/qualitative_render_manifest.json`
- Create: `paper/shared/figures/fig_material_effect_baseline_qualitative.png`
- Modify: `paper/shared/evidence/results_manifest.yaml`
- Modify: `paper/shared/figures/sources.yaml`

- [x] **Step 1: Write failing tests**

Test that the qualitative manifest selects representative cases from the
covered effect bins, reuses existing expanded30 original/noMDL render images,
and creates a third NVIDIA render record with the same camera, dimensions, and
renderer settings.

- [x] **Step 2: Implement manifest builder**

Build records for `original_MDL`, `existing_noMDL`, and
`nvidia_asset_converter_preview_or_bake`. The first two point to existing
target-centered renders; the NVIDIA record points to a new camera-stage and
image path under
`paper/shared/evidence/raw/material_effect_baseline/qualitative_renders/`.

- [x] **Step 3: Implement figure builder**

Generate a storage-bounded contact sheet only when all selected cases have
ready original/noMDL/NVIDIA images. If NVIDIA images are still missing, emit a
clear manifest blocker instead of producing a misleading figure.

- [x] **Step 4: Author and render NVIDIA qualitative views**

Use the existing camera-stage authoring and viewport-capture scripts to render
only the selected NVIDIA rows. Do not rerender the original/noMDL images unless
their existing files are missing.

- [x] **Step 5: Verify and document**

Run the qualitative tests, parse generated JSON/YAML, and update the design
doc/checklist with the exact number of selected cases and remaining missing-bin
limitations.

Actual: qualitative tests pass, the manifest records 4 selected cases and 12/12
ready condition images, and
`fig_material_effect_baseline_qualitative.png` is generated. The remaining
blocker is still missing `clearcoat` and `procedural_texture` coverage.

### Task 7: Missing-Bin Supplemental Candidate Manifest

**Files:**
- Create: `tests/test_material_effect_baseline_supplemental_candidates.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_effect_candidates.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_effect_candidate_manifest.json`
- Modify: `paper/shared/evidence/experiments/08_material_effect_baseline/README.md`
- Modify: `paper/shared/evidence/raw/material_effect_baseline/README.md`
- Modify: `paper/shared/evidence/results_manifest.yaml`

- [x] **Step 1: Write failing tests**

Test that a candidate manifest reads the current effect gaps, detects effect
tokens from candidate MDL files, and recommends one candidate for each missing
effect without claiming that wrapper scenes or baseline conversions already
exist.

- [x] **Step 2: Implement candidate scanner**

Scan bounded local Isaac Sim/sample roots first. Prefer official Isaac Sim
material-library and NVIDIA MDL SDK examples over ad hoc project scratch
copies. Record source USD paths, MDL paths, hashes, effect evidence, and whether
the candidate is directly renderable or needs a small wrapper stage.

- [x] **Step 3: Generate real candidate manifest**

Generate
`paper/shared/evidence/raw/material_effect_baseline/supplemental_effect_candidate_manifest.json`
from the current `effect_sample_manifest.json`. The expected result is that
`clearcoat` and `procedural_texture` have candidate sources, but baseline table
counts remain unchanged until wrapper stages and conversions are run.

- [x] **Step 4: Verify and document**

Run the supplemental-candidate tests, parse the new JSON/YAML, and update the
design/checklist docs with the exact candidate sources and remaining work.

Actual: tests pass and the manifest recommends two source candidates:
`isaac_material_library_omnipbr_clearcoat_opacity` for `clearcoat` and
`nvidia_mdl_sdk_tutorials_checker_noise` for `procedural_texture`.
`ready_for_fixture_authoring=true`, but
`ready_for_baseline_conversion=false` because wrapper scenes and supplemental
conversions have not been run.
