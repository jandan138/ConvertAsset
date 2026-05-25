# Material-Effect Baseline Experiment

> Last updated: 2026-05-25

## Goal

This experiment line turns the reviewer-facing claim from "ConvertAsset has
sanity evidence" into a bounded diagnostic: for representative MDL material
effects, compare original MDL, ConvertAsset no-MDL, and an NVIDIA baseline, then
report where conversion is reliable, where it is risky, and which failures are
visible in qualitative figures.

## Scope

The first sample pool is the existing GRScenes expanded30 material-shift stress
set. It is useful because target-centered original/no-MDL renders, visual QA,
and material dependency closure already exist. It is not enough by itself:
`effect_sample_manifest.json` currently shows no clearcoat or procedural
texture samples in that pool, so official/sample assets must fill those bins
before any "all effects covered" claim.

## Conditions

Each selected sample should eventually have three material conditions:

| Condition | Meaning | Current status |
|---|---|---|
| `original_MDL` | Scratch-materialized source USD with MDL material graph | 30/30 available and static-gated |
| `existing_noMDL` | ConvertAsset MDL-to-UsdPreviewSurface output | 30/30 available and static-gated |
| `nvidia_asset_converter_preview_or_bake` | NVIDIA `omni.kit.asset_converter` preview-surface or MDL-bake output | Official-fixture smoke passed; 30/30 sample outputs still missing |

The NVIDIA condition should use the smoke-validated USD routes first:
`usd_to_usd_preview` and `usd_to_usd_bake_flag`. The glTF route can remain a
secondary diagnostic because it does not produce a USD stage for the same static
material gates.

## Effect Bins

The manifest builder uses stable, explicit bins:

- `clearcoat`
- `opacity_transparency`
- `emission`
- `procedural_texture`
- `normal_bump`
- `displacement_height`

Detection is intentionally conservative. For example, `opacity: 1.f` does not
place a material in the opacity/transparency bin; actual opacity below one,
translucent shader tokens, refraction, transmission, or thin-walled markers do.

## Current Evidence

Generated sample artifact:

```text
paper/shared/evidence/raw/material_effect_baseline/effect_sample_manifest.json
```

Current summary:

| Field | Value |
|---|---:|
| Samples linked to material models | 30 |
| Missing material model links | 0 |
| `normal_bump` samples | 30 |
| `opacity_transparency` samples | 7 |
| `emission` samples | 26 |
| `displacement_height` samples | 26 |
| `clearcoat` samples | 0 |
| `procedural_texture` samples | 0 |

This is a sample-selection and planning artifact, not a baseline result. It
allows the next run to start from known GRScenes samples while explicitly
recording which effect bins need official/sample-asset supplementation.

Generated NVIDIA smoke artifact:

```text
paper/shared/evidence/raw/material_effect_baseline/nvidia_baseline_smoke_manifest.json
```

Smoke summary:

| Field | Value |
|---|---:|
| Attempts | 3 |
| Successful converter attempts | 3 |
| Usable USD baseline attempts | 2 |
| `usd_to_usd_preview` PreviewSurface / active MDL | 4 / 0 |
| `usd_to_usd_bake_flag` PreviewSurface / active MDL | 4 / 0 |
| Ready for sample baseline | true |

This only proves the installed NVIDIA Asset Converter can produce a USD
PreviewSurface baseline candidate on NVIDIA's own MDL fixture. It does not yet
compare ConvertAsset with NVIDIA on the selected GRScenes/material-effect pool.

Generated baseline conversion artifact:

```text
paper/shared/evidence/raw/material_effect_baseline/baseline_conversion_manifest.json
```

Current condition summary:

| Field | Value |
|---|---:|
| Samples | 30 |
| Unique source scenes | 5 |
| `original_MDL` available | 30 |
| `existing_noMDL` available | 30 |
| NVIDIA sample outputs available | 0 |
| NVIDIA sample outputs missing | 30 |
| Preferred NVIDIA smoke route | `usd_to_usd_preview` |

The static gates show the existing ConvertAsset side of the comparison is ready:
the original scratch inputs still contain active MDL shaders, while the no-MDL
outputs contain `UsdPreviewSurface` and zero active MDL source-asset shaders.
The comparison is still incomplete because NVIDIA sample outputs have not been
generated.

Generated effect table artifacts:

```text
paper/shared/tables/material_effect_baseline_summary.csv
paper/shared/tables/tab_material_effect_baseline_summary.tex
paper/shared/evidence/raw/material_effect_baseline/effect_failure_case_manifest.json
```

The current table has 18 rows: six effect bins by three conditions. `clearcoat`
and `procedural_texture` are explicit zero-sample rows. The follow-up case
manifest has 89 cases, all caused by missing NVIDIA sample outputs; these are
not visual conversion failures.

## Next Gate

The next gate is the actual sample-level NVIDIA conversion run:

1. Reuse the five unique source scenes referenced by
   `baseline_conversion_manifest.json`.
2. Convert each scratch-materialized source USD with the smoke-validated
   `usd_to_usd_preview` route into the external NVIDIA output root recorded in
   the manifest.
3. Regenerate `baseline_conversion_manifest.json` so NVIDIA rows move from
   `planned_output_missing` to static-gated available/failed records.
4. Add official/sample assets for `clearcoat` and `procedural_texture` before
   any all-effect coverage claim.

No paper claim should compare ConvertAsset against NVIDIA until NVIDIA sample
outputs, paired renders, effect tables, and qualitative failure panels exist.
