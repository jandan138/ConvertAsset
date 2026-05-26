# ARR Responsible NLP Checklist Draft

Checked: 2026-05-26.

This file is a draft response map for the ARR Responsible NLP Research
Checklist. It is not a replacement for the OpenReview form. Final submission
still requires the authors to copy the answers into the official checklist and
replace section-title references with final section/page/line references.

For the current ACL-facing PDF, use
`OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md` as the copy-ready OpenReview form
source. It adds current PDF page anchors, source-section line anchors, and the
remaining human gates for selected-venue policy, final OpenReview copy,
author/runtime confirmation, and optional media redistribution.

## A. For Every Submission

| Item | Draft answer | Section / justification |
| --- | --- | --- |
| A1. Did you discuss the limitations of your work? | Yes | `Limitations` discusses narrow evidence scope, clean-pool gate status, stress-set scope, Qwen coordinate sensitivity, material-effect boundaries, selected-video status, and official-scene load/render limits. |
| A2. Did you discuss potential risks of your work? | Yes | `Ethical Considerations` discusses synthetic-scene bias, licensing constraints, unsafe deployment assumptions, misleading downstream-robustness claims, and failure cases where material simplification changes semantic grounding signals. |
| A3. Do the abstract and introduction summarize the paper's main claims? | Yes | `Abstract` and `Introduction` state the paper's bounded claim: material conversion is a measurable perturbation for VLM grounding and embodied-data evaluation, not a broad robustness or speedup result. See also `CLAIM_AUDIT.md`. |

## B. Scientific Artifacts

The work uses and creates scientific artifacts.

| Item | Draft answer | Section / justification |
| --- | --- | --- |
| B1. Did you cite the creators of artifacts you used? | Yes, with final citation wording still author-reviewed | `Related Work` cites GRUtopia/GRScenes, InternNav/DualVLN, Habitat, AI2-THOR, TDW, Isaac/Orbit/Isaac Lab, CLIP, DINOv2, Shikra, Ferret, and related synthetic-data systems. `CITATION_PROVENANCE_AUDIT.md` and `MODEL_AND_ASSET_LICENSE_AUDIT.md` record model/provider and InteriorAgent/KuJiaLe provenance cleanup. |
| B2. Did you discuss license or terms for use/distribution? | Mostly complete, with final author/legal review | `Ethical Considerations` requires asset-provenance and license compatibility. `ARTIFACT_PROVENANCE_DRAFT.md` and `MODEL_AND_ASSET_LICENSE_AUDIT.md` record current public terms: GRScenes is CC BY-NC-SA 4.0; InternNav code is MIT; InternData-N1 is CC BY-NC-SA 4.0; InteriorAgent uses custom terms that prohibit data/modified-data redistribution; Qwen2.5-VL-7B-Instruct and the checked Unsloth Gemma4 model metadata report Apache-2.0. Final upload must not redistribute restricted assets or optional selected media unless terms allow it. |
| B3. Did you discuss intended use and compatibility with original access conditions? | Yes, needs final license confirmation | `Method`, `Results`, `Limitations`, and `Ethical Considerations` restrict use to research/evaluation of material-conversion reliability. The paper does not claim commercial deployment, model training at scale, or unrestricted redistribution of source assets. |
| B4. Did you check whether used data contains identifying or offensive content and protect/anonymize it? | N/A with justification | The current evidence uses synthetic 3D scenes, VLM model outputs, and InternNav trajectory metrics, not human-subject text or crowdworker data. Some scene assets may encode synthetic household/object semantics, so the paper flags dataset bias and license risks in `Ethical Considerations`; final supplement should avoid local user paths and non-anonymous URLs. |
| B5. Did you provide artifact documentation? | Yes, with final supplement packaging pending | `paper/shared/evidence/raw/*/README.md`, experiment manifests, `CLAIM_AUDIT.md`, and `ARTIFACT_PROVENANCE_DRAFT.md` document evidence scope, counts, source paths, conversion commands, and claim boundaries. |
| B6. Did you report relevant statistics and splits? | Yes | `Results` reports GRScenes clean 15-pair pilot, GRScenes expanded30 stress set, material-effect sample counts, 99 official KuJiaLe paired episodes, and official-scene load/render run counts. Raw manifests are under `paper/shared/evidence/`. |

## C. Computational Experiments

The work runs computational experiments.

| Item | Draft answer | Section / justification |
| --- | --- | --- |
| C1. Did you report model parameters, compute budget, and infrastructure? | Mostly complete with final author confirmation pending | The repository records local VLM backends and Isaac/InternNav run manifests. `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` now summarizes GPU, Isaac Sim, VLM environment, official-scene runtime evidence, and public model IDs/revisions for Gemma4 and Qwen2.5-VL; final checklist still needs author confirmation that the checked host/runtime matches the submitted runs. |
| C2. Did you discuss experimental setup and hyperparameters? | Partially complete with draft summary | `Method`, `Results`, raw manifests, and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` specify original/noMDL conditions, frozen render/projection manifests, normalized-1000 prompt contract, structured-text VLM output, `max_new_tokens=64`, Qwen eager attention, selected material-effect bins, and official KuJiaLe episode splits. Final appendix should consolidate renderer settings and any checkpoint hashes. |
| C3. Did you report descriptive statistics and clarify max/mean/single-run status? | Yes | `Results` and shared tables report paired counts, means, stress-set hit counts, paired bootstrap CIs, and 18/18 load/render closure runs. Selected videos are explicitly qualitative only. |
| C4. Did you report packages/implementation/settings used? | Mostly complete with final form copy pending | The repository provides scripts under `paper/shared/evidence/experiments/`, ConvertAsset code, run manifests, and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` package/version probes for Isaac, Gemma4, Qwen2.5-VL, and InternNav. Public model IDs/revisions are now recorded; final upload should still exclude local paths and checkpoints. |

## D. Human Annotators Or Subjects

| Item | Draft answer | Section / justification |
| --- | --- | --- |
| D. Did you use human annotators or human subjects? | No | No human-subject study or crowdworker annotation is part of the current evidence package. Visual QA is an internal engineering/author audit over rendered synthetic images, not a human-subject experiment. |
| D1-D5 | N/A | No participants were recruited, paid, instructed, or demographically characterized. No IRB/ethics-board protocol is required for the current synthetic-asset and computational-evaluation evidence as framed. |

## E. AI Assistants

| Item | Draft answer | Section / justification |
| --- | --- | --- |
| E. Did you use AI assistants in research, coding, or writing? | Yes | Codex/Claude-style coding and writing assistance was used for code/documentation/manuscript iteration and audit drafting. |
| E1. Did you include information about AI assistant use? | Draft needed in final submission | For anonymous review, disclose in the ARR checklist field and, if accepted, in acknowledgments or the required public checklist according to the final venue policy. Suggested wording: "We used AI coding and writing assistants for implementation support, documentation organization, and manuscript editing. All claims, citations, experiments, and generated text were checked by the authors against repository evidence and cited sources; the assistants were not credited as authors." |

## Finalization Notes

Before upload, replace this draft with the official checklist form answers and
add exact section/page/line references from the final PDF. Use
`FINAL_SUBMISSION_PACKET_CHECKLIST.md` for the upload-boundary and anonymization
gate. Do not answer with bare yes/no strings; ARR guidance expects section
numbers or justifications.
