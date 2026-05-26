# ACL Final Integrity Delta Audit

Checked: 2026-05-26.

This audit is a current-manuscript integrity delta pass after the 20-reference
web-trail audit. It covers the exact ACL wrapper sources under
`paper/venues/acl27/sections/*.tex` plus `paper/shared/sections/appendix.tex`.
It is now paired with `FINAL_INTEGRITY_SOURCE_FINGERPRINT.json`, which records
the current SHA-256 fingerprint for the ACL manuscript, bibliography, policy,
OpenReview copy sources, key evidence tables, and reference web-trail sources
used by this audit.

It does not replace the final human upload step: if the manuscript,
bibliography, target venue, checklist wording, or supplemental packet changes,
rerun this audit, refresh the fingerprint with
`check_integrity_fingerprint.py --write`, and rerun the staging scans on the
exact upload artifact.

## Scope

| Gate | Coverage in this pass | Verdict |
| --- | --- | --- |
| Citation context | All 10 citation-bearing sentences in the current ACL wrapper were checked against the already verified source URLs and freshly opened primary/authoritative pages. | Pass for current source. |
| Data and quantitative claims | Main numerical claims in abstract, results, conclusion, and appendix were cross-checked against local CSV/JSON tables and evidence summaries. | Pass for current source. |
| Claim boundary | Strong/forbidden wording search covered broad benchmark, speedup, NVIDIA official-scene performance, population failure rate, procedural-texture success, learned classifier, R2R/MP3D, and manipulation claims. | Pass; no manuscript edit required. |
| Originality smoke | Exact-phrase web searches sampled distinctive manuscript sentences across abstract, introduction, method, results, discussion, conclusion, limitations, and appendix. | No copied-source finding in this smoke pass. |
| Venue policy freshness | Official ARR/EACL/ACLPUB pages were reopened on 2026-05-26. | Annual ACL 2027 remains unavailable; EACL 2027 is the public ACL-family ARR route. |
| Source freshness fingerprint | `FINAL_INTEGRITY_SOURCE_FINGERPRINT.json` covers 41 current source files, including ACL LaTeX, shared appendix/tables, `references.bib`, OpenReview copy sources, target-policy notes, reference web-trail, and key CSV/JSON evidence. | Pass for current source; `run_preupload_gate.py` now fails before staging if these sources drift. |

## Citation Context Findings

All citation contexts remain accurate at the level used in the manuscript.

| Context | Cited keys | Source basis | Verdict |
| --- | --- | --- | --- |
| R2R as real-environment VLN and REVERIE as remote object identification from referring instructions. | `Anderson2018Vision`, `Qi2020REVERIE` | CVF pages for R2R and REVERIE. | Pass |
| Shikra and Ferret as referential / coordinate / grounding interfaces. | `Chen2023Shikra`, `You2024Ferret` | arXiv Shikra page and OpenReview Ferret page. | Pass |
| Habitat, AI2-THOR, and ThreeDWorld as embodied/interactive simulation platforms. | `Savva2019Habitat`, `Kolve2017AI2THOR`, `Gan2021ThreeDWorld` | CVF, arXiv, and NeurIPS Datasets and Benchmarks pages. | Pass |
| Isaac/Orbit/Isaac Lab as USD/RTX/Isaac-family robotics simulation context. | `Mittal2023Orbit`, `Mittal2025Isaac` | ETH Research Collection ORBIT record and Isaac Lab arXiv page. | Pass |
| GRUtopia/GRScenes and InternNav/DualVLN as the scene/task and navigation-stack sources. | `Wang2024GRUtopia`, `Wei2026Ground` | GRUtopia arXiv page and DualVLN OpenReview page. | Pass |
| Domain randomization, photorealistic neural domain randomization, SynTable, and Synthetica as related synthetic-data routes. | `Tobin2017Domain`, `Tremblay2018Training`, `Zakharov2022Photo`, `Ng2023SynTable`, `Singh2025Synthetica` | CiNii/Crossref, DBLP/CVF, Springer, arXiv, and J-GLOBAL/DOI records. | Pass |
| SSIM, LPIPS, CLIP, and DINOv2 as perceptual/feature diagnostics. | `Wang2004Image`, `Zhang2018Unreasonable`, `Radford2021Learning`, `Oquab2023DINOv2` | CiNii/Crossref, CVF, PMLR, and OpenReview records. | Pass |

## Data-Claim Checks

| Manuscript claim | Local source checked | Result |
| --- | --- | --- |
| Four single-object assets, 24 matched render pairs; PSNR 35.52, SSIM 0.990, LPIPS 0.020, CLIP 0.925, DINOv2 0.872. | `paper/shared/evidence/raw/image_quality.csv` and `paper/shared/evidence/raw/feature_similarity.csv`; recomputed means. | Matches after rounding. |
| Clean GRScenes pool has 15 visual-QA PASS pairs; Gemma4 15/15 answers in each condition; normalized hits 8/15 and 6/15; Qwen 23/30 scorable rows and stated point-hit counts. | `paper/shared/tables/grscenes_vlm_clean_pool_pass15.csv`. | Matches. |
| Expanded30 stress set has Gemma4 30/30 answers, 27/30 and 29/30 normalized hits, 28/30 agreement; Qwen raw and normalized diagnostics as stated. | `paper/shared/tables/grscenes_vlm_stress_expanded30.csv`. | Matches. |
| Paired bootstrap intervals are descriptive and not population guarantees; InternNav SR/SPL/NE/TL intervals cross zero. | `paper/shared/tables/reviewer_closure_paired_ci.csv`. | Matches. |
| Material-effect bins: four covered bins have bounded three-condition support; clearcoat is a selected NVIDIA target-loss case; procedural texture is a limitation for both converted conditions. | `paper/shared/tables/material_effect_risk_matrix.csv`. | Matches. |
| Official KuJiaLe route covers 99 paired episodes across three local official scenes with SR/SPL/NE/TL means as stated. | `paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/paired_99_summary.json`. | Matches. |
| Official-scene stability has 18/18 required original/noMDL fresh-process runs and overlapping warmed-ready intervals. | `paper/shared/tables/official_scene_performance_summary.csv` and `paper/shared/evidence/raw/official_scene_submission_closure/official_scene_submission_closure_summary.json`. | Matches. |
| Appendix coordinate-only baseline wording: raw pixel center/oracle saturate 30/30; normalized-1000 bbox-center oracle is 30/30 under normalized scoring. | `paper/shared/tables/vlm_coordinate_baselines.csv`. | Matches. |

## Forbidden-Claim Search

The current ACL text explicitly negates the dangerous claims rather than making
them. Searches over ACL sections and appendix found no unsupported assertion of:

- broad embodied-navigation benchmarking;
- all-GRScenes, all-InteriorNav, R2R, MP3D, or manipulation robustness;
- official-scene noMDL speedup;
- NVIDIA official-scene performance comparison;
- population-level NVIDIA failure rate;
- procedural-texture preservation success;
- selected videos as quantitative evidence;
- a learned automatic safe-conversion classifier.

## Originality Smoke

Exact-phrase web searches sampled distinctive sentence fragments including:

- `We study MDL-to-UsdPreviewSurface conversion as a controlled within-simulation perturbation`
- `Scene conversion is usually treated as an engineering detail, but for a vision-language grounding benchmark`
- `The first gate preserves provenance and composition boundaries`
- `material perturbation, prompt contract, and coordinate interpretation interact`
- `answer accuracy, point grounding, and coordinate-frame compliance must be audited separately`
- `The official-scene performance table supports loadability rather than speedup`
- `Material conversion should be treated as a controlled perturbation in VLM and embodied-data evaluation`
- `The clean visual-QA pool has 15 pairs, but it remains a pilot control`

No copied-source finding was found in this smoke pass. This is still not a
substitute for the venue's own plagiarism screening or an institutional
similarity report.

## Venue Policy Check

Official pages reopened on 2026-05-26 confirmed the current route state:

- ARR Dates and Venues lists EACL 2027 with final ARR submission date
  August 3, 2026 and commitment date October 11, 2026.
- The official EACL 2027 site lists Athens, Greece, March 9-14, 2027, and the
  August 3, 2026 ARR deadline.
- The EACL 2027 main-paper page says the comprehensive CFP and detailed
  timetable are still being finalized.
- Public search still did not find an official Annual ACL 2027 CFP, author kit,
  city/date page, or commitment deadline.

## Commands Run

```bash
git status --short --branch
perl -0ne 'while(/((?:[^.!?]|\n){0,260}\\cite\w*\{[^}]+\}(?:[^.!?]|\n){0,260}[.!?])/g){...}' \
  paper/venues/acl27/sections/*.tex paper/shared/sections/appendix.tex
rg -n "(speed|faster|outperform|SOTA|state-of-the-art|benchmark|broad|all-|population|robust|official|NVIDIA|failure rate|guarantee|automatic|classifier|learned|significant|improve|improvement|best|all scenes|R2R|MP3D|manipulation)" \
  paper/venues/acl27/sections paper/shared/sections/appendix.tex
rg -n "[0-9]+(\\.[0-9]+)?(%|/|--| paired| scenes| episodes| runs| pages| targets| records| pairs| rows| CI| SPL| SR| NE| TL| M)" \
  paper/venues/acl27/sections paper/shared/sections/appendix.tex
python - <<'PY'
# recomputed proxy metric means from image_quality.csv and feature_similarity.csv
PY
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
```

## Remaining Gates

This pass narrows the remaining goal blockers to:

1. Lock the selected ACL-family route: EACL 2027 via ARR now, or wait for
   Annual ACL 2027's public official call.
2. Copy the checklist answers into the real OpenReview form after the final
   target and PDF are locked.
3. Obtain final author confirmation for runtime/AI-assistance wording and keep
   optional InteriorAgent / KuJiaLe scene-derived media excluded unless an
   explicit legal/anonymization path is approved.
4. Rerun this integrity delta, refresh
   `FINAL_INTEGRITY_SOURCE_FINGERPRINT.json`, clean PDF build, staging command,
   and anonymization scans after any future manuscript, bibliography, target,
   evidence, OpenReview-copy, or packet change.
