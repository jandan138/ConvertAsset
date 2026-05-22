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

Regenerate with:

```bash
python paper/shared/tables/gen_vlm_pilot_tables.py
```

Most legacy table content remains embedded in `shared/sections/experiments.tex`
until a later paper-editing pass extracts reusable table sources.
