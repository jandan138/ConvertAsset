# 2026-05-25 Material-Effect Baseline Bootstrap

## Summary

Started the reviewer-driven material-effect baseline line. The bootstrap now
creates the first auditable sample manifest linking the existing GRScenes
expanded30 stress pairs to their MDL material files and effect labels, and it
also validates a small NVIDIA Asset Converter USD baseline path on NVIDIA's own
MDL fixture.

## Files Added

- `paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_sample_manifest.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_asset_converter_smoke.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_sample_conversions.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/build_qualitative_render_manifest.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/run_qualitative_nvidia_renders.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_effect_candidates.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/author_supplemental_wrapper_stages.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_conversion_manifest.py`
- `paper/shared/figures/gen_material_effect_qualitative.py`
- `paper/shared/evidence/raw/material_effect_baseline/effect_sample_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/supplemental_effect_candidate_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/supplemental_wrapper_stage_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/supplemental_conversion_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/supplemental_fixtures/`
- `paper/shared/evidence/raw/material_effect_baseline/nvidia_baseline_smoke_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/nvidia_sample_conversion_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/baseline_conversion_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/effect_failure_case_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/qualitative_render_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/qualitative_camera_stage_authoring_report.json`
- `paper/shared/evidence/raw/material_effect_baseline/qualitative_nvidia_render_run_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/qualitative_renders/`
- `paper/shared/evidence/raw/material_effect_baseline/qualitative_render_logs/`
- `paper/shared/evidence/raw/material_effect_baseline/nvidia_baseline_smoke/`
- `paper/shared/figures/fig_material_effect_baseline_qualitative.png`
- `paper/shared/figures/fig_material_effect_baseline_qualitative.report.json`
- `paper/shared/tables/material_effect_baseline_summary.csv`
- `paper/shared/tables/tab_material_effect_baseline_summary.tex`
- `tests/test_material_effect_baseline_manifest.py`
- `tests/test_material_effect_baseline_nvidia_smoke.py`
- `tests/test_material_effect_baseline_nvidia_samples.py`
- `tests/test_material_effect_baseline_conversion_manifest.py`
- `tests/test_material_effect_baseline_tables.py`
- `tests/test_material_effect_baseline_qualitative.py`
- `docs/design/material-effect-baseline-experiment.md`
- `paper/shared/evidence/experiments/08_material_effect_baseline/README.md`

## Findings

The generated manifest has 30 GRScenes stress samples and 0 missing material
model links. Current effect coverage is:

| Effect | Count |
|---|---:|
| `normal_bump` | 30 |
| `opacity_transparency` | 7 |
| `emission` | 26 |
| `displacement_height` | 26 |
| `clearcoat` | 0 |
| `procedural_texture` | 0 |

This confirms the earlier suspicion: GRScenes is useful for real-scene samples,
but it does not by itself cover all reviewer-requested effect bins. Clearcoat
and procedural texture need official/sample assets before a full material-effect
claim is valid.

The NVIDIA smoke used the local Isaac Sim `omni.kit.asset_converter` extension
fixture:

```text
/isaac-sim/extscache/omni.kit.asset_converter-2.8.3+106.5.0.lx64.r.cp310/data/MDL_to_glTF.usd
```

Smoke results:

| Attempt | Converter success | Claimable as USD baseline | PreviewSurface | Active MDL |
|---|---:|---:|---:|---:|
| `usd_to_usd_preview` | true | true | 4 | 0 |
| `usd_to_usd_bake_flag` | true | true | 4 | 0 |
| `usd_to_gltf_bake_flag` | true | false | n/a | n/a |

The smoke manifest records `ready_for_sample_baseline=true`, so the next
experiment can run the NVIDIA USD baseline route over the selected samples.

The sample NVIDIA conversion runner then converted the five unique source scenes
referenced by the 30 selected samples. The large converted USD outputs are kept
outside the repo under the normalized research root; the repo stores only the
small audit manifest.

| Field | Count |
|---|---:|
| Scene jobs | 5 |
| Attempted scene conversions | 5 |
| Successful scene conversions | 5 |
| Failed scene conversions | 0 |
| NVIDIA output footprint | ~4.9 GiB |

The baseline conversion manifest now links each selected sample to available
original/no-MDL/NVIDIA condition records:

| Field | Count |
|---|---:|
| Samples | 30 |
| Unique source scenes | 5 |
| `original_MDL` available | 30 |
| `existing_noMDL` available | 30 |
| NVIDIA sample outputs available | 30 |
| NVIDIA sample outputs missing | 0 |

Static gates pass for all three conditions: original scratch inputs still have
active MDL shaders, while both no-MDL and NVIDIA outputs have
`UsdPreviewSurface` shaders with zero active MDL source-asset shaders.

The effect table generator emits 18 rows, covering six effect bins by three
conditions. After the supplemental wrapper/conversion pass, `clearcoat` and
`procedural_texture` each have one supplemental static-gated sample. The
follow-up case manifest now has one static-gate failure case: NVIDIA Asset
Converter drops material shader output for the supplemental clearcoat wrapper.
This is not yet a visual-quality comparison.

The qualitative render manifest then selects four representative expanded30
cases from the covered effect bins and reuses the existing original/no-MDL
target-centered images. Four NVIDIA camera stages were authored with the same
camera settings and rendered through the viewport-capture path. The resulting
contact sheet is repo-resident and covers bottle, clock, cup, and backpack
cases across original MDL, ConvertAsset no-MDL, and NVIDIA.

| Field | Count |
|---|---:|
| Selected qualitative cases | 4 |
| Ready condition images | 12 |
| NVIDIA camera stages authored | 4 |
| NVIDIA qualitative renders ready | 4 |

The supplemental candidate manifest then checks bounded local official/sample
roots for the missing effect bins. It finds a clearcoat source in the local
Isaac Sim material-library tests and a procedural-texture source in the local
NVIDIA MDL SDK tutorial assets.

| Field | Count |
|---|---:|
| Missing bins checked | 2 |
| Candidate sources found | 2 |
| Remaining missing bins without source | 0 |

Both candidates were then authored into small repo-resident wrapper stages and
run through ConvertAsset no-MDL. The NVIDIA supplemental outputs stay under the
normalized external research root and are summarized through the repo manifest.

| Field | Count |
|---|---:|
| Supplemental wrapper stages | 2 |
| ConvertAsset no-MDL static gates passed | 2 |
| NVIDIA static gates passed | 1 |
| NVIDIA static-gate failures | 1 |

The NVIDIA failure is the clearcoat wrapper: the converter writes a USD output,
but static inspection finds zero shader records and zero PreviewSurface records.

## Validation

Commands run:

```bash
python -m pytest -q tests/test_material_effect_baseline_manifest.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_sample_manifest.py
python -m pytest -q tests/test_material_effect_baseline_nvidia_smoke.py
timeout 240 ./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_asset_converter_smoke.py
python -m pytest -q tests/test_material_effect_baseline_conversion_manifest.py
python -m pytest -q tests/test_material_effect_baseline_nvidia_samples.py
timeout 1800 ./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_sample_conversions.py
timeout 300 ./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py
python -m pytest -q tests/test_material_effect_baseline_tables.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py
python -m pytest -q tests/test_material_effect_baseline_qualitative.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_qualitative_render_manifest.py
timeout 300 ./scripts/isaac_python.sh paper/shared/evidence/experiments/06_grscenes_vlm_grounding/author_render_camera_stages.py --render-manifest paper/shared/evidence/raw/material_effect_baseline/qualitative_render_manifest.json --out paper/shared/evidence/raw/material_effect_baseline/qualitative_camera_stage_authoring_report.json --apply
python paper/shared/evidence/experiments/08_material_effect_baseline/run_qualitative_nvidia_renders.py
python paper/shared/figures/gen_material_effect_qualitative.py
python -m pytest -q tests/test_material_effect_baseline_supplemental_candidates.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_effect_candidates.py
python -m pytest -q tests/test_material_effect_baseline_supplemental_wrappers.py
python paper/shared/evidence/experiments/08_material_effect_baseline/author_supplemental_wrapper_stages.py
./scripts/isaac_python.sh ./main.py no-mdl paper/shared/evidence/raw/material_effect_baseline/supplemental_fixtures/supplemental_clearcoat_omnipbr.usda
./scripts/isaac_python.sh ./main.py no-mdl paper/shared/evidence/raw/material_effect_baseline/supplemental_fixtures/supplemental_procedural_checker.usda
python -m pytest -q tests/test_material_effect_baseline_supplemental_conversion_manifest.py
./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_conversion_manifest.py
python -m pytest -q tests/test_material_effect_baseline_tables.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py
```

Results:

- tests: `3 passed`
- manifest: `samples=30`, `effect_gaps=clearcoat,procedural_texture`
- NVIDIA smoke tests: `4 passed`
- NVIDIA smoke: `attempt_count=3`, `successful_attempt_count=3`,
  `usable_usd_baseline_attempts=usd_to_usd_preview,usd_to_usd_bake_flag`
- baseline conversion tests: `3 passed`
- NVIDIA sample conversion tests: `4 passed`
- NVIDIA sample conversion manifest: `scene_job_count=5`,
  `successful_scene_count=5`, `output_exists_count=5`
- baseline conversion manifest: `samples=30`, `original_available=30`,
  `convertasset_available=30`, `nvidia_available=30`, `nvidia_missing=0`
- effect table tests: `2 passed`
- effect tables: `rows=18`, `cases=0`
- qualitative tests: `7 passed`
- qualitative render manifest: `selected_case_count=4`, `ready_case_count=4`,
  `nvidia_render_pending_count=0`
- qualitative camera stages: `authored_camera_stage_count=4`,
  `blocked_camera_stage_count=0`
- qualitative NVIDIA render run: `ready_output_count=4`, `failed_count=0`
- qualitative figure: `figure_written=true`, `ready_case_count=4`
- supplemental candidate tests: `3 passed`
- supplemental candidate manifest: `recommendation_count=2`,
  `remaining_missing_effects=[]`, `ready_for_fixture_authoring=true`,
  `ready_for_baseline_conversion=false`
- supplemental wrapper tests: `3 passed`
- supplemental wrapper manifest: `wrapper_stage_count=2`,
  `ready_for_baseline_conversion=true`
- supplemental conversion tests: `2 passed`
- supplemental conversion manifest: `sample_count=2`,
  `convertasset_available_count=2`, `nvidia_available_count=1`,
  `nvidia_static_gate_failed_count=1`
- regenerated effect tables: `rows=18`, `cases=1`

## Claim Boundary

Allowed now: "we have an effect-labeled sample-selection manifest and know which
bins are missing", and "the installed NVIDIA Asset Converter has a smoke-passed
USD PreviewSurface baseline route on NVIDIA's official fixture", and "the
existing original/no-MDL sample conditions are statically gated and ready for
sample-level NVIDIA conversion", "the NVIDIA sample outputs for the selected
five scenes are generated and static-gated", and "the current effect table
quantifies condition readiness by effect bin", and "selected covered-bin
qualitative stills exist for original MDL / ConvertAsset / NVIDIA", and "local
official/sample candidate sources have been identified for the missing
clearcoat/procedural bins", and "supplemental clearcoat/procedural wrappers now
have original/noMDL/NVIDIA static-gate records, including one NVIDIA clearcoat
static-gate failure."

Not allowed yet: "ConvertAsset visually beats NVIDIA baseline", "all requested
material effects are visually covered", "the supplemental clearcoat/procedural
cases have rendered qualitative panels", or "these counts are a final
failure-rate distribution."
