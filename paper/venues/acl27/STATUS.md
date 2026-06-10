# ACL 2027 Version Status

Template provenance: ACL 2027 conference-specific files are not published in this repo. The wrapper now vendors the generic official *ACL style files `acl.sty` and `acl_natbib.bst` from `acl-org/acl-style-files` so local compile checks can run until the ACL 2027 author kit or conference-specific instructions are published. Provenance checked on 2026-05-23: ACLPUB's formatting page points authors to `https://github.com/acl-org/acl-style-files`.

Readiness: ACL/ARR candidate packet. It is route-ready for final human route
and OpenReview-form decisions, but not final-upload complete until the authors
lock EACL 2027 via ARR or wait for the official Annual ACL 2027 call.

Target-policy refresh on 2026-05-30: official ARR Dates still lists EACL 2027
with final ARR submission date August 3, 2026 and commitment date October 11,
2026. The EACL 2027 home and main-paper pages still list the August 3, 2026
AoE ARR deadline, with the complete CFP and detailed timetable forthcoming.
Official searches still did not find a public Annual ACL 2027 CFP or author
kit, so the route status remains ACL/ARR candidate-ready, not
Annual-ACL-final-ready.

Readiness sync on 2026-05-30: the reviewer-risk audit, full-PDF visual recheck,
Figure 3 red-material recheck, first-page ACL-fit recheck, and staged packet
now point to the same state. The current 11-page v18 PDF remains the active
candidate; Figure 1 v18 does not need another imagegen iteration because the
post-gate full-PDF visual review still passes page 2 and the exact
`Target: box` label is preserved. The repo has no current paper-side blocker,
but
`report_final_blockers.py` still reports human-only blockers for route lock,
private author-gate completion, OpenReview form copy, runtime/AI/media
approvals, and final upload decision.

Fig.3 provenance-caption, conclusion, and layout polish on 2026-05-30:
Figure 3's caption now says the selected `Original MDL` cells passed a
log-checked clean rerender/provenance gate, the conclusion now states the
paper's practical outcome as an evidence gate, and the Introduction no longer
uses a manual `\newpage` before the contribution list. A longer caption draft
was rejected after rendered page review because it moved Figure 4 to page 10
and left page 9 with a large blank column. The accepted compact wording
preserves the red-material provenance signal while keeping Figure 4 on page 9.
The refreshed staged candidate is an 11-page A4 PDF 1.5 file of 4,066,770 bytes
(`sha256=177466b7d0cf6a557f73f792dc6f718fdae8f42663e7398a54bc2d9252cde356`,
created 2026-05-30 20:25:01 CST). The build and staged PDFs are byte-identical.
The full pre-upload gate passed claim boundaries, target policy, metadata
consistency, OpenReview checklist, citation inventory, evidence-number checks,
the 57-source final-integrity fingerprint, blocker/goal reports, 93 focused
tests, clean ACL rebuild, LaTeX log scan, packet staging,
inventory/checksum/private-token/acknowledgment scans, PDF profile checks, and
ordered text-section checks. Remaining blockers are unchanged and human-only.

InternNav scope wording polish on 2026-05-30: a final reviewer-style pass
removed the awkward `all-InteriorNav` wording from the Limitations scope
boundary and replaced it with explicit `all InternNav or InteriorAgent
settings` language. The claim-boundary checker now catches natural broad-scope
variants such as `all InternNav` and `all InteriorAgent`, not only hyphenated
forms. The consolidated pre-upload gate was rerun after the edit and passed
with 93 focused tests. The current staged candidate is an 11-page A4 PDF 1.5
file of 4,066,626 bytes
(`sha256=137370b33b567ebc55ab6f88ef5d6e6860b6e61debf133e8077b14a22b454c98`,
created 2026-05-30 20:43:58 CST). The build and staged PDFs are
byte-identical. Page 9 was rerendered at 150 DPI; the rendered page hash is
`c102b28d3ca1b6d01713bebd110481c0178f80fa206376cfc23d4eed636f4496`, and local
visual review passed with Figure 4, Limitations, and Ethical Considerations
readable and non-overlapping.

Post-gate full-PDF visual review on 2026-05-30: the current staged PDF with
SHA-256 `177466b7d0cf6a557f73f792dc6f718fdae8f42663e7398a54bc2d9252cde356`
was rerendered at 150 DPI after the Figure 3 provenance-caption hardening,
conclusion takeaway polish, manual Introduction page-break removal, and final
pre-upload-gate restaging. The durable record is
`paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_20260530.json`.
The verdict remains `PASS_WITH_MINOR_QUALITATIVE_CAVEATS`: no blank pages,
detached captions, raw LaTeX artifacts, figure/table overlap, page-level
clipping, or red-material recurrence were found. Page 2 now flows from
Figure 1 into the contributions and Related Work without a manual page break,
and page 8 still carries the compact Figure 3 provenance caption and
strengthened conclusion without moving Figure 4 off page 9. No new imagegen
candidate was generated because the visual review did not identify a concrete
defect that another generated bitmap would solve.

Previous full pre-upload candidate refresh on 2026-05-28: after the material-
effect main-panel promotion, the Figure 2 visual-first readability polish,
Figure 3 readable-label polish/red-material recheck, Table 6 caption
compacting, the Figure 4 wide InternNav panel upgrade, the page-9 Limitations
tail polish, the page-7 official-scene hyphenation polish, the rejected
Figure 1 v17 imagegen candidate audit, the promoted Figure 1 v18 imagegen
schematic, the abstract point-hit direction clarity update, the Figure 1
caption polish, and the final pre-upload gate rerun, the staged candidate is
an 11-page A4 PDF 1.5 file of
4,066,538 bytes
(`sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7`,
created 2026-05-28 23:22:53 CST).
The build and staged PDFs are byte-identical. The full gate passed claim
boundaries, target policy, metadata
consistency, OpenReview checklist, citation inventory, evidence-number checks,
final-integrity fingerprint, blocker/goal reports, 91 focused tests, clean ACL
rebuild, LaTeX log scan, packet staging, inventory/checksum/private-token/
acknowledgment scans, PDF profile checks, and ordered text-section checks.
Remaining blockers are human-only: final route lock, OpenReview form copy,
runtime/AI/media approvals, and final upload decision.

Same-day figure context: Figure 1 is now the accepted low-text imagegen v18
schematic, promoted after local visual review confirmed the exact `Target: box`
label and page-scale readability. Figure 2 remains deterministic real render evidence, now using a
visual-first layout with larger panels and no internal title/subtitle/footer
microcopy. Figure 3 is now the selected material-effect qualitative panel on
page 8 with readable row-level target/effect labels, sourced from
`fig_material_effect_baseline_qualitative.png`, and Figure 4 is now the wide
three-case official KuJiaLe InternNav path panel on page 9, sourced from
`fig_internnav_rollout_0036_0066_main3_readable.png`. Figure 3 and Figure 4 are
included as bounded selected visual evidence only; Table 5 remains the
governing material-effect claim-boundary artifact, and the InternNav
quantitative claims remain tied to the frozen 99-episode paired run.

Table 6 caption polish on 2026-05-28: the official-scene performance table keeps
the same aggregate Original MDL/noMDL rows and the same CSV-backed metrics, but
the main-paper caption is now compact enough for page-7 scanning while still
stating that NVIDIA official-scene performance is omitted until matching
conversions pass smoke gates. Local page-7/page-8 visual review reports
`pass_with_caveat`: the page remains dense, but Table 6 has no visible overlap
or detached caption.

Fig.3 red-material recheck on 2026-05-28: rendered page 8 of the current build
PDF, the extracted embedded PDF image, and the source Figure 3 PNG all have
zero strong-red pixels under the project spot check. The current source figure
hash is `e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a`,
and the rendered page-8 hash is
`e8cf7110e83bfe8b44d7674dd29cee26d7a4917aea70dc783db07ee3e18c7f90`.
`check_qualitative_clean_provenance.py` reports
`status=clean_material_effect_panel_ready`, `selected_case_count=4`,
`checked_original_mdl_log_count=4`, and
`original_mdl_error_signal_count=0`. The current diagnosis is that any red
`Original MDL` material seen in older candidates was stale pre-rerender evidence
or a cached PDF/source image, not a recurrence of the MDL import problem.

Fig.4 wide-panel recheck on 2026-05-28: the source wide InternNav panel
`fig_internnav_rollout_0036_0066_main3_readable.png` now has SHA-256
`818525fcc0a5fd0b4e692ddd9d2738e673eb3b70a2b2dd90895cab7dd0d51a6e` after the
label-readability polish, and the rendered page-9 check has SHA-256
`cb7fbc9efb13ff560646189e2f39067e5c720abb446ce85958ca12e31e4fde10` at 180
DPI. Both report zero strong-red pixels after the overlay recoloring step. The
pre-upload `pdftotext` guard now explicitly allows this top-of-page Figure 4
float before the Limitations heading while still rejecting Figure 4 after
Ethical Considerations or References. A follow-up page-9 polish keeps the right
column starting cleanly at `Ethical Considerations`, while preserving the
stability-only/no-speedup claim boundary.

Page-7 hyphenation polish on 2026-05-28: the official-scene stability paragraph
no longer starts page 7 with a broken `nal/noMDL`, `process official-scene`, or
`scene runs` fragment. The checked text now preserves the `18 required` and
`18/18 successful` evidence markers while phrasing the result as `18 required
paired runs ... in fresh processes` across original and noMDL conditions.

Figure 1 v17/v18 imagegen audit on 2026-05-28: an additional imagegen candidate was
generated and preserved under `fig_acl_method_chain_imagegen_v17_candidate.png`,
but local visual review rejected it for main-paper use because the VLM target
label reads `Target: boy` instead of `Target: box`. A follow-up v18 candidate
was generated, preserved under `fig_acl_method_chain_imagegen_v18_candidate.png`,
and promoted to `fig_acl_method_chain_imagegen_v18.png` because it preserves
the exact `Target: box` label, keeps the low-text four-stage roadmap, and uses
the clearer `VLM Checks` stage title.

Current v18 full-PDF visual review on 2026-05-28: the build PDF with SHA-256
`59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7` was
rerendered at 150 DPI and checked with the local pure-visual rubric after the
Figure 1 caption polish and final pre-upload gate rerun. The durable record is
`paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_v18_20260528.json`.
The verdict is `PASS_WITH_MINOR_QUALITATIVE_CAVEATS`: no blank page, detached
caption, raw LaTeX artifact, table/float overlap, or visible page-level clipping
was found. The page-1 abstract update and page-2 Figure 1 caption polish fit
without visible overlap or clipping.
Figure 1 remains accepted schematic-roadmap art; Figure 2 remains
real render orientation evidence with a cropped-proxy caveat; Figure 3 remains
selected material-effect qualitative evidence without visible red MDL fallback;
and Figure 4 remains selected qualitative InternNav path evidence with improved
case-ID and `SR O/N` label readability while the caption and main-text claim
boundary still carry the quantitative-scope warning.

Main-paper polish update on 2026-05-27: the ACL/ARR manuscript no longer uses
internal venue-wrapper wording such as `ACL-facing`, `main ACL claim`, or
`ACL protocol` in checked manuscript/metadata text. Table captions also no
longer expose `ACL/ARR claim boundary` wording. The text now presents the work
as a claim-bounded evaluation protocol, while `check_claim_boundaries.py`
rejects those wrapper phrases if they are reintroduced.

Table-density polish update on 2026-05-27: the official-scene performance table
in the ACL main PDF now uses a compact aggregate `Metric / Original MDL / noMDL`
layout with wrapping columns. The corresponding CSV still keeps the aggregate
and per-scene rows. This makes the repeated load/render stability result
readable in the main paper without promoting it beyond the existing boundary:
original/noMDL official KuJiaLe runs succeeded with overlapping ready-time
intervals, and no NVIDIA official-scene performance row is reported yet.
The subsequent full pre-upload gate passed with 69 focused tests, a 53-source
integrity fingerprint, and a staged 11-page A4 PDF 1.5 file of 3,364,227 bytes.

Reference-layout polish update on 2026-05-27: a follow-up visual review found
that forcing a fresh References page after Ethical Considerations left a large
blank right column below Figure 3. `main.tex` now lets References begin in the
right column on page 9 after the ethics text, and the OpenReview checklist
anchors now record `References | starts on page 9`. The subsequent full
pre-upload gate passed with 70 focused tests, a 53-source integrity
fingerprint, and a staged 10-page A4 PDF 1.5 file of 3,363,874 bytes.

Introduction-layout polish update on 2026-05-27: a later page-level visual
review found that the contribution list on page 2 started the right column with
a mid-sentence continuation. `sections/intro.tex` now tightens the four-gate
paragraph and first two contribution bullets and uses a deliberate column break
before `We make four contributions`. The subsequent full pre-upload gate passed
with 70 focused tests, the 53-source integrity fingerprint, and a staged
10-page A4 PDF 1.5 file of 3,363,532 bytes, with page 3 still starting Related
Work cleanly.

Fig.3 overlay-color polish update on 2026-05-27: the selected InternNav rollout
panel now recolors source-red agent trajectory/action overlays to purple during
figure composition while leaving the evidence stills unchanged. The Figure 3
caption describes the purple executed paths/action arrows as orientation
overlays with color changed for readability, reducing confusion with the
historical red-material fallback issue. The subsequent full pre-upload gate
passed with 70 focused tests, the 53-source integrity fingerprint, clean build,
staging, scans, PDF profile, and `pdftotext` checks. The staged candidate
remains a 10-page A4 PDF 1.5 file of 3,363,508 bytes; page-9 visual review
confirms that the purple/green legend and caption remain visible.

Page-8 layout polish update on 2026-05-27: after the Fig.3 overlay-color
mitigation, a rendered-PDF review found that the official-scene performance
Table 6 could still force an awkward single-column float before Limitations.
`tab_official_scene_performance_summary.tex` and its generator now emit the
compact aggregate table as a two-column `table*`, and `sections/conclusion.tex`
is shortened to a single claim-boundary paragraph. The subsequent full
pre-upload gate passed with 70 focused tests, the 53-source integrity
fingerprint, clean build, staging, scans, PDF profile, and `pdftotext` checks.
The staged candidate remains a 10-page A4 PDF 1.5 file of 3,363,281 bytes;
rendered page-8/page-9 visual review confirms that Table 6, Limitations, and
the selected InternNav Figure 3 are readable without overlap.

Method-chain v9 imagegen update on 2026-05-27: a follow-up full-PDF visual
review found that Figure 1 could be made less dense without changing the paper
story. A new imagegen/image2 v9 schematic was generated, copied to
`paper/shared/figures/fig_acl_method_chain_imagegen_v9.png`, and connected to
the ACL wrapper with its prompt preserved at
`paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v9.prompt.txt`.
Rendered page-2 visual review of the staged PDF confirms that the four-stage
roadmap, exact `Target: box` label, and claim-boundary footer remain readable.
The subsequent full pre-upload gate passed with 70 focused tests, the 53-source
integrity fingerprint, clean build, staging, scans, PDF profile, and
`pdftotext` checks. The staged candidate remains a 10-page A4 PDF 1.5 file of
3,313,612 bytes.

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

The material-shift stress set now uses `../../shared/evidence/raw/grscene_vlm_grounding/stress_vlm_run_manifest_expanded30.json`: 30 target-visible PASS/WARN zoom pairs, 60 scoring records, and matched Gemma4/Qwen metadata hashes against the same manifest file. This is a frozen target-centered stress set, not a broad GRScenes distribution. The canonical Gemma4 root files are `stress_predictions.jsonl` and `stress_score_summary.json`: answer accuracy is 30/30 original and 30/30 converted, normalized-1000 point hits are 27/30 original and 29/30 converted, normalized-1000 hit-status agreement is 28/30, and both-hit pairs are 27/30. The matching Qwen2.5-VL expanded30 diagnostic under `stress_expanded30_probes/` has 55/60 scorable answer rows, answer hits 27/29 original and 24/26 converted, raw point hits 22/29 original and 19/29 converted, and normalized-1000 point hits 3/29 for both material conditions. The old 14-pair `zoom_stress_probes/` remain pilot/protocol history, not root canonical evidence. The ACL main results section now keeps this evidence tabular rather than relying on selected qualitative grounding panels.

Qualitative grounding-panel QA update on 2026-05-26: the previously included
VLM grounding panel had abnormal red materials in the "Original MDL render"
columns. The scratch repair pass rewrote 1,566 generated MDL files, repaired
23,141 GRScenes pointer entries, and added 51 missing `Materials` symlinks for
render-log-referenced model instances without intentionally modifying the
official source tree. This removed the checked MDL-resolution error terms for
the first selected pair, but the repaired original-condition headless viewport
capture timed out at 1800 seconds, while a direct converted capture probe for
the same view succeeded. The ACL main paper therefore no longer includes
`fig_vlm_grounding_cases`, and `check_claim_boundaries.py` now rejects that
unsafe panel if it is reintroduced before clean render/overlay provenance is
available. See
`../../../docs/records/2026-05-26-acl-fig1-red-material-root-cause.md`.

Material-effect qualitative-panel QA update on 2026-05-28: the earlier
`fig_material_effect_baseline_qualitative.png` red-material issue is repaired
for the four selected covered-bin cases. Each selected original/noMDL pair was
rerendered through `run_paired_render_smoke.py` from the existing zoom camera
stages, the material-effect manifest and contact sheet were regenerated, and the
clean-provenance checker now reports `clean_material_effect_panel_ready` with
`original_mdl_error_signal_count=0`. The ACL main paper still keeps the
material-effect result table-bounded; `check_claim_boundaries.py` now rejects
the panel only when that clean-provenance gate is false. See
`../../../docs/records/2026-05-27-acl-fig3-red-material-diagnosis.md`.

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

Target-call refresh after pre-upload automation on 2026-05-26: official ARR,
EACL, and ACLPUB pages were reopened after the evidence-number gate was added.
The policy state is unchanged: EACL 2027 via ARR is the concrete public
ACL-family route, Annual ACL 2027 remains unavailable as a final public target,
and reviewer-registration plus final route/form-copy/upload decisions remain
human-only gates.

Goal-completion audit update on 2026-05-26: `GOAL_COMPLETION_AUDIT.md` maps
the active ACL/ARR objective to concrete evidence and remaining gates. Verdict:
the package is candidate-ready for target lock and final submission rehearsal,
but it is not final-upload complete until the target route is locked, the
official OpenReview form is filled, author/runtime and optional media/legal
decisions are confirmed, a final citation/data integrity pass runs, and the
exact upload packet is rebuilt and anonymization-scanned. The next large goal
should therefore be target lock plus final integrity/upload gate, not more
unbounded experiment collection.

Goal-completion reporter update on 2026-05-26:
`scripts/report_goal_completion.py` now turns that audit into a machine-readable
status report. It checks claim boundaries, evidence numbers, citation
inventory, OpenReview copy sources, target policy, the final-integrity
fingerprint, and the final blocker report without printing private author
values. The current report is `status=candidate_ready_human_blocked`:
`repo_static_ready=true`, `candidate_ready_for_human_gate=true`,
`repo_requirement_failures=[]`, and `final_goal_complete=false` because the
private author/OpenReview route, form-copy, runtime/AI/media, and final upload
decision remain unresolved. The reporter is part of the consolidated
pre-upload gate, but it is not a substitute for `run_preupload_gate.py`. After
removing the unsafe qualitative VLM panel from the ACL main paper and later
adding the figure-driven evidence panels, the cleaner method-chain imagegen v3
figure, the oblique-view single-object render-pair refresh, the retained
InternNav supplemental/rebuttal panel, plus the earlier abstract refresh
(now tightened to 183 words after the original/converted point-hit clarity
edit), the
2026-05-27 candidate passed the full pre-upload gate. The latest post-Fig.3
mitigation, layout-polish, and venue-neutral wording gate passes with 69
focused ACL tests, a
53-source integrity fingerprint, and a staged 11-page A4 PDF 1.5 file. The
unsafe material-effect
qualitative panel is now removed, while the combined two-column Figure 2 keeps
the selected real-render evidence easier to inspect without changing the
underlying claims.

Private author-gate status update on 2026-05-26:
`scripts/report_final_blockers.py` and `scripts/report_goal_completion.py` now
surface `private_author_gate_status`, a value-free summary of the ignored
private worksheet check. It reports missing/TODO/invalid worksheet field names,
counts, git ignored/tracked booleans, and `prints_private_author_values=false`
without printing author names, OpenReview IDs, emails, private links, or filled
worksheet values. This makes the current human blocker easier to clear while
preserving the safe repository boundary: the filled worksheet remains local and
ignored.

Author-gate prefill update on 2026-05-26: `scripts/prefill_author_gate.py`
fills only repo-verifiable rows in the ignored private worksheet: clean
pre-upload command evidence, PDF profile, citation/reference scan, staging path,
staged file list, private-token scan, acknowledgment scan, and ordered PDF
section scan. It does not fill author names, route selection, OpenReview profile
readiness, form-copy approval, runtime/AI/license approvals, optional-media
decision, or the final upload decision. The local ignored worksheet has been
prefilled for those eight evidence rows and still fails `check_author_gate.py`
until the remaining human rows are approved.

Author-gate prefill restage on 2026-05-28: after the current 23:22 staged PDF
was produced, `prefill_author_gate.py --apply --overwrite` refreshed the eight
repo-verifiable rows in the ignored local worksheet against the exact current
packet. `check_author_gate.py` still reports `ok=false`, but the remaining
`todo_fields` are now the human-only route, OpenReview-copy, runtime/AI/media,
approval, and final upload-decision rows. The final blocker reporter now detects
this state and its first `next_actions` entry tells the author to complete the
remaining human-only worksheet fields, rather than redundantly asking for the
ordinary prefill step again.

OpenReview author-profile sync on 2026-05-30: the ignored private worksheet now
records the current sole-author and OpenReview-profile confirmation rows, and a
fresh prefill refreshed the repo-verifiable rows for the latest staged 11-page
A4 PDF 1.5 artifact of 4,087,616 bytes with SHA-256
`d03af3b4554951ccb51c3a224a8fbbd12fb517180dd36bad5672f0fb07006793`. Those
private values remain outside the tracked repository and outside the anonymous
submission packet. `check_author_gate.py` still reports `ok=false`, with no
missing fields but 19 remaining TODO fields: target route/deadline/commitment,
reviewer-registration commitment, dual-submission and prior-submission answers,
preprint/public-link decisions, OpenReview metadata/checklist copy approvals,
runtime/AI/license wording approvals, optional-media decision, and final upload
decision.

Goal-completion refresh after pre-upload automation on 2026-05-26: the current
candidate is now guarded by `run_preupload_gate.py`, which includes
claim-boundary, OpenReview metadata, citation inventory, evidence-number,
final-integrity source fingerprint, focused pytest, clean build, LaTeX log,
staging, inventory, packet checksum, anonymization, acknowledgment, `pdfinfo`,
`pdf_profile`, and ordered `pdftotext` checks. The focused suite now covers 34
tests after adding citation-inventory, author-gate, final-integrity
fingerprint, and packet-checksum tests, and the current PDF
profile guard enforces the 12-page A4/PDF 1.5 candidate shape. This strengthens
repository-side readiness but still does not close target-route, official
OpenReview, private author, runtime/AI-assistance, or media/legal gates.

Current-commit gate refresh on 2026-05-26: after the gate-status documentation
sync, `run_preupload_gate.py` was rerun from a clean `main` checkout. The pass
completed claim-boundary, metadata, evidence-number, 23-test focused pytest,
clean ACL build, LaTeX log scan, five-file packet staging, private-token scan,
acknowledgment scan, `pdfinfo`, `pdf_profile`, and `pdftotext_sections`. The
staged PDF remained 12 A4 pages, PDF 1.5, and 306187 bytes.

Author-gate checker update on 2026-05-26:
`scripts/check_author_gate.py` now validates the ignored private author
worksheet after the authors fill it. It checks required field names,
TODO/TBD/UNKNOWN/UNDECIDED values, and git ignored/untracked status while
reporting only field names and booleans, not private author values. The focused
pre-upload pytest suite includes `tests/test_acl_author_gate.py`; the checker
itself is expected to fail until
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md` exists and is filled locally.

Author-gate initializer update on 2026-05-26:
`scripts/init_author_gate.py` now creates the ignored private author worksheet
from the blank tracked template, refuses to overwrite an existing private
worksheet, verifies the path is git-ignored, and reports only path/status
metadata. The OpenReview upload runbook and filling guide now prefer this
initializer over a manual copy, and the blank worksheet now points to the same
initializer as the first author-side action. The focused pre-upload pytest
suite includes `tests/test_acl_author_gate_init.py`; this is a repository-side
safety check and still does not fill or validate private author values. The
refreshed full pre-upload gate passes with 53 focused ACL tests, a 12-page A4
PDF 1.5 staged packet, and 306187 bytes for `main.pdf`.

Final-blocker command handoff update on 2026-05-26:
`scripts/report_final_blockers.py` now lists the author-side commands in the
same order as the runbook: initialize the ignored private worksheet, check the
filled private worksheet, then run the repository-side pre-upload gate. This is
a reporting/handoff change only; `run_preupload_gate.py` still does not execute
`init_author_gate.py`, so the automated repository gate does not create or fill
private author data. The current real report therefore remains
`status=human_blocked` with `repo_blockers=[]` until the authors complete the
ignored local worksheet and OpenReview decisions.

Citation-inventory gate update on 2026-05-26:
`scripts/check_citation_inventory.py` now checks the ACL wrapper's cited keys
against `paper/shared/references.bib` and the 2026-05-26 web-trail addendum.
The current pass covers 20 unique cited keys, with no missing BibTeX entries,
no cited key lacking DOI/URL metadata, no missing web-trail key, and no uncited
web-trail key. The checker is part of `run_preupload_gate.py` and has focused
tests in `tests/test_acl_citation_inventory.py`.

Packet-checksum sidecar update on 2026-05-26:
`scripts/stage_submission_packet.py` now writes the ignored adjacent sidecar
`paper/submissions/acl27_arr_candidate_20260526.sha256` after staging. The
sidecar records SHA-256 digests for the five safe packet files without adding a
sixth file to the anonymous review packet. `run_preupload_gate.py` now validates
that sidecar immediately after the exact packet-inventory check. The refreshed
full gate at that stage passed with 31 focused tests, the same five-file packet boundary,
12 A4 PDF pages, PDF 1.5, and 306187 bytes.

Target-policy refresh after current-commit gate on 2026-05-26: official ARR,
EACL, and ACLPUB pages were reopened again. The route state is unchanged:
EACL 2027 via ARR remains the concrete public route with August 3, 2026 AoE as
the ARR submission deadline, the full EACL CFP/timetable is still forthcoming,
and official search still did not find an Annual ACL 2027 CFP or author kit.

Target-policy refresh after final-blocker command handoff on 2026-05-26:
official ARR, EACL, and ACLPUB pages were reopened after the final blocker
report began listing the author-gate initializer command. The route state is
still unchanged: EACL 2027 via ARR remains the concrete public 2027 ACL-family
route with August 3, 2026 AoE as the ARR submission deadline and October 11,
2026 as the commitment date; the EACL full CFP/timetable is still forthcoming;
official search still did not find an Annual ACL 2027 CFP, author kit,
city/date page, commitment deadline, or conference-specific supplement policy.
After the protected target-policy source files changed, the final-integrity
fingerprint was refreshed and the full consolidated pre-upload gate passed
again with 53 focused ACL tests, 41 fingerprinted sources, a 12-page A4 PDF
1.5 staged packet, and 306187 bytes for `main.pdf`.

Target-policy refresh after private author-gate status on 2026-05-26:
official ARR, EACL, ACLPUB, and ACL Resolutions pages were reopened after the
private author-gate status handoff was added. The route state is unchanged:
EACL 2027 via ARR remains the concrete public route, the EACL complete CFP and
detailed timetable are still forthcoming, and Annual ACL 2027 still lacks a
checked official CFP/author kit. `scripts/check_target_policy.py` now also
requires the ACL Resolutions URL and `2027 ACL Conference Branding` marker so
the repository records that ACL 2027 branding exists without promoting the
packet to Annual-ACL-final.

Reference web-trail update on 2026-05-26:
`paper/shared/evidence/references/verification_report.md` now contains a
20/20 ACL-wrapper reference-existence web-trail addendum. The pass also
normalized `paper/shared/references.bib` by adding the Synthetica IROS DOI,
Tobin and Tremblay proceedings pages, and the formal Springer ECCV DOI/pages
for Photo-realistic Neural Domain Randomization. This closes the current
fabricated-reference risk for the ACL wrapper, while final citation-context,
data-claim, and originality checks still remain part of the pre-upload
integrity gate.

Final-integrity delta update on 2026-05-26:
`FINAL_INTEGRITY_DELTA_AUDIT.md` now checks the current ACL wrapper's
citation-bearing sentences, main numerical claims, forbidden-claim wording, and
sampled exact-phrase originality searches. No manuscript edit was required:
citation contexts match the verified sources, the main data claims match local
CSV/JSON evidence after rounding, and the current text negates rather than
makes broad benchmark, speedup, NVIDIA official-scene performance, population
failure-rate, procedural-texture success, selected-video-as-quantitative, or
learned-classifier claims. This narrows the remaining blockers to target-route
lock, official OpenReview form copy, author/runtime/AI-assistance confirmation,
optional media legal decision, and rerunning build/staging/integrity scans
after any future change.

Target-lock rehearsal update on 2026-05-26:
`TARGET_LOCK_OPENREVIEW_REHEARSAL.md` now separates repository-ready artifacts
from author-only OpenReview decisions. The practical route state is unchanged:
EACL 2027 via ARR is the concrete public ACL-family path if the authors want a
2027 target now, while Annual ACL 2027 remains unavailable as a final public
target in checked official sources. The remaining human decisions are target
route, author list/order, OpenReview profiles, reviewer-registration
commitment, dual-submission or resubmission status, preprint status,
runtime/AI-assistance wording, and optional media exclusion or legal approval.

OpenReview metadata update on 2026-05-26:
`OPENREVIEW_METADATA_PACKET.md` now provides copy-ready title, abstract, ARR
area, and keyword material. The ACL abstract was shortened from the extracted
218-word version to an under-200-word plain-text version to satisfy ACLPUB
abstract-length guidance while preserving the same evidence numbers and claim boundary. The
staging script now includes the metadata source as `openreview/METADATA.md` in
the ignored local candidate packet.

Next-large-goal update on 2026-05-26:
`NEXT_LARGE_GOAL.md` now fixes the next executable goal as route lock plus
final integrity/upload gate. It explicitly uses official InternNav / KuJiaLe as
the embodied sanity route, keeps GRScenes as the VLM grounding stress evidence,
and treats selected qualitative videos as optional figure/rebuttal evidence
that stays out of the default safe upload packet unless separately approved.

OpenReview author-gate update on 2026-05-26:
`OPENREVIEW_AUTHOR_GATE_WORKSHEET.md` now provides the blank template for the
human-only submission fields: route choice, author list/order, OpenReview
profiles, reviewer-registration commitment, dual-submission/resubmission,
preprint status, runtime and AI-assistance approval, optional media decision,
and final pre-upload evidence. The filled copy should be
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md`, which is ignored by `.gitignore` and
must not enter the anonymous review packet.

OpenReview author-gate filling guide update on 2026-05-26:
`OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md` now gives the concrete fill order for
the private author worksheet: route decision, author/OpenReview readiness,
submission-history fields, form-copy approvals, optional media decision, final
pre-upload evidence, privacy checks, and stop conditions. This does not fill
the private worksheet for the authors; it makes the remaining human gate
auditable without committing author identities or OpenReview IDs.

Pre-upload rehearsal refresh on 2026-05-26:
After adding the author-gate worksheet, the current ACL/ARR candidate was
re-tested and restaged. `tests/test_acl_submission_staging.py` plus
`tests/test_paper_layout.py` passed 11/11 tests; the abstract count remained
under 200 words; `make -C paper clean-acl27 && make -C paper acl27` rebuilt the
11-page A4 PDF; the final log had no unresolved citation/reference matches; the
staged packet still contained only the anonymous PDF, OpenReview metadata,
OpenReview checklist, supplemental README, and manifest; local path/private
identifier and acknowledgment scans had no matches. See
`SUBMISSION_STAGING_AUDIT.md` and
`docs/records/2026-05-26-acl-preupload-rehearsal-refresh.md`.

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
controlled official InternNav / KuJiaLe downstream sanity result. It still
does not justify a broad GRScenes, all InternNav or InteriorAgent settings,
R2R, MP3D, or manipulation benchmark claim. See
`../../../docs/records/2026-05-25-internnav-official-val-unseen-99-results.md`.

Selected qualitative video update on 2026-05-25: the 0031 selected videos and
new 0036/0066 selected videos are now repo-resident under
`../../shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/`.
The package keeps compressed mp4s, start/mid/end stills, contact sheets, QA,
and manifests; raw InternNav frame directories remain outside git. This closes
the immediate rebuttal/figure need for selected official KuJiaLe videos, but it
does not change the quantitative claim boundary.

External status checked on 2026-05-22: the official ACL resolutions page records a July 2025 resolution that the 2027 conference will be branded as `ACL 2027` with no IJCNLP/AFNLP co-branding. No public ACL 2027 CFP, official conference site, city/date page, or Japan confirmation was found in the checked official sources. Japan is recorded here as the user-requested target until a public official source is available. Source: https://www.aclweb.org/adminwiki/index.php/ACL_Resolutions.

ACL reviewer-risk update on 2026-05-26: `ACL_REVIEWER_RISK_AUDIT.md` now
records the submission-facing interpretation of the next large goal. The
actionable ACL-family route remains EACL 2027 via ARR because ARR Dates and the
EACL 2027 main-paper page list the August 3, 2026 ARR deadline, while Annual
ACL 2027 still lacks a checked public CFP/author kit. The next goal is not more
unbounded experiments by default. It is route lock, reviewer-risk hardening,
and final integrity/upload gating: keep the first page centered on VLM
grounding and embodied-data reliability under 3D material perturbations, keep
InternNav scoped as downstream sanity evidence, keep NVIDIA claims selected and
material-effect bounded, exclude optional scene-derived media by default, and
rerun the exact upload-packet scans after any final edit.

First-page ACL-fit refresh on 2026-05-26: the ACL title now reads `Material
Conversion as a Controlled Perturbation for Vision-Language Grounding in
Synthetic 3D Scenes`, and the abstract removes the tool-first ConvertAsset
sentence in favor of a composition-preserving conversion-path description. The
OpenReview metadata packet was updated to the same title and refreshed
abstract, now 183 words after the later proxy-fidelity boundary and
original/converted point-hit clarity edits. The intent is to make the first
screen read as VLM grounding and embodied-data reliability work under a
controlled material perturbation,
while keeping the same evidence numbers and claim boundary.

OpenReview metadata consistency update on 2026-05-26:
`scripts/check_metadata_consistency.py` and
`tests/test_acl_metadata_consistency.py` now guard the ACL title/abstract copy
source. The checker compares the LaTeX title in `main.tex`, the source abstract
in `sections/abstract.tex`, and the fenced title/abstract fields in
`OPENREVIEW_METADATA_PACKET.md`, and verifies that the abstract remains under
200 words before staging. This makes OpenReview metadata drift an automated
pre-upload failure rather than a manual-only checklist item.

Claim-boundary automation update on 2026-05-26:
`scripts/check_claim_boundaries.py` and `tests/test_acl_claim_boundaries.py`
now guard the highest-risk ACL claims. The checker scans the ACL sections,
shared appendix, and OpenReview metadata source for unguarded broad embodied
robustness, broad benchmark, all GRScenes/all InternNav/InteriorAgent/
R2R/MP3D/manipulation robustness, official-scene speedup, NVIDIA
official-scene performance,
population failure-rate, procedural-texture success, and learned-classifier
claims. Guardrailed statements such as `does not establish`, `rather than
speedup`, `selected`, `scoped`, and `limitation` remain allowed.

Consolidated pre-upload gate update on 2026-05-26:
`scripts/run_preupload_gate.py` and `tests/test_acl_preupload_gate.py` now make
the local repository-side pre-upload rehearsal one command. The gate runs the
claim-boundary checker, metadata consistency checker, citation-inventory
checker, evidence-number checker, final-integrity source fingerprint checker,
focused ACL pytest suite, clean ACL PDF build, final LaTeX log scan, candidate
packet staging, exact packet inventory check, packet-checksum sidecar check,
private-token scan, acknowledgment scan, `pdfinfo`, PDF profile guard, and
`pdftotext` title/header/section-order checks. The full run now passes on the
current ACL/ARR candidate: 34 focused tests passed, the rebuilt staged PDF is
12 A4 pages after the evidence-gate table refresh, the staged packet contains
exactly the five safe files, the adjacent checksum sidecar validates those five
files, and both private-token and acknowledgment scans had no matches. This does
not close the human/external gates: target route lock, official policy refresh,
private author worksheet, official OpenReview form copy, and final author/legal
decisions still remain.

Evidence-number consistency update on 2026-05-26:
`scripts/check_evidence_numbers.py` and `tests/test_acl_evidence_numbers.py`
now guard the most visible ACL-facing numerical claims. The checker reads local
CSV/JSON evidence for proxy metrics, clean and expanded30 VLM grounding,
official KuJiaLe InternNav 99-episode means, official-scene 18/18 stability,
and appendix coordinate baselines, then verifies that the ACL manuscript and
OpenReview metadata source still contain matching numbers. This converts the
manual data-claim table in `FINAL_INTEGRITY_DELTA_AUDIT.md` into an automated
pre-upload gate.

Citation-inventory consistency update on 2026-05-26:
`scripts/check_citation_inventory.py` and `tests/test_acl_citation_inventory.py`
now guard the ACL wrapper's citation inventory before PDF rebuild/staging. The
checker parses citations from ACL section sources plus the shared appendix,
parses `paper/shared/references.bib`, and compares the cited keys with the
current 2026-05-26 web-trail addendum. This turns the reference-existence
web-trail into an automated drift check; it does not replace citation-context
or originality review.

Evidence-gate table update on 2026-05-26: the ACL method now includes
Table `tab:acl_evidence_gate_registry`, a compact registry mapping proxy
similarity, GRScenes VLM grounding, material-mechanism/NVIDIA evidence, and
InternNav/official-scene sanity checks to their allowed claims and forbidden
promotions. This addresses the reviewer-risk concern that the evidence streams
could look heterogeneous, without adding new experiments or widening the claim
boundary. The consolidated pre-upload gate was rerun after this edit and
passed; `pdfinfo` reports a 12-page A4 staged PDF, PDF 1.5, 306187 bytes, and
the anonymous staged packet still has exactly the five safe files.

PDF profile guard update on 2026-05-26: `run_preupload_gate.py` now turns the
current staged PDF shape into an explicit local gate. The runner rejects
unreviewed drift above 12 total pages, non-A4 page size, PDF versions other than
1.5, or a PDF text order where `References` appears before `Limitations` and
`Ethical Considerations`. This is a candidate-profile guard for the current
ACL/ARR packet, not a replacement for final selected-venue page-limit policy.

Final-integrity source fingerprint update on 2026-05-26:
`scripts/check_integrity_fingerprint.py` now validates
`FINAL_INTEGRITY_SOURCE_FINGERPRINT.json`, a 41-source SHA-256 fingerprint over
the ACL manuscript, shared appendix and tables, bibliography, OpenReview copy
sources, target-policy notes, reference web-trail, and key CSV/JSON evidence.
`run_preupload_gate.py` now runs this check after citation/evidence-number
checks and before focused pytest, clean build, and packet staging. The focused
ACL pytest suite now covers 34 tests after adding
`tests/test_acl_integrity_fingerprint.py`. This does not replace the human
final-integrity delta audit; it makes source drift visible so the audit cannot
quietly lag behind a changed manuscript or evidence file.

Final blocker report update on 2026-05-26:
`scripts/report_final_blockers.py` now prints a privacy-preserving final upload
blocker report. The current report has `repo_blockers=[]` and
`status=human_blocked`; the remaining human blockers are the missing private
author worksheet, target-route author confirmation, official OpenReview form
copy, and author/runtime/AI/media approval. `run_preupload_gate.py` now prints
this report before focused tests/build/staging, and the focused ACL pytest suite
now covers 37 tests after adding `tests/test_acl_final_blockers.py`. This is an
upload handoff aid, not upload authorization.

Final blocker clearance update on 2026-05-26:
`scripts/report_final_blockers.py` can now clear the human blockers once
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md` is complete and ignored. The current
repository still reports `status=human_blocked` because the private worksheet
does not exist, but a complete private worksheet can make the report return
`status=upload_ready` when repo evidence blockers are also clear. The report
continues to avoid printing private author values. The focused ACL pytest suite
now covers 46 tests.

Private author-gate semantic update on 2026-05-26:
`scripts/check_author_gate.py` now rejects filled but unsafe private decisions,
including failed final scans, negative approval wording, incomplete OpenReview
profiles, or final decision `do not upload`. The report exposes only
`invalid_fields` names and still does not print private values. The focused ACL
pytest suite now covers 48 tests.

Final blocker handoff detail update on 2026-05-26:
`scripts/report_final_blockers.py` now includes `human_blocker_details` for
each active human blocker. The details map blocker ids to the required action,
private worksheet field names, tracked copy-source files, and done condition.
This makes the final OpenReview handoff field-level without printing private
author values. When a complete ignored private worksheet clears the human
blockers, `human_blocker_details` is empty. The consolidated pre-upload gate
passes with 49 focused ACL tests and the staged PDF remains 12 A4 pages, PDF
1.5, and 306187 bytes.

OpenReview upload runbook update on 2026-05-26:
`OPENREVIEW_UPLOAD_RUNBOOK.md` now provides the final human-facing upload path:
create the ignored private worksheet, lock the route, copy metadata/checklist
fields into OpenReview, record author/runtime/AI/license/media decisions, run
`check_author_gate.py`, `report_final_blockers.py`, and
`run_preupload_gate.py`, and stop on any blocker or privacy leak. The focused
runbook test guards the four active human blocker ids, copy sources, final gate
commands, and `Do not upload` stop condition. `run_preupload_gate.py` now
includes this test in its focused pytest step; the consolidated gate passes
with 50 focused ACL tests and the staged PDF remains 12 A4 pages, PDF 1.5, and
306187 bytes.

OpenReview runbook prefill sync on 2026-05-26:
the upload runbook and final blocker report now include the repo-verifiable
prefill helper in the author handoff. The current blocker surface covers both
`private_author_gate_missing` and `private_author_gate_incomplete`; the final
exact-packet sequence is `run_preupload_gate.py`, then
`prefill_author_gate.py --apply --overwrite`, then `check_author_gate.py` and
`report_final_blockers.py`. This keeps staged packet evidence synchronized with
the ignored private worksheet without making the repository fill author, route,
OpenReview profile, approval, optional-media, or final-upload decisions.

Final next-action sequence update on 2026-05-26: `report_final_blockers.py`
now emits that same exact-packet sequence in `next_actions`, and
`report_goal_completion.py` forwards it. This keeps the machine-readable final
handoff aligned with `OPENREVIEW_UPLOAD_RUNBOOK.md`; it does not clear the
remaining human-only route, OpenReview form-copy, author, approval, media, or
final-upload gates.

OpenReview checklist gate update on 2026-05-26:
`scripts/check_openreview_checklist.py` and
`tests/test_acl_openreview_checklist.py` now guard
`OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md` as the copy source for the ARR /
OpenReview Responsible NLP checklist. The checker requires the expected 17
checklist questions, official policy URLs, current PDF anchors, no placeholder
text, no bare yes/no/N/A answers, and anonymous-review AI-assistance wording.
`run_preupload_gate.py` now runs this check after metadata consistency and
before citation/evidence/build/staging, and the focused ACL pytest suite now
covers 41 tests. This still does not copy the answers into the real OpenReview
form; final form copy remains a human gate.

Target-policy gate update on 2026-05-26:
`scripts/check_target_policy.py` and `tests/test_acl_target_policy.py` now guard
the ACL/ARR route notes. The checker keeps the packet in candidate mode by
requiring the EACL 2027 ARR route markers, official policy URLs, and the
Annual-ACL-not-final boundary, while rejecting unsupported Annual ACL 2027
final-ready wording. `run_preupload_gate.py` now runs this check before
metadata/checklist/citation/evidence/build/staging, and
`report_final_blockers.py` reports unsafe or missing target-policy notes as a
repo blocker. The focused ACL pytest suite now covers 45 tests. This still
does not choose the route for the authors.

Figure-driven ACL candidate update on 2026-05-27: after the Fig.3 red-material
diagnosis, the stale material-effect qualitative panel was removed from the
main paper and from final-integrity sources. The material-effect result is now
table-bounded, and the claim-boundary checker rejects reintroducing the stale
panel until clean original-MDL rerenders or replacement cases exist. The
post-Fig.3 `run_preupload_gate.py` pass rebuilt and staged an 11-page A4 PDF 1.5
candidate, 3,364,751 bytes, with the accepted imagegen/image2 v8 method-chain
schematic on page 2, real render/scene evidence on page 6, selected InternNav
Figure 3 on page 9, ordered `pdftotext` section checks, the reviewer-risk
Discussion reporting-pattern paragraph, and 69 focused tests.
The layout guard now rejects a float-only material-table page immediately before
Limitations.
Remaining blockers
are human-only: route lock, OpenReview form copy,
author/reviewer/submission-history decisions, runtime/AI/license/media
approvals, and final upload decision.

Latest visual-polish note on 2026-05-27: a local rendered-PDF review of all 11
pages found no overlap or clipped figures, but did flag two readability defects:
the Method opening line on page 4 had stretched spacing caused by a long
technical token, and the page-5 prose used the artifact-style token
`expanded30`. Both were corrected in `sections/method.tex` and
`sections/results.tex`; the claim boundary and experiment numbers are unchanged.

Figure 2 visual-polish note on 2026-05-27: the real-render evidence panel was
regenerated from the same source renders with cropped display views for the
white single-object proxy row. The caption now states that the top row is
cropped for display, and the nearby VLM text was compressed so Section 4.3 does
not leave an orphaned sentence fragment on page 6. No generated imagery was used
for empirical evidence. A subsequent visual pass kept the same render sources
but switched the top proxy row to cover-fit cropped display cells, removing most
gray side bands and making the white proxy objects larger in the integrated
page-6 PDF view. A follow-up proxy-row readability pass keeps the same raw
proxy-render pool but replaces the nearly blank `#0004` display example with
the more legible `#0023` pair; `tests/test_render_scene_evidence_figure.py`
guards against returning to an all-low-contrast top row and is included in the
consolidated preupload gate.
A later representative-pair compaction pass addressed the remaining PDF-scale
readability issue: the eight-cell render contact sheet still looked like
thumbnails, so `gen_render_scene_evidence_wide.py` now renders one proxy
original/noMDL pair and one GRScenes original/noMDL pair at larger cell width
from the same recorded sources. An oversized draft grew the build to 11 pages
and was rejected; the accepted compact layout keeps the ACL build at 10 A4 pages
while making the render evidence easier to inspect. A subsequent pure-visual
review still found the selected white proxy row too strip-like in the PDF, so
the generator now uses the same raw `#0023` proxy pair in a narrower
proxy-object cell while keeping the GRScenes scene row full width. The focused
Figure 2 test now checks the selected proxy row rather than only the proxy
candidate pool. The current local ACL build remains 10 A4 pages and renders the
updated Figure 2 on page 6 without overlap. The subsequent full pre-upload gate
passed with 72 focused tests and staged a 10-page A4 PDF 1.5 file of 3,471,360
bytes.
An additional local visual pass on the same page found that the front-view
proxy crop was still too low-detail for the paper narrative. The Figure 2
generator now uses the recorded `#0023` full-object back-view original/noMDL
pair (`A_back.png`/`B_back.png`) for the representative proxy row, while keeping
the GRScenes row unchanged. The selected-proxy readability test was tightened
to require minimum grayscale contrast `>=13.0`; the previous selected display
failed this gate at `12.32`, and the new display passes. This is a
presentation/sample-selection change over existing empirical render files, not
image generation and not a new experiment. The current rebuilt local ACL PDF is
10 A4 pages, PDF 1.5, and 3,487,597 bytes.
The subsequent full pre-upload gate passed again with 72 focused tests, a
53-source final-integrity fingerprint, clean ACL build, staging, scans, PDF
profile, and ordered text-section checks. The staged candidate
`paper/submissions/acl27_arr_candidate_20260526/main.pdf` is a 10-page A4 PDF
1.5 file of 3,487,597 bytes, and a rendered staged page-6 spot check shows the
refreshed Figure 2 without overlap.
A subsequent rendered-PDF spot check found that the #0023 back view still looked
like a low-detail gray slab at page scale. The current front-detail pass uses
the recorded `#0011` front-view original/noMDL proxy pair
(`A_front.png`/`B_front.png`) and replaces the selected-proxy contrast guard
with a front-detail edge-density guard that rejects back-only representative
views. The full pre-upload gate passed again with 72 focused tests, the
53-source fingerprint, clean build/staging, packet scans, PDF profile checks,
and ordered text-section checks. The current build and staged candidate are
identical 10-page A4 PDF 1.5 files of 3,493,873 bytes, and rendered page 6 shows
the drawer/handle details without overlap.
A follow-up pure visual review still found the flat front view usable but less
informative than an angled object render. The current Figure 2 proxy row uses
the recorded `#0011` top-front-right pair
(`A_top_front_right.png`/`B_top_front_right.png`) from the same empirical render
pool. The selected-proxy guard now requires a front/front-angled path plus both
minimum edge density and contrast, avoiding the earlier single-metric false
negative on smooth white geometry. The full pre-upload gate passed again with
72 focused tests, the 53-source fingerprint, clean build/staging, packet scans,
PDF profile checks, and ordered text-section checks. The current build and
staged candidate are identical 10-page A4 PDF 1.5 files of 3,514,678 bytes, and
rendered page 6 shows the angled proxy object, Figure 2 caption, and Table 2
without overlap.
A label-precision pass then changed the representative proxy-row sublabel from
the generic `#0011 full object view` to `#0011 top-front-right object view`, so
the figure text now matches the actual recorded camera direction. This was a
TDD-only figure-generator/label update over the same empirical render files, not
a new experiment and not an imagegen rerun. The full pre-upload gate passed
again with 73 focused tests, the 53-source fingerprint, clean build/staging,
packet scans, PDF profile checks, and ordered text-section checks. The current
build and staged candidate are identical 10-page A4 PDF 1.5 files of 3,515,110
bytes, with SHA-256
`2800402b662904faf83862cd1f5fd1374e9d81fa6bdd8768f72e0a59458fa794`; rendered
staged page 6 shows the angled proxy object, Figure 2 caption, and Table 2
without overlap.

Figure 2 cropped-proxy detail update on 2026-05-27: a follow-up page-6 visual
pass found that the same white `#0011` top-front-right proxy render remained
slightly faint at PDF scale. The generator now crops the existing real
Original MDL/noMDL pair to `(140, 40, 780, 720)`, discloses the crop in the
cell label as `#0011 cropped top-front-right object view`, and has a regression
test that requires improved minimum pair contrast over the uncropped view. This
is a figure-readability update over existing empirical renders, not imagegen
and not a new experiment. The subsequent full pre-upload gate passed with 75
focused tests, the 53-source fingerprint, clean build/staging, packet scans,
PDF profile checks, and ordered text-section checks. The current build and
staged candidate are identical 10-page A4 PDF 1.5 files of 3,553,091 bytes,
with SHA-256
`7fed84db45e19f2e2ed56a67452d27ea04d0e4ffcf9a582e6a591a9e254163fe`; rendered
staged page 6 shows the cropped proxy object, Figure 2 caption, and Table 2
without overlap.

Navigation visual-polish note on 2026-05-27: the selected official KuJiaLe
0036/0066 rollout stills now produce both the superseded single-column
`fig_internnav_rollout_0036_0066_column.png` and the retained full-width
`fig_internnav_rollout_0036_0066_main3_readable.png`, generated by
`paper/shared/figures/gen_internnav_main_readable.py`. The ACL PDF now uses the
single-column representative panel on the Limitations page so readers can
inspect a real navigation path panel without treating selected stills as the
quantitative InternNav result. A clean page-break attempt with a wider panel
grew the candidate and was rejected; the accepted layout preserves the 11-page
profile.
The red marks in the source video stills are InternNav visualization overlays:
`draw_action_pil()` draws red action arrows in the egocentric view and
`draw_trajectory()` draws the executed agent path in red on the top-down map.
The checked current Figure 3 source logs contain no `KooPbr`, `KooPbr_maps`,
`could not find module`, `Failed to create MDL shade node`, `C108`, or `C120`
signals. The current paper panel recolors those source-red agent overlays to
purple during composition, embeds a visible purple/green legend, and the caption
states that purple denotes executed paths/action arrows while green denotes
reference paths. Later reference-layout, page-8 polish, single-column Fig.3,
and v14 schematic passes preserved Figure 3's provenance.
The latest 2026-05-28 user-facing re-check of
`paper/venues/acl27/build/main.pdf` again renders page 9 as the InternNav
rollout panel, not an `Original MDL / ConvertAsset / NVIDIA` material-effect
contact sheet. The old red-material contact sheet was stale pre-rerender
evidence; the 2026-05-28 clean material-effect rerender now passes the
clean-provenance gate, while the ACL main text still keeps that evidence
table-bounded. The later 13:47 CST build re-check on the same path has SHA-256
`4f04c57047e395e2afc86e0adbd247fcf257a9e730e03e0c34a4846521d62250`, still
uses the `1050 x 718`
`fig_internnav_rollout_0036_0066_column.png` image for Figure 3, and has zero
strong-red pixels in the rendered page-9 figure, the Figure 3 source PNG, and
the current material-effect contact sheet. The source video stills do contain
red InternNav action/trajectory overlays before paper composition; the generator
recolors those overlay pixels to purple, and current selected-video logs contain
no `KooPbr` / module-resolution / shade-node error terms.

Method-chain imagegen note on 2026-05-27: after the explicit request to use the
project image-generation skill and image2 route for the method-chain diagram,
fresh backup candidates were generated and retained at
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v5_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v7_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v8_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v9_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v10_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v11_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v12_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v13_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v14_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v15_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v16_candidate.png`,
`paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v17_candidate.png`,
and `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v18_candidate.png`.
The accepted rerun is now copied to
`paper/shared/figures/fig_acl_method_chain_imagegen_v18.png` and referenced by
the ACL draft, with its exact prompt preserved at
`paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v18.prompt.txt`.
Compared with v16, v18 keeps the schematic-only role, preserves page-scale
balance for the VLM and InternNav blocks, keeps purple/green navigation paths,
preserves the `Target: box` Stage 3 text, uses the clearer `VLM Checks` title,
and leaves SR/SPL/NE as neutral metric tiles.
v10/v11 are retained only as rejected backups because v10 used a misleading NE
metric direction cue and v11 introduced a generated-text typo; v12/v13/v14/v15
and v16 are retained as superseded acceptable backups, while v17 is retained as
a rejected wrong-target-text audit artifact.
The schematic
remains claim-bounded: it is roadmap art, not empirical render, VLM, material,
or navigation evidence.

Four-gate narrative alignment note on 2026-05-27: a follow-up manuscript review
found that the Introduction still described the evidence base as two layers
after the paper had become a four-gate ACL story. `sections/intro.tex` now
introduces the same four gates used by Figure 1, Method, Results, and the claim
registry: proxy similarity, GRScenes VLM grounding, material-effect/NVIDIA
baseline risk, and scoped InternNav embodied-stack sanity. The rewritten
paragraph keeps the same claim boundary: no proxy score, selected visual panel,
or navigation sanity run stands in for broad downstream robustness. Rendered
PDF checks of pages 1--2 kept the then-current 11-page profile and did not
disturb Figure 1; the later reference-layout pull-up reduced the final staged
candidate to 10 pages.

Clean-pool Table 2 readability note on 2026-05-30: a local page-scale visual
review found that the GRScenes clean-pool pilot table was technically present
but too compressed when rendered through `\resizebox`. The table now uses
fixed-width text columns, keeps all original metric values, moves the shared
structured-text prompt detail into the caption, and puts pair-level caveats into
a table note below the rows. The focused layout test passes, the ACL build
remains an 11-page A4 PDF, the final LaTeX log has no overfull/undefined/warning
lines, and the rendered page-6 visual review passes for Figure 2 plus Table 2
readability. The staged candidate is now byte-identical to the build PDF with
SHA-256 `d03af3b4554951ccb51c3a224a8fbbd12fb517180dd36bad5672f0fb07006793`.
No new imagegen asset was generated in this iteration because the active defect
was tabular typography, while the accepted Figure 1 imagegen v18 schematic
remains unchanged.
