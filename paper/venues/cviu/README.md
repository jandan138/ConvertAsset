# CVIU Revision Workspace (Updated 2026-11-17)

Status: **Revised CVIU v3 manuscript & empirical campaign completed** (`9,936` strict unquantized `torch.bfloat16` predictions across 30 independent scenes, 240 objects, 480 natural pairs, 4 VLM configurations across `Qwen3-VL` and `InternVL3.5`; plus 99 paired `InternNav/DualVLN` navigation episodes retained as an observational case study).

Build PDF from repository root:

```bash
latexmk -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error paper/venues/cviu/main.tex
```

## Completed Evidence Packages
- `E1`–`E8`: Prior ICLR diagnostic archive, repaired 3-scene pilot (`12` pairs / `72` predictions), and frozen 30-scene manifest (`3,168` SHA-256 verified files).
- `E9`: Formal `13_cviu_formal` runs (`Qwen3-VL-8B` and `Qwen3-VL-32B`, 3 greedy repeats each + 96 independent ray-tracing re-renders = `5,952` predictions).
- `E10` (`14_cviu_v3` & `paper/shared/evidence/raw/cviu_v3/`):
  1. `Qwen3-VL-8B` 5-draw stochastic decoding control (`480` inferences, `T=0.2, top_p=0.95`).
  2. `Qwen3-VL-8B` 480-pair pixel-exact silhouette counterfactuals (`target_only`, `background_only`, $\mathrm{CIE}~L^*a^*b^*$ `photometric_matched`, `1,440` inferences).
  3. `Qwen3-VL-2B` intra-family scaling completion (`24` pilot + `960` primary + `96` repeat control = `1,080` inferences).
  4. `OpenGVLab/InternVL3_5-8B-HF` matched-scale cross-family evaluation (`24` pilot + `960` primary = `984` inferences).
  5. Zero-\textsc{VLM} pre-deployment conversion risk gate (`pair_optical_features.json` + `risk_auditor.json`).
  6. Verified bibliographic expansion covering all 10 Reviewer `51hM` citations + `InternVL3.5` + `Molmo2` ([verification log](../../../docs/records/2026-11-17-cviu-reference-verification.md)).

## Key Documents & Audit Trails
- [Reviewer response tracker](REVIEW_RESPONSE_TRACKER.md) (25 items updated with `2026-11-17` empirical closures and honest scope bounds)
- [Campaign verification record](../../../docs/records/2026-11-17-cviu-v3-colab-campaign-results.md)
- [Protocol v3](PROTOCOL.md)
- [Figure generator](../../shared/evidence/experiments/14_cviu_v3/build_cviu_v3_figures.py)
