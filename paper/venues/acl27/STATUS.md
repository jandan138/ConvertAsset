# ACL 2027 Version Status

Template provenance: ACL 2027 conference-specific files are not published in this repo. The wrapper now vendors the generic official *ACL style files `acl.sty` and `acl_natbib.bst` from `acl-org/acl-style-files` so local compile checks can run until the ACL 2027 author kit or conference-specific instructions are published. Provenance checked on 2026-05-23: ACLPUB's formatting page points authors to `https://github.com/acl-org/acl-style-files`.

Readiness: candidate-target scaffold for the user-requested Annual ACL 2027 Japan route.

Local section overrides: `sections/abstract.tex`, `sections/intro.tex`, and `sections/conclusion.tex` reframe the shared evidence around VLM grounding protocol reliability under material perturbations. The ACL wrapper still inputs the shared related work, method, experiments, and discussion sections directly. It also adds ACL-required local compliance sections for limitations and ethical considerations.

Known missing checks: official ACL 2027 CFP, official city/date confirmation in a public ACL 2027 site, ACL 2027 submission deadline, ARR cycle mapping, final page-limit policy, Responsible NLP Checklist requirements, anonymity policy, AI-use disclosure policy, official style-file provenance, DOI/ACL Anthology citation audit, and full shared-section rewrite toward computational linguistics.

Venue fit: current content is still a synthetic-data and simulation paper. To make this viable for ACL, the main story should shift toward multimodal language grounding, vision-language model evaluation, embodied/agent data generation, and data-conversion reliability for NLP/VLM benchmarks. Without that pivot, AAAI remains the stronger general AI target.

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

CVPR workshop reviewer carry-over status on 2026-05-26: the expanded30 VLM grounding route addresses the most dangerous "proxy-only AI task" weakness only at the image-level grounding layer. It does not mean InternNav, VLN, manipulation, or broad embodied downstream validation has been introduced. Reviewer concerns about overbroad guidelines have been addressed by narrowing the claim to a frozen target-centered stress set. Reviewer concerns about empirical scarcity are partially mitigated by GRScenes targets beyond the original four furniture assets. NVIDIA official-tool baseline and per-MDL-effect analysis are now represented by the material-effect condition manifests, selected qualitative/failure panels, PXR diagnostic, and risk matrix in the shared manuscript: four GRScenes-covered bins have bounded selected qualitative support, clearcoat is a selected NVIDIA target-loss failure case, and procedural texture is a preservation limitation. Multi-scene performance statistics and an automatic safe-conversion recommender remain open.

Near-term ACL target: a defensible ACL/ARR draft should present the current work as a VLM grounding reliability diagnostic under 3D material perturbations, not as a completed embodied benchmark paper. Before claiming ACL-main readiness, add at least point baselines/coordinate ablations, ACL/VLM related-work expansion, citation/integrity audit, and a clear decision on whether InternNav/VLN is a real experiment or future work. A stronger main-conference version should additionally add a real embodied downstream task, multi-scene performance statistics, or a rule-based safe-conversion recommender.

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
