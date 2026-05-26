# ACL 2027 Version Status

Template provenance: ACL 2027 conference-specific files are not published in this repo. The wrapper now vendors the generic official *ACL style files `acl.sty` and `acl_natbib.bst` from `acl-org/acl-style-files` so local compile checks can run until the ACL 2027 author kit or conference-specific instructions are published. Provenance checked on 2026-05-23: ACLPUB's formatting page points authors to `https://github.com/acl-org/acl-style-files`.

Readiness: candidate-target scaffold for the user-requested Annual ACL 2027 Japan route.

Local section overrides: `sections/abstract.tex`, `sections/intro.tex`,
`sections/related.tex`, `sections/method.tex`, `sections/results.tex`,
`sections/discussion.tex`, and `sections/conclusion.tex` now reframe the shared
evidence around VLM grounding protocol reliability and embodied-data reliability
under 3D material perturbations. The ACL wrapper still uses shared evidence,
tables, figures, bibliography, and appendix assets, but no longer inputs the
shared related/method/experiments/discussion sections directly.

Known missing checks: official Annual ACL 2027 CFP, official city/date
confirmation in a public Annual ACL 2027 site, Annual ACL 2027 submission
deadline, final Annual ACL page-limit policy, Annual ACL Responsible NLP
Checklist requirements, Annual ACL anonymity policy, Annual ACL AI-use
disclosure policy, and final DOI/ACL Anthology citation audit. EACL 2027 is now
a public alternative ACL-family route with an ARR deadline, but its complete CFP
is still forthcoming.

Venue fit: the current ACL wrapper has pivoted away from a pure
synthetic-data/simulation-tool paper. The active story is now multimodal
language grounding reliability and embodied-data reliability under material
conversion. AAAI remains a possible broader AI/simulation route, but the ACL
version should be judged by whether the VLM/grounding framing and related work
are convincing, not by whether it proves broad embodied benchmark robustness.

Selected ACL experiment route: use the original GRScenes-100 benchmark package under `/cpfs/user/zhuzihou/assets/zzh-grscenes` with ConvertAsset's MDL-to-UsdPreviewSurface intervention, then evaluate PIO-style VLM grounding prompts over matched original/converted renders. The first episode-backed pilot should sample from the 30 home scenes covered by `mm_episodes.json` / `sn_episodes.json`; commercial scenes are metadata-driven stress tests unless a future episode source is added, and the full 99-scene pool is a later expansion target. ACL claims must cite the official GRUtopia/GRScenes and InternNav/DualVLN sources; the restored test0 mirror is only an engineering validation dataset. Treat InternNav / VL-LN as the downstream navigation extension after the grounding pilot is reproducible. See `../../shared/evidence/references/acl_vlm_benchmark_selection.md` and `../../shared/evidence/experiments/06_grscenes_vlm_grounding/`.

Asset layout update on 2026-05-25: ConvertAsset external research assets now
use `/cpfs/user/zhuzihou/assets/convertasset_research` as the canonical root.
The old `/cpfs/user/zhuzihou/assets/zzh-grscenes`,
`internnav_official_*`, `internnav_vln_downstream_work_*`, and runtime-deps
paths are retained as symlinks for historical manifests. New InternNav official
`val_unseen` expansion runs should write under
`/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_val_unseen_20260525`.
See `../../../docs/operations/research-asset-layout.md` and
`../../../docs/records/2026-05-25-research-asset-layout-normalization.md`.

Current experiment state on 2026-05-23: source selection, target localization, paired render planning, full scratch no-MDL conversion, render-smoke execution, projection QA, blind visual QA, and real-model VLM probes are implemented. `source_manifest.json` fixes 5 episode-backed home scenes, 5 commercial stress scenes, and 40 selected episode records. `target_manifest.json` resolves all 40 selected episode-backed records to USD prim paths and world-space bboxes using original GRScenes scene USDs read-only; these records collapse to 23 unique spatial targets because some `mm` and `sn` episodes refer to the same object. `render_manifest.json` plans 4 target-centered views per unique target, giving 92 original/converted view pairs and 184 material-condition render jobs. The scratch no-MDL route has converted 99 top-level raw scenes and verification records `passed=true`, while the original `/cpfs/user/zhuzihou/assets/zzh-grscenes` source tree remains free of `_noMDL` sidecar pollution.

GRScenes VLM evidence now has one frozen expanded stress set and one pilot clean branch. The clean branch has a 15-pair visual-QA PASS pool under `../../shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/`: Gemma4 structured-text over 15 original/converted pairs produced 30/30 parsed rows, answer accuracy 15/15 original and 15/15 converted, normalized-1000 point-in-bbox 8/15 original and 6/15 converted, normalized-1000 pair hit agreement 11/15, and 5/15 both-hit pairs. The matching Qwen2.5-VL structured-text run produced 30 parsed rows but only 23/30 scorable answer strings, answer accuracy 8/11 original and 9/12 converted, raw point-in-bbox 5/14 original and 5/15 converted, and normalized-1000 point-in-bbox 0/14 original and 0/15 converted. This branch remains below the clean final gate.

The material-shift stress set now uses `../../shared/evidence/raw/grscene_vlm_grounding/stress_vlm_run_manifest_expanded30.json`: 30 target-visible PASS/WARN zoom pairs, 60 scoring records, and matched Gemma4/Qwen metadata hashes against the same manifest file. This is a frozen target-centered stress set, not a broad GRScenes distribution. The canonical Gemma4 root files are `stress_predictions.jsonl` and `stress_score_summary.json`: answer accuracy is 30/30 original and 30/30 converted, normalized-1000 point hits are 27/30 original and 29/30 converted, normalized-1000 hit-status agreement is 28/30, and both-hit pairs are 27/30. The matching Qwen2.5-VL expanded30 diagnostic under `stress_expanded30_probes/` has 55/60 scorable answer rows, answer hits 27/29 original and 24/26 converted, raw point hits 22/29 original and 19/29 converted, and normalized-1000 point hits 3/29 for both material conditions. The old 14-pair `zoom_stress_probes/` remain pilot/protocol history, not root canonical evidence. The shared manuscript now includes the expanded30 stress table and an updated qualitative grounding-case figure.

CVPR workshop reviewer carry-over status on 2026-05-26: the expanded30 VLM grounding route addresses the most dangerous "proxy-only AI task" weakness at the image-level grounding layer, and the official KuJiaLe `val_unseen` route now adds scoped InternNav downstream sanity evidence over 99 paired episodes. This still does not mean manipulation, broad GRScenes embodied validation, or all-scene downstream robustness has been introduced. Reviewer concerns about overbroad guidelines have been addressed by narrowing the claim to frozen evidence pools. NVIDIA official-tool baseline and per-MDL-effect analysis are represented by the material-effect condition manifests, selected qualitative/failure panels, PXR diagnostic, and risk matrix in the shared manuscript: four GRScenes-covered bins have bounded selected qualitative support, clearcoat is a selected NVIDIA target-loss failure case, and procedural texture is a preservation limitation. The reviewer-closure package now adds paired bootstrap CIs, coordinate-only VLM baselines, and a rule-based safe-conversion table. The official-scene submission-closure package adds multi-scene/multi-run original/noMDL load-render statistics across the 0031/0036/0066 KuJiaLe scenes: 18/18 required runs succeeded, with overlapping original/noMDL ready-time intervals. A learned automatic recommender and NVIDIA official-scene performance baseline remain open.

Near-term ACL target: the defensible ACL/ARR draft presents the current work as
a VLM grounding reliability diagnostic under 3D material perturbations plus
scoped official InternNav downstream sanity evidence, not as a completed
embodied benchmark paper. The official-scene closure pass now has performance,
video, and claim-audit gates closed for original/noMDL official KuJiaLe scenes;
its allowed claim is loadability/stability with overlapping ready-time
intervals, not speedup. The ACL wrapper now includes local related work,
method, results, and discussion sections. Remaining ACL-main work is final
venue/citation integrity against the chosen public call and any optional NVIDIA
official-scene conversion/smoke gate if a three-way official-scene performance
comparison is desired. A learned material-risk classifier remains future work
unless the submission claims automatic risk prediction beyond the current rule
table.

ACL/ARR closure update on 2026-05-26: the ACL manuscript wrapper now has an
explicit claim audit in `CLAIM_AUDIT.md`. Current public source check found the
generic official ACL style files at `acl-org/acl-style-files` and the ACLPUB
style guide. A later target-call check found EACL 2027's official site and
main-paper call page with an August 3, 2026 ARR deadline, while Annual ACL 2027
still has no public official CFP/site in checked sources. Treat the wrapper as
an ACL/ARR candidate until the authors choose EACL 2027 or the official Annual
ACL 2027 call, page limits, checklist, and author kit are public.

Submission-readiness audit update on 2026-05-26: `SUBMISSION_READINESS_AUDIT.md`
now maps the current wrapper against public ARR/ACLPUB policy sources, and
`CITATION_PROVENANCE_AUDIT.md` lists all 20 ACL-wrapper citation keys plus the
remaining DOI/URL/provenance gaps. The local ACL PDF is compatible with the
generic long-paper budget in this check, but the goal is not complete until the
final target call is public and the citation/provenance and Responsible NLP
checklist gaps are closed.

Citation/provenance closure update on 2026-05-26: all 20 current ACL-wrapper
citation keys now carry DOI and/or URL metadata in `paper/shared/references.bib`.
`RESPONSIBLE_NLP_CHECKLIST_DRAFT.md` and `ARTIFACT_PROVENANCE_DRAFT.md` provide
the first upload-oriented checklist/provenance packet. The later
`MODEL_AND_ASSET_LICENSE_AUDIT.md` closes the Gemma4/Qwen public-ID gate and
turns InteriorAgent/KuJiaLe media redistribution into a no-optional-media safe
boundary. Remaining gaps are final target-call verification, final OpenReview
form copy, author/runtime confirmation, and any optional media legal approval.

Final-packet closure update on 2026-05-26: `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`
now records the checked local GPU, Isaac Sim/USD, Gemma4, Qwen2.5-VL, InternNav,
and official-scene runtime evidence for ARR C1/C2/C4 answers. `FINAL_SUBMISSION_PACKET_CHECKLIST.md`
defines the upload boundary and anonymization scans. The next large target is a
concrete ARR upload staging directory/archive plus final model/license/terms
confirmation, not more unbounded experiment collection.

Submission-staging smoke update on 2026-05-26:
`scripts/stage_submission_packet.py` now generates the ignored local candidate
packet `paper/submissions/acl27_arr_candidate_20260526/` from the built ACL PDF.
The smoke packet contains `main.pdf`, an OpenReview Responsible NLP checklist
copy source, `supplemental/README.md`, and `supplemental/manifest.json`;
selected videos and raw/scratch/model artifacts remain excluded.
`SUBMISSION_STAGING_AUDIT.md` records the first scan pass: the staged directory
had no local path, username, private-repo, or acknowledgment matches; `pdfinfo`
reported 11 A4 pages; `pdftotext` found the anonymous header, `Limitations`,
`Ethical Considerations`, and `References`. `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`
now gives copy-ready checklist answers with current PDF anchors. This closes
the minimal PDF/form-source staging gate, but not the final selected-venue
policy lock, final OpenReview form copy, author/runtime confirmation, or
optional media redistribution gates.

Model/asset license closure update on 2026-05-26:
`MODEL_AND_ASSET_LICENSE_AUDIT.md` now records the ACL-facing public provenance
closure. The primary Gemma4 VLM is pinned to
`unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` revision
`9746c23553347b443ebdc1caba1d41b52223d0c8`; the Qwen diagnostic VLM is pinned
to `Qwen/Qwen2.5-VL-7B-Instruct`, checked public `main` revision
`cc594898137f460bfe9f0759e9844b3ce807cfb5`. GRScenes metadata is recorded as
CC BY-NC-SA 4.0. InteriorAgent / KuJiaLe is no longer an unknown-terms gate:
the checked terms prohibit redistributing data or modified data, so the safe
ACL packet excludes optional selected scene-derived videos/media by default.
This closes the model-public-ID gate and converts the media question into a
clear author/legal decision rather than an experiment blocker.

Target-call policy update on 2026-05-26:
`TARGET_CALL_POLICY_AUDIT.md` now records the current venue lock state. Annual
ACL 2027 remains unavailable as a final public target in checked official
sources. EACL 2027 is public and ARR Dates lists it with final ARR submission
date August 3, 2026 and commitment date October 11, 2026; the EACL main-paper
call page still says the comprehensive CFP and detailed timetable are being
finalized. The practical next decision is whether to retarget to EACL 2027 via
ARR or wait for Annual ACL 2027.

Goal-completion audit update on 2026-05-26: `GOAL_COMPLETION_AUDIT.md` maps
the active ACL/ARR objective to concrete evidence and remaining gates. Verdict:
the package is candidate-ready for target lock and final submission rehearsal,
but it is not final-upload complete until the target route is locked, the
official OpenReview form is filled, author/runtime and optional media/legal
decisions are confirmed, a final citation/data integrity pass runs, and the
exact upload packet is rebuilt and anonymization-scanned. The next large goal
should therefore be target lock plus final integrity/upload gate, not more
unbounded experiment collection.

Reference web-trail update on 2026-05-26:
`paper/shared/evidence/references/verification_report.md` now contains a
20/20 ACL-wrapper reference-existence web-trail addendum. The pass also
normalized `paper/shared/references.bib` by adding the Synthetica IROS DOI,
Tobin and Tremblay proceedings pages, and the formal Springer ECCV DOI/pages
for Photo-realistic Neural Domain Randomization. This closes the current
fabricated-reference risk for the ACL wrapper, while final citation-context,
data-claim, and originality checks still remain part of the pre-upload
integrity gate.

InternNav/VL-LN bridge status on 2026-05-23: ConvertAsset now has a real
one-episode embodied downstream smoke run for scene
`MV7J6NIKTKJZ2AABAAAAADY8_usd`. The prep manifest is
`../../shared/evidence/raw/internnav_vln_downstream/prep_manifest.json`, the
paired result summary is
`../../shared/evidence/raw/internnav_vln_downstream/internnav_vln_results.json`,
and the external work root is
`/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_20260523`. Original
and no-MDL runs both executed through InternNav/InternVLA-N1 and both ended with
`exceed_total_max_step`, so `SR=0` and `SPL=0` for both. The material intervention
still changed the embodied trajectory: no-MDL increases `TL` from `64.7729` to
`98.2783` and `NE` from `8.3585` to `42.1053`. This upgrades InternNav from a
prepared extension to real protocol evidence and a failure-case seed, but it is
not broad ACL-main evidence until repeated over more scenes/episodes with
aggregate statistics.

InternNav main-result upgrade status on 2026-05-23: the repository now has the
scaffold needed to scale this route: dynamic batch task naming, per-episode LMDB
metric extraction, paired original/modified analysis, and storage-bounded video
case selection. The current extracted per-episode evidence still contains only
one paired smoke row, and `paired_episode_analysis.json` explicitly reports
`acl_main_result_ready=false`. A future main-result claim requires at least 30
paired episodes across five scenes for pilot-main evidence, with 100+ paired
episodes across 10+ scenes preferred.

InternNav flat-filter update on 2026-05-24: the corrected flat-filter protocol
removed the v2-v10 high-z sampling hang class, and the original condition
completed all 14 selected episodes (`TL=80.5189`, `NE=34.2730`, `OS=0.3571`,
`SR=0`, `SPL=0`). The modified condition completed 12 episodes, then hit a true
runtime hang after `Env Reset` on
`MV7J6NIKTKJZ2AABAAAAADY8_usd_tvstand_model_0b7e2a91f26da6b0f1f83c1c7d824399_0_0_6`.
Target-subtree audit does not support a broken-target explanation: geometry and
bbox match the original, no unresolved target references or target-local physics
authoring errors were found, and the modified target contains UsdPreviewSurface
rather than residual MDL. The 12 completed paired rows show trajectory/runtime
differences (`TL` mean delta `-39.1696`, `NE` mean delta `-3.4644`, `OS` mean
delta `-0.2500`), but this remains diagnostic evidence because the modified
aggregate run is incomplete, no selected videos exist yet, and
`paired_flatfilter_partial_episode_analysis.json` reports
`acl_main_result_ready=false`. A follow-up v2 split excluding the hung path has
13 episodes across six scenes; reaching the 30/100+ ACL gate still requires more
ready original/no-MDL scene pairs or a separate nonstandard stress protocol.

InternNav expanded30 input update on 2026-05-25: ten additional GRScenes home
navigation scenes were converted to no-MDL in the scratch tree, raising the
ready navigation inventory to 16 scene pairs and 38 flat-filter candidate
episodes. This enabled
`../../shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_expanded30_prep_manifest.json`,
a 30-episode / 16-scene split with the known modified tvstand reset-hang path
excluded and a clean height audit
`../../shared/evidence/raw/internnav_vln_downstream/acl_main_pilot30_flatfilter_expanded30_height_audit.json`.
This opens the next real-runtime gate, but it is still input evidence only:
expanded30 SR/SPL/NE/TL results and paper videos have not been generated.
`../../shared/evidence/raw/internnav_vln_downstream/video_rerun_manifest_flatfilter_partial.json`
also prepares six selected diagnostic video reruns with `vis_output=True`, but
the mp4 files do not exist until those selected-only runs are executed.

Official KuJiaLe downstream sanity update on 2026-05-25: a separate controlled
pair on public InteriorAgent / KuJiaLe `kujiale_0031` completed the same 33
official episodes for original MDL and ConvertAsset noMDL scenes. Repository
evidence is under
`../../shared/evidence/raw/internnav_vln_downstream/official_kujiale0031_33/`.
Original aggregate metrics are `SR=0.5152`, `SPL=0.4793`; noMDL aggregate
metrics are `SR=0.5758`, `SPL=0.4955`. The selected six-case video rerun has
basic nonblank QA and contact-sheet figures, but it remains qualitative only
because selected-rerun outcomes can differ from the full metric run. This is a
scoped single-official-scene downstream sanity result, not a broad GRScenes
or R2R/MP3D benchmark claim.

Official val-unseen completion on 2026-05-25: the local InteriorAgent_Nav
`val_unseen` split contains 99 episodes across exactly three official KuJiaLe
scenes, and all three now have paired original/noMDL InternNav metrics.
Repository evidence is under
`../../shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/`.
Combined paired means are original/noMDL `SR=0.5253/0.4848`,
`SPL=0.4739/0.4298`, `NE=3.6798/3.6306`, and `TL=6.9754/7.0598`. This is a
controlled official InteriorNav / KuJiaLe downstream sanity result. It still
does not justify a broad GRScenes, R2R, MP3D, or all-InteriorNav embodied
benchmark claim. See
`../../../docs/records/2026-05-25-internnav-official-val-unseen-99-results.md`.

Selected qualitative video update on 2026-05-25: the 0031 selected videos and
new 0036/0066 selected videos are now repo-resident under
`../../shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/`.
The package keeps compressed mp4s, start/mid/end stills, contact sheets, QA,
and manifests; raw InternNav frame directories remain outside git. This closes
the immediate rebuttal/figure need for selected official KuJiaLe videos, but it
does not change the quantitative claim boundary.

External status checked on 2026-05-22: the official ACL resolutions page records a July 2025 resolution that the 2027 conference will be branded as `ACL 2027` with no IJCNLP/AFNLP co-branding. No public ACL 2027 CFP, official conference site, city/date page, or Japan confirmation was found in the checked official sources. Japan is recorded here as the user-requested target until a public official source is available. Source: https://www.aclweb.org/adminwiki/index.php/ACL_Resolutions.
