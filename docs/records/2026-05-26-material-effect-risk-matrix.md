# 2026-05-26 Material-Effect Risk Matrix

## Summary

Added an effect-level risk matrix for the ConvertAsset vs NVIDIA
material-effect baseline. The matrix converts the scattered readiness tables,
selected qualitative manifest, clean-room visual review, and PXR diagnostic into
one claim-boundary artifact for paper/rebuttal writing.

## Artifacts

- `paper/shared/evidence/experiments/08_material_effect_baseline/build_material_effect_risk_matrix.py`
- `paper/shared/evidence/raw/material_effect_baseline/material_effect_risk_profile.json`
- `paper/shared/tables/material_effect_risk_matrix.csv`
- `paper/shared/tables/tab_material_effect_risk_matrix.tex`
- `tests/test_material_effect_baseline_risk_matrix.py`

## Findings

The generated matrix has 6 rows:

| Group | Status | Claim boundary |
|---|---|---|
| `opacity_transparency`, `emission`, `normal_bump`, `displacement_height` | GRScenes expanded30 static gates plus selected qualitative panel | bounded static and selected qualitative evidence only |
| `clearcoat` | supplemental clean-room/PXR failure evidence | selected NVIDIA failure case: target missing in NVIDIA output, ConvertAsset target retained as PreviewSurface approximation |
| `procedural_texture` | supplemental clean-room/PXR failure evidence | limitation case: both converted conditions lose checker/base-color preservation evidence |

## Validation

Commands run during implementation:

```bash
python -m pytest -q tests/test_material_effect_baseline_risk_matrix.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_material_effect_risk_matrix.py
```

The first pytest run failed before implementation because the builder did not
exist. A second red assertion caught an evidence-source bug where GRScenes rows
incorrectly referenced the supplemental clean-room review. After implementation
and the evidence-source fix, the targeted pytest passed and the generator
wrote the CSV, LaTeX table, and JSON profile.

## Claim Boundary

Allowed now: "we have an auditable matrix separating four bounded
GRScenes-covered material-effect bins from selected clearcoat/procedural
supplemental risks."

Not allowed yet: "the supplemental panel is a successful all-effects visual
comparison", "procedural textures are preserved", or "the two supplemental
fixtures define population-level failure rates."
