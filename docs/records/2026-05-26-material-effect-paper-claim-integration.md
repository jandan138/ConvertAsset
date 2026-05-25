# 2026-05-26 Material-Effect Paper Claim Integration

## Summary

Integrated the material-effect risk matrix into the shared manuscript so the
paper text now reflects the reviewer-facing claim boundary, rather than leaving
the evidence only in manifests and tables.

## Changed Manuscript Areas

- `paper/shared/sections/experiments.tex`: added a material-effect baseline
  subsection with the risk matrix, the selected GRScenes qualitative panel, and
  the supplemental failure/limitation panel.
- `paper/shared/sections/discussion.tex`: tied practical recommendations to
  effect-specific claim boundaries.
- `paper/shared/sections/conclusion.tex`: added the ConvertAsset-vs-NVIDIA
  material-effect boundary to the shared conclusion.
- `paper/venues/acl27/sections/limitations.tex`: records that the
  material-effect matrix is selected diagnostic evidence, not a population-level
  failure-rate distribution.
- `paper/venues/acl27/sections/conclusion.tex`: carries the same claim
  discipline into the ACL wrapper.

## Claim Boundary Now In Text

The manuscript can now state:

- Four GRScenes-covered bins (`opacity_transparency`, `emission`,
  `normal_bump`, `displacement_height`) support bounded static and selected
  qualitative evidence across original MDL, ConvertAsset no-MDL, and NVIDIA
  baseline conditions.
- Supplemental clearcoat is a selected NVIDIA failure case: the NVIDIA
  converted output misses the target, while ConvertAsset retains the target as a
  PreviewSurface approximation.
- Supplemental procedural texture is a limitation case: both converted
  conditions lose checker/base-color preservation evidence.

Still forbidden:

- all-effects successful visual preservation,
- population-level material-effect failure rates,
- broad embodied benchmark claims from the current downstream evidence.

## Validation Notes

This change is manuscript integration only. It does not add new experiment
runs. The authoritative evidence remains:

- `paper/shared/evidence/raw/material_effect_baseline/material_effect_risk_profile.json`
- `paper/shared/tables/material_effect_risk_matrix.csv`
- `paper/shared/evidence/raw/material_effect_baseline/supplemental_clean_room_visual_review.json`
- `paper/shared/evidence/raw/material_effect_baseline/supplemental_material_preservation_diagnostic.json`
