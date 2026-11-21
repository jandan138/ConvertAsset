# CVIU v3 Colab Pro+ Campaign & Local Bootstrap Verification Record

- **Date**: `2026-11-17`
- **Cloud Runtime**: Google Colab Pro+ `NVIDIA L4` (`22.03 GiB` VRAM), strict unquantized `torch.bfloat16` (`device_map="auto"`, zero CPU/disk offload), `transformers 5.22.1`
- **Code Overlay Archived & Executed**: `cviu_v3_code_overlay.tar.gz` (`sha256: 843fa267831aeeea3d7d9d6cf4a57e4d680c23edd0f50044fc057f39c3839d06`, unit tests `5/5 OK` both locally and on Colab)
- **Raw Analysis Output Directory**: [raw/cviu_v3](file:///I:/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset/paper/shared/evidence/raw/cviu_v3) (`13_cviu_formal/` and `raw/cviu_formal/v1/` left strictly unmodified)

---

## 1. Completed Prediction Inventory (`9,936` Total Verified Predictions)

| Campaign | Model / Condition | Task | Completed / Expected | Runtime Errors | Sync Source |
|---|---|---|---:|---:|---|
| `13_cviu_formal` (frozen `v1`) | `Qwen/Qwen3-VL-8B-Instruct` (`3` greedy repeats + render controls) | `formal-primary` + `control` | `2,976 / 2,976` | `0` | `cviu_formal_model_runs_v1.tar.gz` |
| `13_cviu_formal` (frozen `v1`) | `Qwen/Qwen3-VL-32B-Instruct` (`3` greedy repeats + render controls) | `formal-primary` + `control` | `2,976 / 2,976` | `0` | `cviu_formal_model_runs_v1.tar.gz` |
| `14_cviu_v3` Stage 2 | `Qwen/Qwen3-VL-8B-Instruct` (`T=0.2, top_p=0.95, 5 draws`) | `stochastic-control` | `480 / 480` | `0` | `remote_runs/cviu_v3_20261116` |
| `14_cviu_v3` Stage 2 | `Qwen/Qwen3-VL-8B-Instruct` (`T_only, B_only, photo`) | `counterfactual` | `1,440 / 1,440` | `0` | `remote_runs/cviu_v3_20261116` |
| `14_cviu_v3` Stage 3 | `Qwen/Qwen3-VL-2B-Instruct` | `pilot-qualify` (`100%` strict valid) | `24 / 24` | `0` | `remote_runs/cviu_v3_20261116` |
| `14_cviu_v3` Stage 3 | `Qwen/Qwen3-VL-2B-Instruct` | `formal-primary` + `control-repeat` | `1,056 / 1,056` | `0` | `remote_runs/cviu_v3_20261116` |
| `14_cviu_v3` Stage 4 | `OpenGVLab/InternVL3_5-8B-HF` | `pilot-qualify` (`100%` strict valid) | `24 / 24` | `0` | `remote_runs/cviu_v3_20261116` |
| `14_cviu_v3` Stage 4 | `OpenGVLab/InternVL3_5-8B-HF` | `formal-primary` | `960 / 960` | `0` | `remote_runs/cviu_v3_20261116` |
| **Total** | **4 VLM configurations across 2 families (`Qwen3-VL`, `InternVL3.5`)** | **All completed runs** | **`9,936 / 9,936`** | **`0`** | Verified & locally analyzed via [analyze_v3_all.py](file:///I:/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset/paper/shared/evidence/experiments/14_cviu_v3/analyze_v3_all.py) |

*Note on Stage 4 Lineage 3 (`Molmo2-8B` / `Molmo-7B-O`)*: After `formal_internvl3_5_8b` finished and synced to Google Drive at `02:05:54`, the unattended browser session disconnected overnight before a 3rd-family checkpoint was written back to Drive. Stage 4 remains resumable via `run_colab_cviu_v3_all.py --stages 4` if a 3rd open-weight lineage is added later; the CVIU v3 manuscript restricts every cross-family claim strictly to the verified `Qwen3-VL` (`2B/8B/32B`) and `InternVL3.5` (`8B`) evidence.

---

## 2. Verified Empirical Headline Metrics (`10,000`-Draw Scene-Cluster Bootstrap)

1. **4-Level Variance Hierarchy** ([variance_decomposition.json](file:///I:/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset/paper/shared/evidence/raw/cviu_v3/variance_decomposition.json)):
   - Level 1 (`Greedy Process Repeat`, `0` vs `1` vs `2` on control scenes): `0.00%` hit disagreement (`0.00 px`) across `Qwen3-VL-2B`, `8B`, and `32B`.
   - Level 2 (`Stochastic Decoding T=0.2, 5 draws` on `Qwen3-VL-8B`, `960` pairwise checks): `8.96%` pairwise hit disagreement (`16.67%` inputs have `>=1` flip; `94.38%` raw text variation; `16.37 px` shift).
   - Level 3 (`Ray-Tracing Re-Render Repeat`, `96` inputs): `3.13%` (`3/96`, `9.52 px`) on `8B`, `1.04%` (`1/96`, `6.39 px`) on `32B`.
   - Level 4 (`Material Conversion` on identical `48` control pairs): `8.33%` (`23.83 px`) on `8B` and `4.17%` (`23.26 px`) on `32B`.

2. **30-Scene Scaling Law & Cross-Family Generalization** ([scaling_and_families.json](file:///I:/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset/paper/shared/evidence/raw/cviu_v3/scaling_and_families.json)):
   - `Qwen3-VL-2B`: `O = 56.25% -> C = 56.25%` (`Δ = +0.00%`), `Flip = 14.17%` (`CI95 [11.67%, 16.88%]`; `Loss = 7.08%`, `Gain = 7.08%`), `Disp = 56.98 px`.
   - `Qwen3-VL-8B`: `O = 81.25% -> C = 83.13%` (`Δ = +1.88%`), `Flip = 9.38%` (`CI95 [7.08%, 11.67%]`; `Loss = 3.75%`, `Gain = 5.63%`), `Disp = 27.23 px`.
   - `InternVL3.5-8B`: `O = 80.21% -> C = 79.58%` (`Δ = -0.63%`), `Flip = 10.21%` (`CI95 [7.50%, 13.13%]`; `Loss = 5.42%`, `Gain = 4.79%`), `Disp = 43.30 px` (`+16.07 px` over matched `Qwen3-VL-8B`, `CI95 [+10.05, +21.61 px]`).
   - `Qwen3-VL-32B`: `O = 91.67% -> C = 92.08%` (`Δ = +0.42%`), `Flip = 4.17%` (`CI95 [2.50%, 6.04%]`; `Loss = 1.88%`, `Gain = 2.29%`), `Disp = 20.78 px` (`-10.00 pp` vs `2B`, `CI95 [-12.71%, -7.29%]`).

3. **480-Pair Silhouette Counterfactuals & Photometric Salience Control** ([optical_mechanisms.json](file:///I:/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset/paper/shared/evidence/raw/cviu_v3/optical_mechanisms.json)):
   - Flip rates vs `Original`: `Photometric-Matched (photo) = 5.83%` (`20.27 px`), `Background-Only (B) = 6.46%` (`23.37 px`), `Target-Only (T) = 8.13%` (`24.16 px`), `Full Conversion (F) = 9.38%` (`27.23 px`).
   - Non-photometric shader/texture residual: `F - photo = +3.54%` (`CI95 [+1.25%, +5.83%]`); confirmed on exact `473` identical-mask pairs (`F - photo = +3.38%`, `CI95 [+1.26%, +5.70%]`).
   - Optical regime stratification: `Reflective/Metallic` (`n=158`) gains `+4.43%` (`O=75.32% -> C=79.75%`, `Gain=7.59%`, `Loss=3.16%`) due to specular glare suppression; `Low-Distortion` pixel regime gains `+3.76%`, while `Specular-Stripped` (`n=14`) loses `-7.14%`.

4. **Zero-VLM Pre-Deployment Risk Gate** ([risk_auditor.json](file:///I:/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset/paper/shared/evidence/raw/cviu_v3/risk_auditor.json)):
   - Predicting `any_8b_32b_loss` (`15 train / 5 val / 10 test` split): `deploy_auto` reaches `test AUROC = 0.7432` (`AUPRC = 0.1947`, `R@20% = 41.7%`, `R@30% = 58.3%`), vs `baseline_global_rgb_mae` (`0.4319`) and `baseline_target_rgb_mae` (`0.5569`). On 30-fold `LOSO`, `geometry_only` achieves `AUROC = 0.7322` (`R@20% = 52.0%`, `R@30% = 60.0%`).

