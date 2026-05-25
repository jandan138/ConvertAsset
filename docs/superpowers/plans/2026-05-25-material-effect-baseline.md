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

### Task 8: Supplemental Wrapper Stages and Static Gates

**Files:**
- Create: `tests/test_material_effect_baseline_supplemental_wrappers.py`
- Create: `tests/test_material_effect_baseline_supplemental_conversion_manifest.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/author_supplemental_wrapper_stages.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_conversion_manifest.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_wrapper_stage_manifest.json`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_conversion_manifest.json`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_fixtures/`
- Modify: `paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py`
- Modify: `paper/shared/tables/material_effect_baseline_summary.csv`
- Modify: `paper/shared/tables/tab_material_effect_baseline_summary.tex`
- Modify: `paper/shared/evidence/raw/material_effect_baseline/effect_failure_case_manifest.json`

- [x] **Step 1: Write failing tests**

Test that wrapper authoring creates bound repo-resident USD stages without
sublayering `/isaac-sim` source USDs, and test that supplemental conversion
manifests record original/noMDL/NVIDIA static gates plus failure cases.

- [x] **Step 2: Author wrapper stages**

Create standalone wrapper stages for `clearcoat` and `procedural_texture`.
They bind official/sample MDL source assets to small renderable target prims and
avoid recursive USD dependencies that would write sidecars under Isaac Sim.

- [x] **Step 3: Run ConvertAsset and NVIDIA static gates**

Run ConvertAsset no-MDL over both wrapper stages and inspect the existing NVIDIA
supplemental conversion outputs under the normalized external research root.

- [x] **Step 4: Regenerate tables and failure cases**

Merge the supplemental conversion manifest into the effect table builder.
`clearcoat` and `procedural_texture` now each have one supplemental sample.
NVIDIA procedural texture passes the static gate; NVIDIA clearcoat fails with
zero shader records in the converted USD.

Actual: supplemental wrapper tests pass, supplemental conversion tests pass,
the wrapper manifest records 2 authored stages, the supplemental conversion
manifest records `convertasset_available_count=2`, `nvidia_available_count=1`,
and `nvidia_static_gate_failed_count=1`, and the regenerated failure-case
manifest records the clearcoat NVIDIA static-gate failure.

### Task 9: Supplemental Qualitative Renders and Machine QA

**Files:**
- Create: `tests/test_material_effect_baseline_supplemental_qualitative.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_qualitative_render_manifest.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/run_supplemental_qualitative_renders.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/review_supplemental_qualitative_renders.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_qualitative_render_manifest.json`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_qualitative_render_run_manifest.json`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_qualitative_visual_qa.json`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_clean_room_visual_review.json`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_qualitative_renders/`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_qualitative_render_logs/`
- Create: `paper/shared/figures/fig_material_effect_supplemental_qualitative.png`
- Create: `paper/shared/figures/fig_material_effect_supplemental_qualitative.report.json`
- Modify: `paper/shared/evidence/results_manifest.yaml`
- Modify: `paper/shared/figures/sources.yaml`

- [x] **Step 1: Write failing tests**

Test that the supplemental qualitative manifest emits 2 cases x 3 conditions,
uses `/World/Camera` for original/noMDL and `/World/Camera/Camera` for NVIDIA
converted wrapper outputs, and records static-gate-failed NVIDIA clearcoat rows
without blocking render generation.

- [x] **Step 2: Implement manifest builder and runner**

Build render records from `supplemental_conversion_manifest.json`, then run the
six viewport-capture commands into repo-resident PNGs.

- [x] **Step 3: Generate supplemental contact sheet**

Reuse `gen_material_effect_qualitative.py` with the supplemental manifest to
write `fig_material_effect_supplemental_qualitative.png`.

- [x] **Step 4: Add machine visual QA**

Record nonblank/near-black checks for the six supplemental images. The QA
report flags NVIDIA clearcoat as `near_black_render`, matching the static
failure.

Actual: supplemental qualitative tests pass (`6 passed`), render run records
`attempted=6`, `ready=6`, `failed=0`, contact sheet writes with
`ready_case_count=2`, and machine QA records 5 PASS / 0 WARN / 1 FAIL.
Clean-room human-style visual review then records overall `FAIL` with 1 PASS /
2 WARN / 3 FAIL across the six images. The remaining gate is retaking or
investigating the failed supplemental cases and integrating only bounded
failure/retake evidence into the paper/rebuttal, not render generation.

### Task 10: Supplemental Static Preservation Diagnostics

**Files:**
- Create: `tests/test_material_effect_baseline_supplemental_diagnostics.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/diagnose_supplemental_material_preservation.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/supplemental_material_preservation_diagnostic.json`
- Modify: `paper/shared/evidence/results_manifest.yaml`
- Modify: `paper/shared/evidence/claims.yaml`
- Modify: `docs/design/material-effect-baseline-experiment.md`

- [x] **Step 1: Write failing diagnostic test**

Test that the diagnostic flags NVIDIA clearcoat target loss and checker/base
color texture loss in both converted procedural conditions.

- [x] **Step 2: Implement PXR diagnostic**

Inspect target prim existence, PreviewSurface networks, diffuseColor
connections, BaseColor texture files, and original MDL checker inputs.

- [x] **Step 3: Generate repo-resident diagnostic manifest**

Actual: the Isaac/PXR run records 2 failed supplemental cases,
`nvidia_target_missing_count=1`, and
`converted_procedural_checker_loss_count=2`. This confirms the next gate is not
just camera retake: NVIDIA clearcoat needs a target-containing rerun or bounded
failure writeup, while procedural texture needs baking/preservation work before
any success claim.

### Task 11: Effect-Level Risk Matrix

**Files:**
- Create: `tests/test_material_effect_baseline_risk_matrix.py`
- Create: `paper/shared/evidence/experiments/08_material_effect_baseline/build_material_effect_risk_matrix.py`
- Create: `paper/shared/evidence/raw/material_effect_baseline/material_effect_risk_profile.json`
- Create: `paper/shared/tables/material_effect_risk_matrix.csv`
- Create: `paper/shared/tables/tab_material_effect_risk_matrix.tex`
- Modify: `paper/shared/evidence/results_manifest.yaml`
- Modify: `paper/shared/evidence/claims.yaml`
- Modify: `docs/design/material-effect-baseline-experiment.md`

- [x] **Step 1: Write failing risk-matrix tests**

Test that covered GRScenes bins, selected NVIDIA clearcoat failure, and
procedural checker-loss limitation are separated into different claim
categories.

- [x] **Step 2: Implement matrix builder**

Merge baseline/supplemental conversion manifests with the selected qualitative
manifest, clean-room visual review, and PXR preservation diagnostic. Emit
effect-level CSV, LaTeX, and JSON profile artifacts.

- [x] **Step 3: Generate and document**

Actual: the matrix records 6 effect rows. Four GRScenes-covered bins are
`bounded_static_and_selected_qualitative`; `clearcoat` is a
`selected_nvidia_failure_case`; `procedural_texture` is a
`diagnostic_limitation_case`. This is the current best reviewer-facing answer to
"where is it reliable, where is it risky, and where does NVIDIA fail" without
overstating the supplemental fixtures as population-level rates.
