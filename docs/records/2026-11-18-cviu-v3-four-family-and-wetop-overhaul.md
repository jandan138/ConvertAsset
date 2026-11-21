# CVIU v3 Campaign Record: Four-Family Homogeneous RTX 4090 Suite, WET-OP Figure Overhaul & Elsevier Two-Column Manuscript

- **Date**: 2026-11-18
- **Repository**: `ConvertAsset`
- **Track**: `paper/shared/evidence/experiments/14_cviu_v3/` & `paper/venues/cviu/`

## 1. Homogeneous Hardware/Software Provenance & Immutability

To eliminate cross-GPU and `transformers` version drift observed between early Colab L4 (`transformers 5.22.1`) runs and local RTX 4090 (`23.99 GiB`, `cu126`, `transformers 5.23.0`) runs (early L4 outputs archived under `.cviu_v3_work/archive_l4_5221/`), all 19 `v3` evaluation directories executed end-to-end on the local RTX 4090 workstation under strictly unquantized `torch.bfloat16` (`device_map="auto"`, zero CPU/disk offload, greedy `do_sample=False`), achieving `0` runtime errors and strictly `0.00%` (`0.00 px`) Level-1 greedy repeat disagreement across every checkpoint.

- **Immutable Anchors Untouched**: `paper/shared/evidence/experiments/13_cviu_formal/` and `paper/shared/evidence/raw/cviu_formal/v1/` (`Qwen3-VL-8B` and `Qwen3-VL-32B`, `5,760` primary + `192` L3 render-control predictions = `5,952`) remain untouched.
- **v3 Local Execution (`19/19` complete, `8,064` predictions)**:
  - 4 pilot qualifications (`24` each = `96`): `Qwen3-VL-2B` (`flex_1000`, `22/24 = 91.7%` valid, `19/24 = 79.2%` hit), `InternVL3.5-8B-HF` (`strict`, `24/24 = 100.0%`, `20/24 = 83.3%`), `Molmo2-8B` (`molmo2_1000`, `24/24 = 100.0%`, `24/24 = 100.0%`), `LLaVA-NeXT-Mistral-7B` (`unit_float_xy`, `24/24 = 100.0%`, `22/24 = 91.7%`).
  - 4 formal 30-scene evaluations (`960` each = `3,840`): `Qwen3-VL-2B`, `InternVL3.5-8B-HF`, `Molmo2-8B`, `LLaVA-NeXT-Mistral-7B`.
  - 4 Level-1 greedy repeat controls (`96` each = `384`) and 4 Level-3 ray-tracing re-render controls (`96` each = `384`).
  - 1 Level-2 stochastic decoding control on `Qwen3-VL-8B` ($T{=}0.2$, $\text{top-}p{=}0.95$, 5 draws = `480`).
  - 2 cross-family silhouette counterfactual suites (`1,440` each = `2,880`): `Qwen3-VL-8B` and `InternVL3.5-8B-HF`.
- **Grand Total**: `5,952 (v1) + 8,064 (v3) = 14,016` strict `torch.bfloat16` predictions (`13,920` formal/control/counterfactual + `96` pilots), mirrored to Google Drive (`J:\我的云端硬盘\UltraSync\ConvertAsset\remote_runs\cviu_v3_20261116\`).

## 2. Final Verified Empirical Results (`paper/shared/evidence/raw/cviu_v3/`)

### 2.1 Four-Level Variance Hierarchy (`variance_decomposition.json`)
- **Level 1 (Greedy Repeat)**: `0.00%` (`0.00 px`) across all 6 checkpoints (`288` pairs 8B/32B; `96` pairs 2B/InternVL/Molmo2/LLaVA-NeXT).
- **Level 2 (`Qwen3-VL-8B`, $T{=}0.2$, 960 pairs)**: `8.96%` pairwise disagreement (`16.67%` inputs with $\ge 1$ flip, `94.38%` text change, `16.37 px` shift).
- **Level 3 (Ray-Tracing Re-Render, 96 pairs) vs. Level 4 (Conversion, 48 pairs)**:
  - `Qwen3-VL-2B`: `7.29%` (`30.96 px`) vs `20.83%` (`65.64 px`, `2.86x`)
  - `LLaVA-NeXT-Mistral-7B`: `5.21%` (`24.38 px`) vs `10.42%` (`59.90 px`, `2.00x`)
  - `InternVL3.5-8B-HF`: `1.04%` (`10.38 px`) vs `6.25%` (`39.23 px`, `6.00x`)
  - `Qwen3-VL-8B`: `3.13%` (`9.52 px`) vs `8.33%` (`23.83 px`, `2.67x`)
  - `Molmo2-8B`: `0.00%` (`5.98 px`) vs `4.17%` (`41.64 px`, `>4x`)
  - `Qwen3-VL-32B`: `1.04%` (`6.39 px`) vs `4.17%` (`23.26 px`, `4.00x`)

### 2.2 30-Scene Scaling & Four-Family Grounding (`scaling_and_families.json`, 480 pairs)
- `Qwen3-VL-2B` (`flex_1000`, `96.88%/96.04%` valid): `H_O=66.67%`, `H_C=63.13%`, `dH=-3.54% [-8.33, +1.25]`, `Flip=23.13% [19.79, 26.67]`, `Loss/Gain=13.33%/9.79%`, `Shift=69.70px`.
- `LLaVA-NeXT-Mistral-7B` (`unit_float_xy`, `99.17%/99.17%`): `H_O=67.50%`, `H_C=67.92%`, `dH=+0.42% [-3.33, +3.96]`, `Flip=16.67% [12.50, 21.25]`, `Loss/Gain=8.13%/8.54%`, `Shift=65.08px`.
- `InternVL3.5-8B-HF` (`strict`, `100.00%/100.00%`): `H_O=78.54%`, `H_C=80.00%`, `dH=+1.46% [-0.42, +3.33]`, `Flip=10.63% [7.92, 13.54]`, `Loss/Gain=4.58%/6.04%`, `Shift=47.11px`.
- `Qwen3-VL-8B` (`strict`, `99.58%/99.38%`): `H_O=81.25%`, `H_C=83.13%`, `dH=+1.88% [-0.42, +4.17]`, `Flip=9.38% [7.08, 11.67]`, `Loss/Gain=3.75%/5.63%`, `Shift=27.23px`.
- `Molmo2-8B` (`molmo2_1000`, `98.75%/99.38%`): `H_O=93.96%`, `H_C=94.38%`, `dH=+0.42% [-1.67, +2.50]`, `Flip=4.58% [2.50, 7.08]`, `Loss/Gain=2.08%/2.50%`, `Shift=33.80px`.
- `Qwen3-VL-32B` (`strict`, `99.79%/99.79%`): `H_O=91.67%`, `H_C=92.08%`, `dH=+0.42% [-1.25, +2.29]`, `Flip=4.17% [2.50, 6.04]`, `Loss/Gain=1.88%/2.29%`, `Shift=20.78px`.
- **Four $\ge$7B Family Regression Overlap (`family_overlap_4x8b`)**: `77/480` pairs lose on $\ge 1$ family (`{0:403, 1:66, 2:10, 3:1, 4:0}`), with `66/77 (85.7%)` unique to a single architecture.

### 2.3 Cross-Family Counterfactuals (`optical_mechanisms.json`, `2,880` evals) & Risk Gate (`risk_auditor.json`)
- Both `Qwen3-VL-8B` (`9.38% - 5.83%`) and `InternVL3.5-8B-HF` (`10.63% - 7.08%`) show an identical **`+3.54%`** non-photometric BSDF residual (`[+1.25%, +5.83%]` and `[+1.04%, +6.04%]`; `+3.38%` on the 473 bit-identical mask subset).
- `Qwen3-VL-8B` gains most on `Reflective/Metallic` (`+4.43%`), whereas `InternVL3.5-8B-HF` gains most on `Emissive/Screen` (`+6.90%`) and drops `-1.14%` on `Matte/Diffuse`.
- Zero-VLM risk gating on `any_8b_32b_loss` reaches `0.743` test (`0.653` LOSO) with `deploy_auto` and `0.742` test (`0.732` LOSO) with `geometry_only` (capturing `41.7%` test / `52.0%` LOSO losses at a `20%` review budget), vs `0.432` test for `baseline_global_rgb_mae` and `0.501` for undirected `8b_flip`; pooling across all 6 checkpoints (`any_family_loss`) drops to `0.582` test / `0.536` LOSO (`deploy_auto`).

## 3. WET-OP-Aligned Figure Suite & Elsevier Two-Column Layout

- Rebuilt all 6 figures following `wet-op-cvpr2027-full-package.zip` typography and color conventions (`#1B3765` navy, `#0B5563` teal, `#E11D48` crimson) via `build_fig1_wetop_pptx.py` (including editable `Figure1_ConvertAsset_Overview.pptx`) and `build_cviu_wetop_figures.py` (`fig1_overview.pdf` through `fig6_navigation_vln.pdf`).
- Converted `paper/venues/cviu/main.tex` to `\documentclass[5p,times,authoryear]{elsarticle}` with CVIU `highlights` and `CRediT Authorship Contribution Statement`, updated all main sections, tables, and appendices, and compiled + visually verified rendered PDF pages.

