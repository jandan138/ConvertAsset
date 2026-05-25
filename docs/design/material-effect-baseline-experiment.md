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
| `nvidia_asset_converter_preview_or_bake` | NVIDIA `omni.kit.asset_converter` preview-surface or MDL-bake output | 30/30 available and static-gated |

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

Generated NVIDIA sample conversion artifact:

```text
paper/shared/evidence/raw/material_effect_baseline/nvidia_sample_conversion_manifest.json
```

Sample conversion summary:

| Field | Value |
|---|---:|
| Unique source scenes | 5 |
| Attempted scene conversions | 5 |
| Successful scene conversions | 5 |
| External NVIDIA output footprint | ~4.9 GiB |

The full NVIDIA USD outputs are intentionally external under
`/cpfs/user/zhuzihou/assets/convertasset_research/experiments/material_effect_baseline/`.
Only the small manifest is repo-resident.

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
| NVIDIA sample outputs available | 30 |
| NVIDIA sample outputs missing | 0 |
| Preferred NVIDIA smoke route | `usd_to_usd_preview` |

The static gates show all three conditions are now available for the selected
GRScenes material-effect pool. Original scratch inputs still contain active MDL
shaders, while both ConvertAsset no-MDL and NVIDIA outputs contain
`UsdPreviewSurface` and zero active MDL source-asset shaders. The comparison is
still incomplete because paired renders and visual quality review are not
finished for all effect bins.

Generated effect table artifacts:

```text
paper/shared/tables/material_effect_baseline_summary.csv
paper/shared/tables/tab_material_effect_baseline_summary.tex
paper/shared/evidence/raw/material_effect_baseline/effect_failure_case_manifest.json
```

The current table has 18 rows: six effect bins by three conditions. After the
supplemental wrapper run, `clearcoat` and `procedural_texture` each have one
supplemental sample instead of zero-sample rows. The follow-up case manifest
currently has one static-gate failure case: NVIDIA Asset Converter produces a
clearcoat output USD with zero shader records. This is a concrete baseline
failure candidate, not yet a render-level visual-quality result.

Generated qualitative artifacts:

```text
paper/shared/evidence/raw/material_effect_baseline/qualitative_render_manifest.json
paper/shared/evidence/raw/material_effect_baseline/qualitative_camera_stage_authoring_report.json
paper/shared/evidence/raw/material_effect_baseline/qualitative_nvidia_render_run_manifest.json
paper/shared/evidence/raw/material_effect_baseline/qualitative_renders/
paper/shared/figures/fig_material_effect_baseline_qualitative.png
paper/shared/figures/fig_material_effect_baseline_qualitative.report.json
```

Current qualitative summary:

| Field | Value |
|---|---:|
| Selected qualitative cases | 4 |
| Ready condition images | 12 / 12 |
| Selected NVIDIA camera stages authored | 4 / 4 |
| Selected NVIDIA renders ready | 4 / 4 |

The selected cases cover the effect bins present in GRScenes:
`opacity_transparency`, `emission`, `normal_bump`, and
`displacement_height`. They are suitable for bounded qualitative comparison of
the GRScenes-covered bins, but they still do not render the supplemental
`clearcoat` and `procedural_texture` cases.

Generated supplemental candidate artifact:

```text
paper/shared/evidence/raw/material_effect_baseline/supplemental_effect_candidate_manifest.json
```

Current supplemental summary:

| Field | Value |
|---|---:|
| Missing bins checked | 2 |
| Candidate sources found | 2 |
| Remaining missing bins without source | 0 |
| Wrapper stages authored | 2 |
| ConvertAsset no-MDL static gates passed | 2 / 2 |
| NVIDIA static gates passed | 1 / 2 |
| NVIDIA static-gate failure cases | 1 |

The recommended sources are local official/sample assets rather than project
scratch copies:

| Effect | Candidate | Source |
|---|---|---|
| `clearcoat` | `isaac_material_library_omnipbr_clearcoat_opacity` | Isaac Sim `omni.kit.material.library` test material binding + `OmniPBR_ClearCoat_Opacity.mdl` |
| `procedural_texture` | `nvidia_mdl_sdk_tutorials_checker_noise` | NVIDIA MDL USD-converter tutorials using checker/noise functions |

These are now counted in the effect table as supplemental static-gate samples.
They still need rendered qualitative inspection before any visual-quality or
all-effects reliability claim.

## Next Gate

The next gate is supplemental qualitative rendering and failure review:

1. Render original/no-MDL/NVIDIA panels for the two supplemental wrapper cases.
2. Inspect the NVIDIA clearcoat static-gate failure and decide whether it is a
   paper/rebuttal failure example.
3. Regenerate qualitative panels with both GRScenes covered-bin cases and
   supplemental clearcoat/procedural cases.
4. Add visual failure examples once render-level inspection identifies concrete
   failure modes, rather than treating static-gate success as visual success.

No paper claim should compare all requested material effects against NVIDIA
until the supplemental cases become rendered condition rows. The current
qualitative figure supports only a GRScenes covered-bin visual comparison.
