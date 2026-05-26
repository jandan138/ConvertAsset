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
or ACL Anthology links as a second resort. The local `.bib` is not yet fully
submission-normalized under that standard.

| Key | Current local identifier status | Submission action |
| --- | --- | --- |
| `Anderson2018Vision` | DOI present. | Keep; verify proceedings name before final. |
| `Qi2020REVERIE` | DOI present. | Keep; verify proceedings name before final. |
| `Mittal2023Orbit` | DOI present. | Keep. |
| `Wang2024GRUtopia` | arXiv DOI present. | Verify whether an archival venue exists before final. |
| `Chen2023Shikra` | arXiv-only local entry, no DOI/URL field. | Add arXiv DOI or URL if retained. |
| `You2024Ferret` | ICLR entry, no OpenReview/DOI/URL field. | Add OpenReview URL or DOI-equivalent metadata. |
| `Wei2026Ground` | ICLR 2026 entry, no OpenReview/DOI/URL field. | Verify final ICLR metadata and add URL. |
| `Mittal2025Isaac` | arXiv-only local entry, no DOI/URL field. | Verify arXiv metadata and add DOI/URL. |
| `Ng2023SynTable` | arXiv-only local entry, no DOI/URL field. | Add arXiv DOI or URL if retained. |
| `Singh2025Synthetica` | IROS entry, no DOI/URL field. | Verify final proceedings metadata and add DOI if available. |
| `Savva2019Habitat` | ICCV entry, no DOI/URL field. | Add DOI or official proceedings URL if available. |
| `Kolve2017AI2THOR` | arXiv-only local entry, no DOI/URL field. | Add arXiv DOI or URL if retained. |
| `Gan2021ThreeDWorld` | NeurIPS entry, no DOI/URL field. | Add OpenReview/proceedings URL if available. |
| `Tobin2017Domain` | IROS entry, no DOI/URL field. | Add DOI if available. |
| `Tremblay2018Training` | CVPRW entry, no DOI/URL field. | Add DOI or proceedings URL if available. |
| `Zakharov2022Photo` | ECCV entry, no DOI/URL field. | Add DOI/proceedings URL if available. |
| `Wang2004Image` | Journal entry, no DOI field. | Add DOI. |
| `Zhang2018Unreasonable` | CVPR entry, no DOI field. | Add DOI or official CVF URL. |
| `Radford2021Learning` | ICML/PMLR entry, no URL field. | Add PMLR URL. |
| `Oquab2023DINOv2` | TMLR entry, no URL field. | Add OpenReview/TMLR URL. |

## Artifact Provenance Status

| Artifact family | Cited / described in manuscript | Current provenance status | Follow-up |
| --- | --- | --- | --- |
| GRUtopia / GRScenes | Cited via `Wang2024GRUtopia`; evidence under `paper/shared/evidence/raw/grscene_vlm_grounding/`. | Scientific source cited; local asset mirror paths and scratch/noMDL conversion manifests are documented. | Add explicit license/access note in final supplement/checklist. |
| InternNav / DualVLN | Cited via `Wei2026Ground`; evidence under `paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/`. | Scientific source cited; local official KuJiaLe route documented. | Verify final paper URL/metadata and dataset/access terms. |
| InteriorAgent / KuJiaLe official scenes | Described as official KuJiaLe `val_unseen` evidence. | Local evidence exists, but manuscript bibliography does not yet contain a separate InteriorAgent/KuJiaLe dataset citation if one is required. | Add official citation/license entry if available. |
| NVIDIA / Isaac Sim / USD / MDL | Method and related work reference Isaac/Orbit/Isaac Lab; repo docs cover MDL-to-UsdPreviewSurface conversion. | Simulation/framework provenance is partially covered. | Add official software/version citation and license note in supplement/checklist. |
| VLM systems used in probes | Results mention Gemma4 and Qwen2.5-VL. | Experimental outputs are recorded, but model/provider citations are not yet fully bibliography-normalized. | Add model citations/version/source fields before final submission. |
| Selected qualitative rollout videos | Evidence package exists under `official_selected_qualitative_videos/`. | Videos are qualitative only and not used as quantitative evidence. | Include only as supplemental/figure support; anonymize packaged paths. |

## Current Claim-Safety Result

The current bibliography is build-clean but not yet final-submission clean.
This is enough for manuscript iteration and local PDF generation, but not enough
to mark the ACL/ARR goal complete. The final submission gate should require:

1. No undefined citations in a clean build.
2. Every cited scientific artifact has DOI, ACL Anthology URL, OpenReview/PMLR
   URL, arXiv DOI/URL, or an explicit reason why no permanent identifier exists.
3. Every dataset/software artifact used in experiments has citation, access
   route, license/terms note, and intended-use note in the paper, appendix, or
   Responsible NLP checklist.
4. Any author-identifying local paths are removed or anonymized from uploadable
   supplemental artifacts.
