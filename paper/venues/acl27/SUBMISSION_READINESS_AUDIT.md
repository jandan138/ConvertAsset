# ACL/ARR Submission Readiness Audit

Checked: 2026-05-26.

This file tracks whether the ACL-facing wrapper is ready for an ARR or
ACL-family submission. It uses the current `paper/venues/acl27/` manuscript as
the source of truth and treats public ACL/ARR pages as external policy inputs.

## Official Sources Checked

| Source | URL | Current relevance |
| --- | --- | --- |
| ARR Authors Guidelines | https://aclrollingreview.org/authors | ARR submission flow, two-month cycles, formatting/template requirement, OpenReview submission, no concurrent archival review, reviewer-registration duty. |
| ARR CFP | https://aclrollingreview.org/cfp | Scope, dual-submission/resubmission, ethics and Responsible NLP checklist requirements. |
| ARR Common Submission Problems | https://aclrollingreview.org/authorchecklist | Desk-rejection risks: page limits, required Limitations section, optional Ethical Considerations placement, anonymity, no acknowledgments in review version, no non-anonymous links, reviewer registration. |
| ACLPUB Formatting Guidelines | https://acl-org.github.io/ACLPUB/formatting.html | Generic ACL formatting, A4, 8-page long / 4-page short review limits, appendix/supplement policy, DOI/ACL Anthology reference guidance. |
| ACLPUB Detailed Style Guide | https://acl-org.github.io/ACLPUB/style.html | Detailed publication-chair formatting checks. |
| ARR Responsible NLP Checklist PDF | https://aclrollingreview.org/static/responsibleNLPresearch.pdf | Checklist questions and requirement to provide section numbers or justifications. |
| ARR checklist-as-appendix update | https://aclrollingreview.org/responsible-nlp-checklist-appendices | Accepted *ACL papers should expect public checklist appendices. |
| EACL 2027 official site | https://2027.eacl.org/ | Confirms EACL 2027 is public and has an ARR deadline; it is not Annual ACL 2027. |
| GRUtopia package/project pages | https://pypi.org/project/grutopia/ and https://github.com/InternRobotics/InternUtopia | Public source/license context for GRUtopia/GRScenes. |
| InternNav repository | https://github.com/InternRobotics/InternNav | Public source/license context for InternNav/InternData-N1. |
| Qwen2.5-VL-7B-Instruct model card | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct | Public source/license context for Qwen diagnostic model. |

Public search on 2026-05-26 found EACL 2027, generic ACLPUB, and ARR policy
pages, but did not find an official public Annual ACL 2027 CFP, author kit,
city/date page, or commitment deadline. Therefore this wrapper is
ACL/ARR-candidate ready, not yet Annual-ACL-2027-final ready.

## Current Manuscript State

| Gate | Evidence | Status |
| --- | --- | --- |
| ACL-specific scientific story | `main.tex` inputs `./sections/abstract`, `intro`, `related`, `method`, `results`, `discussion`, `conclusion`, `limitations`, and `ethical-considerations`. | Pass |
| Anonymous review wrapper | `main.tex` uses `\author{Anonymous ACL 2027 Submission}` and no acknowledgments section. | Pass for local review draft |
| Limitations section present | `sections/limitations.tex`; PDF text places `Limitations` after conclusion and before references. | Pass |
| Ethical considerations present | `sections/ethical-considerations.tex`; PDF text places it before references. | Pass |
| Page size | `pdfinfo paper/venues/acl27/build/main.pdf` reports A4 `595.276 x 841.89 pts`. | Pass |
| Review long-paper page budget | Latest build is 11 PDF pages total; main content ends at conclusion on page 7, limitations begins on page 7, references begin on page 8. Generic ACLPUB long-paper review limit is 8 content pages excluding references, limitations, and ethical considerations. | Pass for generic ARR/ACLPUB long paper |
| Bibliography resolution | Latest `make -C paper clean-acl27 && make -C paper acl27` resolves citations and writes `build/main.pdf`. | Pass |
| Claim boundary | `CLAIM_AUDIT.md` forbids broad embodied benchmark, speedup, NVIDIA official-scene performance, and population NVIDIA failure-rate claims. | Pass |
| Supplement self-contained status | Main paper contains the core evidence and scope boundaries; appendices/supplement add detail. `FINAL_SUBMISSION_PACKET_CHECKLIST.md` now defines the upload boundary. | Needs final human read and archive scan |
| Official Annual ACL 2027 policy | No public Annual ACL 2027 CFP/author kit found in checked sources. | External blocker |

## ARR Desk-Rejection Risk Checklist

| Risk | Local check | Status / action |
| --- | --- | --- |
| Out of ARR scope | The story now emphasizes VLM grounding, vision-language navigation, and embodied-data reliability. | Low risk, but final title/abstract should keep the computational-language contribution explicit. |
| Over page limit | Current generic long-paper content is within 8 pages before references. | Low risk until final venue-specific call is published. |
| Missing Limitations | Present and titled exactly `Limitations`. | Low risk |
| Limitations contains new experiments | Current section summarizes limits and does not introduce new figures/tables. | Low risk |
| Ethical considerations placement | Present before references. | Low risk |
| Acknowledgments in review PDF | No acknowledgments section in `main.tex` or sections. | Low risk |
| Author-identifying links | No `http://` or `https://` links found in `main.tex`, ACL sections, or shared appendix text. | Low risk |
| Non-anonymous repository/service links in supplement | `FINAL_SUBMISSION_PACKET_CHECKLIST.md` defines required `rg` scans, but no concrete upload archive has been assembled and scanned yet. | Follow-up |
| Responsible NLP checklist weak answers | Draft section mapping and compute/runtime summary now exist, but final OpenReview/checklist fields still need human completion and section/page/line references. | Follow-up |
| Reference permanent identifiers | `CITATION_PROVENANCE_AUDIT.md` now records DOI/URL metadata for all 20 currently cited ACL-wrapper keys. | Low risk, with final proceedings metadata check |
| Annual ACL 2027 official details | Public Annual ACL 2027 CFP/site not found. | External blocker |

## Draft Responsible NLP Checklist Map

This is not a completed OpenReview form. It is a section map for the eventual
ARR checklist.

| Checklist item | Draft answer | Evidence location |
| --- | --- | --- |
| A1 limitations | Yes | `Limitations` section |
| A2 potential risks | Yes | `Ethical Considerations`, `Limitations` |
| A3 abstract/introduction summarize claims | Yes | `Abstract`, `Introduction`, `CLAIM_AUDIT.md` |
| B scientific artifacts used/created | Yes | GRScenes/GRUtopia, InternNav/DualVLN, Isaac/UsdPreviewSurface evidence described in `Related Work`, `Method`, `Results`; raw evidence under `paper/shared/evidence/` |
| B1 cite artifact creators | Yes, with final dataset/model cleanup | Manuscript cites GRUtopia/GRScenes and InternNav/DualVLN; `CITATION_PROVENANCE_AUDIT.md` tracks remaining InteriorAgent/KuJiaLe and model-card cleanup. |
| B2 licenses / terms | Partially complete | `Ethical Considerations` notes license compatibility; `ARTIFACT_PROVENANCE_DRAFT.md` records current public license context and flags remaining final checks. |
| B3 intended use | Yes, with final license confirmation | `Method`, `Results`, `Limitations`, and `ARTIFACT_PROVENANCE_DRAFT.md` define research/evaluation use and claim boundaries. |
| B4 personally identifying/offensive content | Likely N/A / needs justification | Current work uses synthetic 3D assets and VLM/InternNav outputs, not human-subject text. Final checklist should justify this. |
| B5 artifact documentation | Partially yes | Evidence manifests and docs exist, but final paper/supplement should expose the artifact inventory clearly. |
| B6 data statistics/splits | Yes for main evidence | Results tables report GRScenes 15/30 and InternNav 99; supplement contains manifests. |
| C computational experiments | Yes | VLM probes, image metrics, material baselines, InternNav sanity runs. |
| C1 compute budget/infrastructure | Partially complete | Run manifests record commands/backends, and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` now gives the concise GPU/Isaac/VLM/runtime summary. Final checklist needs author confirmation and public checkpoint IDs. |
| C2 setup/hyperparameters | Partially yes | Method, experiment manifests, and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` cover protocols, prompt coordinate frame, structured output, `max_new_tokens=64`, and Qwen eager attention. Final appendix should summarize renderer settings and checkpoint hashes. |
| C3 descriptive statistics | Yes for main claims | Results tables include counts, paired means, and closure CIs. |
| C4 packages/implementation settings | Partially yes | Repo scripts and manifests exist, and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` now summarizes checked Isaac/Gemma4/Qwen/InternNav versions. Final appendix should replace local paths with public model IDs and hashes. |
| D human annotators/subjects | No | No human subjects or crowdworker annotations were used in the current evidence package. Visual QA was internal protocol evidence, not a human-subject study. |
| E AI assistants | Yes | This project used AI coding/writing assistance; final checklist or acknowledgments-after-acceptance should disclose according to ACL policy. |

## Remaining Before Submission

1. Re-check the final target call once Annual ACL 2027 or the selected
   ACL-family venue publishes its official CFP, author kit, commitment deadline,
   and supplemental policy.
2. Complete the artifact-license/source audit for GRScenes/GRUtopia,
   InteriorAgent/KuJiaLe, InternNav/DualVLN, Isaac Sim, VLM APIs/models, and any
   generated qualitative videos.
3. Fill the Responsible NLP checklist with section numbers and justifications,
   using `RESPONSIBLE_NLP_CHECKLIST_DRAFT.md` as the starting point.
4. Re-check bibliography permanent identifiers after any new citations are
   added; current ACL-wrapper citations now have DOI or URL metadata.
5. Assemble a concrete upload staging directory and run the anonymization scans
   in `FINAL_SUBMISSION_PACKET_CHECKLIST.md` over the PDF, supplemental paths,
   metadata, and any archive packaged for upload.
