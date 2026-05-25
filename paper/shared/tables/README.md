# Shared Tables

Venue-neutral table sources for the ConvertAsset paper live here.

## Current Generated Tables

- `grscenes_vlm_pass_only_pilot.csv`: machine-readable PASS-only GRScenes VLM
  pilot table over four visually accepted original/converted pairs. It is
  generated from the Gemma4 and Qwen2.5-VL PASS-only score summaries under
  `paper/shared/evidence/raw/grscene_vlm_grounding/probes/`. It separates
  scorable answer rows from per-version point-row coverage so protocol
  diagnostics are not mistaken for final grounding accuracy.
- `tab_grscenes_vlm_pass_only_pilot.tex`: LaTeX table generated from the same
  CSV source. It is pilot-only material and must not be presented as final
  benchmark performance.
- `grscenes_vlm_clean_pool_pass15.csv`: machine-readable clean-pool pilot table
  over 15 blind-visual-QA PASS original/no-MDL pairs. It summarizes Gemma4 and
  Qwen2.5-VL structured-text probes under
  `paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/`. This is
  still below the 20-pair final gate.
- `tab_grscenes_vlm_clean_pool_pass15.tex`: LaTeX table for the same 15-pair
  clean-pool pilot.
- `grscenes_vlm_zoom_stress.csv`: machine-readable zoom material-shift stress
  table over 14 target-visible original/no-MDL pairs. It summarizes Gemma4 and
  Qwen2.5-VL structured-text probes under
  `paper/shared/evidence/raw/grscene_vlm_grounding/zoom_stress_probes/`. This is
  stress/protocol evidence, not clean preservation evidence.
- `tab_grscenes_vlm_zoom_stress.tex`: LaTeX table for the same zoom stress
  pilot.
- `grscenes_vlm_stress_expanded30.csv`: machine-readable expanded stress table
  over 30 target-visible original/no-MDL pairs. Gemma4 is the canonical root
  `stress_predictions.jsonl` / `stress_score_summary.json` run; Qwen2.5-VL is a
  second-model diagnostic under the same frozen expanded30 manifest.
- `tab_grscenes_vlm_stress_expanded30.tex`: LaTeX table for the expanded30
  frozen target-centered material-shift stress set.
- `grscenes_vlm_coordinate_ablation.csv`: machine-readable raw-image versus
  normalized-1000 coordinate scoring ablation for the clean-pool and
  zoom-stress VLM probes. Raw-image scoring is a diagnostic for coordinate
  semantics, not the final metric.
- `tab_grscenes_vlm_coordinate_ablation.tex`: LaTeX appendix table for the same
  coordinate-frame ablation.
- `grscenes_vlm_failure_taxonomy.csv`: machine-readable selected failure-case
  taxonomy assembled from the clean-pool and zoom-stress prediction JSONL plus
  score summaries. It is illustrative appendix material, not a final error
  distribution.
- `tab_grscenes_vlm_failure_taxonomy.tex`: LaTeX appendix table for the same
  selected failure taxonomy.
- `material_effect_baseline_summary.csv`: machine-readable effect-by-condition
  readiness table for the material-effect baseline. It includes zero-sample
  rows for `clearcoat` and `procedural_texture`, static-gated original/no-MDL
  rows for the covered GRScenes effects, and missing NVIDIA rows until the
  sample-level baseline conversion is executed.
- `tab_material_effect_baseline_summary.tex`: LaTeX table generated from the
  same material-effect readiness CSV.

Regenerate with:

```bash
python paper/shared/tables/gen_vlm_pilot_tables.py
python paper/shared/tables/gen_vlm_stress_expanded30.py
python paper/shared/tables/gen_vlm_coordinate_ablation.py
python paper/shared/tables/gen_vlm_failure_taxonomy.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py
```

The two newer clean-pool and zoom-stress tables, coordinate ablation, failure
taxonomy, and material-effect readiness table are registered in
`paper/shared/evidence/results_manifest.yaml`.

Most legacy table content remains embedded in `shared/sections/experiments.tex`
until a later paper-editing pass extracts reusable table sources.
