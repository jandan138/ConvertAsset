# ACL/ARR Goal Completion Audit

Checked: 2026-05-30.

This audit maps the active ACL/ARR paper goal to concrete repository evidence.
It is a goal-status record, not a new experiment and not a final submission
approval.

## Bottom Line

The current ACL/ARR package is **candidate-ready for target lock and final
submission rehearsal**. It is not yet final-upload complete.

The scientific story has been rewritten around VLM grounding reliability and
embodied-data reliability under 3D material perturbations. The current paper
also has a bounded claim audit, citation/provenance packet, OpenReview checklist
source, OpenReview metadata source, author-gate worksheet, compute/runtime
summary, and a minimal staged candidate packet.

The remaining blockers are not "run more experiments by default". They are
target-call and human/integrity gates: choose the final ACL-family route, copy
the checklist into the official OpenReview form, confirm compute/runtime and
media/legal boundaries, and run a final full integrity pass after any last paper
edits.

2026-05-30 status sync: the goal remains active and not final-complete. The
current repository state now includes the 2026-05-30 target-policy refresh,
reviewer-risk refresh, full-PDF visual recheck, first-page ACL-fit recheck, and
Figure 3 red-material recheck. These strengthen candidate readiness; they do
not clear the human-only route, OpenReview form-copy, author/runtime/AI/media,
or final-upload blockers.

Latest refresh: after the OpenReview author-gate worksheet, first-page
ACL-fit hardening, consolidated pre-upload runner, evidence-number checker,
evidence-gate table, citation-inventory checker, final-integrity source
fingerprint checker, target-policy consistency checker, OpenReview checklist
copy-readiness checker, final blocker report, and packet-checksum sidecar were
added, the candidate was rebuilt and restaged on 2026-05-26. The current
evidence is recorded in `SUBMISSION_STAGING_AUDIT.md`,
`docs/records/2026-05-26-acl-preupload-rehearsal-refresh.md`,
`docs/records/2026-05-26-acl-first-page-fit-hardening.md`,
`docs/records/2026-05-26-acl-preupload-gate-runner.md`, and
`docs/records/2026-05-26-acl-evidence-number-check.md`: the consolidated
pre-upload gate passed claim-boundary, target-policy consistency, metadata,
checklist copy-readiness, citation-inventory, evidence-number, final-integrity
fingerprint, final blocker report, focused pytest, clean build, LaTeX log,
staging, inventory, packet checksum,
anonymization, acknowledgment, `pdfinfo`, `pdf_profile`, and `pdftotext`
checks. The focused pytest step now passes 53 tests after adding the
citation-inventory, private author-gate, target-policy, final-integrity
fingerprint, OpenReview checklist, final blocker-report, final blocker
clearance, private author-gate semantic, final blocker handoff-detail, and
OpenReview upload runbook tests, packet-checksum tests, author-gate initializer
handoff checks, figure-driven evidence panels, and the cleaner method-chain
imagegen v3 figure, the refreshed abstract is 183 words by the conservative
tokenizer, the current local clean ACL build produces a 12-page A4 PDF within
the repository candidate cap, and the staged packet still contains only the
safe five-file boundary with an adjacent checksum sidecar outside the packet.

Evidence-gate table refresh: the ACL method now includes
Table `tab:acl_evidence_gate_registry`, which makes the proxy, VLM grounding,
material-mechanism/NVIDIA, and embodied-data sanity gates explicit. This is a
manuscript hardening edit, not a new experiment or broader claim. After the
edit, `run_preupload_gate.py` passed again; the clean staged PDF is now 12 A4
pages and 306187 bytes, with the same safe five-file packet boundary.

PDF-profile gate refresh: `run_preupload_gate.py` now explicitly validates the
current staged PDF profile after `pdfinfo`. It rejects unreviewed page growth
above the current 12-page candidate cap, non-A4 page size, PDF version drift,
or section-order drift where `References` appears before `Limitations` and
`Ethical Considerations`. This strengthens repository-side format readiness;
the final selected venue's official page-limit policy still needs a fresh
human/external check before upload.

Target-policy refresh after final-blocker command handoff: official ARR, EACL,
and ACLPUB pages were reopened again on 2026-05-26. The target state is
unchanged: EACL 2027 via ARR is the concrete public 2027 ACL-family route,
Annual ACL 2027 still has no official CFP/author kit in checked official
sources, and the repository remains candidate-ready rather than final-upload
complete until authors lock the route and complete the private OpenReview
author gate.

Machine-readable goal report: `scripts/report_goal_completion.py` now provides
a JSON status view over this audit. The current output is
`status=candidate_ready_human_blocked`, with `repo_static_ready=true`,
`candidate_ready_for_human_gate=true`, `repo_requirement_failures=[]`, and
`final_goal_complete=false`. Its satisfied static requirements are claim
boundaries, evidence numbers, citation inventory, OpenReview copy sources,
target policy, and final-integrity fingerprint; its remaining requirement is
`final_upload_clearance`, currently `human_blocked`.

## Requirement Map

| Active goal requirement | Current evidence | Status |
| --- | --- | --- |
| Reframe the paper around VLM grounding and embodied-data reliability. | `sections/abstract.tex`, `sections/intro.tex`, `sections/related.tex`, `sections/method.tex`, `sections/results.tex`, `sections/discussion.tex`, `sections/conclusion.tex`, and `build/main.pdf`. | Satisfied for the current candidate draft. |
| Avoid unsupported broad embodied-benchmark, speedup, and NVIDIA official-scene claims. | `CLAIM_AUDIT.md`, `FINAL_SUBMISSION_PACKET_CHECKLIST.md`, and the current ACL sections. | Satisfied for the current candidate draft; re-check after any edits. |
| Make all major paper claims traceable to existing evidence. | `CLAIM_AUDIT.md`, Table `tab:acl_evidence_gate_registry`, `paper/shared/evidence/claims.yaml`, GRScenes, material-effect, InternNav, and official-scene evidence manifests. | Satisfied at candidate level. |
| Expand ACL/VLM-related framing rather than presenting only a simulation-tool paper. | ACL-local `related`, `method`, `results`, and `discussion` sections cite VLM grounding, embodied AI environments, domain randomization, and vision-language navigation sources. | Satisfied at candidate level. |
| Keep first-page reviewer fit current after figure/policy refreshes. | `FIRST_PAGE_ACL_FIT_AUDIT.md` and `paper/shared/evidence/raw/acl27_visual_review/first_page_acl_fit_review_20260530.json`; page 1 and page 2 were rendered at 180 DPI and reviewed locally. | Satisfied at candidate level; final human route/fit read still required before upload. |
| Check citation and artifact provenance for the current ACL wrapper. | `CITATION_PROVENANCE_AUDIT.md`, `FINAL_INTEGRITY_DELTA_AUDIT.md`, `FINAL_INTEGRITY_SOURCE_FINGERPRINT.json`, `paper/shared/evidence/references/verification_report.md`, `MODEL_AND_ASSET_LICENSE_AUDIT.md`, `ARTIFACT_PROVENANCE_DRAFT.md`, `paper/shared/references.bib`, `scripts/check_citation_inventory.py`, `scripts/check_integrity_fingerprint.py`, and `scripts/check_evidence_numbers.py`. | Current 20-reference web-trail existence audit, current-source citation-context/data/originality-smoke delta, automated citation-inventory drift check, automated final-integrity source freshness check, and automated evidence-number check are complete; rerun after any manuscript, bibliography, target, evidence, OpenReview-copy, or packet change. |
| Keep OpenReview checklist copy source complete. | `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`, `scripts/check_openreview_checklist.py`, and `tests/test_acl_openreview_checklist.py`. | Current copy source covers the expected 17 ARR checklist questions, official policy inputs, current PDF anchors, no placeholder text, no bare yes/no/N/A answers, and anonymous-review AI-assistance wording. Final copy into OpenReview remains human-gated. |
| Produce a clean ACL-format PDF. | Latest consolidated candidate after the v18 imagegen/visual-review promotion, material-effect covered-bin clean rerender/provenance pass, material-effect main-panel promotion, OpenReview page-anchor sync, Table 6 overfull fix, two-column and top-float `pdftotext` guard updates, intro evidence-gate polish, Figure 2 visual-first readability polish, Figure 3 readable-label polish, Table 6 caption compacting, Figure 4 wide InternNav panel upgrade, Figure 4 label-readability polish, page-9 Limitations tail polish, page-7 official-scene hyphenation polish, Figure 1 v17 rejected-candidate audit, the abstract point-hit direction clarity update, the Figure 1 caption polish, the 2026-05-30 Fig.3 provenance-caption hardening, conclusion evidence-gate takeaway polish, manual Introduction page-break removal, InternNav/InteriorAgent scope wording polish, and Clean-pool Table 2 readability polish has an 11-page A4 PDF 1.5 staged artifact of 4,087,616 bytes. The build and staged PDFs are identical with SHA-256 `d03af3b4554951ccb51c3a224a8fbbd12fb517180dd36bad5672f0fb07006793`. The material-effect qualitative contact sheet is now main-paper Figure 3 on page 8, with log-checked clean original-MDL provenance, readable row-level target/effect labels, and zero strong-red pixels in source/PDF spot checks; Table 5 remains the governing claim-boundary artifact. Figure 1 now uses v18 after rejecting v17 for wrong in-image text, Figure 2 remains real render evidence with a larger visual-first layout, Table 2 now renders without resizebox compression, Table 6 remains aggregate-only with a compact NVIDIA-omission caption and clean page-7 continuation, and Figure 4 is the wide three-case selected official InternNav path panel on the Limitations page. Targeted page-6 and page-9 visual reviews pass for the dense evidence/table pages; Figure 4, Limitations, and Ethical Considerations are readable and non-overlapping. The material-effect and InternNav qualitative figures remain selected evidence only. | Candidate PDF pass; final upload still depends on human OpenReview/route approvals. |
| Prepare a minimal anonymous submission packet. | Latest consolidated gate regenerated `paper/submissions/acl27_arr_candidate_20260526/` with exactly `main.pdf`, OpenReview metadata/checklist copy sources, `supplemental/README.md`, and `supplemental/manifest.json`, wrote the adjacent local checksum sidecar `paper/submissions/acl27_arr_candidate_20260526.sha256`, then passed packet-inventory, checksum, private-token, and acknowledgment scans. | Candidate staging smoke pass. |
| Keep optional media and raw assets out of the safe upload boundary. | `FINAL_SUBMISSION_PACKET_CHECKLIST.md`, `MODEL_AND_ASSET_LICENSE_AUDIT.md`, and staging manifest exclude raw scenes, scratch USD, InternNav raw frames/logs/LMDBs, local checkpoints, and selected videos. | Satisfied for the safe packet; any future media inclusion is a separate author/legal decision. |
| Keep human-only OpenReview fields out of the anonymous packet. | `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md` is a tracked blank template; filled local copies match `.gitignore` and are excluded from the staged packet. `scripts/check_author_gate.py` validates the filled private copy without printing private values. `scripts/report_final_blockers.py` reports missing/incomplete human gates with `human_blocker_details` field names and copy-source files, but without private values. | Satisfied for the current repository and candidate packet; final author copy remains private/human-gated and must pass the checker after authors fill it. |
| Keep target-policy notes candidate-safe. | `TARGET_CALL_POLICY_AUDIT.md`, `TARGET_LOCK_OPENREVIEW_REHEARSAL.md`, `scripts/check_target_policy.py`, and `tests/test_acl_target_policy.py`. | Satisfied for current notes: EACL 2027 via ARR is recorded as the public route, Annual ACL 2027 is not marked final-ready, and official policy URLs/key route markers are present. |
| Keep goal-completion status machine-readable. | `scripts/report_goal_completion.py`, `tests/test_acl_goal_completion_report.py`, and `scripts/run_preupload_gate.py`. | Current JSON report separates static repo readiness from final upload completion: repo static checks pass, but the final goal remains incomplete because human route, OpenReview form-copy, runtime/AI/media, and final-upload approvals remain. |
| Verify final ACL-family venue policy. | `TARGET_CALL_POLICY_AUDIT.md` and `TARGET_LOCK_OPENREVIEW_REHEARSAL.md`; EACL 2027 official pages and ARR dates are public, while Annual ACL 2027 official CFP/author kit is not available in checked official sources. | Not final-complete. Requires author target decision, OpenReview author/profile/reviewer-registration readiness, and final call check. |

## Evidence That Can Be Written

The current paper can defensibly say:

- ConvertAsset is used as a controlled MDL-to-UsdPreviewSurface material
  perturbation for VLM grounding and embodied-data reliability analysis.
- GRScenes expanded30 is a frozen target-centered material-shift stress set,
  not a population-level GRScenes benchmark.
- Official KuJiaLe InternNav evidence is a scoped 99-episode, three-scene
  downstream sanity result, not a broad embodied-navigation benchmark.
- NVIDIA comparison evidence is limited to selected material-effect bins:
  covered opacity/transparency, emission, normal/bump, and
  displacement/height cases have bounded static and selected qualitative
  evidence; clearcoat is a selected NVIDIA target-loss failure case; procedural
  texture remains a limitation/investigation case.
- Official-scene load/render measurements support loadability/stability with
  overlapping ready-time intervals, not no-MDL speedup.
- Selected qualitative videos support inspection, figures, and rebuttal
  explanation only; they are not quantitative evidence and stay out of the safe
  packet by default.

## Claims Still Forbidden

Do not claim:

- completed broad embodied-navigation benchmarking;
- all GRScenes, all InternNav or InteriorAgent settings, R2R, MP3D, or
  manipulation robustness;
- official-scene noMDL speedup;
- NVIDIA official-scene performance comparison;
- population-level NVIDIA failure rate from selected clearcoat cases;
- procedural-texture preservation success;
- selected videos as quantitative evidence;
- a learned automatic safe-conversion classifier.

## Remaining Gates

1. **Target lock**: choose whether to submit through the currently public EACL
   2027 ARR route, or wait until Annual ACL 2027 publishes its official CFP,
   author kit, page limits, checklist wording, and supplemental policy.
2. **Final OpenReview form and author duties**: fill a private ignored copy of
   `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md`; copy
   `OPENREVIEW_METADATA_PACKET.md` and
   `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md` into the official form after the
   final target and PDF are locked. The ignored private worksheet now records
   the current sole-author and OpenReview-profile confirmation rows, but still
   needs reviewer-registration commitment, dual-submission/resubmission status,
   preprint/public-link decisions, form-copy approvals, optional-media choice,
   and final upload decision.
3. **Author/runtime confirmation**: confirm checked compute/runtime details and
   AI-assistance disclosure wording before upload.
4. **Media/legal decision**: keep InteriorAgent / KuJiaLe scene-derived videos
   excluded unless authors explicitly approve a separate terms/anonymization
   path.
5. **Final integrity pass**: `FINAL_INTEGRITY_DELTA_AUDIT.md` now records a
   current-source citation-context, data-claim, forbidden-claim, and
   originality-smoke pass, and `FINAL_INTEGRITY_SOURCE_FINGERPRINT.json` makes
   source drift a pre-upload failure. Rerun the audit and refresh the
   fingerprint after any manuscript, bibliography, target, evidence,
   OpenReview-copy, or packet change, and do not treat it as a substitute for
   the venue's own plagiarism screening.
6. **Final blocker report**: `report_final_blockers.py` currently reports no
   repo blockers but `status=human_blocked` because the private author
   worksheet, target-route confirmation, official OpenReview form copy, and
   author/runtime/AI/media approval remain pending. The report can now clear
   those human blockers once the ignored private worksheet is complete, without
   printing private author values. It also reports `human_blocker_details` so
   each active human blocker points to required actions, private worksheet
   field names, tracked copy-source files, and done conditions. `check_author_gate.py`
   now also rejects semantically unsafe private values such as failed scans or
   `do not upload`.
7. **Pre-upload rebuild and scans**: rerun clean PDF build, candidate staging,
   anonymization scans, `pdfinfo`, `pdf_profile`, and `pdftotext` checks on
   the exact upload directory.

## Recommended Next Large Goal

Set the next goal as:

> Lock the ACL-family submission route and complete the final integrity/upload
> gate for the current ACL/ARR candidate packet.

The executable handoff is now recorded in `NEXT_LARGE_GOAL.md`.

Practical interpretation:

- If the authors want an actionable 2027 ACL-family deadline now, retarget and
  lock to EACL 2027 via ARR, then run final integrity and upload rehearsal.
- If the authors specifically require Annual ACL 2027, keep the paper in
  ACL/ARR candidate mode and wait for the official Annual ACL 2027 call before
  final venue wording.

Definition of done for that next goal:

- selected venue route recorded;
- final PDF rebuilt from clean state;
- no undefined citations or unsupported claims;
- OpenReview checklist copied to the official form;
- OpenReview metadata copied to the official form;
- private author-gate worksheet completed but not committed;
- `check_author_gate.py` passed on that private worksheet;
- candidate upload packet restaged and anonymization-scanned;
- optional media either explicitly excluded or legally approved;
- final human gates recorded in `STATUS.md`.
