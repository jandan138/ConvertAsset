# ACL Citation And Provenance Audit

Checked: 2026-05-26.

This audit covers citations used by the ACL wrapper in
`paper/venues/acl27/sections/*.tex` plus `paper/shared/sections/appendix.tex`.
It is narrower than a full bibliography cleanup: it verifies local citation
resolution and identifies permanent-identifier/provenance gaps before final
ARR/ACL submission.

## Local Citation Resolution

Command used:

```bash
perl -0ne 'while(/\\cite\w*\{([^}]+)\}/g){for $k (split /,/, $1){$k =~ s/^\s+|\s+$//g; print "$k\n"}}' \
  paper/venues/acl27/sections/*.tex paper/shared/sections/appendix.tex | sort -u
```

Unique cited keys in the current ACL wrapper:

```text
Anderson2018Vision
Chen2023Shikra
Gan2021ThreeDWorld
Kolve2017AI2THOR
Mittal2023Orbit
Mittal2025Isaac
Ng2023SynTable
Oquab2023DINOv2
Qi2020REVERIE
Radford2021Learning
Savva2019Habitat
Singh2025Synthetica
Tobin2017Domain
Tremblay2018Training
Wang2004Image
Wang2024GRUtopia
Wei2026Ground
You2024Ferret
Zakharov2022Photo
Zhang2018Unreasonable
```

All 20 keys are present in `paper/shared/references.bib`, and the latest
`make -C paper clean-acl27 && make -C paper acl27` build resolved the
bibliography without undefined citations.

## Permanent-Identifier Status

ACLPUB formatting guidance says references should include DOI where possible,
or ACL Anthology links as a second resort. The current `.bib` now includes DOI
or URL metadata for every key cited by the ACL wrapper. A few entries still need
final proceedings-level confirmation, but the previous build-clean-only state
has been upgraded to source-linked citation metadata.

| Key | Current local identifier status | Submission action |
| --- | --- | --- |
| `Anderson2018Vision` | DOI and CVF URL present. | Keep; verify proceedings name before final. |
| `Qi2020REVERIE` | DOI and CVF URL present. | Keep; verify proceedings name before final. |
| `Mittal2023Orbit` | DOI present. | Keep. |
| `Wang2024GRUtopia` | arXiv DOI and URL present. | Verify whether an archival venue exists before final. |
| `Chen2023Shikra` | arXiv DOI and URL present. | Keep unless an archival version appears. |
| `You2024Ferret` | ICLR/OpenReview URL present. | Keep; add DOI only if ICLR/CrossRef metadata appears. |
| `Wei2026Ground` | ICLR/OpenReview URL present. | Keep; verify final ICLR metadata before submission. |
| `Mittal2025Isaac` | arXiv DOI and URL present. | Keep unless an archival version appears. |
| `Ng2023SynTable` | arXiv DOI and URL present. | Keep unless an archival version appears. |
| `Singh2025Synthetica` | arXiv URL present for the formal IROS entry. | Verify final IEEE DOI if available. |
| `Savva2019Habitat` | DOI and CVF URL present. | Keep. |
| `Kolve2017AI2THOR` | arXiv DOI and URL present. | Keep unless an archival version appears. |
| `Gan2021ThreeDWorld` | NeurIPS Datasets and Benchmarks URL present. | Keep. |
| `Tobin2017Domain` | DOI and arXiv URL present. | Keep. |
| `Tremblay2018Training` | DOI and CVF URL present. | Keep. |
| `Zakharov2022Photo` | ECVA URL and arXiv DOI present. | Verify final Springer/ECCV DOI if desired. |
| `Wang2004Image` | DOI present. | Keep. |
| `Zhang2018Unreasonable` | DOI and CVF URL present. | Keep. |
| `Radford2021Learning` | PMLR URL present. | Keep. |
| `Oquab2023DINOv2` | TMLR/OpenReview URL present. | Keep. |

## Artifact Provenance Status

| Artifact family | Cited / described in manuscript | Current provenance status | Follow-up |
| --- | --- | --- | --- |
| GRUtopia / GRScenes | Cited via `Wang2024GRUtopia`; evidence under `paper/shared/evidence/raw/grscene_vlm_grounding/`. | Scientific source cited; local asset mirror paths and scratch/noMDL conversion manifests are documented; public project/package pages checked this turn report MIT for GRUtopia code and CC BY-NC-SA 4.0 for open GRScenes. | Confirm exact dataset terms for final upload package. |
| InternNav / DualVLN | Cited via `Wei2026Ground`; evidence under `paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/`. | Scientific source and OpenReview URL cited; public repository pages checked this turn report MIT for InternNav code, CC BY-NC-SA 4.0 for open InternData-N1 data, and inherited licenses for other datasets. | Verify separate InteriorAgent/KuJiaLe terms. |
| InteriorAgent / KuJiaLe official scenes | Described as official KuJiaLe `val_unseen` evidence. | Local evidence exists and the public Hugging Face dataset page lists `interioragent-terms-of-use`; full terms text still needs final review. | Add official citation/license entry if available. |
| NVIDIA / Isaac Sim / USD / MDL | Method and related work reference Isaac/Orbit/Isaac Lab; repo docs cover MDL-to-UsdPreviewSurface conversion. | Simulation/framework provenance is partially covered. | Add official software/version citation and license note in supplement/checklist. |
| VLM systems used in probes | Results mention Gemma4 and Qwen2.5-VL. | Qwen2.5-VL and Google Gemma4 model-card license/source pages checked; Gemma4 local quantized checkpoint still needs exact public model ID/commit matching. | Add model citations/version/source fields before final submission. |
| Selected qualitative rollout videos | Evidence package exists under `official_selected_qualitative_videos/`. | Videos are qualitative only and not used as quantitative evidence. | Include only as supplemental/figure support; anonymize packaged paths. |

## Current Claim-Safety Result

The current bibliography is build-clean and now source-linked for all ACL
wrapper citations. The remaining final-submission risks are artifact/model
provenance and final-venue policy, not undefined citations. The final submission
gate should require:

1. No undefined citations in a clean build.
2. Every cited scientific artifact keeps DOI, ACL Anthology URL, OpenReview/PMLR
   URL, arXiv DOI/URL, or an explicit reason why no permanent identifier exists.
3. Every dataset/software artifact used in experiments has citation, access
   route, license/terms note, and intended-use note in the paper, appendix, or
   Responsible NLP checklist.
4. Any author-identifying local paths are removed or anonymized from uploadable
   supplemental artifacts.
