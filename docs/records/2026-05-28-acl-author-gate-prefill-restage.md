# 2026-05-28 ACL Author-Gate Prefill Restage

## Scope

This record documents the final mechanical author-gate prefill after the
current ACL candidate packet was restaged at 23:22 CST.

## What Changed

The ignored local worksheet
`paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md` was refreshed with:

```bash
python paper/venues/acl27/scripts/prefill_author_gate.py --apply --overwrite
```

The command updated only repo-verifiable fields:

```text
Clean PDF build command and timestamp
Final PDF page count / page size
Undefined citation/reference scan
Staging command and packet path
Staged file list
Local path / username / private-link scan
Acknowledgment scan
Limitations / Ethical Considerations / References text scan
```

The worksheet remains git-ignored and untracked. The prefill command reported
`prints_private_values=false`; no author names, profile IDs, private links,
route decision, OpenReview form-copy status, runtime/AI/media approvals, or
final upload decision were printed or committed.

The final blocker reporter was also tightened: when those repo-verifiable rows
are already filled, the first `next_actions` entry no longer tells the author to
run ordinary prefill again. It now points directly to the remaining human-only
fields and `check_author_gate.py`. The final exact-packet action still keeps the
full safe sequence:

```text
run_preupload_gate.py -> prefill_author_gate.py --apply --overwrite ->
check_author_gate.py -> report_final_blockers.py
```

## Current State

The exact current build and staged PDFs are byte-identical:

```text
paper/venues/acl27/build/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7
```

`check_author_gate.py` still reports `ok=false`, with no missing fields and 19
remaining TODO fields. The remaining TODO rows are human-only: route/deadline,
ARR commitment venue, reviewer commitment, dual submission and preprint status,
public links, OpenReview title/abstract/area/checklist copy, runtime/AI/license
approval, optional media decision, and final upload decision.

The tracked filling guide now mirrors this exact post-prefill state and records
the current staged-PDF SHA-256:

```text
59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7
```

It lists the 19 remaining private worksheet fields by name while preserving the
privacy boundary: the real filled values belong only in the ignored local
worksheet, not in tracked docs or the anonymous submission packet.

`report_final_blockers.py` remains:

```text
status=human_blocked
repo_blockers=[]
human_blockers=[
  author_runtime_ai_media_approval_pending,
  official_openreview_form_copy_pending,
  private_author_gate_incomplete,
  target_route_author_confirmation_pending
]
```

## Verification

Commands run:

```bash
python paper/venues/acl27/scripts/prefill_author_gate.py --apply --overwrite
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/report_final_blockers.py
python -m pytest -q tests/test_acl_final_blockers.py
```

Focused final-blocker tests pass, including the new regression check that an
already-prefilled private worksheet skips the redundant ordinary-prefill
handoff.
