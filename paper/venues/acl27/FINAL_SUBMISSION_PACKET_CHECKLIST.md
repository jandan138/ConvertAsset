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
| OpenReview metadata | Yes, OpenReview form | Use `OPENREVIEW_METADATA_PACKET.md` for title, abstract, ARR area, and keyword copy source. Re-check if the PDF changes. |
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
| Target-policy consistency | `TARGET_CALL_POLICY_AUDIT.md`; `TARGET_LOCK_OPENREVIEW_REHEARSAL.md`; `scripts/check_target_policy.py`; `tests/test_acl_target_policy.py`. | Automated check keeps the packet in ACL/ARR candidate mode, records EACL 2027 as the current public ARR route, and rejects unsupported Annual ACL 2027 final-ready wording. |
| Citation inventory / DOI/URL metadata | `CITATION_PROVENANCE_AUDIT.md`; `paper/shared/references.bib`; `scripts/check_citation_inventory.py`; `tests/test_acl_citation_inventory.py`. | Automated check passes for the current ACL citation set: 20 unique cited keys, no missing BibTeX entries, no cited key without DOI/URL, and exact coverage by the 2026-05-26 web-trail addendum. Re-check after any new citation. |
| Claim-boundary guard | `CLAIM_AUDIT.md`; `scripts/check_claim_boundaries.py`; `tests/test_acl_claim_boundaries.py`. | Automated check passes for the current ACL text and catches unguarded broad embodied robustness, official-scene speedup, NVIDIA official-scene performance, procedural-texture success, and related unsupported claims. |
| Artifact provenance | `ARTIFACT_PROVENANCE_DRAFT.md`; `MODEL_AND_ASSET_LICENSE_AUDIT.md`. | Candidate-ready: Gemma4/Qwen public IDs are recorded, GRScenes license is recorded, and InteriorAgent terms set a no-optional-media safe boundary. Final author/legal review still applies. |
| Compute/runtime summary | `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`. | Candidate-ready; final author confirmation of the checked host/runtime is still needed. |
| OpenReview metadata | `OPENREVIEW_METADATA_PACKET.md`; `scripts/check_metadata_consistency.py`; `tests/test_acl_metadata_consistency.py`. | Title and 189-word abstract are copy-ready and now have an automated drift check against `main.tex` and `sections/abstract.tex`; recommended primary ARR area is `Multimodality and Language Grounding to Vision, Robotics and Beyond`, with `Resources and Evaluation` as secondary fit. |
| OpenReview Responsible NLP checklist | `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`; `scripts/check_openreview_checklist.py`; `tests/test_acl_openreview_checklist.py`. | Copy-ready source now has an automated check for the expected 17 ARR checklist questions, official policy URLs, current PDF anchors, no placeholder text, no bare yes/no/N/A answers, and anonymous-review AI-assistance wording. Final form copy and target-call wording remain human-gated. |
| Evidence-number consistency | `scripts/check_evidence_numbers.py`; `tests/test_acl_evidence_numbers.py`; `FINAL_INTEGRITY_DELTA_AUDIT.md`. | Automated checker reads local evidence CSV/JSON artifacts and verifies the ACL manuscript/OpenReview metadata still contain the matching proxy, VLM, InternNav, official-scene, and coordinate-baseline numbers. |
| Final-integrity source freshness | `FINAL_INTEGRITY_SOURCE_FINGERPRINT.json`; `scripts/check_integrity_fingerprint.py`; `tests/test_acl_integrity_fingerprint.py`. | Automated checker validates 41 current manuscript, bibliography, policy, OpenReview-copy, reference web-trail, table, and CSV/JSON evidence sources before staging. If any source changes, refresh the human integrity audit and rewrite the fingerprint before upload. |
| Final blocker report | `scripts/report_final_blockers.py`; `tests/test_acl_final_blockers.py`. | Read-only report currently returns `status=human_blocked` with no repo blockers and four human blockers because the private author worksheet is not filled. Once the ignored private worksheet is complete, the report can clear the route, OpenReview form-copy, runtime/AI/media, and final upload-decision blockers without printing private author values. |
| Author/OpenReview human gates | `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md`; `OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md`; `scripts/check_author_gate.py`; `tests/test_acl_author_gate.py`. | Blank template, fill-order guide, and private worksheet checker exist. Fill only a private ignored copy, not the tracked template and not the review packet. The checker is expected to fail until `OPENREVIEW_AUTHOR_GATE_FILLED.local.md` exists and required fields are filled. |
| Responsible NLP checklist | `RESPONSIBLE_NLP_CHECKLIST_DRAFT.md`; `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`; `scripts/check_openreview_checklist.py`. | OpenReview copy-ready packet now exists with current PDF section/page anchors and automated copy-readiness checks; final form copy and any target-call wording remain human-gated. |
| Supplemental anonymization | `SUBMISSION_STAGING_AUDIT.md`; `paper/venues/acl27/scripts/stage_submission_packet.py`. | Minimal PDF-first staging smoke passed for the ignored local packet; final archive and optional media still need pre-upload re-scan. |
| Consolidated pre-upload gate | `scripts/run_preupload_gate.py`; `tests/test_acl_preupload_gate.py`; `tests/test_acl_author_gate.py`; `tests/test_acl_target_policy.py`; `tests/test_acl_citation_inventory.py`; `tests/test_acl_integrity_fingerprint.py`; `tests/test_acl_final_blockers.py`; `tests/test_acl_openreview_checklist.py`; `SUBMISSION_STAGING_AUDIT.md`. | Repository-side rehearsal command passes on the current candidate state: claim/target-policy/metadata/checklist/citation-inventory/evidence-number/fingerprint gates, final blocker report, focused tests, clean PDF build, LaTeX log scan, five-file packet staging, adjacent checksum-sidecar validation, private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`, and ordered `pdftotext` markers. The current profile guard enforces a 12-page cap, A4 page size, and PDF 1.5 for this candidate packet. |
| Target-call lock | `TARGET_CALL_POLICY_AUDIT.md`; `TARGET_LOCK_OPENREVIEW_REHEARSAL.md`. | EACL 2027 is a public ARR-family route with August 3, 2026 ARR deadline, but its full CFP is still forthcoming. Annual ACL 2027 CFP/author kit remains unavailable in checked official sources. Author route/profile/reviewer-registration/preprint decisions remain human-gated. |

## Candidate Staging Command

The primary repository-side rehearsal command is:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

It wraps the local automated gate: claim-boundary check, target-policy
consistency check, OpenReview metadata consistency check, OpenReview checklist copy-readiness check,
citation-inventory check, evidence-number consistency check,
final-integrity source fingerprint check, final blocker report, focused ACL
pytest suite, clean ACL PDF rebuild, final LaTeX log scan,
candidate packet staging, exact packet inventory, adjacent checksum-sidecar
validation, private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`,
and `pdftotext` section/title checks.

For a narrower staging-only smoke, the underlying commands are:

```bash
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_target_policy.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
python paper/venues/acl27/scripts/check_openreview_checklist.py
python paper/venues/acl27/scripts/check_citation_inventory.py
python paper/venues/acl27/scripts/check_evidence_numbers.py
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/report_final_blockers.py
python paper/venues/acl27/scripts/stage_submission_packet.py --force
```

It creates an ignored local packet at
`paper/submissions/acl27_arr_candidate_20260526/` containing only:

- `main.pdf`
- `openreview/METADATA.md`
- `openreview/RESPONSIBLE_NLP_CHECKLIST.md`
- `supplemental/README.md`
- `supplemental/manifest.json`

The staging command also writes the ignored adjacent local checksum sidecar
`paper/submissions/acl27_arr_candidate_20260526.sha256`. The sidecar is not
part of the review packet; it records SHA-256 digests for exactly the five
staged files so the final upload can be checked against the rehearsed packet.

The `openreview/` files are local copy sources for submission form fields, not
paper supplements to upload unless the final venue explicitly requests them. The
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
- Review PDF remains within the current candidate profile: at most 12 pages,
  A4 page size, and PDF 1.5. Update the profile cap only after a final
  venue-policy review.
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
