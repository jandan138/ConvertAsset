# ACL Final Submission Packet Checklist

Checked: 2026-05-30.

This checklist defines the next submission-facing packet. It assumes the paper
is submitted through ARR or an ACL-family venue using the generic ACLPUB review
format until the final target call publishes conference-specific instructions.

2026-05-30 status sync: no packet boundary changed after the current v18 PDF
candidate. The first-page ACL-fit recheck, reviewer-risk refresh, Figure 3
red-material recheck, target-policy refresh, and full-PDF visual recheck all
support the same conclusion: the repository-side packet is candidate-ready, but
final upload remains blocked by human route/OpenReview/approval fields.

2026-05-30 provenance-caption, conclusion, and layout polish: the packet
boundary still did not change, but the candidate PDF was rebuilt and restaged
after Figure 3's caption was tightened to say the selected `Original MDL` cells
passed a log-checked clean rerender/provenance gate, after the conclusion was
strengthened into an evidence-gate takeaway, and after the manual Introduction
page break before the contribution list was removed. The refreshed staged PDF
is 11 pages, 4,066,770 bytes, and byte-identical to the build PDF with SHA-256
`177466b7d0cf6a557f73f792dc6f718fdae8f42663e7398a54bc2d9252cde356`.
The full pre-upload gate passed with a 57-source final-integrity fingerprint
and 93 focused tests.

2026-05-30 InternNav scope wording polish: the packet boundary still did not
change after replacing the awkward `all-InteriorNav` limitation wording with
explicit `all InternNav or InteriorAgent settings` scope language and extending
the claim-boundary guard to catch natural broad-scope variants. The refreshed
staged PDF is 11 pages, 4,066,626 bytes, and byte-identical to the build PDF
with SHA-256
`137370b33b567ebc55ab6f88ef5d6e6860b6e61debf133e8077b14a22b454c98`.
The adjacent checksum sidecar has SHA-256
`0439826be4d8dd283dc82b277a8a206f6964e031d43bee0f3cadaf2bbf7fb86c`.
The consolidated pre-upload gate passed again with 57 fingerprinted sources and
93 focused tests. Targeted page-9 visual review passed after rerendering
`paper/submissions/acl27_arr_candidate_20260526/main.pdf` at 150 DPI.

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
| First-page reviewer fit | `FIRST_PAGE_ACL_FIT_AUDIT.md`; `paper/shared/evidence/raw/acl27_visual_review/first_page_acl_fit_review_20260530.json`. | Current page-1/page-2 visual review passes with human route caveat. The title, abstract, opening introduction, Figure 1 v18, and contribution list foreground VLM grounding and claim-bounded evaluation rather than a standalone conversion tool. |
| Clean PDF build | `make -C paper clean-acl27 && make -C paper acl27`. | Must be rerun immediately before upload. |
| Page/format sanity | `SUBMISSION_READINESS_AUDIT.md`; ACLPUB generic formatting check. | Candidate-ready under generic ACL long-paper budget; final venue-specific policy still external. |
| Target-policy consistency | `TARGET_CALL_POLICY_AUDIT.md`; `TARGET_LOCK_OPENREVIEW_REHEARSAL.md`; `scripts/check_target_policy.py`; `tests/test_acl_target_policy.py`. | Automated check keeps the packet in ACL/ARR candidate mode, records EACL 2027 as the current public ARR route, requires the ACL Resolutions source for the `2027 ACL Conference Branding` marker, and rejects unsupported Annual ACL 2027 final-ready wording. |
| Citation inventory / DOI/URL metadata | `CITATION_PROVENANCE_AUDIT.md`; `paper/shared/references.bib`; `scripts/check_citation_inventory.py`; `tests/test_acl_citation_inventory.py`. | Automated check passes for the current ACL citation set: 20 unique cited keys, no missing BibTeX entries, no cited key without DOI/URL, and exact coverage by the 2026-05-26 web-trail addendum. Re-check after any new citation. |
| Claim-boundary guard | `CLAIM_AUDIT.md`; `scripts/check_claim_boundaries.py`; `tests/test_acl_claim_boundaries.py`. | Automated check passes for the current ACL text and catches unguarded broad embodied robustness, official-scene speedup, NVIDIA official-scene performance, procedural-texture success, and related unsupported claims. |
| Artifact provenance | `ARTIFACT_PROVENANCE_DRAFT.md`; `MODEL_AND_ASSET_LICENSE_AUDIT.md`. | Candidate-ready: Gemma4/Qwen public IDs are recorded, GRScenes license is recorded, and InteriorAgent terms set a no-optional-media safe boundary. Final author/legal review still applies. |
| Compute/runtime summary | `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`. | Candidate-ready; final author confirmation of the checked host/runtime is still needed. |
| OpenReview metadata | `OPENREVIEW_METADATA_PACKET.md`; `scripts/check_metadata_consistency.py`; `tests/test_acl_metadata_consistency.py`. | Title and 183-word abstract are copy-ready and now have an automated drift check against `main.tex` and `sections/abstract.tex`; recommended primary ARR area is `Multimodality and Language Grounding to Vision, Robotics and Beyond`, with `Resources and Evaluation` as secondary fit. |
| OpenReview Responsible NLP checklist | `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`; `scripts/check_openreview_checklist.py`; `tests/test_acl_openreview_checklist.py`. | Copy-ready source now has an automated check for the expected 17 ARR checklist questions, official policy URLs, current PDF anchors, no placeholder text, no bare yes/no/N/A answers, and anonymous-review AI-assistance wording. Final form copy and target-call wording remain human-gated. |
| Evidence-number consistency | `scripts/check_evidence_numbers.py`; `tests/test_acl_evidence_numbers.py`; `FINAL_INTEGRITY_DELTA_AUDIT.md`. | Automated checker reads local evidence CSV/JSON artifacts and verifies the ACL manuscript/OpenReview metadata still contain the matching proxy, VLM, InternNav, official-scene, and coordinate-baseline numbers. |
| Qualitative VLM panel safety | `docs/records/2026-05-26-acl-fig1-red-material-root-cause.md`; `paper/shared/figures/gen_vlm_grounding_cases.py`; GRScenes paired render reports/logs; `scripts/check_claim_boundaries.py`; `tests/test_acl_claim_boundaries.py`. | Candidate-safe by exclusion. The unsafe `fig_vlm_grounding_cases` panel has been removed from the ACL main paper after render-log audit and original-condition capture timeout. The claim-boundary checker now rejects reintroducing that panel until clean render/overlay provenance exists. |
| Material-effect panel safety | `docs/records/2026-05-27-acl-fig3-red-material-diagnosis.md`; `docs/records/2026-05-28-acl-fig3-material-panel-red-recheck.md`; `scripts/check_claim_boundaries.py`; `tests/test_acl_claim_boundaries.py`; `paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py`. | Clean-log ready and now included as main-paper Figure 3 after the 2026-05-28 original/noMDL rerender pass: 4/4 selected original-MDL logs have zero `KooPbr` / shade-node error signal, and the source/PDF-rendered panel has zero strong-red pixels. The ACL main paper still keeps the material-effect claim table-bounded; the checker allows this panel only when the clean-provenance gate passes. |
| Final-integrity source freshness | `FINAL_INTEGRITY_SOURCE_FINGERPRINT.json`; `scripts/check_integrity_fingerprint.py`; `tests/test_acl_integrity_fingerprint.py`. | Automated checker validates 57 current manuscript, bibliography, policy, OpenReview-copy, reference web-trail, table, figure, figure-prompt, provenance, figure-builder, and CSV/JSON evidence sources before staging. If any source changes, refresh the human integrity audit and rewrite the fingerprint before upload. |
| Final blocker report | `scripts/report_final_blockers.py`; `tests/test_acl_final_blockers.py`. | Read-only report currently returns `status=human_blocked` with no repo blockers and four human blockers because the private author worksheet is incomplete. Its required command list shows the last-mile commands: `init_author_gate.py`, `prefill_author_gate.py --apply`, `check_author_gate.py`, and `run_preupload_gate.py`; its incomplete-worksheet handoff points to `prefill_author_gate.py --apply` before manual completion only when repo-verifiable rows are still missing. After those rows are prefilled, the first next action asks only for the remaining human-only fields plus `check_author_gate.py`, while the final exact-packet action still names `run_preupload_gate.py` -> `prefill_author_gate.py --apply --overwrite` -> `check_author_gate.py` -> `report_final_blockers.py`. It also prints `human_blocker_details`, mapping each active human blocker to required action, private worksheet field names, tracked copy-source files, and done condition without printing private values. Its `private_author_gate_status` object reports only safe field names/counts, git ignored/tracked booleans, and `prints_private_author_values=false`; it does not print filled worksheet values. Once the ignored private worksheet is complete, the report can clear the route, OpenReview form-copy, runtime/AI/media, and final upload-decision blockers. |
| Goal-completion report | `scripts/report_goal_completion.py`; `tests/test_acl_goal_completion_report.py`. | Machine-readable completion audit reports the current state as `candidate_ready_human_blocked`: static repo requirements pass, no repo requirement failures are present, and final completion remains false until the human blockers clear and the exact upload packet is approved by the authors. |
| Final OpenReview upload runbook | `OPENREVIEW_UPLOAD_RUNBOOK.md`; `tests/test_acl_openreview_upload_runbook.py`. | Human-facing last-mile runbook exists and is guarded for missing/incomplete private worksheet coverage, OpenReview copy sources, private worksheet path, prefill commands, final gate commands, and stop conditions. It does not contain private author values and does not authorize upload by itself. |
| Author/OpenReview human gates | `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md`; `OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md`; `scripts/init_author_gate.py`; `scripts/prefill_author_gate.py`; `scripts/check_author_gate.py`; `tests/test_acl_author_gate_init.py`; `tests/test_acl_author_gate_prefill.py`; `tests/test_acl_author_gate.py`. | Blank template, fill-order guide, private worksheet initializer, repo-verifiable prefill helper, and private worksheet checker exist. Initialize only the ignored local copy, not the tracked template and not the review packet. The initializer refuses to overwrite an existing private worksheet and verifies the path is git-ignored before the authors fill it. The prefill helper only fills final evidence rows proven by the repo/staged packet and leaves author, route, approval, optional-media, and final-upload rows human-gated. The checker is expected to fail until `OPENREVIEW_AUTHOR_GATE_FILLED.local.md` exists, required fields are filled, and high-risk private decisions have positive approval/pass/upload semantics. |
| Responsible NLP checklist | `RESPONSIBLE_NLP_CHECKLIST_DRAFT.md`; `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`; `scripts/check_openreview_checklist.py`. | OpenReview copy-ready packet now exists with current PDF section/page anchors and automated copy-readiness checks; final form copy and any target-call wording remain human-gated. |
| Supplemental anonymization | `SUBMISSION_STAGING_AUDIT.md`; `paper/venues/acl27/scripts/stage_submission_packet.py`. | Minimal PDF-first staging smoke passed for the ignored local packet; final archive and optional media still need pre-upload re-scan. |
| Consolidated pre-upload gate | `scripts/run_preupload_gate.py`; `tests/test_acl_preupload_gate.py`; `tests/test_acl_author_gate.py`; `tests/test_acl_author_gate_init.py`; `tests/test_acl_author_gate_prefill.py`; `tests/test_acl_goal_completion_report.py`; `tests/test_acl_target_policy.py`; `tests/test_acl_citation_inventory.py`; `tests/test_acl_integrity_fingerprint.py`; `tests/test_acl_final_blockers.py`; `tests/test_acl_openreview_checklist.py`; `tests/test_acl_openreview_upload_runbook.py`; `SUBMISSION_STAGING_AUDIT.md`. | Repository-side rehearsal passed after the v18 imagegen/visual-review promotion, material-effect covered-bin clean rerender/provenance pass, material-effect main-panel promotion, page-anchor sync, Table 6 overfull fix, two-column and top-float `pdftotext` guard updates, intro evidence-gate polish, Figure 2 visual-first readability polish, Figure 3 readable-label polish, Table 6 caption compacting, Figure 4 wide InternNav panel upgrade, Figure 4 label-readability polish, page-9 Limitations tail polish, page-7 official-scene hyphenation polish, Figure 1 v17 rejected-candidate audit, the abstract point-hit direction clarity update, the Figure 1 caption polish, the 2026-05-30 Fig.3 provenance-caption hardening, conclusion evidence-gate takeaway polish, manual Introduction page-break removal, and InternNav/InteriorAgent scope wording polish; the current staged candidate is an 11-page A4 PDF 1.5, 4,066,626 bytes. The build and staged PDFs are identical with SHA-256 `137370b33b567ebc55ab6f88ef5d6e6860b6e61debf133e8077b14a22b454c98`. The staged candidate keeps the material-effect result table-bounded while including the cleaned contact sheet as selected Figure 3 with larger row-level target/effect labels and log-checked clean provenance wording, makes Method/Results explicit that static material-effect gates do not certify mechanism-level MDL preservation, keeps Figure 1 v18 as AI-generated schematic roadmap rather than empirical evidence after rejecting v17 for a wrong `Target: boy` label, keeps Figure 2 as real cropped render evidence rather than generated imagery with a larger visual-first layout, keeps Table 6 aggregate-only with a compact NVIDIA-omission caption, and keeps Figure 4 as a wide three-case selected official InternNav path panel. The page-9 scope wording now negates broad InternNav/InteriorAgent coverage directly, and targeted page-9 visual review passes with Figure 4, Limitations, and Ethical Considerations readable and non-overlapping. The profile guard still enforces a 12-page cap and ordered text extraction, now allowing the top-of-page Figure 4 float before Limitations. |
| Target-call lock | `TARGET_CALL_POLICY_AUDIT.md`; `TARGET_LOCK_OPENREVIEW_REHEARSAL.md`. | EACL 2027 is a public ARR-family route with August 3, 2026 ARR deadline, but its full CFP is still forthcoming. Annual ACL 2027 CFP/author kit remains unavailable in checked official sources. Author route/profile/reviewer-registration/preprint decisions remain human-gated. |

## Candidate Staging Command

The primary repository-side rehearsal command is:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

It wraps the local automated gate: claim-boundary check, target-policy
consistency check, OpenReview metadata consistency check, OpenReview checklist copy-readiness check,
citation-inventory check, evidence-number consistency check,
final-integrity source fingerprint check, final blocker report,
goal-completion report, focused ACL pytest suite, clean ACL PDF rebuild,
final LaTeX log scan,
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
