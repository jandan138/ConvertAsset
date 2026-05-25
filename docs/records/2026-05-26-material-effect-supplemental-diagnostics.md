# 2026-05-26 Material-Effect Supplemental Diagnostics

## Summary

Added a PXR-based static diagnosis pass for the supplemental clearcoat and
procedural-texture material-effect fixtures. The diagnostic turns the previous
clean-room visual review failures into inspectable USD-network findings, so the
paper/rebuttal claim can state why the supplemental panel is not yet a
success-style comparison.

## Artifacts

- `paper/shared/evidence/experiments/08_material_effect_baseline/diagnose_supplemental_material_preservation.py`
- `paper/shared/evidence/raw/material_effect_baseline/supplemental_material_preservation_diagnostic.json`
- `tests/test_material_effect_baseline_supplemental_diagnostics.py`

## Findings

The generated diagnostic records two failed supplemental cases:

| Case | Finding | Consequence |
|---|---|---|
| `supplemental_clearcoat_omnipbr` | NVIDIA converted USD has no `/World/ClearcoatTarget`, zero shaders, and zero PreviewSurface shaders. | A camera-only retake cannot fix the NVIDIA clearcoat panel; treat it as a selected conversion failure unless rerunning conversion produces a target-containing USD. |
| `supplemental_procedural_checker` | Original MDL has checker/file-texture inputs, but both ConvertAsset no-MDL and NVIDIA outputs lack checker/base-color texture preservation evidence in their PreviewSurface networks. | Static gate pass is not sufficient for procedural texture preservation; this needs baking/preservation work or a bounded risk statement. |

Current summary from
`paper/shared/evidence/raw/material_effect_baseline/supplemental_material_preservation_diagnostic.json`:

| Field | Value |
|---|---:|
| Cases | 2 |
| Failed cases | 2 |
| NVIDIA target-missing rows | 1 |
| Converted procedural checker-loss rows | 2 |
| Ready for success panel | `false` |
| Ready for failure-case writeup | `true` |

## Validation

Commands run:

```bash
python -m pytest -q tests/test_material_effect_baseline_supplemental_diagnostics.py::test_build_supplemental_material_diagnostics_flags_target_and_checker_loss
./scripts/isaac_python.sh paper/shared/evidence/experiments/08_material_effect_baseline/diagnose_supplemental_material_preservation.py
```

The targeted pytest passed after the expected red state, and the Isaac/PXR run
generated the diagnostic manifest with blockers
`nvidia_clearcoat_target_missing` and
`procedural_checker_not_preserved_in_converted_conditions`.

## Claim Boundary

Allowed now: "the supplemental missing-bin fixtures expose two concrete risk
modes: target loss in NVIDIA clearcoat conversion and procedural checker loss
in converted preview networks."

Not allowed yet: "the supplemental clearcoat/procedural panel is a successful
three-way qualitative comparison", "static gates prove procedural texture
preservation", or "these two fixtures define a population-level material-effect
failure rate."
