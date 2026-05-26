# ACL Model And Asset License Audit

Checked: 2026-05-26.

This audit closes the submission-facing provenance questions that previously
blocked the ARR Responsible NLP checklist. It records public identifiers,
licenses or terms, and the safe upload boundary. It is not legal advice; final
authors should still confirm the chosen venue's upload rules before submission.

## Summary

| Artifact | Public identifier checked | License / terms status | Local evidence status | Upload boundary |
| --- | --- | --- | --- | --- |
| Gemma4 primary VLM | `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit`, revision `9746c23553347b443ebdc1caba1d41b52223d0c8`; model card points to base `google/gemma-4-E4B-it`. | Hugging Face API/model-card metadata reports Apache-2.0 and links the Gemma 4 license page. | Local release metadata records the same repo and revision. Local config reports `gemma4`, `Gemma4ForConditionalGeneration`, bfloat16, bitsandbytes 4-bit NF4, and double quantization. | Report public model ID, revision, quantization, and decoding settings. Do not upload local checkpoint files. |
| Qwen2.5-VL diagnostic VLM | `Qwen/Qwen2.5-VL-7B-Instruct`, `main` revision checked at `cc594898137f460bfe9f0759e9844b3ce807cfb5`. | Hugging Face API/model-card metadata reports Apache-2.0. | Local README/config/generation files match the public model family and report `qwen2_5_vl`, `Qwen2_5_VLForConditionalGeneration`, bfloat16, and structured multimodal use. The local copy has file hashes but no separate source snapshot manifest. | Report public model ID, checked public revision, local file hashes, decoding settings, and `attn-implementation=eager`. Do not upload local checkpoint files. |
| GRScenes / GRUtopia | Hugging Face dataset metadata resolves to `InternRobotics/GRScenes`, revision `4760b9031881c985e3582075cb2d8dbde1530a68`. | Dataset metadata reports CC BY-NC-SA 4.0. Local README also states GRUtopia simulation code is MIT and open GRScenes are CC BY-NC-SA 4.0. | GRScenes evidence remains repo-side as derived summaries, tables, figures, and manifests. Raw scene trees and scratch noMDL USD trees stay outside the review packet. | Use derived evidence only; do not redistribute source scenes or full converted scene trees. |
| InteriorAgent / KuJiaLe scenes | Hugging Face dataset `spatialverse/InteriorAgent`, revision `ac599fe2d2285ed0ddfafb70ba56e489462e0650`. | Dataset card labels `interioragent-terms-of-use`; the linked terms allow non-commercial access/use but prohibit redistribution of the data or modified data. | Official `val_unseen` evidence covers 99 episodes across `kujiale_0031`, `kujiale_0036`, and `kujiale_0066`. Download provenance and split manifests are present in the evidence tree. | Safe default is no raw scene redistribution and no optional selected scene-derived videos/media in the upload packet unless authors obtain explicit permission or venue/legal approval. |
| InternNav / DualVLN | Public InternNav repository and paper cited in the manuscript. | Checked public pages state InternNav code is MIT and InternData-N1 is CC BY-NC-SA 4.0; other datasets inherit their own licenses. | Local evidence records the official three-scene KuJiaLe route, InternNav checkout, commands, summaries, and selected qualitative outputs. | Report code/source provenance and scoped 99-episode split. Do not upload raw logs, LMDBs, raw frames, or restricted scene assets. |
| NVIDIA Isaac Sim / Asset Converter | Local runtime and converter versions recorded in compute/runtime draft and manifests. | NVIDIA software and generated outputs remain governed by NVIDIA software terms plus source asset terms. | Material-effect baseline evidence is selected/static and manifest-backed; it is not an official-scene performance baseline. | Include small derived tables/figures/manifests only when allowed; do not ship full scratch outputs. |

## Closed Gates

- The Gemma4 public checkpoint gate is now closed for the paper/checklist:
  public repo ID, full revision, model-card license metadata, local release
  metadata, quantization, and decoding settings are documented.
- The Qwen2.5-VL public model gate is now closed for the paper/checklist:
  public repo ID, checked public revision, Apache-2.0 metadata, local file
  hashes, and decoding/runtime settings are documented.
- The GRScenes public dataset license status is documented as CC BY-NC-SA 4.0.
- The InteriorAgent / KuJiaLe terms gate is no longer an unknown: the safe
  submission boundary is to exclude raw scenes and optional selected media.

## Model Hashes

These hashes support local auditability without uploading checkpoint files.

| Model | File | SHA256 |
| --- | --- | --- |
| Gemma4 | `README.md` | `999d460e1e70bfbcb0b56048a8286f1350dd6e03f5e277a53af0780de2bec6eb` |
| Gemma4 | `config.json` | `f2dc6a64e3ae4fbcda3526de3fda5f5245a2fb12a64949db90510687fbcddce7` |
| Gemma4 | `generation_config.json` | `002fcdd119e744ae5863f4cf21455b8831d43a280ce7291fbc6ec54cb5f6b818` |
| Gemma4 | `tokenizer_config.json` | `992248b166c1d756631fb46c8757514cdfa6c25be2b84e0a6a03a971145db1a1` |
| Qwen2.5-VL | `README.md` | `1fa65dbb08bc9ffe0b020409c8686f08b23008c5a68554353305fd2de6f2b81e` |
| Qwen2.5-VL | `config.json` | `77d9ec7321cc572e3579e2c84799c9cadaded63c49ce93b101733349fc330c43` |
| Qwen2.5-VL | `generation_config.json` | `0a3aea82869fe29f20dc95ccf3e2bcff380eca1f5ad6447a4a4b37110b08e43e` |
| Qwen2.5-VL | `tokenizer_config.json` | `4abd3520120e266da84c0864fee064d1fb10806f02225911a47253dd38dc5f56` |

## Public Source Links

- Gemma4 Unsloth model card/API:
  `https://huggingface.co/unsloth/gemma-4-E4B-it-unsloth-bnb-4bit`
- Qwen2.5-VL model card/API:
  `https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct`
- InteriorAgent dataset card:
  `https://huggingface.co/datasets/spatialverse/InteriorAgent`
- InteriorAgent terms PDF:
  `https://kloudsim-usa-cos.kujiale.com/InteriorAgent/InteriorAgent_Terms_of_Use.pdf`
- GRScenes dataset metadata:
  `https://huggingface.co/datasets/InternRobotics/GRScenes`

## Still Human-Gated

- Final venue policy: Annual ACL 2027 public CFP/author kit was not available
  in the latest local readiness check. Re-check the exact target call before
  upload.
- Final OpenReview form: copy the checklist answers into the official form and
  refresh page anchors after the final PDF build.
- Final author/legal review: confirm whether any scene-derived images or videos
  beyond those embedded in the manuscript PDF are allowed under the relevant
  asset terms. The staging script keeps optional media out by default.
- Final author confirmation: verify the checked local compute host/runtime is
  the intended experiment host for the submitted numbers.

## Local Evidence Anchors

- `paper/shared/evidence/raw/grscene_vlm_grounding/`
- `paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/`
- `paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/`
- `paper/shared/evidence/raw/material_effect_baseline/`
- `paper/venues/acl27/ARTIFACT_PROVENANCE_DRAFT.md`
- `paper/venues/acl27/COMPUTE_RUNTIME_SUMMARY_DRAFT.md`
- `paper/venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`
- `paper/venues/acl27/FINAL_SUBMISSION_PACKET_CHECKLIST.md`
