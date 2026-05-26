# ACL Final Submission Packet Checklist

Checked: 2026-05-26.

This checklist defines the next submission-facing packet. It assumes the paper
is submitted through ARR or an ACL-family venue using the generic ACLPUB review
format until the final target call publishes conference-specific instructions.

## Packet Boundary

| Item | Include in review packet? | Notes |
| --- | --- | --- |
| Main PDF | Yes | Build from `paper/venues/acl27/main.tex`; latest local target is `paper/venues/acl27/build/main.pdf`. Rebuild from clean state immediately before upload. |
| ACL LaTeX source | Usually no, unless requested | Keep source repo-side for reproducibility; upload source only if the submission system requires it and after path/anonymization audit. |
| Bibliography | Yes, embedded in PDF/source package if source is requested | `paper/shared/references.bib` currently has DOI and/or URL metadata for all ACL-wrapper cited keys. |
| Main figures/tables | Yes, in PDF | Current ACL wrapper uses local ACL sections and shared figures/tables. Verify all captions remain claim-bounded. |
| Responsible NLP checklist | Yes, OpenReview form / required appendix if requested | Use `RESPONSIBLE_NLP_CHECKLIST_DRAFT.md`, `ARTIFACT_PROVENANCE_DRAFT.md`, `MODEL_AND_ASSET_LICENSE_AUDIT.md`, and `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` as source material. Replace section-title references with final PDF section/page/line references. |
| Supplemental stills/contact sheets/videos | No by default | Selected qualitative media is useful internally for figures/rebuttal, but InteriorAgent / KuJiaLe terms make optional scene-derived media a separate author/legal decision. Treat all videos as qualitative inspection evidence only. |
| Raw source scenes | No | GRScenes, InteriorAgent/KuJiaLe, and other source assets may carry separate terms; do not redistribute raw scene trees. |
| Full scratch noMDL USD trees | No | Generated outputs inherit source asset constraints and are too large for review upload. |
| InternNav raw frames / LMDBs / logs | No | Keep outside upload packet; include summaries and tables only. Optional scene-derived media requires explicit terms/anonymization approval. |
| Local model checkpoints | No | Report public model IDs, license, and checkpoint hashes instead. |
| Legacy shared workshop manuscript sections | No | Do not upload `paper/shared/sections/*` as an ACL supplement without filtering; those sections retain CVPR/workshop framing and a single-scene GRScenes speedup discussion that is not an ACL main claim. |

## Current Gate Status

| Gate | Evidence | Status |
| --- | --- | --- |
| ACL story and claim boundary | `CLAIM_AUDIT.md`; ACL local sections. | Ready for candidate ARR draft. |
| Clean PDF build | `make -C paper clean-acl27 && make -C paper acl27`. | Must be rerun immediately before upload. |
| Page/format sanity | `SUBMISSION_READINESS_AUDIT.md`; ACLPUB generic formatting check. | Candidate-ready under generic ACL long-paper budget; final venue-specific policy still external. |
| Citation DOI/URL metadata | `CITATION_PROVENANCE_AUDIT.md`; `paper/shared/references.bib`. | Ready for current citation set; re-check after any new citation. |
| Artifact provenance | `ARTIFACT_PROVENANCE_DRAFT.md`; `MODEL_AND_ASSET_LICENSE_AUDIT.md`. | Candidate-ready: Gemma4/Qwen public IDs are recorded, GRScenes license is recorded, and InteriorAgent terms set a no-optional-media safe boundary. Final author/legal review still applies. |
| Compute/runtime summary | `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`. | Candidate-ready; final author confirmation of the checked host/runtime is still needed. |
| Responsible NLP checklist | `RESPONSIBLE_NLP_CHECKLIST_DRAFT.md`; `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`. | OpenReview copy-ready packet now exists with current PDF section/page anchors; final form copy and any target-call wording remain human-gated. |
| Supplemental anonymization | `SUBMISSION_STAGING_AUDIT.md`; `paper/venues/acl27/scripts/stage_submission_packet.py`. | Minimal PDF-first staging smoke passed for the ignored local packet; final archive and optional media still need pre-upload re-scan. |
| Target-call lock | `TARGET_CALL_POLICY_AUDIT.md`. | EACL 2027 is a public ARR-family route with August 3, 2026 ARR deadline, but its full CFP is still forthcoming. Annual ACL 2027 CFP/author kit remains unavailable in checked official sources. |

## Candidate Staging Command

The current minimal staging command is:

```bash
python paper/venues/acl27/scripts/stage_submission_packet.py --force
```

It creates an ignored local packet at
`paper/submissions/acl27_arr_candidate_20260526/` containing only:

- `main.pdf`
- `openreview/RESPONSIBLE_NLP_CHECKLIST.md`
- `supplemental/README.md`
- `supplemental/manifest.json`

The `openreview/` file is a local copy source for the submission form, not a
paper supplement to upload unless the final venue explicitly requests it. The
script currently refuses `--include-media`; selected qualitative videos stay out
of the review packet because InteriorAgent / KuJiaLe terms make optional
scene-derived media a separate author/legal decision. See
`SUBMISSION_STAGING_AUDIT.md` for the 2026-05-26 smoke results.

## Anonymization Scan Commands

Run these against the exact upload directory or archive staging directory:

```bash
rg -n "/cpfs|/home/|/root/|zhuzihou|jandan138|github.com/jandan138|ConvertAsset.git" <upload-dir>
rg -n "Acknowledg|thanks|Acknowledgment" <upload-dir>
find <upload-dir> -type f \( -name "*.pdf" -o -name "*.mp4" -o -name "*.png" -o -name "*.json" -o -name "*.tex" -o -name "*.bib" \) -print
pdfinfo <upload-dir>/main.pdf
pdftotext <upload-dir>/main.pdf - | rg -n "Anonymous ACL submission|Anonymous ACL 2027 Submission"
pdftotext <upload-dir>/main.pdf - | rg -n "Limitations|Ethical Considerations|References"
```

Expected result:

- No local absolute paths, usernames, private repository URLs, or raw checkpoint
  paths in uploadable text/metadata.
- Review PDF uses anonymous author block and has no acknowledgments.
- `Limitations` and `Ethical Considerations` appear before `References`.
- Supplemental media is excluded unless a separate author/legal media path is
  approved; any future media must be described as selected qualitative evidence,
  not population-level quantitative evidence.

## Claim Guardrails

Allowed in the ACL packet:

- Material conversion is a measurable perturbation for VLM grounding and
  embodied-data reliability.
- GRScenes expanded30 is a frozen target-centered material-shift stress set.
- Official KuJiaLe InternNav evidence is a scoped 99-episode, three-scene
  downstream sanity result.
- Official-scene load/render measurements show successful repeated
  loadability/stability with overlapping ready-time intervals.
- NVIDIA material-effect evidence is selected: covered bins support bounded
  static plus selected qualitative comparison; clearcoat is a selected failure
  case; procedural texture is a limitation/investigation case.

Forbidden in the ACL packet:

- Broad embodied benchmark completion across GRScenes, R2R, MP3D, or all
  InteriorNav.
- Official-scene noMDL speedup.
- NVIDIA official-scene performance comparison.
- Population-level NVIDIA failure rate from selected cases.
- Procedural texture preservation success.
- Treating selected videos as quantitative evidence.
