# OpenReview Author Gate Worksheet

Checked: 2026-05-26.

This worksheet is a blank, commit-safe template for the human-only fields that
must be resolved before a real ARR/OpenReview submission. Do not put real author
names, OpenReview profile IDs, email addresses, or private submission history
into the committed template.

For a real submission, create the ignored local copy with the safe initializer:

```bash
python paper/venues/acl27/scripts/init_author_gate.py
git check-ignore -v paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
```

The initializer refuses to overwrite an existing private worksheet and reports
only path/status metadata. The filled copy is ignored by `.gitignore` and must
not be uploaded as review supplemental material.

When filling high-risk rows, use explicit positive wording such as `approved`,
`confirmed`, `copied`, `excluded by default`, `pass`, `clean`, or final decision
`upload`. Values such as `do not upload`, `failed`, `not approved`, `not
confirmed`, or `not complete` intentionally keep `check_author_gate.py` failing.

## Route Decision

| Field | Fill in local copy | Notes |
| --- | --- | --- |
| Selected route | TODO: EACL 2027 via ARR / Annual ACL 2027 later / other | EACL 2027 via ARR is the current public ACL-family route; Annual ACL 2027 is not final-ready until its official CFP/author kit is public. |
| Final policy refresh date | TODO | Re-check ARR dates, ARR author guidelines, ARR common submission problems, ARR areas, ACLPUB formatting, and the selected venue call. |
| Target deadline | TODO | For EACL 2027 via ARR, current recorded ARR deadline is August 3, 2026 AoE. |
| Commitment venue if ARR-reviewed | TODO | Fill only when committing ARR reviews to a venue. |

## Author And OpenReview Fields

| Field | Fill in local copy | Gate |
| --- | --- | --- |
| Final author list and order | TODO | Must be correct before submission. Do not rely on post-submission changes. |
| Corresponding author / submitter | TODO | Must have access to the OpenReview submission form and confirmation email. |
| OpenReview profile complete for each author | TODO: yes/no per author | Required before submission. |
| Reviewer-registration commitment | TODO: confirmed by all authors / not confirmed | ARR requires submitting authors to register as reviewers shortly after the deadline. |
| All authors notified of reviewer-duty sanctions | TODO | ARR author guidelines describe consequences for irresponsible reviewing. |
| Author contribution / authorship approval | TODO | Confirm all authors approve the final submission and order. |

## Submission History And Conflict Fields

| Field | Fill in local copy | Gate |
| --- | --- | --- |
| Dual submission status | TODO | Confirm the paper is not under concurrent archival review elsewhere. |
| Prior ARR/OpenReview submission link | TODO: none / link in local copy | Required if this is a resubmission. |
| Explanation of revisions needed | TODO: yes/no | Required if resubmitting after receiving reviews. |
| Preprint status answer | TODO | ARR allows an anonymous preprint option at submission; choose deliberately. |
| Public repository or project links | TODO | Review version must not include non-anonymous links. |

## Checklist And Disclosure Approval

| Field | Fill in local copy | Source file |
| --- | --- | --- |
| Title approved | TODO | `OPENREVIEW_METADATA_PACKET.md` |
| Abstract approved and under current venue limit | TODO | `OPENREVIEW_METADATA_PACKET.md`; `sections/abstract.tex` |
| Primary ARR area approved | TODO | Current recommendation: `Multimodality and Language Grounding to Vision, Robotics and Beyond`. |
| Secondary area / keywords approved | TODO | Current secondary fit: `Resources and Evaluation`. |
| Responsible NLP checklist copied into OpenReview | TODO | `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md` |
| Runtime / compute wording approved | TODO | `COMPUTE_RUNTIME_SUMMARY_DRAFT.md` |
| AI-assistance wording approved | TODO | `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md` section E |
| Model and asset license wording approved | TODO | `MODEL_AND_ASSET_LICENSE_AUDIT.md`, `ARTIFACT_PROVENANCE_DRAFT.md` |

## Optional Media Decision

Default decision for the safe review packet:

```text
Exclude selected scene-derived videos and raw media from the review upload.
```

| Gate | Fill in local copy |
| --- | --- |
| Optional media decision | TODO: excluded by default / approved separate media path |

Only change that decision if all of the following are true in the local copy:

- author/legal approval is recorded;
- terms allow the proposed redistribution;
- media is anonymized and scanned;
- media is described only as selected qualitative evidence;
- the final staged packet and manifest explicitly list the media.

## Final Pre-Upload Evidence

Fill this section in the local copy after the exact final packet is staged.

| Gate | Fill in local copy |
| --- | --- |
| Clean PDF build command and timestamp | TODO |
| Final PDF page count / page size | TODO |
| Undefined citation/reference scan | TODO |
| Staging command and packet path | TODO |
| Staged file list | TODO |
| Local path / username / private-link scan | TODO |
| Acknowledgment scan | TODO |
| Limitations / Ethical Considerations / References text scan | TODO |
| Final decision: upload / do not upload | TODO |

## Sources To Re-Check Before Filling

- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/authorchecklist`
- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/areas`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://2027.eacl.org/calls/papers/`
