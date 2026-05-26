# ACL Goal Completion Audit

Date: 2026-05-26

## Purpose

Close the current ACL/ARR planning loop by mapping the active paper goal to
concrete evidence and remaining gates. This was a documentation and integrity
status pass, not a new experiment run.

## Changes

- Added `paper/venues/acl27/GOAL_COMPLETION_AUDIT.md`.
- Updated `paper/venues/acl27/STATUS.md` with the new goal-status verdict.
- Added this record to `docs/index.md` and `docs/records/README.md`.

## Findings

- The paper package is candidate-ready for target lock and final submission
  rehearsal: the ACL story, claim boundaries, citation/provenance packet,
  Responsible NLP checklist source, OpenReview metadata source, author-gate
  worksheet, compute/runtime summary, clean PDF, and minimal staged packet all
  exist.
- The goal is not final-upload complete. The remaining gates are target-call
  lock, official OpenReview form copy, author/runtime confirmation, optional
  media/legal approval, final citation/data integrity, and pre-upload rebuild
  plus anonymization scans.
- The next large goal should be target lock plus final integrity/upload gate,
  not more unbounded experiment collection.

## Refresh On 2026-05-26

After the OpenReview author-gate worksheet, first-page ACL-fit hardening,
consolidated pre-upload runner, and evidence-number checker were added, the
completion audit was refreshed against the latest full gate evidence:

- `python paper/venues/acl27/scripts/run_preupload_gate.py` is now the primary
  repository-side rehearsal command.
- The runner passed claim-boundary, OpenReview metadata consistency,
  evidence-number consistency, focused pytest, clean ACL build, LaTeX log,
  packet staging, inventory, local/private-token scan, acknowledgment scan,
  `pdfinfo`, `pdf_profile`, and `pdftotext` checks on the current candidate.
- The focused pytest step now passes 27 tests across staging, layout, metadata,
  claim-boundary, evidence-number, private author-gate, and pre-upload runner
  checks.
- The abstract remains under the ACLPUB 200-word guidance by the repository
  tokenizer.
- The clean build produces a 12-page A4 review PDF under the current candidate
  profile guard.
- The staged packet remains the safe five-file boundary: anonymous PDF,
  OpenReview metadata source, OpenReview checklist source, supplemental README,
  and manifest.

This refresh strengthens the candidate-readiness evidence but does not close
the human gates: route lock, official OpenReview form copy, private author-gate
worksheet completion, `check_author_gate.py` pass on the filled ignored
worksheet, optional media/legal decision, author/runtime and AI-assistance
confirmation, and final integrity rerun remain required before a real upload.

## Next Goal Wording

Recommended next goal:

> Lock the ACL-family submission route and complete the final integrity/upload
> gate for the current ACL/ARR candidate packet.

If the authors want a concrete public 2027 route now, the policy-backed option
is EACL 2027 via ARR. If the authors specifically require Annual ACL 2027, the
repo should remain in candidate mode until the official Annual ACL 2027 call and
author kit are public.

## Verification To Run After This Pass

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
git diff --check
```
