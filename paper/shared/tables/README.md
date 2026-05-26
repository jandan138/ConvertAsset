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
  readiness table for the material-effect baseline. It combines 30 GRScenes
  selected samples with one supplemental `clearcoat` wrapper and one
  supplemental `procedural_texture` wrapper across original, ConvertAsset, and
  NVIDIA conditions.
- `tab_material_effect_baseline_summary.tex`: LaTeX table generated from the
  same material-effect readiness CSV.
- `material_effect_risk_matrix.csv`: machine-readable effect-level
  claim-boundary table derived from the material-effect conversion manifests,
  selected qualitative manifest, supplemental clean-room visual review, and PXR
  diagnostic. It separates the four bounded GRScenes-covered bins from the
  selected NVIDIA clearcoat failure and the procedural texture limitation case.
- `tab_material_effect_risk_matrix.tex`: LaTeX table generated from the same
  material-effect risk matrix.
- `reviewer_closure_paired_ci.csv`: machine-readable paired bootstrap confidence
  interval table for the existing expanded30 VLM stress evidence and official
  KuJiaLe InternNav val-unseen evidence.
- `tab_reviewer_closure_paired_ci.tex`: LaTeX table generated from the same
  reviewer-closure CI CSV.
- `vlm_coordinate_baselines.csv`: machine-readable coordinate-only baseline
  table for random seeded pixels, image center, pixel bbox center, and
  normalized-1000 bbox center on the expanded30 VLM stress set.
- `tab_vlm_coordinate_baselines.tex`: LaTeX table generated from the same
  coordinate-only baseline CSV.
- `material_safe_conversion_recommender.csv`: machine-readable rule table
  derived from the material-effect risk matrix.
- `tab_material_safe_conversion_recommender.tex`: LaTeX table generated from the
  same safe-conversion recommender CSV.
- `official_scene_submission_closure_status.csv`: machine-readable status table
  for the official KuJiaLe / InteriorAgent submission-closure package. It
  records the current video, performance, and final claim-audit gates.
- `tab_official_scene_submission_closure_status.tex`: LaTeX table generated
  from the same official-scene closure status CSV.
- `official_scene_performance_summary.csv`: machine-readable official
  KuJiaLe / InteriorAgent repeated performance summary with aggregate and
  per-scene success/failure counts, ready-time CIs, FPS CIs, and GPU-memory CIs.
- `tab_official_scene_performance_summary.tex`: LaTeX table generated from the
  same official-scene performance summary CSV.

Regenerate with:

```bash
python paper/shared/tables/gen_vlm_pilot_tables.py
python paper/shared/tables/gen_vlm_stress_expanded30.py
python paper/shared/tables/gen_vlm_coordinate_ablation.py
python paper/shared/tables/gen_vlm_failure_taxonomy.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py
python paper/shared/evidence/experiments/08_material_effect_baseline/build_material_effect_risk_matrix.py
python paper/shared/evidence/experiments/09_reviewer_closure_package/build_reviewer_closure_package.py
python paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py
```

The two newer clean-pool and zoom-stress tables, coordinate ablation, failure
taxonomy, material-effect readiness table, material-effect risk matrix, and
reviewer-closure and official-scene submission-closure package tables are registered in
`paper/shared/evidence/results_manifest.yaml`.

Most legacy table content remains embedded in `shared/sections/experiments.tex`
until a later paper-editing pass extracts reusable table sources.
