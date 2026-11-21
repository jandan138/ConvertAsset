# 2026-11-16 CVIU v3 Experimental Suite and Colab A100 Runner

## Scope & Protocol Redesign

- Upgraded `paper/venues/cviu/PROTOCOL.md` and `paper/venues/cviu/experiment_plan.json` (`schema_version: 3`) from observation-only reporting to the **Bidirectional Optical Trade-off + 4-Level Variance Hierarchy + Zero-VLM Pre-Deployment Conversion Risk Gate** design.
- Preserved `paper/shared/evidence/experiments/13_cviu_formal/` and `paper/shared/evidence/raw/cviu_formal/v1/` untouched as immutable provenance for the completed `Qwen3-VL-8B` / `Qwen3-VL-32B` (`5,760` primary + `192` render-control) runs.

## Added Modules (`paper/shared/evidence/experiments/14_cviu_v3/`)

- `v3_common.py`: asset path resolution, SHA-256 verification, strict/relaxed/Molmo coordinate parsers, vectorized CIE $L^*a^*b^*$ transforms, 10,000-draw scene-cluster bootstrap, pure-NumPy damped-Newton L2 logistic regression, AUROC/AUPRC.
- `build_counterfactual_inputs.py`: synthesizes 480-pair (`1,440` PNG) pixel-exact `target_only`, `background_only`, and per-region CIE $L^*a^*b^*$ `photometric_matched` counterfactuals.
- `optical_and_risk_features.py`: extracts geometry priors, optical-regime tags, local 8×8 SSIM, Sobel texture ratio, specular highlight deltas, and contour contrast deltas into `pair_optical_features.json/.csv`.
- `run_v3_vlm_suite.py`: resumable strict-`bfloat16` GPU inference runner supporting `pilot-qualify`, `formal-primary`, `control-repeat`, `stochastic-control`, and `counterfactual`.
- `analyze_v3_all.py`: computes `scaling_and_families.json`, `variance_decomposition.json`, `optical_mechanisms.json`, and `risk_auditor.json` (`15 train / 5 validation / 10 test` + 30-fold LOSO CV).
- `run_colab_cviu_v3_all.py` & `CVIU_v3_Colab_A100_Runner.ipynb`: idempotent Colab Pro+ runner syncing stage outputs to `UltraSync/ConvertAsset/remote_runs/cviu_v3_20261116/` with `AUTO_DISCONNECT = True`.

## Verification

- `python -m py_compile` across all six Python modules in `14_cviu_v3/`: passed (`exit 0`).
- `python -m unittest discover -s tests -p "test_cviu_v3_pipeline.py" -v`: passed (`Ran 5 tests in 13.027s — OK`).
- Built and verified `J:\我的云端硬盘\UltraSync\ConvertAsset\remote_runs\cviu_v3_20261116\cviu_v3_code_overlay.tar.gz` (`37,411` bytes, `11` members) and `J:\我的云端硬盘\Colab Notebooks\CVIU_v3_Colab_A100_Runner.ipynb` (`nbformat=4`, `6` cells).
- `colab-mcp` `open_colab_browser_connection` timed out (`false`) because Windows default HTTPS handler (`MSEdgeHTM`) opened Microsoft Edge instead of logged-in Chrome; ready for 1-click Colab execution or manual Chrome MCP proxy reconnect.

