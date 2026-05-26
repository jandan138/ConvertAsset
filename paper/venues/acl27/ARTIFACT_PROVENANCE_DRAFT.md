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
| InternNav / DualVLN | Downstream embodied-route sanity evidence. | `Wei2026Ground` ICLR/OpenReview source and InternRobotics/InternNav repository. | Public InternNav page checked this turn states the code is MIT licensed, InternData-N1 uses CC BY-NC-SA 4.0, and other datasets inherit their own licenses. | `paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/`. | Confirm whether KuJiaLe/InteriorAgent scenes have separate terms and cite them if required. |
| InteriorAgent / KuJiaLe scenes | Official `val_unseen` three-scene source for 99 paired episodes. | Hugging Face `spatialverse/InteriorAgent` dataset page checked this turn lists `interioragent-terms-of-use`; local download provenance is in `interioragent_scene_download_report.json`. | Terms label is identified, but the full terms text and redistribution allowance still need final human/legal review before packaging media. | `official_val_unseen_prep_manifest.json`, `interioragent_scene_download_report.json`, per-scene summaries. | Add separate citation/license entry if the dataset card or paper requests it; do not redistribute raw scenes. |
| NVIDIA Isaac Sim / USD / MDL / UsdPreviewSurface | Runtime and material-conversion substrate. | Related work cites Orbit/Isaac Lab; method describes MDL-to-UsdPreviewSurface conversion. | Isaac Sim and NVIDIA tooling are governed by NVIDIA software terms; USD/OpenUSD terms should be cited separately if needed. | ConvertAsset code, run commands, render manifests, material-effect baseline manifests. | Add software/version table in appendix and Responsible NLP C4 answer. |
| Gemma4 local multimodal checkpoint | Primary VLM for GRScenes stress and clean-pool grounding probes. | Local checkpoint path records an Unsloth quantized Gemma4 E4B-style model. Public Google Gemma4 model-card pages checked this turn list Apache-2.0, but the exact local checkpoint must still be matched to a public model ID/commit before final claim. | Base model license source is identified; exact local quantized checkpoint provenance is not final until matched. | `stress_predictions.jsonl.metadata.json`, clean-pool metadata files. | Replace local path with anonymized public model ID, commit/hash, license, and model size in appendix/checklist. |
| Qwen2.5-VL-7B-Instruct | Secondary VLM diagnostic exposing coordinate-contract sensitivity. | Hugging Face `Qwen/Qwen2.5-VL-7B-Instruct` page checked this turn reports Apache-2.0 and links Qwen papers. | Apache-2.0 per checked model card. | `stress_expanded30_probes/*qwen25*metadata.json`, clean-pool metadata files. | Add public model ID, license, local checkpoint hash/commit if available, and decoding settings. |
| Selected qualitative rollout videos | Supplemental qualitative evidence and figure/rebuttal candidates. | Generated from local InternNav selected reruns. | Derived media inherits source scene/data constraints; selected rerun metrics are not quantitative evidence. | `official_selected_qualitative_videos/` with mp4s, stills, contact sheets, QA, and manifests. | Keep as supplemental only; anonymize paths and do not present selected metrics as population evidence. |
| NVIDIA material-effect baseline outputs | Third-route selected material-effect comparison. | Local Isaac Sim/NVIDIA Asset Converter smoke and sample conversion manifests. | NVIDIA tool outputs and fixture terms need final review before public redistribution. | `paper/shared/evidence/raw/material_effect_baseline/`. | Include only small allowed stills/manifests; keep large scratch outputs external. |

## Current Upload Boundary

The current safe upload candidate is the ACL PDF plus repo-resident evidence
summaries, tables, selected stills/contact sheets, and compressed selected
videos after anonymization. Do not upload raw source scene trees, full scratch
USD trees, InternNav raw frame directories, LMDBs, local model checkpoints, or
absolute `/cpfs/...` paths.

## Remaining Provenance Gates

1. Match Gemma4 local checkpoint to an exact public model page, commit, and
   license.
2. Review the full `interioragent-terms-of-use` text and confirm the preferred
   InteriorAgent/KuJiaLe citation.
3. Add software/runtime versions for Isaac Sim, USD/PXR, PyTorch,
   Transformers, InternNav, and VLM inference backends.
4. Decide whether supplemental videos can be redistributed or should be shared
   only as still/contact-sheet evidence.
