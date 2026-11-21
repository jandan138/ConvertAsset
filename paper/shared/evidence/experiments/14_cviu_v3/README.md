# CVIU v3 Experiments (`14_cviu_v3`)

Modular experiment suite implementing `paper/venues/cviu/PROTOCOL.md` (v3):

- `v3_common.py` — Path resolution, point parsing (`strict` / `relaxed_xy` / `molmo_0_100`), CIE $L^*a^*b^*$ transforms, 10,000-draw scene-cluster bootstrap, pure-NumPy L2 Logistic Regression & AUROC/AUPRC.
- `build_counterfactual_inputs.py` — Builds pixel-exact 480-pair (`1,440` image) `target_only`, `background_only`, and per-region CIE $L^*a^*b^*$ `photometric_matched` counterfactuals.
- `optical_and_risk_features.py` — Extracts zero-VLM geometry, optical priors, local 8×8 SSIM, Sobel texture retention, highlight shifts, and contour contrast deltas (`pair_optical_features.json/.csv`).
- `run_v3_vlm_suite.py` — Resumable `torch.bfloat16` GPU runner supporting `pilot-qualify`, `formal-primary`, `control-repeat`, `stochastic-control`, and `counterfactual`.
- `analyze_v3_all.py` — Generates `scaling_and_families.json`, `variance_decomposition.json`, `optical_mechanisms.json`, and `risk_auditor.json` under `paper/shared/evidence/raw/cviu_v3/`.
- `run_colab_cviu_v3_all.py` — Idempotent Colab Pro+ stage orchestrator syncing results directly to `/content/drive/MyDrive/UltraSync/ConvertAsset/remote_runs/cviu_v3_20261116/`.

