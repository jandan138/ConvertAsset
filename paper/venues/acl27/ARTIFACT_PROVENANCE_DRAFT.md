# ACL Artifact Provenance Draft

Checked: 2026-05-26.

This draft lists the main artifacts used by the ACL wrapper and whether their
source, license/terms, intended use, and local evidence status are ready for an
ARR Responsible NLP checklist response. It is intentionally conservative:
unknown terms are marked as follow-up rather than inferred.

| Artifact | Role in paper | Public/source provenance | License/terms status | Local evidence | Submission action |
| --- | --- | --- | --- | --- | --- |
| GRUtopia / GRScenes | Source synthetic scene benchmark and GRScenes VLM grounding evidence. | Paper/source cited by `Wang2024GRUtopia`; arXiv page points to the OpenRobotLab/GRUtopia project. Public package pages checked this turn state GRUtopia simulation code is MIT licensed and open GRScenes are CC BY-NC-SA 4.0. | Research/non-commercial terms must be respected; do not redistribute source assets in supplemental unless explicitly allowed. | `paper/shared/evidence/raw/grscene_vlm_grounding/`, source/target/render manifests, scratch/noMDL conversion reports. | Add final license/access note in appendix/checklist; keep upload package to derived evidence and small permitted artifacts. |
| ConvertAsset noMDL outputs | Intervention under study. | This repository's own code and generated noMDL scratch outputs. | Repo/license policy should be confirmed before public release; generated outputs inherit source asset constraints. | `convert_asset/no_mdl/`, evidence manifests, `CLAIM_AUDIT.md`. | Public code release should exclude restricted source assets and local paths. |
| InternNav / DualVLN | Downstream embodied-route sanity evidence. | `Wei2026Ground` ICLR/OpenReview source and InternRobotics/InternNav repository. | Public InternNav page checked this turn states the code is MIT licensed, InternData-N1 uses CC BY-NC-SA 4.0, and other datasets inherit their own licenses. InteriorAgent / KuJiaLe scenes are tracked separately below. | `paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/`. | Cite InternNav/DualVLN for the runtime and InteriorAgent/KuJiaLe for the official scenes; keep raw logs/LMDBs out of the packet. |
| InteriorAgent / KuJiaLe scenes | Official `val_unseen` three-scene source for 99 paired episodes. | Hugging Face `spatialverse/InteriorAgent` dataset metadata checked this turn resolves to revision `ac599fe2d2285ed0ddfafb70ba56e489462e0650` and lists `interioragent-terms-of-use`; local download provenance is in `interioragent_scene_download_report.json`. | The linked terms allow non-commercial access/use but prohibit redistribution of the data or modified data. Safe review-packet default is therefore no raw scenes and no optional selected scene-derived media unless authors obtain explicit permission or legal approval. | `official_val_unseen_prep_manifest.json`, `interioragent_scene_download_report.json`, per-scene summaries. | Cite the dataset/terms, keep scene assets out of the packet, and keep selected media excluded by default. |
| NVIDIA Isaac Sim / USD / MDL / UsdPreviewSurface | Runtime and material-conversion substrate. | Related work cites Orbit/Isaac Lab; method describes MDL-to-UsdPreviewSurface conversion. `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` records the checked local Isaac Sim package version and USD/PXR metadata. | Isaac Sim and NVIDIA tooling are governed by NVIDIA software terms; USD/OpenUSD terms should be cited separately if needed. | ConvertAsset code, run commands, render manifests, material-effect baseline manifests. | Add software/version table in appendix and Responsible NLP C4 answer from the compute/runtime draft. |
| Gemma4 local multimodal checkpoint | Primary VLM for GRScenes stress and clean-pool grounding probes. | Hugging Face API/model-card metadata checked this turn identifies `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` at revision `9746c23553347b443ebdc1caba1d41b52223d0c8`, with base `google/gemma-4-E4B-it` and Apache-2.0 metadata. Local release metadata records the same repo and revision. | Public checkpoint identity, revision, model-card license metadata, quantization, and decoding settings are now documented for the checklist. Final author/legal confirmation still applies to model terms. | `stress_predictions.jsonl.metadata.json`, clean-pool metadata files, `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`, `MODEL_AND_ASSET_LICENSE_AUDIT.md`. | Report public model ID/revision, license metadata, quantization, and decoding settings; do not upload local checkpoint files or local paths. |
| Qwen2.5-VL-7B-Instruct | Secondary VLM diagnostic exposing coordinate-contract sensitivity. | Hugging Face API/model-card metadata checked this turn identifies `Qwen/Qwen2.5-VL-7B-Instruct`, `main` revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`, with Apache-2.0 metadata. | Public model ID/license and checked public revision are documented. The local copy has file hashes and config/generation metadata but no separate source snapshot manifest. | `stress_expanded30_probes/*qwen25*metadata.json`, clean-pool metadata files, `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`, `MODEL_AND_ASSET_LICENSE_AUDIT.md`. | Report public model ID, checked public revision, local file hashes, and decoding settings; do not upload local checkpoint files or local paths. |
| Selected qualitative rollout videos | Supplemental qualitative evidence and figure/rebuttal candidates. | Generated from local InternNav selected reruns over InteriorAgent / KuJiaLe scenes. | Derived media inherits scene/data constraints. Because InteriorAgent terms prohibit redistributing data or modified data, selected videos are excluded from the safe review packet by default. Selected rerun metrics are not quantitative evidence. | `official_selected_qualitative_videos/` with mp4s, stills, contact sheets, QA, and manifests. | Keep repo-resident for internal figure/rebuttal inspection; do not stage optional videos/media unless authors approve a separate terms/anonymization path. |
| NVIDIA material-effect baseline outputs | Third-route selected material-effect comparison. | Local Isaac Sim/NVIDIA Asset Converter smoke and sample conversion manifests. | NVIDIA tool outputs and fixture terms need final review before public redistribution. | `paper/shared/evidence/raw/material_effect_baseline/`. | Include only small allowed stills/manifests; keep large scratch outputs external. |

## Current Upload Boundary

The current safe upload candidate is the ACL PDF plus the OpenReview form
source and minimal repo-resident metadata generated by the staging script. Use
`FINAL_SUBMISSION_PACKET_CHECKLIST.md` as the staging checklist. Do not upload
raw source scene trees, full scratch USD trees, InternNav raw frame directories,
LMDBs, local model checkpoints, optional selected scene-derived media, or
absolute `/cpfs/...` paths.

## Remaining Provenance Gates

1. Confirm the preferred InteriorAgent/KuJiaLe citation and whether any
   scene-derived media beyond the manuscript PDF is allowed under the final
   author/legal interpretation.
2. Confirm the software/runtime versions summarized in
   `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` and replace local paths with public IDs.
3. Re-check the final target-call and OpenReview instructions immediately
   before upload.
