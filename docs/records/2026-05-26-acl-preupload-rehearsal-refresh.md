# ACL Pre-Upload Rehearsal Refresh

Date: 2026-05-26.

## Summary

After adding the OpenReview author-gate worksheet, the ACL/ARR candidate packet
was rebuilt and restaged from the current repository state. This refresh checks
that the new human-gate template did not enter the upload packet and that the
anonymous PDF/staging boundary still holds.

## Commands And Results

| Check | Result |
| --- | --- |
| `git status --short --branch` | Clean before the rehearsal: `## main...origin/main`. |
| Abstract count script | 183 tokens by the current conservative metadata tokenizer; still under the ACLPUB 200-word guidance. |
| `python -m pytest -q tests/test_acl_submission_staging.py tests/test_paper_layout.py` | Pass: 11 tests passed. |
| `make -C paper clean-acl27 && make -C paper acl27` | Pass: built `venues/acl27/build/main.pdf`. |
| Final LaTeX log scan for undefined citations/references | Pass: no matches in the final `main.log`. |
| `python paper/venues/acl27/scripts/stage_submission_packet.py --force` | Pass: regenerated `paper/submissions/acl27_arr_candidate_20260526/`. |
| Staged file inventory | Pass: exactly `main.pdf`, `openreview/METADATA.md`, `openreview/RESPONSIBLE_NLP_CHECKLIST.md`, `supplemental/README.md`, and `supplemental/manifest.json`. |
| Staged local path / username / private repo scan | Pass: no matches. |
| Staged acknowledgment scan | Pass: no matches. |
| `pdfinfo` | Pass: 11 pages, A4, PDF 1.5, file size 299407 bytes. |
| `pdftotext` section scan | Pass: found `Anonymous ACL submission`, `Limitations`, `Ethical Considerations`, and `References`. |

## Packet Boundary

The regenerated manifest keeps:

- `include_media=false`;
- `claim_boundary=selected_media_excluded_by_default_pending_explicit_media_approval`;
- selected qualitative videos, raw source scenes, scratch USD trees, InternNav
  raw outputs, LMDBs/logs, and local model checkpoints excluded.

The new `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md` remains repository-side only. A
filled local copy is ignored by `.gitignore` and is not staged into the
candidate packet.

## Remaining Gates

The goal is still not final-upload complete. The remaining blockers are:

- author route decision: EACL 2027 via ARR now, or wait for Annual ACL 2027
  official policy;
- final official policy refresh immediately before upload;
- private author-gate worksheet completion;
- official OpenReview form copy;
- final integrity rerun after any manuscript, bibliography, checklist, or
  packet change.

## Sources Refreshed

- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/authorchecklist`
- `https://aclrollingreview.org/areas`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://2027.eacl.org/calls/papers/`
