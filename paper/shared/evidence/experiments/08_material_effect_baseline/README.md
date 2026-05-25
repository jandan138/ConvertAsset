# Material-Effect Baseline Experiment

This experiment line prepares the ConvertAsset vs NVIDIA baseline comparison
requested by the reviews. It starts from the existing GRScenes expanded30 stress
pool and labels samples by MDL material effects.

Sample-manifest entry point:

```bash
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_sample_manifest.py
```

Default sample output:

```text
paper/shared/evidence/raw/material_effect_baseline/effect_sample_manifest.json
```

The manifest is a planning artifact. It does not contain NVIDIA baseline results
yet. It records the current GRScenes coverage and the missing effect bins that
must be filled with official/sample assets before full material-effect claims.

Current GRScenes coverage:

- 30 linked expanded30 stress samples
- 0 missing material model links
- covered: `opacity_transparency`, `emission`, `normal_bump`,
  `displacement_height`
- missing: `clearcoat`, `procedural_texture`

NVIDIA Asset Converter smoke entry point:

```bash
timeout 240 ./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_asset_converter_smoke.py
```

Default smoke output:

```text
paper/shared/evidence/raw/material_effect_baseline/nvidia_baseline_smoke_manifest.json
```

Current smoke result:

- 3 converter attempts succeeded
- 2 USD outputs are claimable baseline candidates:
  `usd_to_usd_preview` and `usd_to_usd_bake_flag`
- both claimable USD outputs have 4 `UsdPreviewSurface` shaders and 0 active
  MDL source-asset shaders

Baseline conversion manifest entry point:

```bash
./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py
```

NVIDIA sample conversion entry point:

```bash
timeout 1800 ./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_sample_conversions.py
```

Default conversion-manifest output:

```text
paper/shared/evidence/raw/material_effect_baseline/baseline_conversion_manifest.json
paper/shared/evidence/raw/material_effect_baseline/nvidia_sample_conversion_manifest.json
```

Current conversion-manifest result:

- 30 samples across 5 unique source scenes
- 30/30 `original_MDL` condition records are available
- 30/30 `existing_noMDL` condition records are available
- 5/5 unique source scenes were converted by NVIDIA Asset Converter
- 30/30 NVIDIA sample condition records are available and static-gated
- preferred NVIDIA route: `usd_to_usd_preview`
- external NVIDIA output footprint: about 4.9 GiB

Effect table entry point:

```bash
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py
```

Default table outputs:

```text
paper/shared/tables/material_effect_baseline_summary.csv
paper/shared/tables/tab_material_effect_baseline_summary.tex
paper/shared/evidence/raw/material_effect_baseline/effect_failure_case_manifest.json
```

Current table result:

- 18 effect-by-condition rows: 6 effect bins x 3 material conditions
- `clearcoat` and `procedural_texture` are explicit zero-sample rows
- 0 static-gate follow-up cases after NVIDIA sample conversion

Next scripts should add:

- paired render manifest for original / ConvertAsset / NVIDIA;
- effect-grouped tables and qualitative failure panels.
