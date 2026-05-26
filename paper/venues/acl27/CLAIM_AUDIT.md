# ACL/ARR Claim Audit

Checked: 2026-05-26.

This audit maps the ACL-facing manuscript claims to existing evidence. It is a
submission-readiness checklist, not a new experiment.

## Supported Claims

| Claim | Manuscript use | Evidence |
| --- | --- | --- |
| ConvertAsset is a composition-preserving MDL-to-UsdPreviewSurface intervention. | Method | `convert_asset/no_mdl/`, `paper/shared/evidence/claims.yaml`, `docs/records/2026-05-26-paper-story-progress-snapshot.md` |
| Single-object proxy metrics are high but only a screening gate. | Abstract, Results | `paper/shared/evidence/raw/image_quality.csv`, `paper/shared/evidence/raw/feature_similarity.csv`, `paper/shared/evidence/claims.yaml` |
| GRScenes clean pool is pilot-only. | Abstract, Results, Limitations | `paper/shared/evidence/raw/grscene_vlm_grounding/clean_pool_probes/`, `paper/shared/tables/grscenes_vlm_clean_pool_pass15.csv` |
| GRScenes expanded30 is a frozen target-centered material-shift stress set. | Abstract, Results | `paper/shared/evidence/raw/grscene_vlm_grounding/stress_vlm_run_manifest_expanded30.json`, `paper/shared/tables/grscenes_vlm_stress_expanded30.csv` |
| Qwen2.5-VL exposes coordinate-contract sensitivity. | Abstract, Results, Discussion | `paper/shared/evidence/raw/grscene_vlm_grounding/stress_expanded30_probes/`, `paper/shared/tables/vlm_coordinate_baselines.csv` |
| NVIDIA baseline exists for selected material-effect bins, not for official-scene performance. | Results, Limitations | `paper/shared/evidence/raw/material_effect_baseline/`, `paper/shared/tables/material_effect_risk_matrix.csv` |
| Official KuJiaLe InternNav evidence is a scoped sanity run over 99 paired episodes. | Results, Discussion, Limitations | `paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/`, `paper/shared/tables/reviewer_closure_paired_ci.csv` |
| Official-scene load/render evidence supports stability/loadability, not speedup. | Results, Conclusion, Limitations | `paper/shared/evidence/raw/official_scene_submission_closure/`, `paper/shared/tables/official_scene_performance_summary.csv` |

## Disallowed Claims Removed Or Avoided

- Broad embodied-navigation benchmark completion.
- All-GRScenes, all-InteriorNav, R2R, MP3D, or manipulation robustness.
- Official-scene noMDL speedup.
- NVIDIA official-scene performance comparison.
- Population-level NVIDIA failure rate from the selected clearcoat case.
- Procedural-texture preservation success.
- Treating selected rollout videos as quantitative evidence.
- Treating the safe-conversion recommender as a learned classifier.

## External Venue And Citation Checks

- Generic official ACL style source checked from `acl-org/acl-style-files`:
  https://github.com/acl-org/acl-style-files
- ACLPUB style-guide entry checked:
  https://acl-org.github.io/ACLPUB/style.html
- Submission-readiness policy audit:
  `SUBMISSION_READINESS_AUDIT.md`
- Citation and provenance audit:
  `CITATION_PROVENANCE_AUDIT.md`
- Responsible NLP checklist draft:
  `RESPONSIBLE_NLP_CHECKLIST_DRAFT.md`
- Artifact provenance draft:
  `ARTIFACT_PROVENANCE_DRAFT.md`
- Compute/runtime summary draft:
  `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`
- Final submission packet checklist:
  `FINAL_SUBMISSION_PACKET_CHECKLIST.md`
- Current public search found a live EACL 2027 site and main-paper call page
  with August 3, 2026 ARR deadline, but the page says the complete CFP is still
  forthcoming:
  https://2027.eacl.org/
  https://2027.eacl.org/calls/papers/
- Existing Annual ACL 2027 target should therefore remain an ACL/ARR candidate
  wrapper until the official Annual ACL 2027 call and author kit are public, or
  until the authors explicitly retarget to EACL 2027 via ARR.

## Remaining Human Checks Before Submission

- Confirm the final target venue: Annual ACL 2027 via ARR, or another
  ACL-family venue.
- Re-check official page limit, anonymity, Responsible NLP Checklist, AI-use
  disclosure, and supplemental policy against the final target call.
- Re-run citation/provenance checks after any bibliography additions.
