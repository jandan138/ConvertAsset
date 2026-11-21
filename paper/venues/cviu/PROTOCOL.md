# CVIU Protocol v3 — Bidirectional Optical Trade-off, Variance Hierarchy, Four-Family Grounding & Pre-Deployment Conversion Risk Gate

**Core Thesis**: Preserving 3D geometry during material simplification (`MDL -> UsdPreviewSurface`) does not preserve embodied model decisions. Across 4 independent open-weight VLM families and 6 unquantized `torch.bfloat16` checkpoints, small marginal deltas (`+0.42%` on `Qwen3-VL-32B`, `Molmo2-8B`, and `LLaVA-NeXT-Mistral-7B`) conceal a **deterministic bidirectional optical trade-off** (`4.17%--23.13%` flips) cleanly above `0.00%` greedy and `0.00%--7.29%` ray-tracing re-render noise floors. Counterfactual evaluation across 2 independent 8B families (`2,880` inferences) isolates an identical **`+3.54%`** non-photometric BSDF residual beyond $\mathrm{CIE}~L^*a^*b^*$ salience matching; `85.7%` of $\ge$7B losses are architecture-specific, making family-calibrated zero-VLM risk gating (`0.743` test / `0.732` LOSO AUROC) effective where global RGB MAE fails (`0.432`).

`paper/shared/evidence/experiments/13_cviu_formal/` and `paper/shared/evidence/raw/cviu_formal/v1/` remain immutable provenance for the completed 5,760-prediction `Qwen3-VL-8B` / `Qwen3-VL-32B` primary runs and 192-prediction ray-tracing render-repeat controls. All v3 experiments live under `paper/shared/evidence/experiments/14_cviu_v3/` and write outputs under `paper/shared/evidence/raw/cviu_v3/`.

---

## Frozen Cohort & Provenance

- **Cohort**: 30 frozen natural GRScenes-100 scenes (`20 home / 10 commercial`: `15 train / 5 validation / 10 test` in `paper/shared/evidence/raw/cviu_formal/v1/scenes.json`) × 8 distinct objects × 2 camera views (`1024×768`) = **480 pairs (`960` inputs)** (`manifest.json`, SHA-256 `1efcbeb7cc37f1d29ccb38eae7ff5607d222d23cd051f878e0c91a1231dc8854`).
- **Held-out Pilot Gate**: 3 pilot scenes × 6 objects × 2 views = **12 pairs (`24` inputs)** (`paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/manifest.json`) used strictly to qualify model loaders and native parser modes (`>= 90%` valid rate: `strict`, `flex_1000`, `molmo2_1000`, `unit_float_xy`) prior to running the 960 formal inputs.
- **Homogeneous Hardware/Software Provenance**: All 19 `v3` local runs (formal, L1 repeat, L2 stochastic, L3 re-render, 2-family counterfactuals, and 4 pilots) executed on local `RTX 4090 23.99 GiB` in strictly unquantized `torch.bfloat16` (`transformers 5.23.0`, `cu126`, zero runtime errors; early mixed `5.22.1` L4 runs archived under `.cviu_v3_work/archive_l4_5221/`). Combined with immutable `v1` `Qwen3-VL-8B/32B` runs (`5,952`), total verified predictions = **`14,016`** (`13,920` formal/control/CF + `96` pilots).
- **Primary Metric**: Point-in-visible-target-mask (`hit`) under `[0, 1000)` normalized-to-`1024×768` pixel projection (`mask[int(y * 768 / 1000), int(x * 1024 / 1000)]`), alongside `valid_point_rate`, cross-condition `loss_rate` (`O=1, C=0`), `gain_rate` (`O=0, C=1`), `flip_rate` (`O != C`), and valid-pair Euclidean displacement in pixels (`1024, 768` scale).
- **Uncertainty**: 10,000 scene-cluster bootstrap draws (`seed = 20261114`), resampling all objects, views, and repeats within a scene together; 95% intervals reported.

---

## Research Questions & Experimental Modules

### RQ1: Variance Hierarchy, Intra-Family Capacity Scaling & 4-Family Generalization
1. **Completed Anchor (`13_cviu_formal`)**:
   - `Qwen/Qwen3-VL-8B-Instruct` & `Qwen/Qwen3-VL-32B-Instruct`: 3 greedy runs × 960 inputs = **5,760 primary predictions** + **192 ray-tracing render-control predictions** across 3 control scenes (`MV7J6NIKTKJZ2AABAAAAADY8_usd`, `MWBGLKQKTKJZ2AABAAAAACA8_usd`, `MVSGSAIKTKJ66AABAAAAAEA8_usd`).
2. **Capacity Scaling & 4 Independent Open-Weight Families (`14_cviu_v3`)**:
   - `Qwen/Qwen3-VL-2B-Instruct` (`flex_1000`, `96.5%` valid), `OpenGVLab/InternVL3_5-8B-HF` (`strict`, `100.0%` valid), `allenai/Molmo2-8B` (SigLIP-2 pointing specialist, `molmo2_1000`, `99.1%` valid), and `llava-hf/llava-v1.6-mistral-7b-hf` (pure non-Qwen Mistral-7B + CLIP, `unit_float_xy`, `99.2%` valid): each evaluated on all `960` formal inputs + `96` L1 repeat + `96` L3 ray-tracing controls (`torch.bfloat16`, greedy `T=0`) after passing the 24-input pilot gate (`>= 91.7%` valid).
   - Cross-architecture regression overlap across the 4 $\ge$7B families (`family_overlap_4x8b`): `77/480` pairs lose on $\ge 1$ family, with `66/77 (85.7%)` unique to a single architecture.
3. **4-Level Variance Decomposition (3 Control Scenes = 48 Pairs / 96 Inputs)**:
   - Level 1: Greedy process determinism across ALL 6 checkpoints (`0.00%` flip rate, `0.00 px` everywhere).
   - Level 2: Stochastic decoding (`Qwen/Qwen3-VL-8B-Instruct`, `temperature=0.2`, `top_p=0.95`, 5 independent draws = **480 predictions** / 960 pairwise checks: `8.96%` pairwise, `16.67%` any-flip, `94.38%` text change).
   - Level 3: Ray-tracing re-render variance (`render_controls.json`, 3 independent Isaac Sim renders: `0.00%--7.29%` across 6 checkpoints).
   - Level 4: `MDL -> UsdPreviewSurface` conversion flips (`4.17%--20.83%`, `2.00x--6.00x` or `>4x` above L3 on controls).

### RQ2: 2,880 Cross-Family Silhouette Counterfactuals & Optical Regimes
1. **Pixel-Exact Silhouette-Mask Composites (480 Pairs = 1,440 Images × 2 Families = 2,880 Evaluations)**:
   - Evaluates **both** `Qwen3-VL-8B` and `InternVL3.5-8B-HF` on **Target-Only ($I^T$)**, **Background-Only ($I^B$)**, and per-region $\mathrm{CIE}~L^*a^*b^*$ **Photometric-Matched Control ($I^{\text{photo}}$)** (`1,440` counterfactual inferences each).
   - Both families yield an identical **`+3.54%`** non-photometric BSDF residual (`I^F - I^{\text{photo}}`; `+3.38%` on `473/480` bit-identical masks).
2. **Optical Stratification (`Gain` vs `Loss`)**:
   - Stratifies `Gain`, `Loss`, and `Flip` across prior optical regimes (`Reflective/Metallic`, `Transparent/Glass`, `Matte/Diffuse`, `Emissive/Screen`) and objective pixel distortion strata (`Low-Distortion`, `Specular-Stripped`, `Texture/Detail-Degraded`, `Mask/Opacity-Shift`).

### RQ3: Pre-Deployment Conversion Risk Gate (Family-Calibrated vs. Pooled)
1. **Strictly Out-of-Sample Split**: Fit standardized L2 Logistic Regression on **15 training scenes** (240 pairs), tune `C` on **5 validation scenes** (80 pairs), evaluate on **10 held-out test scenes** (160 pairs) + 30-scene LOSO with 10,000 scene-cluster bootstrap CIs.
2. **Targets & Key Finding**: `any_8b_32b_loss` (`0.743` test / `0.653` LOSO `deploy_auto`; `0.742` / `0.732` `geometry_only`) outperforms `baseline_global_rgb_mae` (`0.432` test / `0.490` LOSO) and undirected `8b_flip` (`0.501` test); pooling heterogeneous losses across all 6 checkpoints (`any_family_loss`) drops to `0.582` test / `0.536` LOSO (`deploy_auto`) due to `85.7%` single-architecture divergence, demonstrating the need for family-calibrated gates.

### RQ4: Downstream Propagation to Closed-Loop Navigation (Section 6 Case Study)
- Retain KuJiaLe 3-scene / 99-episode paired navigation (`original` vs `converted`, `52.5% -> 48.5%` SR, 17 losses / 13 gains, `30.3%` turnover) as a scoped observational case study alongside `paper/venues/cviu/navigation_followup.json`.
