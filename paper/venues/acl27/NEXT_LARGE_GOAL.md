# ACL/ARR Next Large Goal

Checked: 2026-05-26.

This file turns the current ACL/ARR candidate state into the next executable
goal. It is intentionally larger than a small documentation cleanup and smaller
than an open-ended experiment campaign.

## Goal

Lock the ACL-family submission route and complete the final integrity/upload
gate for the current ACL/ARR candidate packet.

## Why This Is The Right Next Goal

The paper story, claim audit, citation/provenance packet, Responsible NLP
checklist draft, OpenReview metadata packet, and safe staging script now exist.
The remaining risk is no longer "we need more experiments by default". The
main risk is that a candidate paper that is scientifically bounded could still
fail as a submission because the route, form fields, author duties, final
integrity pass, or upload packet are not locked.

For ACL specifically, the next goal is also a reviewer-risk hardening goal. The
paper should read as a VLM grounding and embodied-data reliability paper under
3D material perturbations, not as a standalone asset-conversion tool paper. The
reviewer-facing risk audit is recorded in `ACL_REVIEWER_RISK_AUDIT.md`.

## Target Route

Use the current paper as an ACL/ARR review packet until the authors lock the
route.

Recommended route if the authors want an actionable 2027 ACL-family deadline
now:

- EACL 2027 via ARR.
- Official public deadline currently recorded by ARR and EACL: August 3, 2026
  AoE.
- Keep a policy-refresh gate because the complete EACL CFP and detailed
  timetable are still forthcoming.

If the authors specifically mean Annual ACL 2027:

- Do not mark the packet Annual-ACL-final.
- Wait for the official Annual ACL 2027 CFP, author kit, deadline, checklist
  wording, and supplemental policy.

## InternNav Evidence Scope

The next goal should use the official InternNav / KuJiaLe route for embodied
sanity evidence, not a new GRScenes navigation claim.

Current paper-safe scope:

- GRScenes: image-level VLM grounding evidence, including the 15-pair clean
  pilot and frozen 30-pair target-centered stress set.
- InternNav official KuJiaLe: scoped downstream sanity evidence over the
  public official `val_unseen` route, currently 99 paired episodes across three
  official scenes.
- Official-scene load/render closure: loadability/stability evidence with
  overlapping ready-time intervals.

Do not convert this into a broad embodied-navigation benchmark claim without a
new experimental design and review.

## Video Evidence Decision

Selected qualitative videos are useful for paper figures, reviewer response,
and internal visual audit. They are not required for the main submission goal.

Default upload policy:

- exclude selected scene-derived videos from the safe packet;
- keep videos as qualitative inspection evidence only;
- do not count selected videos as quantitative evidence;
- include videos only after explicit author/legal approval and a fresh
  anonymization/media scan.

## Definition Of Done

This goal is done only when all of the following are true:

1. The selected route is recorded: EACL 2027 via ARR, or Annual ACL 2027 after
   the official Annual ACL call exists.
2. The final target policy has been refreshed against official pages.
3. The first-page story has been checked against the reviewer-risk audit:
   title/abstract/introduction/contributions read as language-grounding
   reliability, not as a tool-only paper.
4. Author list/order, OpenReview profiles, reviewer-registration commitment,
   dual-submission/resubmission status, preprint status, runtime wording, and
   AI-assistance wording are recorded in a private local copy of
   `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md`, and
   `check_author_gate.py` passes on that private copy.
5. The PDF is rebuilt from a clean state.
6. The final log has no unresolved citations or references.
7. The PDF profile guard passes on the final staged PDF, or any cap change is
   deliberately made after official venue-policy review.
8. The claim-boundary checker passes over the final ACL manuscript and
   OpenReview metadata source.
9. `FINAL_INTEGRITY_SOURCE_FINGERPRINT.json` matches the exact manuscript,
   bibliography, target-policy, OpenReview-copy, reference web-trail, table,
   and evidence sources used by the final integrity audit.
10. The final staged packet contains only the safe upload boundary, and the
   adjacent local checksum sidecar validates those staged files.
11. Anonymization scans over the exact staged packet pass.
12. Responsible NLP checklist and metadata copy sources match the final PDF;
   `check_metadata_consistency.py` and `check_openreview_checklist.py` pass
   before staging.
13. Any optional media is either explicitly excluded or legally approved and
   separately scanned.
14. `report_final_blockers.py` reports no repo blockers and no human blockers.
15. `STATUS.md`, `SUBMISSION_READINESS_AUDIT.md`,
    `FINAL_SUBMISSION_PACKET_CHECKLIST.md`, and
    `TARGET_LOCK_OPENREVIEW_REHEARSAL.md` are updated with the final result.

Do not commit the filled author worksheet. Use
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md`, which is ignored by `.gitignore`.

## Minimum Commands For The Final Gate

Run these on the exact final state:

```bash
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

The author-gate checker is the final private-human gate and requires
`paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md`; it is expected to
fail until the authors fill that ignored local file. `run_preupload_gate.py` is
the preferred repository-side final-gate rehearsal. It wraps the clean build,
focused tests, claim-boundary check, metadata consistency check,
OpenReview checklist copy-readiness check, citation-inventory check,
evidence-number consistency check, packet staging, final-integrity source
fingerprint check, final blocker report, packet inventory check, anonymization
scan, acknowledgment scan, `pdfinfo`, PDF profile guard,
packet checksum-sidecar validation, and `pdftotext` checks.

If the runner needs to be expanded or debugged manually, its component commands
are:

```bash
make -C paper clean-acl27 && make -C paper acl27
python -m pytest -q tests/test_acl_submission_staging.py tests/test_paper_layout.py tests/test_acl_metadata_consistency.py tests/test_acl_openreview_checklist.py tests/test_acl_claim_boundaries.py tests/test_acl_citation_inventory.py tests/test_acl_integrity_fingerprint.py tests/test_acl_final_blockers.py tests/test_acl_evidence_numbers.py tests/test_acl_author_gate.py tests/test_acl_preupload_gate.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
python paper/venues/acl27/scripts/check_openreview_checklist.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_citation_inventory.py
python paper/venues/acl27/scripts/check_evidence_numbers.py
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/report_final_blockers.py
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/stage_submission_packet.py --force
rg -n "/cpfs|/home/|/root|zhuzihou|jandan138|github.com/jandan138|ConvertAsset.git" \
  paper/submissions/acl27_arr_candidate_20260526
rg -n "Acknowledg|thanks|Acknowledgment" \
  paper/submissions/acl27_arr_candidate_20260526
pdfinfo paper/submissions/acl27_arr_candidate_20260526/main.pdf
pdftotext paper/submissions/acl27_arr_candidate_20260526/main.pdf - | \
  rg -n "Anonymous ACL submission|Limitations|Ethical Considerations|References"
```

Manual fallback must also confirm that `pdfinfo` reports no more than 12 pages,
A4 page size, and PDF version 1.5 for the current candidate profile unless the
final venue policy justifies updating `PDF_MAX_TOTAL_PAGES`.

Expected staged files:

```text
main.pdf
openreview/METADATA.md
openreview/RESPONSIBLE_NLP_CHECKLIST.md
supplemental/README.md
supplemental/manifest.json
```

## Source Policy Inputs

- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/areas`
- `https://aclrollingreview.org/authors`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://2027.eacl.org/calls/papers/`
