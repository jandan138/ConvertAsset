# ACL/ARR Target Lock And OpenReview Rehearsal

Checked: 2026-05-26.

This packet turns the remaining ACL/ARR readiness work into an executable
author-decision checklist. It does not choose the target for the authors. It
separates what the repository can already prove from the decisions that must be
made in the official submission system.

## Current Route Decision

| Route | Public policy state on 2026-05-26 | Repository action |
| --- | --- | --- |
| EACL 2027 via ARR | Public official route. ARR Dates lists EACL 2027 with final ARR submission date August 3, 2026 and commitment date October 11, 2026. The EACL 2027 site lists Athens, Greece, March 9-14, 2027 and the same ARR deadline. The main-paper call page says the comprehensive CFP and detailed timetable are still being finalized. | Recommended if the authors want a concrete 2027 ACL-family target now. Keep this wrapper as an ACL/ARR review packet until the complete EACL CFP is published. |
| Annual ACL 2027 | No public official Annual ACL 2027 CFP, author kit, city/date page, commitment deadline, or supplemental policy was found in checked official sources. | Wait. Do not label the packet Annual-ACL-final, do not claim Japan/date/deadline, and do not invent policy details. |
| Generic ARR / ACLPUB | ARR author guidelines, common submission problems, Responsible NLP checklist, ARR dates, and ACLPUB review formatting are public. | Continue using the current generic ACL review build and safe staging packet as the rehearsal target. |

Practical recommendation: if the authors want an actionable route now, lock to
EACL 2027 via ARR and keep a final policy-refresh gate for the complete CFP. If
the authors specifically require Annual ACL 2027, keep the paper in candidate
mode until official Annual ACL information appears.

## Repository Readiness For OpenReview

| OpenReview / ARR item | Current local evidence | Status |
| --- | --- | --- |
| Anonymous PDF | `paper/venues/acl27/build/main.pdf`; staged as `paper/submissions/acl27_arr_candidate_20260526/main.pdf`. | Ready for rehearsal; rebuild immediately before upload. |
| Title, abstract, track, and keywords | `paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md`; staged as `openreview/METADATA.md`. | Copy-ready source; final OpenReview fields remain author-gated. |
| Responsible NLP checklist answers | `paper/venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`. | Copy-ready source, not yet entered into official OpenReview. |
| Limitations and Ethical Considerations | PDF text scan finds both before references. | Ready for rehearsal. |
| Page format | `pdfinfo` reports A4; current PDF is 11 pages total and within generic long-paper review budget before references. | Ready under generic ACLPUB policy; final venue-specific check still required. |
| Bibliography and citation existence | `paper/shared/evidence/references/verification_report.md` and `CITATION_PROVENANCE_AUDIT.md`. | Current 20-reference web trail complete. |
| Citation-context/data/originality delta | `FINAL_INTEGRITY_DELTA_AUDIT.md`. | Current-source pass complete; rerun after any edit. |
| Safe packet boundary | `FINAL_SUBMISSION_PACKET_CHECKLIST.md`, `SUBMISSION_STAGING_AUDIT.md`, and `stage_submission_packet.py`. | Minimal PDF-first packet ready; selected media remains excluded by default. |
| Model/asset license notes | `MODEL_AND_ASSET_LICENSE_AUDIT.md` and `ARTIFACT_PROVENANCE_DRAFT.md`. | Candidate-ready, with author/legal confirmation still required. |

## Author Decisions Required Before Real Submission

These fields cannot be completed by repository evidence alone:

1. **Target route**: choose EACL 2027 via ARR now, or wait for Annual ACL 2027.
2. **Author list and order**: final author list/order must be correct before
   OpenReview submission; ARR warns that author-list/order changes are not
   allowed after submission.
3. **OpenReview profiles**: all authors must have complete OpenReview profiles
   before submission.
4. **Reviewer registration commitment**: ARR requires all submitting authors to
   sign up as reviewers shortly after submission; non-compliance can cause desk
   rejection or sanctions.
5. **Dual-submission / resubmission status**: confirm the paper is not under
   archival review elsewhere and whether any prior version must be disclosed as
   a resubmission.
6. **Preprint status**: choose the OpenReview preprint-status answer; ARR notes
   this field can be binding.
7. **Runtime and AI-assistance wording**: approve the compute/runtime summary
   and AI-assistance disclosure wording used in the checklist.
8. **Optional media decision**: keep selected InteriorAgent / KuJiaLe
   scene-derived media excluded unless a separate legal/anonymization path is
   explicitly approved.

Use `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md` as the blank template for these
decisions. Fill a private ignored copy named
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md`; do not commit real author names,
OpenReview IDs, email addresses, or private submission-history links.
Use `OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md` for the exact fill order,
privacy checks, and stop conditions.

## Upload Rehearsal Checklist

Run this only after the route and author decisions above are known, and rerun
it after any future manuscript, bibliography, checklist, or packet change. The
preferred command is now the consolidated repository-side gate:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Expected packet contents:

```text
main.pdf
openreview/METADATA.md
openreview/RESPONSIBLE_NLP_CHECKLIST.md
supplemental/README.md
supplemental/manifest.json
```

The `openreview/` files are copy sources for form fields, not required
supplements unless the final venue explicitly asks for them. Do not upload
selected videos, raw scenes, scratch USD trees, raw InternNav outputs, LMDBs,
local checkpoints, or non-anonymous repository links.

## Sources

- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/authorchecklist`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://acl-org.github.io/ACLPUB/review-version.html`
- `https://2027.eacl.org/`
- `https://2027.eacl.org/calls/papers/`
