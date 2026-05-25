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
- `paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py`
- `paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py`
- `paper/shared/evidence/raw/material_effect_baseline/effect_sample_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/nvidia_baseline_smoke_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/baseline_conversion_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/effect_failure_case_manifest.json`
- `paper/shared/evidence/raw/material_effect_baseline/nvidia_baseline_smoke/`
- `paper/shared/tables/material_effect_baseline_summary.csv`
- `paper/shared/tables/tab_material_effect_baseline_summary.tex`
- `tests/test_material_effect_baseline_manifest.py`
- `tests/test_material_effect_baseline_nvidia_smoke.py`
- `tests/test_material_effect_baseline_conversion_manifest.py`
- `tests/test_material_effect_baseline_tables.py`
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

The baseline conversion manifest then links each selected sample to the
available original/no-MDL condition records and planned NVIDIA output path:

| Field | Count |
|---|---:|
| Samples | 30 |
| Unique source scenes | 5 |
| `original_MDL` available | 30 |
| `existing_noMDL` available | 30 |
| NVIDIA sample outputs available | 0 |
| NVIDIA sample outputs missing | 30 |

For the existing ConvertAsset side, static gates pass: original scratch inputs
still have active MDL shaders, and no-MDL outputs have `UsdPreviewSurface`
shaders with zero active MDL source-asset shaders. NVIDIA rows remain
`planned_output_missing`, so no head-to-head baseline claim is made yet.

The effect table generator emits 18 rows, covering six effect bins by three
conditions. `clearcoat` and `procedural_texture` are zero-sample rows so the
reviewer-facing gap is visible in the table. The follow-up case manifest has 89
cases; all are missing NVIDIA sample outputs, not visual conversion failures.

## Validation

Commands run:

```bash
python -m pytest -q tests/test_material_effect_baseline_manifest.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_sample_manifest.py
python -m pytest -q tests/test_material_effect_baseline_nvidia_smoke.py
timeout 240 ./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_asset_converter_smoke.py
python -m pytest -q tests/test_material_effect_baseline_conversion_manifest.py
timeout 300 ./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py
python -m pytest -q tests/test_material_effect_baseline_tables.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py
```

Results:

- tests: `3 passed`
- manifest: `samples=30`, `effect_gaps=clearcoat,procedural_texture`
- NVIDIA smoke tests: `4 passed`
- NVIDIA smoke: `attempt_count=3`, `successful_attempt_count=3`,
  `usable_usd_baseline_attempts=usd_to_usd_preview,usd_to_usd_bake_flag`
- baseline conversion tests: `2 passed`
- baseline conversion manifest: `samples=30`, `original_available=30`,
  `convertasset_available=30`, `nvidia_missing=30`
- effect table tests: `2 passed`
- effect tables: `rows=18`, `cases=89`

## Claim Boundary

Allowed now: "we have an effect-labeled sample-selection manifest and know which
bins are missing", and "the installed NVIDIA Asset Converter has a smoke-passed
USD PreviewSurface baseline route on NVIDIA's official fixture", and "the
existing original/no-MDL sample conditions are statically gated and ready for
sample-level NVIDIA conversion", and "the current effect table quantifies
readiness and missing NVIDIA rows by effect bin."

Not allowed yet: "ConvertAsset beats NVIDIA baseline", "all requested material
effects are covered", or "these counts are a final failure-rate distribution."
