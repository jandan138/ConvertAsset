# ACL Citation And Provenance Audit

Checked: 2026-05-26.

This audit covers citations used by the ACL wrapper in
`paper/venues/acl27/sections/*.tex` plus `paper/shared/sections/appendix.tex`.
It verifies local citation resolution, permanent identifiers, and the
2026-05-26 web-trail existence check for the current 20-reference ACL wrapper.
It is still narrower than a final full-submission integrity pass because it
does not re-check every citation context, data claim, or originality sample.

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
or URL metadata for every key cited by the ACL wrapper. The 2026-05-26
web-trail pass verified all 20 current ACL-wrapper references against arXiv,
CVF, OpenReview, PMLR, NeurIPS, ETH Research Collection, CiNii/Crossref-backed
records, J-GLOBAL, Springer, ECVA, DBLP, or DOI redirects, depending on the
reference.

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
| `Singh2025Synthetica` | Formal IROS DOI and arXiv URL present. | Keep; DOI resolved to IEEE document `11247126` in the 2026-05-26 check. |
| `Savva2019Habitat` | DOI and CVF URL present. | Keep. |
| `Kolve2017AI2THOR` | arXiv DOI and URL present. | Keep unless an archival version appears. |
| `Gan2021ThreeDWorld` | NeurIPS Datasets and Benchmarks URL present. | Keep. |
| `Tobin2017Domain` | DOI and arXiv URL present. | Keep. |
| `Tremblay2018Training` | DOI and CVF URL present. | Keep. |
| `Zakharov2022Photo` | Springer ECCV DOI and ECVA URL present. | Keep. |
| `Wang2004Image` | DOI present. | Keep. |
| `Zhang2018Unreasonable` | DOI and CVF URL present. | Keep. |
| `Radford2021Learning` | PMLR URL present. | Keep. |
| `Oquab2023DINOv2` | TMLR/OpenReview URL present. | Keep. |

## Artifact Provenance Status

| Artifact family | Cited / described in manuscript | Current provenance status | Follow-up |
| --- | --- | --- | --- |
| GRUtopia / GRScenes | Cited via `Wang2024GRUtopia`; evidence under `paper/shared/evidence/raw/grscene_vlm_grounding/`. | Scientific source cited; local asset mirror paths and scratch/noMDL conversion manifests are documented; public metadata checked this turn reports CC BY-NC-SA 4.0 for GRScenes. | Keep raw scenes and full scratch outputs out of the upload package. |
| InternNav / DualVLN | Cited via `Wei2026Ground`; evidence under `paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/`. | Scientific source and OpenReview URL cited; public repository pages checked this turn report MIT for InternNav code, CC BY-NC-SA 4.0 for open InternData-N1 data, and inherited licenses for other datasets. | Keep separate dataset terms visible in the final checklist. |
| InteriorAgent / KuJiaLe official scenes | Described as official KuJiaLe `val_unseen` evidence. | Local evidence exists; public Hugging Face metadata lists `interioragent-terms-of-use`, and the linked terms prohibit redistributing data or modified data. | Add official citation/license entry if available; exclude optional scene-derived media by default. |
| NVIDIA / Isaac Sim / USD / MDL | Method and related work reference Isaac/Orbit/Isaac Lab; repo docs cover MDL-to-UsdPreviewSurface conversion. | Simulation/framework provenance is partially covered. | Add official software/version citation and license note in supplement/checklist. |
| VLM systems used in probes | Results mention Gemma4 and Qwen2.5-VL. | Public IDs and checked revisions are recorded in `MODEL_AND_ASSET_LICENSE_AUDIT.md`; metadata reports Apache-2.0 for both checked model cards. | Add final model citation wording if the venue form requests it. |
| Selected qualitative rollout videos | Evidence package exists under `official_selected_qualitative_videos/`. | Videos are qualitative only, not quantitative evidence, and scene-derived media is excluded from the safe packet by default. | Use internally for figure/rebuttal inspection unless authors approve separate media redistribution. |

## Current Claim-Safety Result

The current bibliography is build-clean, source-linked, and web-trail verified
for all 20 current ACL-wrapper references. The remaining final-submission risks
are citation-context/data/originality checking after any edits, artifact/model
provenance, and final-venue policy, not fabricated or undefined references in
the current ACL wrapper. The final submission gate should require:

1. No undefined citations in a clean build.
2. Every cited scientific artifact keeps DOI, ACL Anthology URL, OpenReview/PMLR
   URL, arXiv DOI/URL, or an explicit reason why no permanent identifier exists.
3. Every dataset/software artifact used in experiments has citation, access
   route, license/terms note, and intended-use note in the paper, appendix, or
   Responsible NLP checklist.
4. Any author-identifying local paths are removed or anonymized from uploadable
   supplemental artifacts.
5. A final citation-context/data/originality pass is rerun after any manuscript
   or bibliography change.
