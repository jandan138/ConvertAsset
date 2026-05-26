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
| ARR Dates and Venues | https://aclrollingreview.org/dates | Current ARR cycle dates and participating venues; lists EACL 2027 with final ARR submission date August 3, 2026 and commitment date October 11, 2026. |
| EACL 2027 official site | https://2027.eacl.org/ | Confirms EACL 2027 is public, Athens, March 9-14, 2027, and has an ARR deadline of August 3, 2026; it is not Annual ACL 2027. |
| EACL 2027 main-paper call | https://2027.eacl.org/calls/papers/ | Confirms the EACL 2027 main-paper route and deadline while noting that the comprehensive CFP and detailed timetable are still being finalized. |
| GRUtopia package/project pages | https://pypi.org/project/grutopia/ and https://github.com/InternRobotics/InternUtopia | Public source/license context for GRUtopia/GRScenes. |
| InternNav repository | https://github.com/InternRobotics/InternNav | Public source/license context for InternNav/InternData-N1. |
| Gemma4 Unsloth model card/API | https://huggingface.co/unsloth/gemma-4-E4B-it-unsloth-bnb-4bit | Public source/license context for the primary Gemma4 VLM; checked revision `9746c23553347b443ebdc1caba1d41b52223d0c8`. |
| Qwen2.5-VL-7B-Instruct model card | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct | Public source/license context for Qwen diagnostic model. |
| InteriorAgent dataset card and terms | https://huggingface.co/datasets/spatialverse/InteriorAgent | Public source/terms context for the official KuJiaLe scenes used in the 99-episode downstream sanity run. |

Public search on 2026-05-26 found generic ACLPUB and ARR policy pages and now
confirms EACL 2027 as a concrete public 2027 ACL-family ARR route. Public search
still did not find an official Annual ACL 2027 CFP, author kit, city/date page,
or commitment deadline. Therefore this wrapper is ACL/ARR-candidate ready and
EACL-2027-route plausible, but not Annual-ACL-2027-final ready.

Latest refresh on 2026-05-26 reopened the policy-critical pages after the
pre-upload runner and evidence-number checker were added. ARR Dates still lists
EACL 2027 with final ARR submission date August 3, 2026 and commitment date
October 11, 2026; the EACL main-paper page still lists August 3, 2026 AoE while
stating that the full CFP and detailed timetable are forthcoming. ACLPUB still
states the generic 8-content-page long-paper review budget plus unlimited
references, and ARR common-submission guidance still leaves author order,
OpenReview profiles, and reviewer-registration confirmation as human gates.

## Current Manuscript State

| Gate | Evidence | Status |
| --- | --- | --- |
| ACL-specific scientific story | `main.tex` inputs `./sections/abstract`, `intro`, `related`, `method`, `results`, `discussion`, `conclusion`, `limitations`, and `ethical-considerations`. | Pass |
| Anonymous review wrapper | `main.tex` uses `\author{Anonymous ACL 2027 Submission}` and no acknowledgments section. | Pass for local review draft |
| Limitations section present | `sections/limitations.tex`; PDF text places `Limitations` after conclusion and before references. | Pass |
| Ethical considerations present | `sections/ethical-considerations.tex`; PDF text places it before references. | Pass |
| Abstract length | `OPENREVIEW_METADATA_PACKET.md` and `sections/abstract.tex`; current plain-text abstract is 189 words by the repository's conservative tokenizer. | Pass under ACLPUB 200-word guidance |
| Page size | `pdfinfo paper/venues/acl27/build/main.pdf` reports A4 `595.276 x 841.89 pts`. | Pass |
| Review long-paper page budget | Latest build is 11 PDF pages total; main content ends at conclusion on page 7, limitations begins on page 7, references begin on page 8. Generic ACLPUB long-paper review limit is 8 content pages excluding references, limitations, and ethical considerations. | Pass for generic ARR/ACLPUB long paper |
| Bibliography resolution | Latest `make -C paper clean-acl27 && make -C paper acl27` resolves citations and writes `build/main.pdf`. | Pass |
| Claim boundary | `CLAIM_AUDIT.md` forbids broad embodied benchmark, speedup, NVIDIA official-scene performance, and population NVIDIA failure-rate claims. | Pass |
| Citation context / data integrity delta | `FINAL_INTEGRITY_DELTA_AUDIT.md` checks all current citation-bearing sentences, main numerical claims, forbidden-claim search results, and sampled exact-phrase originality searches. | Pass for current source; rerun after any manuscript, bibliography, target, or packet change |
| Automated evidence-number consistency | `scripts/check_evidence_numbers.py` recomputes the ACL-facing proxy, GRScenes VLM, InternNav, official-scene, and coordinate-baseline numbers from local CSV/JSON evidence and checks manuscript/OpenReview markers. | Pass for current source; included in `run_preupload_gate.py` |
| Supplement self-contained status | Main paper contains the core evidence and scope boundaries; appendices/supplement add detail. `FINAL_SUBMISSION_PACKET_CHECKLIST.md` defines the upload boundary and `SUBMISSION_STAGING_AUDIT.md` records the first minimal PDF-first staging smoke. | Candidate staging smoke pass; final human read and any archive/media scan still required |
| Official Annual ACL 2027 policy | No public Annual ACL 2027 CFP/author kit found in checked sources. | External blocker |
| EACL 2027 route | Official EACL 2027 site and ARR Dates page list August 3, 2026 as the ARR paper deadline; EACL page says the complete CFP is still forthcoming. | Concrete public route exists; final venue-specific upload wording still pending |

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
| Non-anonymous repository/service links in supplement | The ignored local packet `paper/submissions/acl27_arr_candidate_20260526/` was assembled by `stage_submission_packet.py` and scanned; no local path, username, private-repo, or acknowledgment matches were found in the staged directory. | Low risk for the minimal PDF-first packet; re-run before upload and after any media/source additions |
| Responsible NLP checklist weak answers | `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md` now provides copy-ready answers with current PDF section/page anchors and remaining human gates. | Lower risk; final OpenReview copy, target-call wording, and author/legal confirmation for optional media still required |
| OpenReview metadata drift | `OPENREVIEW_METADATA_PACKET.md` now provides title, abstract, ARR area, and keyword copy source; staging copies it to `openreview/METADATA.md`. | Lower risk; re-check after PDF or target change |
| Reference permanent identifiers | `CITATION_PROVENANCE_AUDIT.md` now records DOI/URL metadata for all 20 currently cited ACL-wrapper keys. | Low risk, with final proceedings metadata check |
| Annual ACL 2027 official details | Public Annual ACL 2027 CFP/site not found. | External blocker if the authors insist on Annual ACL 2027 |
| EACL 2027 official details | EACL 2027 site and ARR dates are public, but the full CFP is still forthcoming. | Lower risk if authors accept EACL 2027 as the active target |

## Draft Responsible NLP Checklist Map

This is not a completed OpenReview form. It is a section map for the eventual
ARR checklist.

| Checklist item | Draft answer | Evidence location |
| --- | --- | --- |
| A1 limitations | Yes | `Limitations` section |
| A2 potential risks | Yes | `Ethical Considerations`, `Limitations` |
| A3 abstract/introduction summarize claims | Yes | `Abstract`, `Introduction`, `CLAIM_AUDIT.md` |
| B scientific artifacts used/created | Yes | GRScenes/GRUtopia, InternNav/DualVLN, Isaac/UsdPreviewSurface evidence described in `Related Work`, `Method`, `Results`; raw evidence under `paper/shared/evidence/` |
| B1 cite artifact creators | Yes, with final wording review | Manuscript cites GRUtopia/GRScenes and InternNav/DualVLN; `CITATION_PROVENANCE_AUDIT.md` and `MODEL_AND_ASSET_LICENSE_AUDIT.md` track model-card and InteriorAgent/KuJiaLe cleanup. |
| B2 licenses / terms | Mostly complete | `Ethical Considerations` notes license compatibility; `ARTIFACT_PROVENANCE_DRAFT.md` and `MODEL_AND_ASSET_LICENSE_AUDIT.md` record public model IDs/licenses, GRScenes terms, and InteriorAgent no-optional-media upload boundary. |
| B3 intended use | Yes, with final license confirmation | `Method`, `Results`, `Limitations`, and `ARTIFACT_PROVENANCE_DRAFT.md` define research/evaluation use and claim boundaries. |
| B4 personally identifying/offensive content | Likely N/A / needs justification | Current work uses synthetic 3D assets and VLM/InternNav outputs, not human-subject text. Final checklist should justify this. |
| B5 artifact documentation | Partially yes | Evidence manifests and docs exist, but final paper/supplement should expose the artifact inventory clearly. |
| B6 data statistics/splits | Yes for main evidence | Results tables report GRScenes 15/30 and InternNav 99; supplement contains manifests. |
| C computational experiments | Yes | VLM probes, image metrics, material baselines, InternNav sanity runs. |
| C1 compute budget/infrastructure | Mostly complete | Run manifests record commands/backends, and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` now gives the concise GPU/Isaac/VLM/runtime summary plus public Gemma4/Qwen IDs. Final checklist needs author confirmation of the checked host/runtime. |
| C2 setup/hyperparameters | Partially yes | Method, experiment manifests, and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` cover protocols, prompt coordinate frame, structured output, `max_new_tokens=64`, and Qwen eager attention. Final appendix should summarize renderer settings and checkpoint hashes. |
| C3 descriptive statistics | Yes for main claims | Results tables include counts, paired means, and closure CIs. |
| C4 packages/implementation settings | Mostly yes | Repo scripts and manifests exist, and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` now summarizes checked Isaac/Gemma4/Qwen/InternNav versions and public VLM identifiers. Local paths and checkpoints remain excluded from upload. |
| D human annotators/subjects | No | No human subjects or crowdworker annotations were used in the current evidence package. Visual QA was internal protocol evidence, not a human-subject study. |
| E AI assistants | Yes | This project used AI coding/writing assistance; final checklist or acknowledgments-after-acceptance should disclose according to ACL policy. |

## Remaining Before Submission

1. Lock the target route: either wait for Annual ACL 2027's official CFP/author
   kit, or retarget the current ACL/ARR candidate packet to the currently public
   EACL 2027 ARR route after the complete EACL CFP appears.
2. Keep optional InteriorAgent/KuJiaLe scene-derived media out of the packet
   unless authors approve a separate terms/anonymization path.
3. Copy the `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md` answers into the official
   OpenReview form after one final PDF rebuild and target-call check.
4. Re-check bibliography permanent identifiers and rerun
   `FINAL_INTEGRITY_DELTA_AUDIT.md` after any new citations, manuscript edits,
   target changes, or packet changes; current ACL-wrapper citations now have
   DOI or URL metadata and current-source citation/data checks.
5. Re-run the consolidated `run_preupload_gate.py` immediately before upload,
   especially if any source, bibliography, checklist, evidence table, or
   supplemental media changes are made after the 2026-05-26 staging smoke.
