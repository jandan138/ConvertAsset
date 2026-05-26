# ACL Compute And Runtime Summary Draft

Checked: 2026-05-26.

This file is the working source for ARR Responsible NLP checklist items C1,
C2, and C4. It summarizes what the repository can currently prove from local
metadata, run manifests, and fresh lightweight version probes. It is not a
substitute for the final OpenReview checklist answer: final submission still
needs author confirmation that the checked runtime matches the submitted runs.

## Hardware And Runtime Snapshot

| Component | Current evidence | Submission status |
| --- | --- | --- |
| GPU host | `nvidia-smi` on this workspace reports one NVIDIA GeForce RTX 4090 with 46068 MiB memory and driver 570.153.02. | Usable as a local hardware note if authors confirm this is the experiment host. |
| Isaac Sim / USD runtime | `/isaac-sim/VERSION` reports Isaac Sim `4.5.0-rc.36+release.19112.f59b3005.gl`; `/isaac-sim/PACKAGE-INFO.yaml` reports commit `f59b30053cf43dfdddc273a3f850424942a33e0c`. `./scripts/isaac_python.sh` reports Python 3.10.15, `usd-core` 26.5, and NumPy 2.2.6. | Ready for appendix/checklist, with final author confirmation. |
| ConvertAsset code | Current ACL work is on this repository. Historical experiment manifests record per-run git commits and dirty-state snapshots. | Cite the final public/anonymized repository only if allowed by the review policy; otherwise cite scripts and manifests in supplement. |
| InternNav runtime | Local InternNav checkout currently resolves to commit `7a5c624`; official KuJiaLe runs use the ConvertAsset Isaac wrapper and the InternNav / InternVLA-N1 runtime stack. | Needs final public source/license note for the exact checkpoint and any non-code assets. |

## VLM Probe Environments

| Probe family | Evidence | Settings | Remaining action |
| --- | --- | --- | --- |
| Gemma4 primary VLM | `stress_predictions.jsonl.metadata.json` and `gemma4_clean_pool_pass15_predictions.jsonl.metadata.json` record backend `local_gemma4_multimodal`, coordinate frame `normalized_1000`, response format `structured_text`, and `max-new-tokens=64`. The interpreter recorded in those commands currently reports Python 3.10.15, Torch 2.10.0, Transformers 5.8.0.dev0, Unsloth 2026.4.8, Accelerate 1.13.0, BitsAndBytes 0.49.2, and Pillow 11.3.0. | Local model config reports `model_type=gemma4`, `Gemma4ForConditionalGeneration`, bfloat16, and bitsandbytes 4-bit NF4 quantization with double quantization. Local model README states `base_model: google/gemma-4-E4B-it` and Apache-2.0 license metadata. | Match the local Unsloth quantized checkpoint to an exact public model page and commit/hash before final submission. Do not expose local checkpoint paths in upload artifacts. |
| Qwen2.5-VL diagnostic VLM | `qwen25_stress_expanded30_structured_predictions.jsonl.metadata.json` records backend `local_hf_qwen`, coordinate frame `normalized_1000`, response format `structured_text`, `attn-implementation=eager`, and `max-new-tokens=64`. The interpreter recorded in those commands currently reports Python 3.13.11, Torch 2.10.0, Transformers 5.2.0, Accelerate 1.12.0, Pillow 12.1.1, and `qwen-vl-utils` 0.0.14. | Local model config reports `model_type=qwen2_5_vl`, `Qwen2_5_VLForConditionalGeneration`, and bfloat16; local README metadata states Apache-2.0. | Add final Hugging Face model ID, commit/hash if available, and decoding settings in appendix/checklist. |

## Experiment Runtime Evidence

| Experiment block | Repository evidence | Runtime/compute facts currently supportable |
| --- | --- | --- |
| GRScenes noMDL conversion | `full_nomdl_multi_root_run_report.json`, `full_nomdl_apply_verification_report.json`, and `docs/records/2026-05-21-grscenes-full-nomdl-apply.md`. | Full scratch conversion processed 99 top-level GRScenes raw scenes; verification passed with 99/99 expected top outputs and no source-tree pollution. The dated record reports elapsed conversion time as 6627 seconds. |
| GRScenes paired rendering | `retake_zoom_expanded30_paired_render_summary.json` and paired render reports. | Expanded stress set contains 30 target-visible paired render records; 30/30 paired render-smoke checks pass, with 600 x 450 images. These are render/protocol checks, not runtime benchmark claims. |
| GRScenes VLM scoring | Gemma4 and Qwen metadata plus score summaries under `grscene_vlm_grounding/`. | Gemma4 expanded30 primary run has 60 predictions. Qwen expanded30 diagnostic run has 60 predictions. Both use structured-text output and normalized-1000 coordinate prompting; Qwen additionally records `attn-implementation=eager`. |
| Official KuJiaLe InternNav route | `official_val_unseen_99/paired_99_summary.json`, `per_scene_aggregate_summary.json`, and `official_val_unseen_prep_manifest.json`. | The local official `val_unseen` split has 99 episodes across three KuJiaLe scenes. Quantitative navigation metrics come from full metric runs without selected-video rerun metrics. |
| Official-scene load/render closure | `official_scene_submission_closure_summary.json` and `official_scene_performance_runs.csv`. | The closure package has 18/18 successful required fresh-process runs: three official scenes x original MDL/noMDL x three repetitions. Aggregated ready-time intervals overlap: original MDL 13.95 s, 95% CI [11.64, 16.28], and ConvertAsset noMDL 14.12 s, 95% CI [12.31, 16.24]. GPU memory means are about 3807 MB and 3829 MB. This supports loadability/stability, not speedup. |
| NVIDIA material-effect baseline | `material_effect_baseline/nvidia_baseline_smoke_manifest.json` and material-effect manifests. | The installed NVIDIA Asset Converter smoke uses `omni.kit.asset_converter-2.8.3+106.5.0...`; two USD baseline attempts opened with PreviewSurface and zero active MDL shaders. This is selected material-effect evidence, not official-scene performance evidence. |

## Final Checklist Text Seed

Draft answer for ARR C1/C2/C4:

> We ran all experiments on a local GPU workstation; the checked host reports
> an NVIDIA GeForce RTX 4090 with 46 GB memory and driver 570.153.02. USD and
> rendering experiments used Isaac Sim 4.5.0-rc.36 with Python 3.10.15 and
> USD/PXR package metadata `usd-core` 26.5. VLM probes used local Gemma4 and
> Qwen2.5-VL checkpoints with structured-text output, normalized-1000
> coordinate prompting, and `max_new_tokens=64`; Qwen used eager attention.
> InternNav downstream runs used the local InternNav / InternVLA-N1 stack over
> the three-scene official KuJiaLe `val_unseen` split. Repository manifests
> record exact commands, script hashes, run timestamps, and output hashes.

Before final upload, replace local-path evidence with anonymized public model
IDs, software versions, and checkpoint hashes. Do not upload local model
checkpoints, raw scenes, LMDBs, or absolute `/cpfs/...` paths.
