# OpenReview Author Gate Filling Guide

Checked: 2026-05-26.

This guide explains how to fill the private author-gate worksheet without
leaking author identities, OpenReview IDs, emails, or private submission
history into the tracked repository or anonymous review packet.

It complements `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md`; it does not replace the
blank worksheet.

## Safety Boundary

Do not edit the tracked worksheet with real author data. Create the ignored
local copy:

```bash
cp paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_WORKSHEET.md \
  paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
git check-ignore -v paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
```

Expected result: `.gitignore` ignores
`paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md`.

If `git check-ignore` does not report an ignore rule, stop before filling the
file.

After the private copy is filled, validate it with:

```bash
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/report_final_blockers.py
```

Expected result after filling: the command exits 0 and prints a JSON status
report. `check_author_gate.py` lists field names, missing fields, TODO fields,
semantically invalid fields, and git ignore/tracked status; it does not print
the private field values.
`report_final_blockers.py` should no longer list human blockers after the
worksheet is complete, because the route, OpenReview form-copy,
runtime/AI/media, and final upload decision fields are recorded in that private
copy. Before the authors create and fill `OPENREVIEW_AUTHOR_GATE_FILLED.local.md`,
`check_author_gate.py` is expected to exit nonzero.
When blockers remain, `report_final_blockers.py` includes
`human_blocker_details` with only blocker ids, required actions, worksheet field
names, copy-source files, and done conditions. It does not print private
worksheet values.

For high-risk rows, do not write vague placeholders such as `filled`. Use
positive wording such as `approved`, `confirmed`, `copied`, `excluded by
default`, `pass: no leaks`, or final decision `upload`. Values such as `do not
upload`, `failed`, `not approved`, `not confirmed`, or `not complete` keep the
private gate incomplete.

## Fill Order

Fill the private worksheet in this order.

1. **Route decision**

   Record either `EACL 2027 via ARR` or `Annual ACL 2027 later`.

   Current public route state: ARR Dates lists EACL 2027 with final ARR
   submission date August 3, 2026 and commitment date October 11, 2026. The
   EACL 2027 main-paper page lists August 3, 2026 AoE and still says the full
   CFP and detailed timetable are forthcoming. Annual ACL 2027 is not final
   ready in this repo until its official CFP and author kit are public.

2. **Author and OpenReview fields**

   Fill final author list/order, corresponding submitter, OpenReview profile
   readiness, reviewer-registration commitment, reviewer-duty awareness, and
   authorship approval.

   ARR currently requires all submitting authors to sign up as reviewers after
   submission. The common-problems checklist also says author list/order and
   OpenReview profiles must be complete before submission.

3. **Submission history and conflict fields**

   Fill dual-submission status, prior ARR/OpenReview status, revision
   explanation requirement, preprint-status answer, and public-link decision.

   The review PDF and packet must not contain non-anonymous project, repository,
   profile, or service links.

4. **Form copy approvals**

   Approve the exact title, abstract, ARR area, keywords, Responsible NLP
   checklist answers, runtime wording, AI-assistance wording, and model/asset
   license wording before copying anything into OpenReview.

   Source files:

   - `OPENREVIEW_METADATA_PACKET.md`
   - `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`
   - `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`
   - `MODEL_AND_ASSET_LICENSE_AUDIT.md`
   - `ARTIFACT_PROVENANCE_DRAFT.md`

5. **Optional media decision**

   Default answer: exclude selected scene-derived videos and raw media from the
   review upload.

   Only change this if author/legal approval, redistribution permission,
   anonymization, and a separate media scan are all recorded. The current safe
   packet is PDF/form-source first and excludes selected videos.

6. **Final pre-upload evidence**

   Run the repository-side final rehearsal:

   ```bash
   python paper/venues/acl27/scripts/check_author_gate.py
   python paper/venues/acl27/scripts/run_preupload_gate.py
   ```

   Then copy the final evidence into the private worksheet:

   - command and timestamp;
   - PDF page count and page size;
   - staged packet path;
   - staged file list;
   - local path / private-token scan result;
   - acknowledgment scan result;
   - title/header/Limitations/Ethical Considerations/References text scan;
   - final upload / do-not-upload decision.

## Final Privacy Checks

Before upload or commit, run:

```bash
git status --short
git status --short --ignored paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/report_final_blockers.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Expected result:

- the filled local worksheet is ignored, not staged;
- the tracked repository has no private author data;
- the private author worksheet has no missing required field and no TODO/TBD
  value;
- the staged packet still contains only:

```text
main.pdf
openreview/METADATA.md
openreview/RESPONSIBLE_NLP_CHECKLIST.md
supplemental/README.md
supplemental/manifest.json
```

The `openreview/` files are copy sources for the submission form. They are not
extra anonymous supplement files unless the final venue explicitly asks for
them.

## Stop Conditions

Stop before upload if any of these are true:

- the selected route is still undecided;
- Annual ACL 2027 is selected but its official CFP/author kit is still absent;
- any author has not approved final order or OpenReview profile readiness;
- reviewer-registration commitment is not confirmed;
- dual-submission or resubmission status is unclear;
- runtime, AI-assistance, license, or optional-media wording is not approved;
- `check_author_gate.py` fails after the private worksheet is filled;
- `run_preupload_gate.py` fails;
- `git status` shows the filled local worksheet as staged or unignored;
- the staged packet contains raw scenes, converted USD trees, selected videos,
  local model checkpoints, local paths, private repo links, or acknowledgments.

## Sources To Reopen At Fill Time

- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/authorchecklist`
- `https://aclrollingreview.org/areas`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://2027.eacl.org/calls/papers/`
