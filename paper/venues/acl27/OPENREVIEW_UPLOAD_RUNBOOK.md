# OpenReview Upload Runbook

Checked: 2026-05-26.

This runbook is the final human-facing upload path for the current ACL/ARR
candidate packet. It does not authorize upload by itself and it must not contain
author names, OpenReview IDs, emails, private submission links, or private
worksheet values.

Use it after the repository-side packet has passed `run_preupload_gate.py` and
before any real ARR/OpenReview submission.

## Current Repository State

The current repository-side blocker report is expected to show:

```text
status=human_blocked
repo_blockers=[]
```

The active human blockers are:

- `private_author_gate_missing`
- `target_route_author_confirmation_pending`
- `official_openreview_form_copy_pending`
- `author_runtime_ai_media_approval_pending`

Use `human_blocker_details` from:

```bash
python paper/venues/acl27/scripts/report_final_blockers.py
```

That JSON maps each blocker to required actions, private worksheet field names,
tracked copy-source files, and done conditions without printing private values.

## Step 1: Create The Private Worksheet

Create the ignored local copy with the safe initializer:

```bash
python paper/venues/acl27/scripts/init_author_gate.py
git check-ignore -v paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
```

Stop if the file is not ignored.

The initializer refuses to overwrite an existing private worksheet and prints
only path/status metadata, not worksheet values. If the script is unavailable,
the manual fallback is to copy
`OPENREVIEW_AUTHOR_GATE_WORKSHEET.md` to
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md`, then run the same `git check-ignore`
command before filling anything.

Fill only the local ignored file. Do not edit the tracked blank template with
real author information.

## Step 2: Lock The Route

Resolve `target_route_author_confirmation_pending` in the private worksheet.

Required private worksheet rows:

- `Selected route`
- `Final policy refresh date`
- `Target deadline`
- `Commitment venue if ARR-reviewed`

Tracked copy sources:

- `TARGET_CALL_POLICY_AUDIT.md`
- `TARGET_LOCK_OPENREVIEW_REHEARSAL.md`
- `OPENREVIEW_METADATA_PACKET.md`

Current repository recommendation: use EACL 2027 via ARR if the authors want a
concrete 2027 ACL-family route now. Do not label the packet Annual ACL 2027
final-ready until Annual ACL 2027 publishes its official CFP, author kit, and
venue-specific policy.

## Step 3: Copy OpenReview Form Fields

Resolve `official_openreview_form_copy_pending` in the private worksheet.

Copy source files:

- `OPENREVIEW_METADATA_PACKET.md`
- `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`

Copy/check these form surfaces:

- title;
- abstract;
- ARR primary area;
- secondary area or keywords, if the form allows them;
- Responsible NLP checklist answers.

Required private worksheet rows:

- `Title approved`
- `Abstract approved and under current venue limit`
- `Primary ARR area approved`
- `Secondary area / keywords approved`
- `Responsible NLP checklist copied into OpenReview`

Do not upload `openreview/METADATA.md` or
`openreview/RESPONSIBLE_NLP_CHECKLIST.md` as supplements unless the final venue
explicitly requests them. They are copy sources for the official form.

## Step 4: Record Author, Runtime, AI, License, And Media Decisions

Resolve `author_runtime_ai_media_approval_pending` in the private worksheet.

Tracked copy sources:

- `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`
- `MODEL_AND_ASSET_LICENSE_AUDIT.md`
- `ARTIFACT_PROVENANCE_DRAFT.md`
- `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`
- `FINAL_SUBMISSION_PACKET_CHECKLIST.md`

Private worksheet rows must cover:

- final author list/order and submitter;
- OpenReview profile readiness;
- reviewer-registration commitment;
- author notification and authorship approval;
- dual-submission, prior ARR/OpenReview, revision, preprint, and public-link
  status;
- runtime/compute wording;
- AI-assistance wording;
- model and asset license wording;
- optional media decision;
- final citation/reference, private-token, acknowledgment, and PDF-text scans;
- final upload decision.

Default media decision: exclude selected scene-derived videos and raw media from
the review upload. Include optional media only after separate author/legal,
redistribution, and anonymization approval.

## Step 5: Run Final Gates

Run these commands on the exact state intended for upload:

```bash
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/report_final_blockers.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Expected upload-ready repository result:

```text
status=upload_ready
repo_blockers=[]
human_blockers=[]
human_blocker_details={}
```

The staged packet should still contain only:

```text
main.pdf
openreview/METADATA.md
openreview/RESPONSIBLE_NLP_CHECKLIST.md
supplemental/README.md
supplemental/manifest.json
```

The adjacent `.sha256` sidecar is local validation evidence, not part of the
review packet.

## Stop Conditions

Do not upload if any of these are true:

- `check_author_gate.py` fails.
- `report_final_blockers.py` reports any repo or human blocker.
- `run_preupload_gate.py` fails.
- `OPENREVIEW_AUTHOR_GATE_FILLED.local.md` is not ignored, is staged, or appears
  in the upload packet.
- The selected route is undecided.
- Annual ACL 2027 is selected before an official Annual ACL 2027 CFP/author kit
  exists.
- OpenReview form fields differ from `OPENREVIEW_METADATA_PACKET.md` or
  `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md` without a documented author
  decision.
- Runtime, AI-assistance, license, or optional-media wording is not approved.
- The packet contains raw scenes, converted USD trees, selected videos, local
  model checkpoints, local paths, private repository links, or acknowledgments.
- Final decision says `Do not upload`.

## After Upload

Record only non-private upload evidence in the repository. Keep confirmation
emails, author profile data, OpenReview IDs, and private submission links out of
tracked files.
