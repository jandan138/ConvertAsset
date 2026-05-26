# ACL/ARR Goal Completion Audit

Checked: 2026-05-26.

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

Latest refresh: after the OpenReview author-gate worksheet was added, the
candidate was rebuilt and restaged on 2026-05-26. The current evidence is
recorded in `SUBMISSION_STAGING_AUDIT.md`,
`docs/records/2026-05-26-acl-preupload-rehearsal-refresh.md`, and
`docs/records/2026-05-26-acl-first-page-fit-hardening.md`: 11 focused tests
passed, the refreshed abstract is 189 words by the conservative tokenizer, the
clean ACL build produced an 11-page A4 PDF, the final log had no unresolved
citation/reference matches, and the staged packet still contained only the safe
five-file boundary.

## Requirement Map

| Active goal requirement | Current evidence | Status |
| --- | --- | --- |
| Reframe the paper around VLM grounding and embodied-data reliability. | `sections/abstract.tex`, `sections/intro.tex`, `sections/related.tex`, `sections/method.tex`, `sections/results.tex`, `sections/discussion.tex`, `sections/conclusion.tex`, and `build/main.pdf`. | Satisfied for the current candidate draft. |
| Avoid unsupported broad embodied-benchmark, speedup, and NVIDIA official-scene claims. | `CLAIM_AUDIT.md`, `FINAL_SUBMISSION_PACKET_CHECKLIST.md`, and the current ACL sections. | Satisfied for the current candidate draft; re-check after any edits. |
| Make all major paper claims traceable to existing evidence. | `CLAIM_AUDIT.md`, `paper/shared/evidence/claims.yaml`, GRScenes, material-effect, InternNav, and official-scene evidence manifests. | Satisfied at candidate level. |
| Expand ACL/VLM-related framing rather than presenting only a simulation-tool paper. | ACL-local `related`, `method`, `results`, and `discussion` sections cite VLM grounding, embodied AI environments, domain randomization, and vision-language navigation sources. | Satisfied at candidate level. |
| Check citation and artifact provenance for the current ACL wrapper. | `CITATION_PROVENANCE_AUDIT.md`, `FINAL_INTEGRITY_DELTA_AUDIT.md`, `paper/shared/evidence/references/verification_report.md`, `MODEL_AND_ASSET_LICENSE_AUDIT.md`, `ARTIFACT_PROVENANCE_DRAFT.md`, and `paper/shared/references.bib`. | Current 20-reference web-trail existence audit and current-source citation-context/data/originality-smoke delta are complete; rerun after any manuscript, bibliography, target, or packet change. |
| Produce a clean ACL-format PDF. | Latest refresh ran `make -C paper clean-acl27 && make -C paper acl27`; `pdfinfo` reported 11 pages, A4 page size, PDF 1.5, and 299433 bytes. | Satisfied for the current candidate build; rerun immediately before upload. |
| Prepare a minimal anonymous submission packet. | Latest refresh regenerated `paper/submissions/acl27_arr_candidate_20260526/` with exactly `main.pdf`, OpenReview metadata/checklist copy sources, `supplemental/README.md`, and `supplemental/manifest.json`. | Candidate staging smoke pass. |
| Keep optional media and raw assets out of the safe upload boundary. | `FINAL_SUBMISSION_PACKET_CHECKLIST.md`, `MODEL_AND_ASSET_LICENSE_AUDIT.md`, and staging manifest exclude raw scenes, scratch USD, InternNav raw frames/logs/LMDBs, local checkpoints, and selected videos. | Satisfied for the safe packet; any future media inclusion is a separate author/legal decision. |
| Keep human-only OpenReview fields out of the anonymous packet. | `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md` is a tracked blank template; filled local copies match `.gitignore` and are excluded from the staged packet. | Satisfied for the current repository and candidate packet; final author copy remains private/human-gated. |
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
- all-GRScenes, all-InteriorNav, R2R, MP3D, or manipulation robustness;
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
   final target and PDF are locked; confirm author list/order, OpenReview
   profiles, reviewer-registration commitment, dual-submission/resubmission
   status, and preprint status.
3. **Author/runtime confirmation**: confirm checked compute/runtime details and
   AI-assistance disclosure wording before upload.
4. **Media/legal decision**: keep InteriorAgent / KuJiaLe scene-derived videos
   excluded unless authors explicitly approve a separate terms/anonymization
   path.
5. **Final integrity pass**: `FINAL_INTEGRITY_DELTA_AUDIT.md` now records a
   current-source citation-context, data-claim, forbidden-claim, and
   originality-smoke pass. Rerun it after any manuscript, bibliography, target,
   or packet change, and do not treat it as a substitute for the venue's own
   plagiarism screening.
6. **Pre-upload rebuild and scans**: rerun clean PDF build, candidate staging,
   anonymization scans, `pdfinfo`, and `pdftotext` checks on the exact upload
   directory.

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
- candidate upload packet restaged and anonymization-scanned;
- optional media either explicitly excluded or legally approved;
- final human gates recorded in `STATUS.md`.
